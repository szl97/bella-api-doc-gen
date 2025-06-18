import pytest
from fastapi import status


@pytest.mark.api
class TestHealthAPI:
    """Test cases for health check endpoint."""

    def test_health_check_success(self, client):
        """Test health check endpoint returns success."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
        assert data["message"] == "Application is healthy."

    def test_health_check_no_auth_required(self, client):
        """Test health check doesn't require authentication."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK