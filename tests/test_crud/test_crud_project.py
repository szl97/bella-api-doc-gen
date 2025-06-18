import pytest
from fastapi import HTTPException

from app.crud import crud_project
from app.models.project import Project, ProjectStatusEnum
from app.schemas.project import ProjectBase, ProjectUpdate
from app.core.security import hash_token


@pytest.mark.database
class TestCRUDProject:
    """Test cases for project CRUD operations."""

    def test_create_project_success(self, db_session):
        """Test creating a project successfully."""
        project_data = ProjectBase(
            name="test-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git",
            git_auth_token="test-token"
        )
        
        created_project = crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        assert created_project.id is not None
        assert created_project.name == "test-project"
        assert created_project.language == "python"
        assert created_project.status == ProjectStatusEnum.init
        assert created_project.token_hash == hash_token("test-api-key")

    def test_create_project_duplicate_name(self, db_session):
        """Test creating project with duplicate name raises exception."""
        project_data = ProjectBase(
            name="duplicate-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        # Create first project
        crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        # Try to create second project with same name
        with pytest.raises(HTTPException) as exc_info:
            crud_project.create_project(
                db=db_session,
                project=project_data,
                apikey="test-api-key-2"
            )
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail).lower()

    def test_get_project_success(self, db_session):
        """Test retrieving a project by ID."""
        # Create a project first
        project_data = ProjectBase(
            name="get-test-project",
            language="java",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        created_project = crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        # Retrieve the project
        retrieved_project = crud_project.get_project(db_session, created_project.id)
        
        assert retrieved_project is not None
        assert retrieved_project.id == created_project.id
        assert retrieved_project.name == "get-test-project"

    def test_get_project_not_found(self, db_session):
        """Test retrieving non-existent project returns None."""
        project = crud_project.get_project(db_session, 999)
        assert project is None

    def test_get_projects_by_token_hash(self, db_session):
        """Test retrieving projects by token hash."""
        token = "test-token-123"
        token_hash = hash_token(token)
        
        # Create projects with same token
        for i in range(3):
            project_data = ProjectBase(
                name=f"project-{i}",
                language="python",
                source_openapi_url="https://example.com/openapi.json",
                git_repo_url="https://github.com/test/repo.git"
            )
            crud_project.create_project(
                db=db_session,
                project=project_data,
                apikey=token
            )
        
        # Create project with different token
        project_data = ProjectBase(
            name="different-token-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="different-token"
        )
        
        # Retrieve projects by token hash
        projects = crud_project.get_projects_by_token_hash(db_session, token_hash)
        
        assert len(projects) == 3
        for project in projects:
            assert project.token_hash == token_hash

    def test_update_project_success(self, db_session):
        """Test updating a project successfully."""
        # Create a project first
        project_data = ProjectBase(
            name="update-test-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        created_project = crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        # Update the project
        update_data = ProjectUpdate(
            name="updated-project-name",
            language="java",
            status=ProjectStatusEnum.active
        )
        
        updated_project = crud_project.update_project(
            db=db_session,
            project_id=created_project.id,
            project_update=update_data
        )
        
        assert updated_project is not None
        assert updated_project.name == "updated-project-name"
        assert updated_project.language == "java"
        assert updated_project.status == ProjectStatusEnum.active

    def test_update_project_not_found(self, db_session):
        """Test updating non-existent project returns None."""
        update_data = ProjectUpdate(name="not-found-project")
        
        result = crud_project.update_project(
            db=db_session,
            project_id=999,
            project_update=update_data
        )
        
        assert result is None

    def test_delete_project_success(self, db_session):
        """Test deleting a project successfully."""
        # Create a project first
        project_data = ProjectBase(
            name="delete-test-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        created_project = crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        # Delete the project
        deleted_project = crud_project.delete_project(
            db=db_session,
            project_id=created_project.id
        )
        
        assert deleted_project is not None
        assert deleted_project.id == created_project.id
        
        # Verify project is deleted
        retrieved_project = crud_project.get_project(db_session, created_project.id)
        assert retrieved_project is None

    def test_delete_project_not_found(self, db_session):
        """Test deleting non-existent project returns None."""
        result = crud_project.delete_project(db_session, 999)
        assert result is None