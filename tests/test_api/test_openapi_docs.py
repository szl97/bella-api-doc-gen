import pytest
from fastapi import status
from unittest.mock import patch

from app.crud import crud_openapi_doc
from app.models.openapi_doc import OpenAPIDoc


@pytest.mark.api
class TestOpenAPIDocsAPI:
    """Test cases for OpenAPI docs API endpoints."""

    def test_get_latest_openapi_doc_success(self, client, db_session, mock_openapi_spec):
        """Test getting latest OpenAPI document successfully."""
        # Create a project first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            project_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-openapi",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers={"Authorization": "Bearer test-token"}
            )
        
        project_id = project_response.json()["id"]
        
        # Create an OpenAPI document for this project
        openapi_doc = OpenAPIDoc(
            project_id=project_id,
            openapi_spec=mock_openapi_spec,
            version="1.0.0"
        )
        db_session.add(openapi_doc)
        db_session.commit()
        
        response = client.get(f"/v1/api-doc/openapi/{project_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["openapi"] == "3.0.0"
        assert data["info"]["title"] == "Test API"
        assert "/test" in data["paths"]

    def test_get_openapi_doc_not_found(self, client):
        """Test getting OpenAPI document for non-existent project returns 404."""
        response = client.get("/v1/api-doc/openapi/999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No OpenAPI document found" in response.json()["detail"]

    def test_get_openapi_doc_no_auth_required(self, client, db_session, mock_openapi_spec):
        """Test that getting OpenAPI doc doesn't require authentication."""
        # Create a project first
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            project_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "test-project-openapi-no-auth",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git"
                },
                headers={"Authorization": "Bearer test-token"}
            )
        
        project_id = project_response.json()["id"]
        
        # Create an OpenAPI document for this project
        openapi_doc = OpenAPIDoc(
            project_id=project_id,
            openapi_spec=mock_openapi_spec,
            version="1.0.0"
        )
        db_session.add(openapi_doc)
        db_session.commit()
        
        # Test without auth headers
        response = client.get(f"/v1/api-doc/openapi/{project_id}")
        
        assert response.status_code == status.HTTP_200_OK