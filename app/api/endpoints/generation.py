import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Path as FastAPIPath

from ...models import project as project_model
from ...core.dependencies import get_current_project
from ...services.orchestration_service import initiate_doc_generation_process

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/gen-api-doc/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_generation_endpoint(
    project_id: int = FastAPIPath(..., title="The ID of the project for which to generate documentation"),
    current_project: project_model.Project = Depends(get_current_project), # Handles auth and project retrieval
    background_tasks: BackgroundTasks = BackgroundTasks() # For running the process in the background
):
    """
    Triggers the documentation generation process for the specified project.
    Authentication via Bearer token for the project is required.
    """
    # current_project is the authenticated project instance, project_id from path is already validated by get_current_project
    logger.info(f"Documentation generation manually triggered for project: {current_project.name} (ID: {current_project.id}) via API endpoint.")

    # Add the generation process to background tasks
    # Ensure initiate_doc_generation_process is designed to be called this way (it is async, so it should work)
    background_tasks.add_task(initiate_doc_generation_process, project_id=current_project.id)
    
    return {"message": f"Documentation generation process initiated for project: {current_project.name}"}
