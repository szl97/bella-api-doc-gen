# Bella API Doc Gen Service

English | [中文](./README_CN.md)

Bella API Doc Gen is an API service designed to automatically generate and update OpenAPI 3.0 documentation. It works by fetching a source OpenAPI specification, processing it, and storing the result in a database. Users can track the generation process via a task ID and retrieve the generated OpenAPI JSON through a dedicated API endpoint.

## Features

*   **Project Registration:** Configure projects with specific details including source OpenAPI URL and optional Git credentials for private source repositories.
*   **API-Triggered Generation:** Documentation generation is initiated via a secure API call.
*   **Authentication:** Project-specific operations are protected by Bearer token authentication.
*   **Task-Based Generation:** All document generation processes are handled as asynchronous tasks. A `task_id` is returned for tracking.
*   **Task Status Tracking:** API endpoint to check the status of generation tasks (pending, processing, success, failed) and view results or error messages.
*   **Database Storage:** Generated OpenAPI specifications are stored in the database.
*   **Direct OpenAPI Access:** API endpoint to retrieve the latest successfully generated OpenAPI JSON for a project.
*   **Project Status Tracking:** Monitor the overall state of projects (`init`, `pending`, `active`, `failed`). Generation progress is tracked via tasks.
*   **OpenAPI Spec Diffing:** Identifies changes between the current source spec and the previously generated one to enable targeted processing.
*   **Targeted Description Completion:** Supported by [Code-Aware-RAG](https://github.com/szl97/Code-Aware-RAG)

## Dependencies

### **Code-Aware-RAG** This service is a prerequisite for the targeted description completion feature.

**Project Link:** [Code-Aware-RAG](https://github.com/szl97/Code-Aware-RAG)
**Description:** If you plan to use the description completion feature, please ensure that the Code-Aware-RAG service is running before starting the Bella API documentation generation service.
**Important Note:** About vector database updates:
- If the vector database for a project in the Code-Aware-RAG service does not exist, the system will automatically create it.
- If the vector database for a project in the Code-Aware-RAG service already exists, the system will not force update it.
- If you need to update the vector database (e.g., after major code updates), you need to manually call the `/v1/code-rag/repository/setup` endpoint of the Code-Aware-RAG service and set both `force_reindex` and `force_reclone` parameters to `true`.
- For detailed operation instructions, please refer to the [Code-Aware-RAG project documentation](https://github.com/szl97/Code-Aware-RAG).

### Code-Aware-RAG Usage Instructions
#### Using API:
- Re-index repository for new projects or after major updates:
    - Send a request to POST /v1/code-rag/repository/setup endpoint.
    - Request Header: `Authorization: Bearer {apikey}` (only required in `non-configured apikey mode`)
      Request body example:
      ```json
      {  
        "repo_id": "bella-issues-bot",  
        "repo_url_or_path": "https://github.com/szl97/bella-issues-bot.git",  
        "force_reclone": true,  
        "force_reindex": true  
      }  
      ```
        * This operation runs in the background and immediately returns a task ID.
        * `repo_id` is the unique identifier you specify for this repository.
        * `force_reclone` and `force_reindex` will trigger re-indexing.

- Query repository setup status:
    - Send a request to GET /v1/code-rag/repository/status/{repo_id} endpoint.
    - Request Header: `Authorization: Bearer {apikey}` (only required in `non-configured apikey mode`)
    * Response example:
       ```json
       {
      "repo_id": "bella-issues-bot",
      "status": "completed",  // "pending"(in progress), "completed"(finished), or "failed"(failed)
      "message": "Repository setup process completed", 
      "index_status": "Indexed Successfully",
      "repository_path": "/path/to/repository"
       }
       ```

## API Endpoints

The base URL for all API endpoints is `/v1/api-doc` .

### Authentication

Most project-specific endpoints (PUT, DELETE for projects, and triggering generation) require a Bearer Token to be included in the `Authorization` header:
`Authorization: Bearer <your_project_token>`, expect for GET openapi-docs

This token is defined by you when creating the project and is unique to that project.

### Projects Management (`/v1/api-doc/projects`)

*   **`POST /v1/api-doc/projects`**
    *   **Description:** Registers a new project for documentation generation. An initial documentation generation task is automatically started.
    *   **Request Header:** `Authorization: Bearer {apikey}` (where `{apikey}` is your chosen API key for creating projects, not to be confused with the project-specific bearer token generated upon creation).
    *   **Request Body:**
        *   `name` (string, required): Unique name for the project.
        *   `source_openapi_url` (string, required): URL to fetch the source OpenAPI 3.0 JSON spec. This can be a public URL or a URL to a file in a Git repository.
        *   `git_repo_url` (string, required): This is the URL of that Git repository which is used for pull code.
        *   `git_auth_token` (string, optional): Authentication token (e.g., GitHub PAT) if the `git_repo_url` is private.
    *   **Response (Success: 201 Created):** Details of the created project and a `task_id` for the initial documentation generation.
        ```json
        {
          "project": {
            "id": 1,
            "name": "My Awesome API Project",
            "source_openapi_url": "https://api.example.com/v1/openapi.json",
            "git_repo_url": "https://git.example.com/my/repo.git",
            "created_at": "2025-05-28T12:00:00Z",
            "updated_at": "2025-05-28T12:00:00Z"
          },
          "task_id": "xyz123abc"
        }
        ```
    *   **Request Body Example:**
        ```json
        {
          "name": "My Awesome API Project",
          "source_openapi_url": "https://api.example.com/v1/openapi.json"
        }
        ```
    *   **Request Body Example (Source from Private Git):**
        ```json
        {
          "name": "Project From Private Git",
          "source_openapi_url": "path/to/openapi.json", // Relative path within the cloned repo
          "git_repo_url": "https://github.com/your_username/my-private-spec-repo.git",
          "git_auth_token": "your_github_pat"
        }
        ```

*   **`GET /v1/api-doc/projects`**
    *   **Description:** Lists all registered projects. (Note: This endpoint might be restricted or require admin privileges in a production environment).
    *   **Response:** A list of project details. Sensitive tokens are excluded.

*   **`GET /v1/api-doc/projects/{project_id}`**
    *   **Description:** Get details of a specific project by its ID.
    *   **Response:** Project details. Sensitive tokens are excluded.

*   **`PUT /v1/api-doc/projects/{project_id}`**
    *   **Description:** Updates an existing project's configuration. Requires Bearer token authentication for this project.
    *   **Request Body:** Similar to project creation (name, source_openapi_url, git_repo_url, git_auth_token), all fields optional. Can also include `bearer_token` to update the project's API token.
    *   **Response:** The updated project details.

*   **`DELETE /v1/api-doc/projects/{project_id}`**
    *   **Description:** Deletes a registered project. Requires Bearer token authentication for this project.
    *   **Response:** The details of the deleted project.

### Manual Documentation Generation (`/v1/api-doc/gen`)

*   **`POST /v1/api-doc/gen/{project_id}`**
    *   **Description:** Triggers the documentation generation and processing workflow for a specific project. Requires Bearer token authentication for this project.
    *   **Response (Success: 202 Accepted):** A confirmation message and a `task_id` for tracking the generation process.
        ```json
        {
          "message": "Documentation generation process initiated for project: ExampleProjectName",
          "task_id": "abc789def"
        }
        ```

### Task Management (`/v1/api-doc/tasks`)

*   **`GET /v1/api-doc/tasks/{task_id}`**
    *   **Description:** Retrieves the status and result of a specific documentation generation task.
    *   **Response:** 
        *   `id` (string): The Task ID.
        *   `project_id` (integer): ID of the project this task belongs to.
        *   `status` (string): Current status of the task (e.g., `pending`, `processing`, `success`, `failed`).
        *   `created_at` (datetime): Task creation timestamp.
        *   `updated_at` (datetime): Task last update timestamp.
        *   `result` (string/json, optional): Contains a success message or structured error details upon task completion.
        *   `error_message` (string, optional): Detailed error message if the task failed.
    *   **Example Response (Success):**
        ```json
        {
          "id": "xyz123abc",
          "project_id": 1,
          "status": "success",
          "created_at": "2023-10-28T12:00:00Z",
          "updated_at": "2023-10-28T12:05:00Z",
          "result": "{"message": "OpenAPI documentation generated successfully."}",
          "error_message": null
        }
        ```
    *   **Example Response (Failure):**
        ```json
        {
          "id": "abc789def",
          "project_id": 2,
          "status": "failed",
          "created_at": "2023-10-28T11:00:00Z",
          "updated_at": "2023-10-28T11:01:00Z",
          "result": "{"error": "Failed to fetch OpenAPI spec from source."}",
          "error_message": "HTTPError: 404 Client Error: Not Found for url: https://invalid.url/openapi.json"
        }
        ```

### OpenAPI Document Retrieval (`/v1/api-doc/openapi`)

*   **`GET /v1/api-doc/{project_id}`**
    *   **Description:** Retrieves the latest successfully generated OpenAPI JSON document for the specified project.
    *   **Response:** The OpenAPI JSON document.
    *   **Example Response:**
        ```json
        {
          "openapi": "3.0.0",
          "info": {
            "title": "Sample API",
            "version": "1.0.0"
          },
          "paths": {
            "/items": {
              "get": {
                "summary": "List all items"
              }
            }
          }
        }
        ```

## Project Configuration Fields

*   `name`: (string, required) Unique name for the project.
*   `bearer_token`: (string, required on create/update) The secret token you define for authenticating API requests related to this project. This token is hashed and stored by Bella.
*   `source_openapi_url`: (string, required) URL from which Bella will fetch the source OpenAPI 3.0 JSON specification. Can be a public URL or a path within a Git repository if `git_repo_url` is also provided.
*   `git_repo_url`: (string, optional) URL of the Git repository. Required if `source_openapi_url` points to a resource within a private Git repository that needs to be cloned.
*   `git_auth_token`: (string, optional) Token for Bella to authenticate with the Git repository (e.g., a GitHub Personal Access Token) if it's private.

## Workflow Overview

1.  **Register Project:** Use `POST /v1/api-doc/projects` to register your API project. Provide its `name` and `source_openapi_url`. If the source spec is in a private Git repository, also provide `git_repo_url` and `git_auth_token`. Define a `bearer_token` for securing your project's API interactions with Bella.
2.  **Initial Generation Task:** Upon successful registration, Bella automatically triggers an initial documentation generation task. A `task_id` is returned in the response.
3.  **Track Task Status:** Use `GET /v1/api-doc/tasks/{task_id}` with the received `task_id` to monitor the generation progress (states: `pending` -> `processing` -> `success` or `failed`). The `result` and `error_message` fields provide details on completion.
4.  **Manual Trigger:** To update the documentation later, make a `POST` request to `/v1/api-doc/gen/{project_id}`, authenticating with your project's `bearer_token`. This also returns a `task_id`.
5.  **Fetch Source Spec:** Bella fetches the latest OpenAPI spec from the `source_openapi_url` (using Git credentials if provided for a private repo).
6.  **Fetch Previous Spec (for diffing):** Bella retrieves the last successfully generated OpenAPI specification for this project from its internal database.
7.  **Process Spec:**
    *   Bella Docs calculates the differences between the new source spec and the previous one.
    *   For new or modified parts, it can apply description completion using an LLM.
    *   The changes are then merged into a new version of the specification.
8.  **Store Generated Spec:** The newly processed OpenAPI specification is saved to Bella's database, associated with the project and the completed task.
9.  **Retrieve Generated Spec:** Once the task status is `success`, you can access the latest generated OpenAPI document via `GET /v1/api-doc/openapi/projects/{project_id}/openapi-json`.
10. **Status Updates:** The project's main status (`active`, `failed`) reflects its overall health regarding documentation. Task statuses provide details on individual generation attempts.

## Setup & Running (Basic - Conceptual)

This outlines a basic setup for development or testing. Production deployment would require further consideration for aspects like WSGI servers, containerization, and database management.

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd bella-api-doc-gen # Or your project directory name
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment:**
    *   The application uses Pydantic's `BaseSettings` for configuration, which can load from environment variables or a `.env` file.
    *   Key settings include `DATABASE_URL` (e.g., `sqlite:///./test.db` or `postgresql://user:pass@host:port/dbname`). Refer to `app/core/config.py`.
    *   Create a `.env` file in the project root if you prefer, e.g.:
        ```env
        DATABASE_URL="sqlite:///./bella_doc_gen.db"
        ```
4.  **Initialize Database:**
    *   The application is configured to initialize the database and create tables on startup (via `init_db(engine)` in `app/main.py`). Ensure your database server is running and accessible if using a non-SQLite database.
5.  **Run the Application:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will typically be available at `http://127.0.0.1:8000`.
6. **Start with docker:**
    ```bash
    docker build -t bella-api-doc-gen .
    docker run -d -p 8000:8000 --name bella-api-doc-gen bella-api-doc-gen
    ```

### Database Configuration

The service uses SQLAlchemy and Pydantic settings, allowing database connection configuration through `app/core/config.py` or environment variables.

**MySQL Configuration:**

If you are using a MySQL database, the `DATABASE_URL` should be configured in the following format:

`mysql+mysqlconnector://USER:PASSWORD@HOST:PORT/DATABASE_NAME`

Where:
*   `USER`: Your MySQL username.
*   `PASSWORD`: Your MySQL password.
*   `HOST`: The hostname or IP address of your MySQL server (e.g., `localhost`).
*   `PORT`: The port number for MySQL (default is `3306`).
*   `DATABASE_NAME`: The name of your database.

**Example:**
`mysql+mysqlconnector://bella_user:bella_pass@127.0.0.1:3306/bella_db`

You can set this `DATABASE_URL` in a couple of ways:

1.  **Via Environment Variable (Recommended):**
    Set the `DATABASE_URL` environment variable before running the application:
    ```bash
    export DATABASE_URL="mysql+mysqlconnector://USER:PASSWORD@HOST:PORT/DATABASE_NAME"
    uvicorn app.main:app --reload
    ```
    This is the recommended approach for security and flexibility, especially in production.

2.  **Directly in `app/core/config.py`:**
    You can also hardcode it in the `Settings` class within `app/core/config.py` (though this is less flexible and not recommended for sensitive credentials in production):
    ```python
    # In app/core/config.py
    class Settings(BaseSettings):
        # ... other settings ...
        DATABASE_URL: str = "mysql+mysqlconnector://USER:PASSWORD@HOST:PORT/DATABASE_NAME"
        # ...
    ```

The application is configured by default to use a SQLite database (`sqlite:///./test.db`) if `DATABASE_URL` is not otherwise specified, which is convenient for quick local testing but not suitable for production.
