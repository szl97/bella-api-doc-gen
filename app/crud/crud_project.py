from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.exc import OperationalError  # Added
from sqlalchemy.orm import Session

from ..models.project import Project, ProjectStatusEnum  # Updated import
from ..schemas.project import ProjectBase, ProjectUpdate


# Custom exception for lock errors
class ProjectLockedError(Exception):
    pass

def get_project(db: Session, project_id: int) -> Optional[Project]:
    """
    Retrieves a project by its ID.
    """
    return db.query(Project).filter(Project.id == project_id).first()

def get_project_for_update(db: Session, project_id: int) -> Optional[Project]:
    """
    Retrieves a project by its ID for update, using NOWAIT to avoid blocking.
    Raises ProjectLockedError if the row is locked.
    """
    try:
        # Attempt to import psycopg2 errors for specific lock checking
        try:
            import psycopg2.errors
            LockNotAvailable = psycopg2.errors.LockNotAvailable
        except ImportError:
            LockNotAvailable = None # Fallback if psycopg2 is not available or not the driver

        db_project = db.query(Project).filter(Project.id == project_id).with_for_update(nowait=True).first()
        return db_project
    except OperationalError as e:
        # Check if the error is due to a lock not being available
        # This check might need to be adapted based on the specific database and driver
        if LockNotAvailable and isinstance(e.orig, LockNotAvailable):
            raise ProjectLockedError(f"Project {project_id} is locked by another process.") from e
        # A more generic check (less precise) if specific error type is unknown or not psycopg2
        # For example, some drivers might have a specific SQLSTATE or error code.
        # This part might need adjustment for other DBs like MySQL.
        # If e.g. e.orig has a .pgcode or similar attribute for SQLSTATE '55P03' (lock_not_available for PostgreSQL)
        # elif hasattr(e.orig, 'pgcode') and e.orig.pgcode == '55P03':
        #     raise ProjectLockedError(f"Project {project_id} is locked by another process.") from e
        else:
            # If it's another OperationalError, re-raise it
            raise e

def get_project_by_name(db: Session, name: str) -> Optional[Project]:
    """
    Retrieves a project by its name.
    """
    return db.query(Project).filter(Project.name == name).first()

def get_projects_by_token_hash(db: Session, token_hash: str) -> Optional[list[Project]]:
    """
    Retrieves a list of projects with hash token.
    """
    return db.query(Project).filter(Project.token_hash == token_hash).all()

# Removed get_projects_by_listening_mode as listening_mode field was removed from Project model.

def create_project(db: Session, project: ProjectBase, apikey: str) -> Project:
    """
    Creates a new project.
    - Before saving git_auth_token and custom_api_token, add a comment placeholder like # TODO: Encrypt token before saving.
    - Check if a project with the same name already exists; if so, raise an HTTPException (status_code 400).
    """
    db_project_by_name = get_project_by_name(db, name=project.name)
    if db_project_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project with name '{project.name}' already exists.",
        )

    # TODO: Encrypt token before saving (for git_auth_token) - This is for Bella's access to user's repo
    # TODO: Encrypt token before saving (for custom_api_token) - This is for Bella's callback to user's custom API

    from ..core.security import hash_token
    
    # Hash the provided bearer_token for storing
    hashed_bearer_token = hash_token(apikey)

    # Create the Project instance
    db_project = Project(
        name=project.name,
        token_hash=hashed_bearer_token,
        source_openapi_url=project.source_openapi_url,
        git_repo_url=project.git_repo_url,
        git_auth_token=project.git_auth_token, # TODO: Encrypt token before saving
        status=ProjectStatusEnum.init # Default status on creation
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(db: Session, project_id: int, project_update: ProjectUpdate) -> Optional[Project]:
    """
    Updates an existing project.
    - Similar to creation, add # TODO: Encrypt token if updated for tokens.
    """
    db_project = get_project(db, project_id=project_id)
    if not db_project:
        return None

    update_data = project_update.dict(exclude_unset=True) 
    from ..core.security import hash_token # Import for hashing

    for field_name, value in update_data.items():
        if field_name == "bearer_token" and value is not None:
            db_project.token_hash = hash_token(value) # Hash the new bearer_token
        elif field_name == "git_auth_token" and value is not None:
            # TODO: Encrypt token if updated (for git_auth_token)
            setattr(db_project, field_name, value)
        # Removed handling for custom_callback_token and callback_type
        elif field_name not in ["callback_type", "custom_callback_url", "custom_callback_token"]: # Ensure removed fields are not set
            setattr(db_project, field_name, value)

    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int) -> Optional[Project]:
    """
    Deletes a project.
    """
    db_project = get_project(db, project_id=project_id)
    if not db_project:
        return None
    
    db.delete(db_project)
    db.commit()
    return db_project

def update_project_status(db: Session, project_id: int, status: ProjectStatusEnum) -> Optional[Project]: # Updated enum type
    """
    Updates the status of a project.
    """
    db_project = get_project(db, project_id=project_id)
    if not db_project:
        return None
    
    db_project.status = status
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
