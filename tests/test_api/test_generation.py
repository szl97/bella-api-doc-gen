import pytest
from fastapi import status
from unittest.mock import patch


@pytest.mark.api
class TestGenerationAPI:
    """Test cases for generation API endpoints."""

    def test_trigger_generation_success(self, client, auth_headers):
        """Test triggering documentation generation successfully."""
        # Create a project first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            project_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-gen",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers=auth_headers
            )
        
        project_id = project_response.json()["id"]
        
        # Mock the generation process
        with patch('app.api.endpoints.generation.initiate_doc_generation_process') as mock_generate:
            response = client.post(
                f"/v1/api-doc/gen/{project_id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            assert "message" in data
            assert "task_id" in data
            assert f"project: test-project-gen" in data["message"]
            mock_generate.assert_called_once()

    def test_trigger_generation_project_not_found(self, client, auth_headers):
        """Test triggering generation for non-existent project returns 404."""
        response = client.post(
            "/v1/api-doc/gen/999",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_trigger_generation_no_auth(self, client):
        """Test triggering generation without authentication fails."""
        response = client.post("/v1/api-doc/gen/1")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_trigger_generation_wrong_token(self, client):
        """Test triggering generation with wrong token fails."""
        # Create a project first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            project_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-wrong-token",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers={"Authorization": "Bearer correct-token"}
            )
        
        project_id = project_response.json()["id"]
        
        # Try with wrong token
        response = client.post(
            f"/v1/api-doc/gen/{project_id}",
            headers={"Authorization": "Bearer wrong-token"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND