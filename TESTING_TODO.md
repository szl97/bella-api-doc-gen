# Bella API Doc Gen - Testing TODO

This document outlines the key areas and types of tests that should be implemented for the `bella-api-doc-gen` service to ensure its reliability and correctness.

## 1. API Endpoints (`app/api/endpoints/`)

Testing will primarily use FastAPI's `TestClient`.

### Project CRUD (`projects.py` - `/v1/api-doc/projects`)

*   **`POST /projects` (Project Creation):**
    *   [ ] Test successful project creation with all valid data fields.
    *   [ ] Test validation errors for missing required fields (e.g., `name`, `source_openapi_url`, `bearer_token`, `callback_type`).
    *   [ ] Test validation errors for invalid field formats (e.g., invalid URL).
    *   [ ] Verify that `bearer_token` is correctly hashed and stored as `token_hash` in the database (do not store/return the plain token).
    *   [ ] Verify that the initial project `status` is set to `pending`.
    *   [ ] Verify that `initiate_doc_generation_process` is called asynchronously in the background.
    *   [ ] Test creation fails if a project with the same name already exists (HTTP 400).

*   **`GET /projects` (List Projects):**
    *   [ ] Test successful retrieval of a list of projects.
    *   [ ] Verify that sensitive tokens (`token_hash`, `git_auth_token`, `custom_callback_token`) are excluded from the response.
    *   [ ] Test with an empty database (returns empty list).
    *   [ ] Test pagination (`skip`, `limit`).

*   **`GET /projects/{project_id}` (Get Single Project):**
    *   [ ] Test successful retrieval of a specific project.
    *   [ ] Verify that sensitive tokens are excluded from the response.
    *   [ ] Test HTTP 404 error for a non-existent `project_id`.

*   **`PUT /projects/{project_id}` (Update Project):**
    *   **Authentication (`get_current_project` dependency):**
        *   [ ] Test successful update with a valid Bearer token.
        *   [ ] Test HTTP 401/403 error with an invalid Bearer token.
        *   [ ] Test HTTP 401/403 error with a missing Bearer token.
        *   [ ] Test HTTP 404 error if `project_id` does not exist (even with valid token for another project).
    *   **Field Updates:**
        *   [ ] Test successful update of `name`, `source_openapi_url`, `callback_type`, `git_repo_url`, `custom_callback_url`.
        *   [ ] Test successful update of `git_auth_token` and `custom_callback_token` (verify they are stored, not for hashing).
        *   [ ] Test updating `bearer_token`: verify that `token_hash` in the database is updated.
        *   [ ] Test updating `status` (though this is mainly system-driven, API might allow admin override).
    *   [ ] Test that updating a project with a name that already exists (for a different project) fails if `name` is unique.

*   **`DELETE /projects/{project_id}` (Delete Project):**
    *   **Authentication:**
        *   [ ] Test successful deletion with a valid Bearer token.
        *   [ ] Test HTTP 401/403 error with an invalid/missing Bearer token.
    *   [ ] Verify HTTP 200/204 response on successful deletion.
    *   [ ] Verify that the project is actually removed from the database.
    *   [ ] Test HTTP 404 error when trying to delete a non-existent `project_id`.
    *   [ ] Test that accessing the project via `GET /projects/{project_id}` after deletion results in HTTP 404.

### Documentation Generation Trigger (`generation.py` - `/v1/api-doc/gen-api-doc/{project_id}`)

*   **`POST /gen-api-doc/{project_id}`:**
    *   **Authentication:**
        *   [ ] Test successful trigger with a valid Bearer token for the specified `project_id`.
        *   [ ] Test HTTP 401/403 error with an invalid/missing Bearer token.
        *   [ ] Test HTTP 404 error if `project_id` does not exist.
    *   [ ] Verify HTTP 202 Accepted response on successful initiation.
    *   [ ] Verify that `initiate_doc_generation_process` is called asynchronously in the background with the correct `project_id`.

## 2. Core Services (`app/services/`)

### `orchestration_service.py` (`initiate_doc_generation_process`)

Mock dependencies heavily (database sessions, `fetch_openapi_spec`, `get_previous_spec`, `calculate_spec_diff`, `description_completion_demo`, and callback functions).

*   [ ] Test the complete successful orchestration flow:
    *   Initial status set to `pending`.
    *   Source spec fetched.
    *   Previous spec fetched (or handled if none).
    *   Diff calculated.
    *   Description completion called (with appropriate conceptual input).
    *   Merge logic called (conceptual).
    *   Callback executed successfully.
    *   Final status updated to `active`.
*   [ ] Test handling of first run (no `previous_spec` found).
*   [ ] Test handling of subsequent runs ( `previous_spec` is found).
*   [ ] Test error handling during source spec fetching (`fetch_openapi_spec` fails):
    *   Verify status is set to `failed`.
    *   Verify process terminates gracefully.
*   [ ] Test error handling if `source_openapi_url` is missing on the project.
*   [ ] Test error handling during callback execution (e.g., `push_to_repo_callback` fails):
    *   Verify status is set to `failed`.
*   [ ] Verify correct arguments are passed to mocked service calls.

### `diff_service.py` (`calculate_spec_diff`)

*   [ ] Test with `old_spec` as `None` (all new paths/schemas should be "added").
*   [ ] Test with identical `old_spec` and `new_spec` (no changes reported).
*   [ ] Test with only added paths.
*   [ ] Test with only removed paths.
*   [ ] Test with only modified paths (based on current naive dictionary comparison).
*   [ ] Test with only added component schemas.
*   [ ] Test with only removed component schemas.
*   [ ] Test with only modified component schemas (naive comparison).
*   [ ] Test with a mix of added, removed, and modified paths and schemas.

### `callback_service.py`

*   **`push_to_repo_callback`:**
    *   Mock `git.Repo`, `os.makedirs`, `json.dump`, `Path.exists()`.
    *   [ ] Verify correct local repository path construction.
    *   [ ] Verify correct `.openapi/v3.0/openapi.json` file path and that `json.dump` is called with correct spec.
    *   [ ] Test scenario: repository does not exist locally (clone is called).
        *   Verify `git.Repo.clone_from` is called with correct URL (including auth token if provided).
    *   [ ] Test scenario: repository exists locally (pull is called).
        *   Verify `repo.remotes.origin.pull` is called.
        *   Verify remote URL update logic if token changes.
    *   [ ] Verify `repo.index.add` and `repo.index.commit` are called with correct file and message.
    *   [ ] Verify `origin.push` is called.
    *   [ ] Test handling of `git_auth_token` (presence leads to authenticated URL).
    *   [ ] Test error handling for Git command failures (clone, pull, commit, push).
    *   [ ] Test "no changes detected" scenario.
*   **`custom_api_callback`:**
    *   Mock `httpx.AsyncClient`.
    *   [ ] Verify correct request URL is used (`project.custom_callback_url`).
    *   [ ] Verify correct request body is sent (`{"repo": ..., "openapi": ...}`).
    *   [ ] Verify `Content-Type: application/json` header.
    *   [ ] Test with `custom_callback_token` present (Authorization: Bearer token header).
    *   [ ] Test without `custom_callback_token` (no Authorization header).
    *   [ ] Test successful POST request (2xx response).
    *   [ ] Test handling of HTTP errors (non-2xx responses).
    *   [ ] Test handling of `httpx.TimeoutException` and `httpx.RequestError`.
    *   [ ] Test error if `custom_callback_url` is not set on project.

### `fetch_openapi_spec` (in `orchestration_service.py`)

*   Mock `httpx.AsyncClient`.
*   [ ] Test successful fetching and valid JSON parsing.
*   [ ] Test handling of `httpx.TimeoutException`.
*   [ ] Test handling of `httpx.RequestError`.
*   [ ] Test handling of non-200 HTTP status codes.
*   [ ] Test handling of invalid JSON in response body.

## 3. Authentication & Authorization (`app/core/`)

### `security.py`

*   [ ] Test `hash_token`: ensure it produces a consistent hash for the same input and different for different inputs.
*   [ ] Test `verify_token`:
    *   Test with a correct plain token and its hash.
    *   Test with an incorrect plain token.

### `dependencies.py` (`get_current_project`)

Use a test database session and mock `oauth2_scheme` if needed.
*   [ ] Test successful authentication: valid `project_id` in path, valid token in header, project has `token_hash`.
    *   Verify the correct project object is returned.
*   [ ] Test authentication failure: invalid token.
    *   Verify HTTP 401/403 response.
*   [ ] Test authentication failure: missing token.
    *   Verify HTTP 401/403 response.
*   [ ] Test failure: non-existent `project_id`.
    *   Verify HTTP 404 response.
*   [ ] Test failure: project exists but `token_hash` is `None` or empty in DB.
    *   Verify HTTP 401/403 response.

## 4. Database Operations (`app/crud/crud_project.py`)

Test each function with a dedicated in-memory SQLite database or a test database instance.

*   **`create_project`:**
    *   [ ] Verify project is created with all fields correctly stored.
    *   [ ] Verify `token_hash` is stored (not the plain `bearer_token`).
    *   [ ] Verify default `status` is `pending`.
    *   [ ] Verify default `callback_type` (if applicable, e.g., `push_to_repo`).
    *   [ ] Test constraint: duplicate project name raises error (handled by DB unique constraint, ensure CRUD reflects this).
*   **`get_project`:**
    *   [ ] Test retrieval of an existing project.
    *   [ ] Test returns `None` for non-existent project.
*   **`get_projects`:**
    *   [ ] Test retrieval of multiple projects.
    *   [ ] Test pagination (`skip`, `limit`).
*   **`update_project`:**
    *   [ ] Test updating various fields (`name`, `source_openapi_url`, etc.).
    *   [ ] Test updating `bearer_token` correctly re-hashes and updates `token_hash`.
    *   [ ] Test returns `None` or raises error if project to update does not exist.
*   **`update_project_status`:**
    *   [ ] Test updating the `status` of a project.
    *   [ ] Test returns `None` or raises error if project does not exist.
*   **`delete_project`:**
    *   [ ] Test successful deletion of a project.
    *   [ ] Test returns `None` or raises error if project to delete does not exist.

## General Considerations

*   **Test Database:** Use a separate test database configuration (e.g., in-memory SQLite for speed, or a dedicated test PostgreSQL instance). Ensure proper setup and teardown of the database/tables for each test or test suite.
*   **Mocking:** Utilize `unittest.mock` or `pytest-mock` extensively for external services (GitPython calls, `httpx` requests, future LLM interactions) to isolate unit tests and control external dependencies.
*   **FastAPI `TestClient`:** Leverage `TestClient` for testing API endpoints, which allows making requests to the application without running a live server.
*   **Fixtures (`pytest`):** Use fixtures to set up reusable test data (e.g., sample project data, test database sessions).
*   **Coverage:** Aim for high test coverage across different modules.
*   **Environment Variables:** Ensure tests can run with test-specific configurations (e.g., test database URL) if `.env` files are used.
*   **Asynchronous Code:** Use appropriate testing patterns for `async` functions (e.g., `pytest-asyncio`).
