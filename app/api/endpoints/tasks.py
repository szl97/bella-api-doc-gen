from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_project
from ...crud import crud_task
from ...models import project as project_model
from ...schemas.task import TaskResponse

router = APIRouter()

@router.get("/{task_id}", response_model=TaskResponse)
def read_task_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    db_task = crud_task.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    return db_task
