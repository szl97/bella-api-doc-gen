from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path as FastAPIPath, BackgroundTasks # Added BackgroundTasks
from sqlalchemy.orm import Session

from ...core import oauth2_scheme
from ...core.database import get_db
from ...schemas.project import ProjectResponse, ProjectUpdate, ProjectBase
from ...crud import crud_project
from ...models import project as project_model # To type hint current_project
from ...core.dependencies import get_current_project # Import the new dependency
from ...services.orchestration_service import initiate_doc_generation_process # Import for background task

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED) # Changed response_model
def create_project_endpoint(
    project_in: ProjectBase, # Renamed to project_in to avoid confusion with returned project
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    token: str = Depends(oauth2_scheme)
    # No auth for project creation, as token is defined during creation
):
    # The CRUD function already handles the HTTPException for duplicate names
    created_project = crud_project.create_project(db=db, project=project_in, apikey=token)
    # Trigger initial documentation generation in the background
    background_tasks.add_task(initiate_doc_generation_process, project_id=created_project.id, apikey= token)
    
    return created_project


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
