from typing import Optional

from sqlalchemy.orm import Session

from ..models.task import Task, TaskStatusEnum


# Forward declaration for TaskCreate schema items (or assume it will exist)
# For now, create_task can just take individual arguments if TaskCreate is not yet defined.
# Alternatively, define a minimal TaskCreate in app/schemas/task.py first.
# Let's proceed by defining what create_task would expect,
# and it can be adapted once app/schemas/task.py is created.

def create_task(db: Session, project_id: int) -> Task:
    db_task = Task(project_id=project_id, status=TaskStatusEnum.pending)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()

def update_task_status(
    db: Session, 
    task_id: int, 
    status: TaskStatusEnum, 
    result: Optional[str] = None, 
    error_message: Optional[str] = None
) -> Optional[Task]:
    db_task = get_task(db, task_id)
    if db_task:
        db_task.status = status
        if result is not None:
            db_task.result = result
        if error_message is not None:
            db_task.error_message = error_message
        db.add(db_task) # Use add for existing objects too, SQLAlchemy handles it
        db.commit()
        db.refresh(db_task)
    return db_task
