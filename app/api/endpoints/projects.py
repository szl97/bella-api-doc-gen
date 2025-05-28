from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path as FastAPIPath, BackgroundTasks # Added BackgroundTasks
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.project import ProjectResponse, ProjectCreate, ProjectUpdate # Changed response model to ProjectResponse
from ...crud import crud_project
from ...models import project as project_model # To type hint current_project
from ...core.dependencies import get_current_project # Import the new dependency
from ...services.orchestration_service import initiate_doc_generation_process # Import for background task

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED) # Changed response_model
def create_project_endpoint(
    project_in: ProjectCreate, # Renamed to project_in to avoid confusion with returned project
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
    # No auth for project creation, as token is defined during creation
):
    # The CRUD function already handles the HTTPException for duplicate names
    created_project = crud_project.create_project(db=db, project=project_in)
    
    # Trigger initial documentation generation in the background
    background_tasks.add_task(initiate_doc_generation_process, project_id=created_project.id)
    
    return created_project

@router.get("/", response_model=List[ProjectResponse]) # Changed response_model
def read_projects_endpoint(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
    # This endpoint could be protected or filtered based on a global admin/user auth in a real app
):
    projects = crud_project.get_projects(db, skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def read_project_endpoint(
    project_id: int = FastAPIPath(..., title="The ID of the project to get"), # Explicitly use FastAPIPath
    db: Session = Depends(get_db)
    # This endpoint could also be protected by get_current_project if desired,
    # or have a simpler auth check if any logged-in user can view any project.
    # For now, keeping it as is, but typically GET would also be protected.
):
    # Note: get_project returns the SQLAlchemy model. FastAPI will map it to ProjectResponse.
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return db_project

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
