import json
import logging
from typing import Optional, Dict, Any  # Added Any

import httpx  # For making HTTP requests
from sqlalchemy.exc import OperationalError  # Added for the new try-except block

from ..core.database import get_session_scope
from ..crud import crud_project, crud_task, crud_openapi_doc
from ..crud.crud_project import ProjectLockedError  # Import ProjectLockedError
from ..models.project import ProjectStatusEnum, Project as ProjectModel
from ..models.task import TaskStatusEnum
from .des_completion_service import generate_descriptions
from .code_rag_service import setup_code_rag_repository # Added import

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 20

async def fetch_openapi_spec(openapi_api_url: str) -> Optional[Dict]: # Added api_key parameter
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
                logger.error(f"Failed to parse JSON from {openapi_api_url}. Error: {e}. Response text: {response.text[:500]}...")
                return None
        else:
            logger.error(
                f"Failed to fetch OpenAPI spec from {openapi_api_url}. "
                f"Status code: {response.status_code}. Response: {response.text[:500]}..."
            )
            return None
    except httpx.TimeoutException:
        logger.error(f"Timeout occurred while trying to fetch OpenAPI spec from {openapi_api_url} after {REQUEST_TIMEOUT_SECONDS} seconds.")
        return None
    except httpx.RequestError as e:
        logger.error(f"An error occurred during the request to {openapi_api_url}. Error: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching OpenAPI spec from {openapi_api_url}. Error: {e}")
        return None

# Imports for get_previous_spec and the main orchestration logic
# import git # No longer needed for get_previous_spec
from sqlalchemy.orm import Session

# from ..models.project import ProjectStatusEnum, Project as ProjectModel # Already imported
# Removed callback_service import

# Note: httpx, json, logging, Optional, Dict, get_session_scope, crud_project
# are already imported at the top of the file.

async def get_previous_spec(db: Session, project: ProjectModel) -> Optional[Dict[str, Any]]:
    """
    Fetches the latest stored OpenAPI specification for the project from the database.
    """
    logger.info(f"Fetching latest stored OpenAPI spec for project: {project.name} (ID: {project.id})")
    latest_doc = crud_openapi_doc.get_latest_openapi_doc_by_project_id(db, project_id=project.id)
    
    if latest_doc and latest_doc.openapi_spec:
        logger.info(f"Successfully retrieved latest spec (Doc ID: {latest_doc.id}) for project {project.name}.")
        # Assuming openapi_spec is already a dict. If it's a string, json.loads() would be needed.
        # Given it's a JSON type in model, SQLAlchemy should handle this.
        return latest_doc.openapi_spec 
    else:
        logger.info(f"No previous spec found in database for project {project.name}.")
        return None


async def initiate_doc_generation_process(project_id: int, task_id: int, apikey: str): # Added task_id
    """
    Main orchestration function to generate documentation for a project.
    The apikey is the project's API token, potentially used for fetching its own source_openapi_url if protected.
    """
    logger.info(f"Orchestration: Starting for project_id={project_id}, task_id={task_id}")

    with get_session_scope() as db:
        try:
            # Update task status to processing right away
            crud_task.update_task_status(db, task_id=task_id, status=TaskStatusEnum.processing)
            logger.info(f"Task {task_id}: Status updated to processing.")

            try:
                project = crud_project.get_project_for_update(db, project_id=project_id)
            except ProjectLockedError as ple:
                logger.error(f"Failed to acquire lock for project {project_id} during generation process: {ple}")
                crud_task.update_task_status(
                    db,
                    task_id=task_id,
                    status=TaskStatusEnum.failed,
                    error_message=f"Project is locked by another process: {str(ple)}", 
                    result=json.dumps({"error": "Project is currently being processed by another request. Please try again later."})
                )
                return 
            except OperationalError as oe: 
                logger.error(f"Database operational error while fetching project {project_id} for update: {oe}")
                crud_task.update_task_status(
                    db,
                    task_id=task_id,
                    status=TaskStatusEnum.failed,
                    error_message=f"Database operational error: {str(oe)}",
                    result=json.dumps({"error": "A database error occurred while trying to access project details."})
                )
                return 
            except Exception as e: 
                logger.error(f"An unexpected error occurred fetching project {project_id} for update: {e}", exc_info=True)
                crud_task.update_task_status(
                    db,
                    task_id=task_id,
                    status=TaskStatusEnum.failed,
                    error_message=f"Unexpected error fetching project: {str(e)}",
                    result=json.dumps({"error": "An unexpected error occurred while retrieving project details."})
                )
                return 

            if not project:
                logger.error(f"Project with ID {project_id} not found after lock attempt. Cannot initiate documentation generation.")
                crud_task.update_task_status(
                    db,
                    task_id=task_id,
                    status=TaskStatusEnum.failed,
                    error_message=f"Project with ID {project_id} not found.",
                    result=json.dumps({"error": "Project not found."})
                )
                return 

            logger.info(f"Project '{project.name}' (ID: {project.id}) found. Source OpenAPI URL: {project.source_openapi_url}")

            if not project.source_openapi_url:
                error_msg = f"Project '{project.name}' (ID: {project.id}) does not have a Source OpenAPI URL configured."
                logger.error(error_msg)
                crud_task.update_task_status(db, task_id=task_id, status=TaskStatusEnum.failed,
                                             error_message=error_msg, result=json.dumps({"error": "Source OpenAPI URL not configured"}))
                # Also update project status to failed as it's a configuration issue
                crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.failed)
                return

            # Update project status to 'pending' (meaning generation is in progress)
            # This is distinct from task 'processing'. Project 'pending' means "Bella is working on it".
            crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.pending)
            logger.info(f"Project {project.name} status updated to 'pending'.")

            # Fetch User's Source Spec (potentially using the project's API key if the URL is protected)
            openapi_spec_source = await fetch_openapi_spec(project.source_openapi_url)
            if openapi_spec_source is None:
                error_msg = f"Failed to fetch source OpenAPI spec for project '{project.name}' from {project.source_openapi_url}."
                logger.error(error_msg)
                crud_task.update_task_status(db, task_id=task_id, status=TaskStatusEnum.failed,
                                             error_message=error_msg, result=json.dumps({"error": "Failed to fetch source OpenAPI spec"}))
                crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.failed)
                return
            logger.info(f"Task {task_id}: Successfully fetched source OpenAPI spec for project '{project.name}'.")

            # Fetch Bella's Stored/Previous Spec from our DB
            previous_spec = await get_previous_spec(db, project) # This is now from crud_openapi_doc
            if previous_spec is None:
                logger.info(f"Task {task_id}: No previous spec found for project '{project.name}'. Assuming first run or unable to retrieve.")
            else:
                logger.info(f"Task {task_id}: Successfully fetched previous spec for project '{project.name}'.")

            # Perform Real Diff
            from .diff_service import calculate_spec_diff # Import the new diff function
            spec_diff_report = calculate_spec_diff(previous_spec, openapi_spec_source)
            diff_summary = {k: len(v) if isinstance(v, (list, dict)) else v for k, v in spec_diff_report.items()} # Summarize counts
            logger.info(f"Task {task_id}: Spec diff report summary: {diff_summary}")
            logger.debug(f"Task {task_id}: Full spec_diff_report: {spec_diff_report}")


            # Targeted Description Completion (Demo)
            logger.info(f"Task {task_id}: Initiating targeted description completion (demo)...")
            # Conceptual LLM input based on diff (summary of keys/items)
            llm_input_summary = {
                "added_paths": list(spec_diff_report["added_paths"].keys()),
                "modified_paths_new_keys": list(spec_diff_report["modified_paths"].keys()), 
                "added_schemas": list(spec_diff_report["added_components_schemas"].keys()),
                "modified_schemas_new_keys": list(spec_diff_report["modified_components_schemas"].keys()) 
            }
            logger.info(f"Task {task_id}: Conceptual LLM input summary (keys): {llm_input_summary}")

            # Call Code-RAG Service to setup repository
            logger.info(f"Task {task_id}: Initiating Code-RAG repository setup for project '{project.name}'.")
            code_rag_setup_successful = await setup_code_rag_repository(
                project_name=project.name,
                git_repo_url=project.git_repo_url,
                git_auth_token=project.git_auth_token,
                apikey=apikey # This is the project's bearer token passed to initiate_doc_generation_process
            )

            if not code_rag_setup_successful:
                error_msg = f"Task {task_id}: Code-RAG repository setup failed for project '{project.name}'. See previous logs for details."
                logger.error(error_msg)
                # Update task and project status to failed
                crud_task.update_task_status(db, task_id=task_id, status=TaskStatusEnum.failed,
                                             error_message=error_msg, result=json.dumps({"error": "Code-RAG setup failed."}))
                crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.failed)
                return # Exit the generation process

            logger.info(f"Task {task_id}: Code-RAG repository setup successful for project '{project.name}'.")

            # Targeted Description Completion
            logger.info(f"Task {task_id}: Initiating targeted description completion...")
            # spec_diff_report is available from previous steps
            newly_generated_spec = await generate_descriptions(openapi_spec_source=openapi_spec_source, spec_diff_report=spec_diff_report, repo_id=project.name, language=project.language, apikey=apikey)
            logger.info(f"Task {task_id}: Targeted description completion finished.")

            # Merge Changes (Placeholder)
            logger.info(f"Task {task_id}: Merging changes (placeholder)...")
            # Actual merge logic would use spec_diff_report and newly_generated_spec parts.
            # For now, newly_generated_spec (which is currently the full source spec + demo changes) is used.
            final_openapi_spec = newly_generated_spec # This will be saved
            logger.info(f"Task {task_id}: Merging changes (placeholder) complete.")

            # Store the newly generated OpenAPI spec
            crud_openapi_doc.create_openapi_doc(db, project_id=project.id, task_id=task_id, openapi_spec=final_openapi_spec)
            logger.info(f"Task {task_id}: Successfully stored newly generated OpenAPI spec in DB for project {project.id}.")

            # Final Status Updates
            crud_task.update_task_status(db, task_id=task_id, status=TaskStatusEnum.success,
                                         result=json.dumps({"message": "OpenAPI documentation generated and stored successfully."}))
            crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.active) # Project is now active with new doc
            logger.info(f"Task {task_id}: Orchestration completed successfully for project '{project.name}'. Task status 'success', Project status 'active'.")

        except Exception as e:
            # Catch-all for any unexpected errors during the process
            error_msg_detail = f"An unexpected error occurred during documentation generation for project {project_id}, task {task_id}: {str(e)}"
            logger.error(error_msg_detail, exc_info=True) # Log traceback
            
            # Ensure session is active before trying to update task status
            if db.is_active:
                try:
                    crud_task.update_task_status(db, task_id=task_id, status=TaskStatusEnum.failed,
                                                 error_message=error_msg_detail, 
                                                 result=json.dumps({"error": "An unexpected server error occurred.", "details": str(e)}))
                    # Optionally update project status to failed if it's not already
                    if project and project.status != ProjectStatusEnum.failed:
                         crud_project.update_project_status(db, project_id=project.id, status=ProjectStatusEnum.failed)
                except Exception as db_error: # If updating status itself fails
                    logger.error(f"Failed to update task/project status to failed after unexpected error. DB Error: {db_error}", exc_info=True)
            return # Exit function
