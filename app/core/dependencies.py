from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import oauth2_scheme, verify_token
from ..models import project as project_model # To access Project model
from ..crud import crud_project # To fetch project

async def get_current_project(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db), 
    project_id: int = Path(...) # Use Path to extract project_id from the URL path
) -> project_model.Project:
    """
    Dependency to authenticate and retrieve the current project based on project_id from path
    and Bearer token from Authorization header.
    """
    # Fetch project by ID
    db_project = crud_project.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found.",
        )

    # Verify token
    if not db_project.token_hash: # Project might exist but has no token configured
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Project with ID {project_id} does not have an API token configured.",
            headers={"WWW-Authenticate": "Bearer"}, # Standard header for 401
        )
        
    if not verify_token(plain_token=token, hashed_token=db_project.token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or missing token for project ID {project_id}.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return db_project
