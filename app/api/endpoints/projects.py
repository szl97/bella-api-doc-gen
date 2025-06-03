from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks  # Added BackgroundTasks
from sqlalchemy.orm import Session

from ...core import oauth2_scheme, hash_token
from ...core.database import get_db
from ...core.dependencies import get_current_project  # Import the new dependency
from ...crud import crud_project, crud_task  # Added crud_task
from ...models import project as project_model  # To type hint current_project
from ...schemas.project import ProjectResponse, ProjectUpdate, ProjectBase, ProjectCreationResponse  # Updated import
from ...services.orchestration_service import initiate_doc_generation_process  # Import for background task

router = APIRouter()

@router.post("/", response_model=ProjectCreationResponse, status_code=status.HTTP_201_CREATED) # Changed response_model
def create_project_endpoint(
    project_in: ProjectBase, # Renamed to project_in to avoid confusion with returned project
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    token: str = Depends(oauth2_scheme)
    # No auth for project creation, as token is defined during creation
):
    # The CRUD function already handles the HTTPException for duplicate names
    created_project = crud_project.create_project(db=db, project=project_in, apikey=token)
    
    # Create a new task for this project creation
    db_task = crud_task.create_task(db=db, project_id=created_project.id)
    
    # Trigger initial documentation generation in the background, now passing task_id
    background_tasks.add_task(initiate_doc_generation_process, project_id=created_project.id, apikey=token, task_id=db_task.id)
    
    # Construct and return the ProjectCreationResponse
    # Ensure all fields for ProjectResponse are available from created_project.
    # Pydantic models can be created from ORM objects using `from_orm` if Config.from_attributes = True (which it is for ProjectResponse)
    # Or by spreading the dictionary of the ORM object.
    
    # Create the response object
    response_data = {
        "id": created_project.id,
        "name": created_project.name,
        "language": created_project.language,
        "status": created_project.status,
        "source_openapi_url": created_project.source_openapi_url,
        "git_repo_url": created_project.git_repo_url,
        "created_at": created_project.created_at,
        "updated_at": created_project.updated_at,
        "task_id": db_task.id,
        "message": f"Documentation generation process initiated for project: {created_project.name}"
    }
    return ProjectCreationResponse(**response_data)

@router.get("/list", response_model=list[ProjectResponse])
def list_project_endpoint(
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    token_hash = hash_token(token)
    return crud_project.get_projects_by_token_hash(db, token_hash = token_hash)

@router.get("/{project_id}", response_model=ProjectResponse)
def read_project_endpoint(
    current_project: project_model.Project = Depends(get_current_project),
):
    return current_project

@router.put("/{project_id}", response_model=ProjectResponse) # Changed response_model
def update_project_endpoint(
    project_update_data: ProjectUpdate, 
    current_project: project_model.Project = Depends(get_current_project), # Auth dependency
    db: Session = Depends(get_db) # DB session still needed for update operation
    # project_id is implicitly used by get_current_project from the path
):
    # current_project is the authenticated project instance.
    # We use its id to update, ensuring one can only update the project they authenticated for.
    db_project = crud_project.update_project(db, project_id=current_project.id, project_update=project_update_data)
    if db_project is None: 
        # This case should ideally not be reached if get_current_project succeeded,
        # as it means the project was found. However, keeping for robustness.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found after authentication.")
    return db_project

@router.delete("/{project_id}", response_model=ProjectResponse) # Changed response_model
def delete_project_endpoint(
    current_project: project_model.Project = Depends(get_current_project), 
    db: Session = Depends(get_db) # DB session still needed for delete operation
    # project_id is implicitly used by get_current_project from the path
):
    # current_project is the authenticated project instance.
    db_project = crud_project.delete_project(db, project_id=current_project.id)
    if db_project is None:
        # Similar to PUT, this should ideally not be reached.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found after authentication for deletion.")
    return db_project
