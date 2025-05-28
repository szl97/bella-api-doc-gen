import logging

from fastapi import FastAPI

from .api.api_router import api_router  # Import the main API router
from .core.database import engine, init_db  # Import engine and init_db

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize database and create tables
# This should ideally be managed with Alembic for migrations in a production app
logger.info("Initializing database...")
init_db(engine) # Create tables based on models
logger.info("Database initialization complete.")

app = FastAPI(
    title="Bella API Doc Gen",
    description="API for managing projects to automatically generate API documentation.",
    version="0.1.0"
)

# Include the main API router
app.include_router(api_router, prefix="/v1/api-doc") # Prefix all API routes with /v1/api-doc

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "Application is healthy."}
