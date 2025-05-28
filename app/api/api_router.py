from fastapi import APIRouter
from .endpoints import projects # Import only projects router

api_router = APIRouter()

# Include the projects router
# The full path will be /v1/api-doc/projects
api_router.include_router(projects.router, prefix="/projects", tags=["Projects Management"])

# Webhook router removed as per instructions.

# Include the documentation generation router
from .endpoints import generation # Ensure this import is active
# The full path for the endpoint will be /v1/api-doc/gen-api-doc/{project_id}
# The router prefix for 'generation.router' should be such that it combines correctly.
# If generation.router's endpoint is "/gen-api-doc/{project_id}", then prefix here should be empty or "/".
# Let's assume generation.router uses "/gen-api-doc/{project_id}" path directly.
api_router.include_router(generation.router, prefix="", tags=["Documentation Generation"])
