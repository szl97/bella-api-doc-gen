import enum

from sqlalchemy import Column, Integer, Enum as SQLEnum, DateTime, func, TEXT

from .project import Base  # Assuming Base is in project.py or a shared models.base


class TaskStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, nullable=False, index=True)
    status = Column(SQLEnum(TaskStatusEnum), nullable=False, default=TaskStatusEnum.pending)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    # result field can store either a success message or structured error details (JSON as string)
    result = Column(TEXT, nullable=True)
    # error_message is specifically for traceback or simple error strings
    error_message = Column(TEXT, nullable=True)

    def __repr__(self):
        return f"<Task(id={self.id}, project_id={self.project_id}, status='{self.status.value}')>"
