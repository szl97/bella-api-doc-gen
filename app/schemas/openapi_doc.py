from datetime import datetime
from typing import Dict, Any

from pydantic import BaseModel


class OpenAPIDocBase(BaseModel):
    project_id: int
    task_id: int
    openapi_spec: Dict[str, Any]

class OpenAPIDocResponse(OpenAPIDocBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
