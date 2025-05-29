import logging

from fastapi import APIRouter, Depends, status, BackgroundTasks, Path as FastAPIPath
from sqlalchemy.orm import Session  # Added Session

from ...core import oauth2_scheme
from ...core.database import get_db  # Added get_db
from ...core.dependencies import get_current_project
from ...crud import crud_task  # Added crud_task
from ...models import project as project_model
from ...services.orchestration_service import initiate_doc_generation_process

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/gen/{project_id}", status_code=status.HTTP_202_ACCEPTED) # Response model might need adjustment if not a generic dict
async def trigger_generation_endpoint(
    project_id: int = FastAPIPath(..., title="The ID of the project for which to generate documentation"),
    current_project: project_model.Project = Depends(get_current_project), # Handles auth and project retrieval
    background_tasks: BackgroundTasks = BackgroundTasks(), # For running the process in the background
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db) # Added db session
):
    """
    Triggers the documentation generation process for the specified project.
    Authentication via Bearer token for the project is required.
    Returns the task_id for tracking the generation process.
    """
    # current_project is the authenticated project instance, project_id from path is already validated by get_current_project
    logger.info(f"Documentation generation manually triggered for project: {current_project.name} (ID: {current_project.id}) via API endpoint.")

    # Create a new task for this generation request
    db_task = crud_task.create_task(db=db, project_id=current_project.id)

    # Add the generation process to background tasks, now passing task_id
    background_tasks.add_task(initiate_doc_generation_process, project_id=current_project.id, apikey=token, task_id=db_task.id)
    
    return {"message": f"Documentation generation process initiated for project: {current_project.name}", "task_id": db_task.id}
