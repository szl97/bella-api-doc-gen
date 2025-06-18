import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from app.services import git_service


@pytest.mark.service
class TestGitService:
    """Test cases for Git service."""

    def test_get_repo_url_with_auth_https(self):
        """Test constructing authenticated Git URL for HTTPS."""
        url = "https://github.com/user/repo.git"
        token = "test_token"
        
        result = git_service._get_repo_url_with_auth(url, token)
        
        assert result == "https://oauth2:test_token@github.com/user/repo.git"

    def test_get_repo_url_with_auth_no_token(self):
        """Test URL remains unchanged when no token provided."""
        url = "https://github.com/user/repo.git"
        token = None
        
        result = git_service._get_repo_url_with_auth(url, token)
        
        assert result == url

    def test_get_repo_url_with_auth_ssh(self):
        """Test SSH URL remains unchanged."""
        url = "git@github.com:user/repo.git"
        token = "test_token"
        
        result = git_service._get_repo_url_with_auth(url, token)
        
        assert result == url

    def test_get_repo_url_with_auth_existing_auth(self):
        """Test URL with existing auth gets token replaced."""
        url = "https://user:oldtoken@github.com/user/repo.git"
        token = "new_token"
        
        result = git_service._get_repo_url_with_auth(url, token)
        
        assert result == "https://oauth2:new_token@github.com/user/repo.git"

    def test_create_temp_dir(self):
        """Test creating temporary directory."""
        temp_dir = git_service.create_temp_dir()
        
        try:
            assert temp_dir.startswith("/tmp/")
            assert "git_temp_" in temp_dir
            import os
            assert os.path.exists(temp_dir)
            assert os.path.isdir(temp_dir)
        finally:
            # Clean up
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def test_create_temp_dir_custom_prefix(self):
        """Test creating temporary directory with custom prefix."""
        temp_dir = git_service.create_temp_dir(prefix="custom_prefix_")
        
        try:
            assert "custom_prefix_" in temp_dir
            import os
            assert os.path.exists(temp_dir)
        finally:
            # Clean up
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)