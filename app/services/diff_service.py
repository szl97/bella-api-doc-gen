from typing import Optional, Dict, Any

def calculate_spec_diff(old_spec: Optional[Dict[str, Any]], new_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates a simplified diff between two OpenAPI specifications.
    Focuses on added, removed, and modified paths and component schemas.
    """
    diff_report: Dict[str, Any] = {
        "added_paths": {},
        "removed_paths": {},
        "modified_paths": {},
        "added_components_schemas": {},
        "removed_components_schemas": {},
        "modified_components_schemas": {},
    }

    old_paths = old_spec.get("paths", {}) if old_spec else {}
    new_paths = new_spec.get("paths", {})

    old_schemas = old_spec.get("components", {}).get("schemas", {}) if old_spec else {}
    new_schemas = new_spec.get("components", {}).get("schemas", {})

    # Handle case where old_spec is None (first run)
    if old_spec is None:
        diff_report["added_paths"] = new_paths
        diff_report["added_components_schemas"] = new_schemas
        return diff_report

    # Paths diffing
    for path, path_item in new_paths.items():
        if path not in old_paths:
            diff_report["added_paths"][path] = path_item
        elif old_paths[path] != path_item: # Naive modification check
            diff_report["modified_paths"][path] = {
                "old": old_paths[path],
                "new": path_item,
            }
    
    for path, path_item in old_paths.items():
        if path not in new_paths:
            diff_report["removed_paths"][path] = path_item
    
    # TODO: Implement more granular diff within path items (e.g., per operation, parameters, responses).

    # Component Schemas diffing
    for schema_name, schema_def in new_schemas.items():
        if schema_name not in old_schemas:
            diff_report["added_components_schemas"][schema_name] = schema_def
        elif old_schemas[schema_name] != schema_def: # Naive modification check
            diff_report["modified_components_schemas"][schema_name] = {
                "old": old_schemas[schema_name],
                "new": schema_def,
            }

    for schema_name, schema_def in old_schemas.items():
        if schema_name not in new_schemas:
            diff_report["removed_components_schemas"][schema_name] = schema_def
            
    # TODO: Implement more granular diff for schema properties.
    # TODO: Potentially extend to other components like parameters, responses etc.

    return diff_report
