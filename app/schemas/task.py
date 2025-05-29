from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel

from ..models.task import TaskStatusEnum  # Import the enum from models


class TaskBase(BaseModel):
    project_id: int

class TaskCreate(TaskBase):
    # No extra fields needed for creation beyond what's in TaskBase for now,
    # as status is defaulted in CRUD.
    pass

class TaskResponse(TaskBase):
    id: int
    status: TaskStatusEnum
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None # Assuming result might be JSON
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
