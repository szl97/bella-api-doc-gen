import enum
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProjectStatusEnum(str, enum.Enum):
    init = "init"
    pending = "pending"
    active = "active"
    failed = "failed"

class CallbackTypeEnum(str, enum.Enum):
    push_to_repo = "push_to_repo"
    custom_api = "custom_api"

# ListeningModeEnum is no longer needed and will be removed.

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    
    token_hash = Column(String(128), nullable=False) 
    source_openapi_url = Column(String(512), nullable=False)

    # For 'push_to_repo' callback
    git_repo_url = Column(String(512), nullable=True) 
    git_auth_token = Column(String(512), nullable=True)

    # Callback configuration
    callback_type = Column(SQLEnum(CallbackTypeEnum), nullable=False, default=CallbackTypeEnum.push_to_repo)
    
    # For 'custom_api' callback
    custom_callback_url = Column(String(512), nullable=True)
    custom_callback_token = Column(String(512), nullable=True)

    status = Column(SQLEnum(ProjectStatusEnum), nullable=False, default=ProjectStatusEnum.init)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status.value}')>"
