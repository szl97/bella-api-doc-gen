import logging
import httpx # For making HTTP requests
import json
from typing import Optional, Dict

from .callback_service import push_to_repo_callback, custom_api_callback
from ..core.database import get_session_scope
from ..crud import crud_project

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 20

async def fetch_openapi_spec(openapi_api_url: str) -> Optional[Dict]:
    """
    Fetches the OpenAPI specification from the given URL.
    Returns the parsed JSON content as a dictionary, or None if an error occurs.
    """
    logger.info(f"Attempting to fetch OpenAPI spec from: {openapi_api_url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(openapi_api_url, timeout=REQUEST_TIMEOUT_SECONDS)

        if response.status_code == 200:
            try:
                spec_content = response.json()
                logger.info(f"Successfully fetched and parsed OpenAPI spec from {openapi_api_url}")
                return spec_content
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from {openapi_api_url}. Error: {e}. Response text: {response.text[:500]}...") # Log snippet of text
                return None
        else:
            logger.error(
                f"Failed to fetch OpenAPI spec from {openapi_api_url}. "
                f"Status code: {response.status_code}. Response: {response.text[:500]}..." # Log snippet of text
            )
            return None
    except httpx.TimeoutException:
        logger.error(f"Timeout occurred while trying to fetch OpenAPI spec from {openapi_api_url} after {REQUEST_TIMEOUT_SECONDS} seconds.")
        return None
    except httpx.RequestError as e:
        logger.error(f"An error occurred during the request to {openapi_api_url}. Error: {e}")
        return None
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred while fetching OpenAPI spec from {openapi_api_url}. Error: {e}")
        return None


async def initiate_doc_generation_process(project_id: int):
    """
    Main orchestration function to generate documentation for a project.
    1. Fetches project details.
    2. Fetches the OpenAPI specification.
    3. (Placeholder) Calls description completion and callback logic.
    """
    logger.info(f"Orchestration Service: Starting documentation generation process for project ID: {project_id}")

    with get_session_scope() as db:
        project = crud_project.get_project_for_update(db, project_id=project_id)

    if not project:
        logger.error(f"Project with ID {project_id} not found. Cannot initiate documentation generation.")
        # TODO: Update project status to 'failed' if appropriate
        return

    logger.info(f"Project '{project.name}' (ID: {project.id}) found. Source OpenAPI URL: {project.source_openapi_url}")

    if not project.source_openapi_url:
        logger.error(f"Project '{project.name}' (ID: {project.id}) does not have a Source OpenAPI URL configured. Cannot fetch spec.")
        # TODO: Update project status to 'failed'
        return

    openapi_spec = await fetch_openapi_spec(project.source_openapi_url)

    if openapi_spec is None:
        logger.error(f"Failed to fetch or parse OpenAPI spec for project '{project.name}' (ID: {project.id}) from {project.source_openapi_url}. Stopping process.")
        # TODO: Update project status to 'failed'
        return

# Imports for get_previous_spec and the main orchestration logic
import os 
import git 
from pathlib import Path 
from sqlalchemy.orm import Session 

from ..models.project import ProjectStatusEnum, Project as ProjectModel
from ..core.config import settings 
from . import callback_service # Import the module to access its functions properly
# from .callback_service import push_to_repo_callback, custom_api_callback # Direct imports are also fine

# Note: httpx, json, logging, Optional, Dict, get_session_scope, crud_project
# are already imported at the top of the file.

async def get_previous_spec(db: Session, project: ProjectModel) -> Optional[Dict]:
    """
    Fetches the previously stored/generated OpenAPI specification for the project.
    """
    logger.info(f"Fetching previous spec for project: {project.name} (ID: {project.id})")
    
    if project.callback_type.value == 'push_to_repo':
        project_slug = project.name.lower().replace(" ", "-").replace("_", "-")
        local_repo_path = Path(settings.GIT_REPOS_BASE_PATH) / f"{project.id}_{project_slug}"
        openapi_file_path = local_repo_path / ".openapi" / "v3.0" / "openapi.json"

        if not openapi_file_path.exists():
            logger.info(f"Previous spec file not found at {openapi_file_path} for project {project.name}. This might be the first run.")
            # Attempt to clone/pull repo to see if file exists on remote, as it might be first run for this instance
            try:
                repo_url_with_auth = callback_service._get_repo_url_with_auth(project.git_repo_url, project.git_auth_token)
                if local_repo_path.exists():
                    repo = git.Repo(local_repo_path)
                    origin = repo.remotes.origin
                    if origin.url != repo_url_with_auth: # Update URL if token changed
                        origin.set_url(repo_url_with_auth, origin.url)
                    origin.pull(repo.active_branch.name) # Pull latest
                    logger.info(f"Pulled latest from repo for {project.name} to check for existing spec.")
                else:
                    os.makedirs(local_repo_path.parent, exist_ok=True)
                    git.Repo.clone_from(repo_url_with_auth, str(local_repo_path))
                    logger.info(f"Cloned repo for {project.name} to check for existing spec.")
                
                if not openapi_file_path.exists(): # Check again after clone/pull
                     logger.info(f"Spec file {openapi_file_path} still not found after repo operations.")
                     return None

            except git.exc.GitCommandError as e:
                logger.error(f"Git error while trying to fetch previous spec for {project.name}: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error during Git operation for previous spec of {project.name}: {e}")
                return None

        try:
            with open(openapi_file_path, 'r') as f:
                previous_spec_content = json.load(f)
            logger.info(f"Successfully read previous spec from {openapi_file_path} for project {project.name}.")
            return previous_spec_content
        except FileNotFoundError: # Should be caught by exists() check, but as fallback
            logger.info(f"Previous spec file not found at {openapi_file_path} (after potential pull/clone).")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from previous spec file {openapi_file_path} for project {project.name}. Error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading previous spec file {openapi_file_path} for {project.name}: {e}")
            return None

    elif project.callback_type.value == 'custom_api':
        if not project.custom_callback_url:
            logger.warning(f"Project {project.name} configured for 'custom_api' but no custom_callback_url set. Cannot fetch previous spec.")
            return None
        
        # Assuming the custom_callback_url can also serve GET requests for the current spec
        # This is a simplification; the user's API would need to support this.
        # For now, let's use the same fetch_openapi_spec logic.
        logger.info(f"Attempting to fetch previous spec via custom_callback_url GET for {project.name}: {project.custom_callback_url}")
        # TODO: Add authentication if needed for GET request to custom_callback_url
        # headers = {}
        # if project.custom_callback_token: headers["Authorization"] = f"Bearer {project.custom_callback_token}" (depends on user API)
        return await fetch_openapi_spec(project.custom_callback_url) # Reusing fetch_openapi_spec for simplicity

    else:
        logger.warning(f"Unsupported callback type '{project.callback_type.value}' for fetching previous spec for project {project.name}.")
        return None


async def initiate_doc_generation_process(project_id: int, apikey: str):
    """
    Main orchestration function to generate documentation for a project.
    """

    with get_session_scope() as db:
        project = crud_project.get_project(db, project_id=project_id)

        if not project:
            logger.error(f"Project with ID {project_id} not found. Cannot initiate documentation generation.")
            return

        logger.info(f"Starting orchestration for project: {project.name} (ID: {project.id}). Current status: {project.status.value}")

        if project.status == ProjectStatusEnum.pending:
            logger.warning(f"Project {project.name} (ID: {project.id}) is already in 'pending' state. Reprocessing allowed.")
            return
        
        # 1. Initial Setup & Status Update
        crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.pending)
        logger.info(f"Project {project.name} status updated to 'pending'.")

        # 2. Fetch User's Source Spec
        openapi_spec_source = await fetch_openapi_spec(project.source_openapi_url)
        if openapi_spec_source is None:
            logger.error(f"Failed to fetch source OpenAPI spec for project '{project.name}' from {project.source_openapi_url}.")
            crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.failed)
            logger.info(f"Project {project.name} status updated to 'failed' due to source spec fetch failure.")
            return

        logger.info(f"Successfully fetched source OpenAPI spec for project '{project.name}'.")

        # 3. Fetch Bella's Stored/Previous Spec
        previous_spec = await get_previous_spec(db, project)
        if previous_spec is None:
            logger.info(f"No previous spec found for project '{project.name}'. Assuming first run or unable to retrieve.")
        else:
            logger.info(f"Successfully fetched previous spec for project '{project.name}'.")

        # 4. Perform Diff (Placeholder)
        logger.info("Performing API specification diff (placeholder)...")
        diff_results = {"added": [], "modified": [], "deleted": []}
        if previous_spec is None:
            diff_results["added"] = list(openapi_spec_source.get("paths", {}).keys()) # Simplified
            logger.info(f"Diff (placeholder): All paths considered 'added' as no previous spec found. Count: {len(diff_results['added'])}")
        else:
            # Simplified: assume all current paths are "modified" if previous spec exists
            diff_results["modified"] = list(openapi_spec_source.get("paths", {}).keys()) 
            logger.info(f"Diff (placeholder): All paths considered 'modified' for now. Count: {len(diff_results['modified'])}")
        # logger.info(f"Placeholder diff_results: {diff_results}") # Can be verbose
        
        # 4. Perform Real Diff
        from .diff_service import calculate_spec_diff # Import the new diff function
        spec_diff_report = calculate_spec_diff(previous_spec, openapi_spec_source)
        
        # Log a summary of the diff report
        diff_summary = {
            "added_paths_count": len(spec_diff_report["added_paths"]),
            "removed_paths_count": len(spec_diff_report["removed_paths"]),
            "modified_paths_count": len(spec_diff_report["modified_paths"]),
            "added_components_schemas_count": len(spec_diff_report["added_components_schemas"]),
            "removed_components_schemas_count": len(spec_diff_report["removed_components_schemas"]),
            "modified_components_schemas_count": len(spec_diff_report["modified_components_schemas"]),
        }
        logger.info(f"Spec diff report summary: {diff_summary}")
        # For more detailed logging if needed:
        logger.debug(f"Full spec_diff_report: {spec_diff_report}")


        # 5. Targeted Description Completion (Demo) - Conceptual Update
        logger.info("Initiating targeted description completion (demo)...")
        # Log which parts *would* be sent to the LLM based on spec_diff_report
        llm_input_summary = {
            "added_paths": list(spec_diff_report["added_paths"].keys()),
            "modified_paths_new": {k: v["new"] for k, v in spec_diff_report["modified_paths"].items()}, # Send new versions of modified paths
            "added_schemas": list(spec_diff_report["added_components_schemas"].keys()),
            "modified_schemas_new": {k: v["new"] for k, v in spec_diff_report["modified_components_schemas"].items()} # Send new versions of modified schemas
        }
        logger.info(f"Conceptual LLM input based on diff (summary of keys/items): {llm_input_summary}")
        # logger.debug(f"Conceptual LLM input (full data for modified): {llm_input_summary}") # Could be very verbose

        # TODO: Adapt description_completion_demo to take targeted elements from diff_results
        # For now, it processes the whole source spec.
        processed_elements_spec = await description_completion_demo(openapi_spec_source) # Remains as is for now
        newly_generated_spec = processed_elements_spec # This is a simplification for now
        logger.info("Targeted description completion (demo) finished (still processing full spec).")


        # 6. Merge Changes (Placeholder) - Conceptual Update
        logger.info("Merging changes (placeholder)...")
        # Log that the merge should use spec_diff_report
        logger.info("Merge logic placeholder: Should use spec_diff_report to combine original parts, LLM-enhanced parts, and handle deletions.")
        logger.info(f"  - Retain unchanged paths/schemas from openapi_spec_source.")
        logger.info(f"  - Apply LLM-enhanced descriptions to items identified in spec_diff_report (added/modified).")
        logger.info(f"  - Remove items identified as 'removed' in spec_diff_report from the final spec.")
        # TODO: Implement actual merge logic: take openapi_spec_source, apply LLM changes to "added/modified"
        # sections from spec_diff_report, remove "deleted" sections from spec_diff_report.
        
        # For now, newly_generated_spec remains the result of description_completion_demo (which is openapi_spec_source)
        logger.info("Merging changes (placeholder) complete. Using processed spec (currently full source spec) as final for callback.")

        # 7. Execute Callback
        logger.info(f"Executing callback type '{project.callback_type.value}' for project '{project.name}'...")
        if project.callback_type.value == 'push_to_repo':
            callback_successful = await push_to_repo_callback(project, newly_generated_spec)
        elif project.callback_type.value == 'custom_api':
            callback_successful = await custom_api_callback(project, newly_generated_spec)
        else:
            logger.warning(f"Unknown callback type '{project.callback_type.value}' for project '{project.name}'. No callback executed.")
            callback_successful = False # Explicitly false

        # 8. Final Status Update
        if callback_successful:
            crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.active)
            logger.info(f"Orchestration completed successfully for project '{project.name}'. Status updated to 'active'.")
        else:
            crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.failed)
            logger.error(f"Orchestration failed for project '{project.name}' (callback execution). Status updated to 'failed'.")


async def description_completion_demo(openapi_spec: Dict) -> Dict:
    """
    (Demo) Processes an OpenAPI specification to add or enhance descriptions.
    Currently, this is a placeholder and returns the spec unchanged.
    """
    logger.info("Performing description completion (demo)...")
    # TODO: Replace with actual LLM-based description completion logic.
    # This function would iterate through the spec, find fields needing descriptions
    # (e.g., operations, parameters, schemas) and use an LLM to generate them.
    logger.info("Description completion (demo) complete. Returning spec as is.")
    return openapi_spec
