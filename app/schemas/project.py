from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..models.project import ProjectStatusEnum


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_openapi_url: str = Field(..., max_length=512, description="URL from which Bella fetches the source OpenAPI spec.")
    
    # Optional fields for git repo
    git_repo_url: str = Field(..., max_length=512, description="URL of the user's Git repository.")
    git_auth_token: Optional[str] = Field(None, max_length=512, description="Token for Bella to access the Git repository. Not returned in API responses.")


class ProjectUpdate(BaseModel): # Using BaseModel for full flexibility, all fields optional
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    source_openapi_url: Optional[str] = Field(None, max_length=512)
    
    git_repo_url: Optional[str] = Field(None, max_length=512)
    git_auth_token: Optional[str] = Field(None, max_length=512, description="Token for Bella to access the Git repository.")
    
    status: Optional[ProjectStatusEnum] = Field(None, description="Project status (e.g., active, failed). Typically system-driven.")
    bearer_token: Optional[str] = Field(None, min_length=10, description="New Bearer token for API authentication for this project. If provided, will be hashed and updated.")

class ProjectResponse(BaseModel): # API response model
    id: int
    name: str
    status: ProjectStatusEnum
    source_openapi_url: str
    git_repo_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        # Sensitive fields like token_hash, bearer_token, git_auth_token, custom_callback_token are excluded
        # because they are not listed as fields in this specific response model.

# This 'Project' schema might be an internal representation or a more detailed one if needed.
# For API responses, ProjectResponse is preferred.
class Project(ProjectBase): 
    id: int
    status: ProjectStatusEnum
    created_at: datetime
    updated_at: datetime
    # This schema would inherit git_auth_token and custom_callback_token from ProjectBase.
    # It's generally better to use ProjectResponse for API outputs.

    class Config:
        from_attributes = True

# Update __all__ to reflect removal of ListeningModeEnum and other changes
__all__ = [
    "ProjectBase",
    "ProjectUpdate",
    "Project",         # General Project schema (includes potentially sensitive inherited fields if not careful)
    "ProjectResponse", # Cleaned response schema
    "ProjectStatusEnum",
]

# In app/schemas/project.py, add this:
class ProjectCreationResponse(ProjectResponse): # Inherits fields from ProjectResponse
    task_id: int
    message: str

# Ensure ProjectCreationResponse is added to __all__ if applicable.
__all__.append("ProjectCreationResponse")
