from contextlib import contextmanager  # For get_session_scope

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..core.config import settings  # Import settings to use DATABASE_URL

# Define DATABASE_URL using the one from settings
DATABASE_URL = settings.DATABASE_URL

# Adjust engine creation based on database type (SQLite needs different options for FastAPI)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for declarative models will be imported from models
# from ..models import Base

def init_db(engine_to_init):
    # Import Base from models here to avoid circular import issues
    # and ensure models are loaded before creating tables.
    from ..models import Base # Base is defined in models.project
    Base.metadata.create_all(bind=engine_to_init)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_session_scope():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit() # Commit on successful completion of the block
    except Exception:
        db.rollback() # Rollback on any exception within the block
        raise
    finally:
        db.close() # Always close the session
