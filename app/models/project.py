import enum

from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProjectStatusEnum(str, enum.Enum):
    init = "init"
    pending = "pending"
    active = "active"
    failed = "failed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    
    token_hash = Column(String(128), nullable=False, index=True)
    source_openapi_url = Column(String(512), nullable=False)

    git_repo_url = Column(String(512), nullable=False)
    git_auth_token = Column(String(512), nullable=True)

    status = Column(SQLEnum(ProjectStatusEnum), nullable=False, default=ProjectStatusEnum.init)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status.value}')>"
