from fastapi import APIRouter

from .endpoints import openapi_docs as openapi_docs_router  # Import the new openapi_docs router
from .endpoints import projects, generation  # Combined imports
from .endpoints import tasks as tasks_router  # Import the new task router

api_router = APIRouter()

# Include the projects router
# The full path will be /v1/api-doc/projects
api_router.include_router(projects.router, prefix="/projects", tags=["Projects Management"])

# Include the documentation generation router
# The full path for the endpoint will be /v1/api-doc/gen-api-doc/{project_id}
api_router.include_router(generation.router, prefix="", tags=["Documentation Generation"])

# Include the tasks router
# The full path will be /v1/api-doc/tasks
api_router.include_router(tasks_router.router, prefix="/tasks", tags=["Tasks"])

# Include the OpenAPI documents router
# The full path will be /v1/api-doc/openapi
api_router.include_router(openapi_docs_router.router, prefix="/openapi", tags=["OpenAPI Documents"])
