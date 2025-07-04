from sqlalchemy import Column, Integer, DateTime, func, JSON

from .project import Base  # Assuming Base is in project.py or a shared models.base


class OpenAPIDoc(Base):
    __tablename__ = "openapi_docs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, nullable=False, index=True)
    task_id = Column(Integer, nullable=False, unique=True, index=True) # Assuming one doc per successful task
    
    # Storing OpenAPI spec as JSON is generally better for querying if DB supports it,
    # otherwise TEXT and handle JSON conversion in application code.
    # Using JSON type if available, fallback to TEXT.
    # For SQLite, JSON type is often emulated as TEXT.
    openapi_spec = Column(JSON, nullable=False) 
    created_at = Column(DateTime, default=func.now(), index=True)

    def __repr__(self):
        return f"<OpenAPIDoc(id={self.id}, project_id={self.project_id}, task_id={self.task_id})>"
