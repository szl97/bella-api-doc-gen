# Bella API Doc Gen Service

Bella API Doc Gen is an API service designed to automatically generate and update OpenAPI 3.0 documentation. It works by fetching a source OpenAPI specification, optionally processing it (e.g., with an LLM for description enrichment - a future capability), and then dispatching the processed specification via configured callback mechanisms.

## Features

*   **Project Registration:** Configure projects with specific details including source OpenAPI URL, callback type, and credentials for Git or custom APIs.
*   **API-Triggered Generation:** Documentation generation is initiated via a secure API call.
*   **Authentication:** Project-specific operations are protected by Bearer token authentication.
*   **Callback Mechanisms:**
    *   **Push to Git Repository:** Automatically commit and push the generated OpenAPI spec to a specified Git repository.
    *   **Custom API Endpoint:** Send the generated OpenAPI spec to a user-defined API endpoint.
*   **Project Status Tracking:** Monitor the state of projects (`in` `pending`, `active`, `failed`).
*   **(Placeholder) OpenAPI Spec Diffing:** Identifies changes between the current source spec and the previously generated one to enable targeted processing.
*   **(Placeholder) Targeted Description Completion:** Future capability to use LLMs to enrich descriptions for new or modified parts of the API specification.

## API Endpoints

The base URL for all API endpoints is `/v1/api-doc`.

### Authentication

Most project-specific endpoints (PUT, DELETE for projects, and triggering generation) require a Bearer Token to be included in the `Authorization` header:
`Authorization: Bearer <your_project_token>`

This token is defined by you when creating the project and is unique to that project.

### Projects Management (`/projects`)

*   **`POST /projects`**
    *   **Description:** Registers a new project for documentation generation.
    *   **Request Header:** Authorization: `Bearer {apikey}`
    *   **Request Body:**
        *   `name` (string, required): Unique name for the project.
        *   `source_openapi_url` (string, required): URL to fetch the source OpenAPI 3.0 JSON spec.
        *   `callback_type` (string, required): How to dispatch the generated spec. Enum: `push_to_repo` or `custom_api`.
        *   `git_repo_url` (string, optional): URL of the Git repository (required if `callback_type` is `push_to_repo`).
        *   `git_auth_token` (string, optional): Authentication token for the Git repository (e.g., GitHub PAT).
        *   `custom_callback_url` (string, optional): URL for the custom API callback (required if `callback_type` is `custom_api`).
        *   `custom_callback_token` (string, optional): Authentication token for the custom API.
    *   **Response:** Details of the created project, including its ID and initial `pending` status. An initial documentation generation process is triggered asynchronously in the background.

#### Request Body Examples

**Example 1: Project with "Push to Repo" Callback**

```json
{
  "name": "My Awesome API Project",
  "source_openapi_url": "https://api.example.com/v1/openapi.json",
  "callback_type": "push_to_repo",
  "git_repo_url": "https://github.com/your_username/my-awesome-api-docs.git",
  "git_auth_token": "your_github_pat_if_needed_for_private_repo"
}
```

**Example 2: Project with "Custom API" Callback**

```json
{
  "name": "My Other Service Docs",
  "source_openapi_url": "https://my.service.com/api/swagger.json",
  "callback_type": "custom_api",
  "custom_callback_url": "https://my.webhook-receiver.com/api/receive-openapi",
  "custom_callback_token": "optional_token_for_my_webhook_receiver"
}
```

**Field Descriptions (briefly):**

*   `name`: Unique project name.
*   `source_openapi_url`: URL for Bella to fetch your latest OpenAPI spec.
*   `callback_type`: `push_to_repo` or `custom_api`.
*   `git_repo_url`: Required if `callback_type` is `push_to_repo`.
*   `git_auth_token`: Optional, for Bella to auth with your Git repo.
*   `custom_callback_url`: Required if `callback_type` is `custom_api`.
*   `custom_callback_token`: Optional, for Bella to auth with your custom callback API.


*   **`GET /projects`**
    *   **Description:** Lists all registered projects. (Note: This endpoint might be restricted or require admin privileges in a production environment).
    *   **Response:** A list of project details. Sensitive tokens are excluded.

*   **`GET /projects/{project_id}`**
    *   **Description:** Get details of a specific project by its ID.
    *   **Response:** Project details. Sensitive tokens are excluded.

*   **`PUT /projects/{project_id}`**
    *   **Description:** Updates an existing project's configuration. Requires Bearer token authentication for this project.
    *   **Request Body:** Similar to project creation, but all fields are optional. Can also include `bearer_token` to update the project's API token.
    *   **Response:** The updated project details.

*   **`DELETE /projects/{project_id}`**
    *   **Description:** Deletes a registered project. Requires Bearer token authentication for this project.
    *   **Response:** The details of the deleted project.

### Documentation Generation (`/gen`)

*   **`POST /gen/{project_id}`**
    *   **Description:** Triggers the documentation generation and processing workflow for a specific project. Requires Bearer token authentication for this project.
    *   **Response:** `202 Accepted` if the generation process is successfully initiated. The process runs in the background.

## Project Configuration Fields

*   `name`: (string, required) Unique name for the project.
*   `bearer_token`: (string, required on create/update) The secret token you define for authenticating API requests related to this project. This token is hashed and stored by Bella.
*   `source_openapi_url`: (string, required) URL from which Bella will fetch the source OpenAPI 3.0 JSON specification.
*   `callback_type`: (enum, required) Method for dispatching the processed OpenAPI specification.
    *   `push_to_repo`: Bella will commit and push the spec to a Git repository.
    *   `custom_api`: Bella will send the spec via a POST request to a custom API endpoint.
*   `git_repo_url`: (string, optional) URL of the Git repository. Required if `callback_type` is `push_to_repo`.
*   `git_auth_token`: (string, optional) Token for Bella to authenticate with the Git repository (e.g., a GitHub Personal Access Token).
*   `custom_callback_url`: (string, optional) URL for your custom API. Required if `callback_type` is `custom_api`. Bella will `POST` the generated spec to this URL. Bella may also attempt a `GET` request to this URL to fetch the previously generated spec for diffing purposes.
*   `custom_callback_token`: (string, optional) Token for Bella to use when authenticating with your `custom_callback_url`.

## Workflow Overview

1.  **Register Project:** Use `POST /projects` to register your API project. Provide its configuration details, including where to find the source OpenAPI spec (`source_openapi_url`), how you want the processed spec delivered (`callback_type` and related details), and a unique `bearer_token` for securing your project's API interactions with Bella.
2.  **Initial Generation:** Upon successful registration, Bella automatically triggers an initial documentation generation process in the background.
3.  **Manual Trigger:** To update the documentation later, make a `POST` request to `/v1/api-doc/gen-api-doc/{project_id}`, authenticating with your project's `bearer_token`.
4.  **Fetch Source Spec:** Bella fetches the latest OpenAPI spec from the `source_openapi_url` you provided.
5.  **Fetch Previous Spec:** Bella attempts to retrieve the previously generated/stored version of the spec.
    *   If `callback_type` is `push_to_repo`, it looks in the configured Git repository.
    *   If `callback_type` is `custom_api`, it may attempt a `GET` request to your `custom_callback_url`.
6.  **Process Spec (Conceptual):**
    *   Bella (conceptually) calculates the differences between the new source spec and the previous one.
    *   (Future) For new or modified parts, it can apply description completion using an LLM.
    *   (Future) The changes are then merged into a new version of the specification.
    *   (Currently) The fetched source spec is processed as a whole by the placeholder description completion and then sent to the callback.
7.  **Dispatch via Callback:** The newly processed OpenAPI specification is dispatched using your configured `callback_type` (e.g., pushed to your Git repo or sent to your custom API).
8.  **Status Update:** The project's status (`init`, `pending`, `active`, `failed`) is updated to reflect the outcome of the generation process.

## Setup & Running (Basic - Conceptual)

This outlines a basic setup for development or testing. Production deployment would require further consideration for aspects like WSGI servers, containerization, and database management.

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd bella-api-doc-gen
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
