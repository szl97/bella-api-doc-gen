import pytest
from fastapi import status
from unittest.mock import patch

from app.models.task import TaskStatusEnum


@pytest.mark.api
class TestTasksAPI:
    """Test cases for tasks API endpoints."""

    def test_get_task_success(self, client, auth_headers, db_session):
        """Test getting task status successfully."""
        # Create a project and task first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            project_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-task",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers=auth_headers
            )
        
        task_id = project_response.json()["task_id"]
        
        response = client.get(f"/v1/api-doc/tasks/{task_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == task_id
        assert "status" in data
        assert "created_at" in data

    def test_get_task_not_found(self, client):
        """Test getting non-existent task returns 404."""
        response = client.get("/v1/api-doc/tasks/999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in response.json()["detail"]

    def test_get_task_no_auth_required(self, client, db_session):
        """Test that getting task status doesn't require authentication."""
        # Create a project and task first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            project_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-task-no-auth",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers={"Authorization": "Bearer test-token"}
            )
        
        task_id = project_response.json()["task_id"]
        
        # Test without auth headers
        response = client.get(f"/v1/api-doc/tasks/{task_id}")
        
        assert response.status_code == status.HTTP_200_OK