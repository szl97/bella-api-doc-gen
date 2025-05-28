from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.project import Project, Project as ProjectModel # For ListeningModeEnum
from ..schemas.project import ProjectBase, ProjectUpdate


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """
    Retrieves a project by its ID.
    """
    return db.query(Project).filter(Project.id == project_id).first()

def get_project_for_update(db: Session, project_id: int) -> Optional[Project]:
    """
    Retrieves a project by its ID for update.
    """
    return db.query(Project).filter(Project.id == project_id).with_for_update().first()

def get_project_by_name(db: Session, name: str) -> Optional[Project]:
    """
    Retrieves a project by its name.
    """
    return db.query(Project).filter(Project.name == name).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    """
    Retrieves a list of projects with pagination.
    """
    return db.query(Project).offset(skip).limit(limit).all()

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

    # Create the Project instance with new field names and default status
    db_project = Project(
        name=project.name,
        token_hash=hashed_bearer_token,
        source_openapi_url=project.source_openapi_url, # New field name
        git_repo_url=project.git_repo_url,
        git_auth_token=project.git_auth_token,
        callback_type=project.callback_type,
        custom_callback_url=project.custom_callback_url, # New field name
        custom_callback_token=project.custom_callback_token, # New field name
        status=ProjectModel.status.type.enum_class.init # Default status on creation
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
            # Hash the new bearer_token and update token_hash
            db_project.token_hash = hash_token(value)
            # Do not set the bearer_token field directly on the model if it doesn't exist
        elif field_name == "git_auth_token" and value is not None:
            # TODO: Encrypt token if updated (for git_auth_token)
            setattr(db_project, field_name, value)
        elif field_name == "custom_callback_token" and value is not None: # Updated field name
            # TODO: Encrypt token if updated (for custom_callback_token)
            setattr(db_project, field_name, value)
        else:
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

def update_project_status(db: Session, project_id: int, status: ProjectModel.status.type.enum_class) -> Optional[Project]:
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
