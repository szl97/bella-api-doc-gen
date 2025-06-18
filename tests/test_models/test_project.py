import pytest
from datetime import datetime

from app.models.project import Project, ProjectStatusEnum


@pytest.mark.unit
class TestProjectModel:
    """Test cases for Project model."""

    def test_project_creation(self, db_session):
        """Test creating a project model instance."""
        project = Project(
            name="test-project",
            language="python",
            token_hash="hashed_token",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git",
            git_auth_token="auth_token",
            status=ProjectStatusEnum.init
        )
        
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        assert project.id is not None
        assert project.name == "test-project"
        assert project.language == "python"
        assert project.token_hash == "hashed_token"
        assert project.status == ProjectStatusEnum.init
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    def test_project_status_enum_values(self):
        """Test ProjectStatusEnum has correct values."""
        assert ProjectStatusEnum.init == "init"
        assert ProjectStatusEnum.pending == "pending"
        assert ProjectStatusEnum.active == "active"
        assert ProjectStatusEnum.failed == "failed"

    def test_project_repr(self, db_session):
        """Test project string representation."""
        project = Project(
            name="repr-test-project",
            language="java",
            token_hash="hashed_token",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git",
            status=ProjectStatusEnum.active
        )
        
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        repr_str = repr(project)
        assert f"Project(id={project.id}" in repr_str
        assert "name='repr-test-project'" in repr_str
        assert "status='active'" in repr_str

    def test_project_unique_name_constraint(self, db_session):
        """Test that project names must be unique."""
        project1 = Project(
            name="unique-test",
            language="python",
            token_hash="hash1",
            source_openapi_url="https://example.com/openapi1.json",
            git_repo_url="https://github.com/test/repo1.git"
        )
        
        project2 = Project(
            name="unique-test",  # Same name
            language="java",
            token_hash="hash2",
            source_openapi_url="https://example.com/openapi2.json",
            git_repo_url="https://github.com/test/repo2.git"
        )
        
        db_session.add(project1)
        db_session.commit()
        
        db_session.add(project2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    def test_project_default_status(self, db_session):
        """Test that project has default status of init."""
        project = Project(
            name="default-status-test",
            language="python",
            token_hash="hashed_token",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        assert project.status == ProjectStatusEnum.init