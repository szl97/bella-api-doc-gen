import pytest
from fastapi import status
from unittest.mock import patch, MagicMock

from app.models.project import ProjectStatusEnum


@pytest.mark.api
class TestProjectsAPI:
    """Test cases for projects API endpoints."""

    def test_create_project_success(self, client, mock_project_data, auth_headers):
        """Test successful project creation."""
        with patch('app.api.endpoints.projects.initiate_doc_generation_process') as mock_initiate:
            response = client.post(
                "/v1/api-doc/projects/",
                json=mock_project_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["name"] == mock_project_data["name"]
            assert data["language"] == mock_project_data["language"]
            assert data["status"] == ProjectStatusEnum.init.value
            assert "task_id" in data
            assert "message" in data
            mock_initiate.assert_called_once()

    def test_create_project_duplicate_name(self, client, mock_project_data, auth_headers):
        """Test creating project with duplicate name fails."""
        # Create first project
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            client.post(
                "/v1/api-doc/projects/",
                json=mock_project_data,
                headers=auth_headers
            )
            
            # Try to create another with same name
            response = client.post(
                "/v1/api-doc/projects/",
                json=mock_project_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_project_missing_auth(self, client, mock_project_data):
        """Test creating project without authentication fails."""
        response = client.post(
            "/v1/api-doc/projects/",
            json=mock_project_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_projects_success(self, client, auth_headers, db_session):
        """Test listing projects successfully."""
        # Create a project first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-1",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers=auth_headers
            )
        
        response = client.get("/v1/api-doc/projects/list", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "test-project-1"

    def test_list_projects_no_auth(self, client):
        """Test listing projects without authentication fails."""
        response = client.get("/v1/api-doc/projects/list")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_project_success(self, client, auth_headers):
        """Test getting specific project successfully."""
        # Create a project first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            create_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-get",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers=auth_headers
            )
        
        project_id = create_response.json()["id"]
        
        response = client.get(f"/v1/api-doc/projects/{project_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "test-project-get"

    def test_get_project_not_found(self, client, auth_headers):
        """Test getting non-existent project returns 404."""
        response = client.get("/v1/api-doc/projects/999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_project_success(self, client, auth_headers):
        """Test updating project successfully."""
        # Create a project first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            create_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-update",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers=auth_headers
            )
        
        project_id = create_response.json()["id"]
        
        update_data = {
            "name": "updated-project-name",
            "language": "java"
        }
        
        response = client.put(
            f"/v1/api-doc/projects/{project_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "updated-project-name"
        assert data["language"] == "java"

    def test_delete_project_success(self, client, auth_headers):
        """Test deleting project successfully."""
        # Create a project first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            create_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-delete",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers=auth_headers
            )
        
        project_id = create_response.json()["id"]
        
        response = client.delete(f"/v1/api-doc/projects/{project_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify project is deleted
        get_response = client.get(f"/v1/api-doc/projects/{project_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND