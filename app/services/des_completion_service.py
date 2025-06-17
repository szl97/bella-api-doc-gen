import copy
import logging
from typing import Dict, Any, List, Set

from .code_rag_service import call_code_rag

logger = logging.getLogger(__name__)

def _extract_schema_references(element: Any, current_schemas: Set[str]) -> None:
    """
    Recursively traverses an OpenAPI element and extracts schema references.
    A schema reference is a dict with a '$ref' key whose value starts with '#/components/schemas/'.
    """
    if isinstance(element, dict):
        if '$ref' in element and isinstance(element['$ref'], str) and element['$ref'].startswith('#/components/schemas/'):
            schema_name = element['$ref'].split('/')[-1]
            current_schemas.add(schema_name)
        for key, value in element.items():
            _extract_schema_references(value, current_schemas)
    elif isinstance(element, list):
        for item in element:
            _extract_schema_references(item, current_schemas)

def group_openapi_paths(openapi_paths: Dict[str, Any], openapi_components_schemas: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Groups OpenAPI paths by their prefix (e.g., /v1/users) and identifies all schemas
    referenced within each group. Each group contains at most 10 paths.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}

    for path_string, path_item_object in openapi_paths.items():
        parts = path_string.strip('/').split('/')
        if len(parts) >= 2:
            # Group by the first two segments, e.g., /v1/users
            group_key = f"/{parts[0]}/{parts[1]}"
        elif len(parts) == 1 and parts[0] != "":
            # Group by the first segment if only one, e.g., /health
            group_key = f"/{parts[0]}"
        else:
            # Default group for paths like "/" or if something is unexpected
            group_key = "/default_group"

        if group_key not in groups:
            groups[group_key] = []

        # Check if we need to create a new subgroup (if the current one has 10 paths already)
        current_group_idx = 0
        if len(groups[group_key]) > 0:
            current_group_idx = len(groups[group_key]) - 1
            if len(groups[group_key][current_group_idx]['paths']) >= 10:
                # Create a new subgroup
                groups[group_key].append({'paths': {}, 'schema_names': set()})
                current_group_idx += 1
        else:
            # First subgroup for this prefix
            groups[group_key].append({'paths': {}, 'schema_names': set()})

        # Add the path to the current subgroup
        groups[group_key][current_group_idx]['paths'][path_string] = path_item_object

        # Extract schema references from the current path_item_object
        _extract_schema_references(path_item_object, groups[group_key][current_group_idx]['schema_names'])

    # Convert groups dictionary to the desired list format
    result_list: List[Dict[str, Any]] = []
    for group_prefix, subgroups in groups.items():
        for i, subgroup in enumerate(subgroups):
            # Create a unique group prefix for each subgroup
            unique_group_prefix = f"{group_prefix}" if i == 0 else f"{group_prefix}_part{i+1}"
            result_list.append({
                'group_prefix': unique_group_prefix,
                'paths': subgroup['paths'],
                'schema_names': subgroup['schema_names']
            })

    return result_list

async def generate_descriptions(openapi_spec_source: Dict[str, Any], spec_diff_report: Dict[str, Any], repo_id: str, language: str, apikey: str) -> Dict[str, Any]:
    """
    Generates descriptions for added/modified paths in an OpenAPI specification
    by calling a Code RAG service.
    """
    # Logger is already initialized at the module level
    # global logger

    updated_spec = copy.deepcopy(openapi_spec_source)
    paths_to_process: Dict[str, Any] = {}

    for path_key, path_item in spec_diff_report.get('added_paths', {}).items():
        paths_to_process[path_key] = path_item

    for path_key, diff_item in spec_diff_report.get('modified_paths', {}).items():
        if 'new' in diff_item: # 'new' contains the new path_item_object
            paths_to_process[path_key] = diff_item['new']
        else: # Fallback if 'new' is not present, though it should be for modified_paths
            paths_to_process[path_key] = diff_item

    if not paths_to_process:
        logger.info("No added or modified paths found in the diff report. No descriptions to generate.")
        return updated_spec

    # Ensure components and schemas structures exist before calling group_openapi_paths
    components = updated_spec.get('components', {})
    schemas = components.get('schemas', {})

    raw_groups = group_openapi_paths(paths_to_process, schemas)

    if not raw_groups:
        logger.info("No path groups were formed from the paths_to_process. Nothing to send to RAG.")
        return updated_spec

    batched_api_calls: List[Dict[str, Any]] = []
    current_call_paths: Dict[str, Any] = {}
    current_call_schema_names: Set[str] = set()

    # Ensure basic OpenAPI structure for partial_spec_for_rag
    base_partial_spec = {
        "openapi": updated_spec.get("openapi", "3.0.0"), # Default to 3.0.0 if not present
        "info": updated_spec.get("info", {"title": "Partial API", "version": "1.0.0"}), # Provide default info
        "paths": {},
        "components": {"schemas": {}}
    }


    for group in raw_groups:
        current_call_paths.update(group.get('paths', {}))
        current_call_schema_names.update(group.get('schema_names', set()))

        partial_spec_for_rag = copy.deepcopy(base_partial_spec)
        partial_spec_for_rag["paths"] = current_call_paths
        # Filter only relevant schemas for the current batch
        relevant_schemas = {s_name: schemas[s_name] for s_name in current_call_schema_names if s_name in schemas}
        partial_spec_for_rag["components"]["schemas"] = relevant_schemas

        batched_api_calls.append(partial_spec_for_rag)

        current_call_paths = {}
        current_call_schema_names = set()


    # Add any remaining paths as the last batch
    if current_call_paths:
        partial_spec_for_rag = copy.deepcopy(base_partial_spec)
        partial_spec_for_rag["paths"] = current_call_paths
        relevant_schemas = {s_name: schemas[s_name] for s_name in current_call_schema_names if s_name in schemas}
        partial_spec_for_rag["components"]["schemas"] = relevant_schemas
        batched_api_calls.append(partial_spec_for_rag)

    if not batched_api_calls:
        logger.info("No batches were created to call the RAG service.")
        return updated_spec

    for partial_spec_input in batched_api_calls:
        num_paths_in_batch = len(partial_spec_input.get('paths', {}))
        if num_paths_in_batch == 0:
            logger.info("Skipping an empty batch.")
            continue

        logger.info(f"Calling code-rag service for a batch of {num_paths_in_batch} paths.")

        processed_chunk = await call_code_rag(partial_openapi_spec=partial_spec_input, repo_id=repo_id, language=language, apikey=apikey)

        if processed_chunk:
            logger.info(f"Successfully received processed chunk for {num_paths_in_batch} paths. Merging paths and schemas.")

            # Merge paths
            if 'paths' in processed_chunk:
                updated_spec.setdefault('paths', {}).update(processed_chunk['paths'])

            # Merge schemas
            if 'components' in processed_chunk and 'schemas' in processed_chunk['components']:
                updated_spec.setdefault('components', {}).setdefault('schemas', {}).update(processed_chunk['components']['schemas'])
        else:
            logger.warning(f"Failed to process a batch of {num_paths_in_batch} paths. Descriptions for this batch will be missing.")
            logger.error(f"Failed Json is {partial_spec_input}")


    return updated_spec
