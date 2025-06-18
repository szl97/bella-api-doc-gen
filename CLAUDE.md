# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with required settings:
# DATABASE_URL, CODE_RAG_SERVICE_URL, GIT_REPOS_BASE_PATH
```

### Docker Operations
```bash
# Build image
docker build -t bella-api-doc-gen .

# Run container
docker run -d -p 8000:8000 bella-api-doc-gen
```

## Architecture Overview

This is a **FastAPI-based API documentation generation service** that automatically enhances OpenAPI 3.0 specifications with intelligent descriptions using a Code-Aware RAG system.

### Core Architecture Pattern
The service follows a **layered architecture**:
- **API Layer** (`app/api/`): FastAPI routers and endpoints
- **Service Layer** (`app/services/`): Business logic and orchestration
- **Data Layer** (`app/crud/`, `app/models/`): Database operations and SQLAlchemy models
- **Schema Layer** (`app/schemas/`): Pydantic models for request/response validation

### Key Components

#### Orchestration Service (`app/services/orchestration_service.py`)
Central orchestrator that coordinates the entire documentation generation workflow:
- Fetches OpenAPI specs from URLs or Git repositories
- Processes and compares specs for changes
- Coordinates with external Code-RAG service
- Manages async task execution

#### Code-RAG Integration (`app/services/code_rag_service.py`)
Handles integration with external Code-Aware-RAG service:
- Repository setup in RAG system
- Intelligent description generation queries
- Chinese language prompt engineering
- Multi-language framework support (Spring, FastAPI, Node.js)

#### Database Models
Three core entities with relationships:
- **Project**: Git repo configuration and OpenAPI source URLs
- **Task**: Async operation tracking with status/progress
- **OpenAPIDoc**: Generated documentation storage with versioning

### External Dependencies
- **Code-Aware-RAG Service**: Must be running at `CODE_RAG_SERVICE_URL` for description enhancement
- **Git Repositories**: Cloned to `GIT_REPOS_BASE_PATH` for code analysis
- **Database**: SQLite (dev) or MySQL (prod) via `DATABASE_URL`

### API Structure
All endpoints prefixed with `/v1/api-doc`:
- `/projects` - Project CRUD operations with bearer token auth
- `/gen/{project_id}` - Trigger async documentation generation
- `/tasks/{task_id}` - Track generation task progress
- `/openapi/{project_id}` - Retrieve generated OpenAPI specs

### Configuration Management
Environment-based configuration via `app/core/config.py` using Pydantic Settings:
- Supports `.env` files
- Database connection strings
- External service URLs
- File system paths

## Important Implementation Notes

### Async Task Pattern
All generation operations are asynchronous with task tracking. When implementing new features:
1. Create task record with `pending` status
2. Execute operation asynchronously
3. Update task status (`in_progress` → `completed`/`failed`)
4. Store results in appropriate tables

### Chinese Language Context
The RAG integration is specifically designed for Chinese API documentation generation. Prompts and responses are in Chinese, which should be considered when modifying `code_rag_service.py`.

### Security Considerations
- Bearer token authentication required for project operations
- Git credentials stored for private repository access
- Database URL and service URLs configured via environment variables

### Database Initialization
Tables are auto-created on startup via `init_db()` in `main.py`. In production, this should be replaced with proper Alembic migrations.