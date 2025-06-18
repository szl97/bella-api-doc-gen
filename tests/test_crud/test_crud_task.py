import pytest

from app.crud import crud_task, crud_project
from app.models.task import TaskStatusEnum
from app.schemas.project import ProjectBase


@pytest.mark.database
class TestCRUDTask:
    """Test cases for task CRUD operations."""

    def test_create_task_success(self, db_session):
        """Test creating a task successfully."""
        # Create a project first
        project_data = ProjectBase(
            name="task-test-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        project = crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        # Create task
        task = crud_task.create_task(db=db_session, project_id=project.id)
        
        assert task.id is not None
        assert task.project_id == project.id
        assert task.status == TaskStatusEnum.pending
        assert task.created_at is not None

    def test_get_task_success(self, db_session):
        """Test retrieving a task by ID."""
        # Create a project first
        project_data = ProjectBase(
            name="get-task-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        project = crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        # Create task
        created_task = crud_task.create_task(db=db_session, project_id=project.id)
        
        # Retrieve task
        retrieved_task = crud_task.get_task(db_session, created_task.id)
        
        assert retrieved_task is not None
        assert retrieved_task.id == created_task.id
        assert retrieved_task.project_id == project.id

    def test_get_task_not_found(self, db_session):
        """Test retrieving non-existent task returns None."""
        task = crud_task.get_task(db_session, 999)
        assert task is None

    def test_update_task_status_success(self, db_session):
        """Test updating task status successfully."""
        # Create a project first
        project_data = ProjectBase(
            name="update-task-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        project = crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        # Create task
        task = crud_task.create_task(db=db_session, project_id=project.id)
        
        # Update task status
        updated_task = crud_task.update_task_status(
            db=db_session,
            task_id=task.id,
            status=TaskStatusEnum.completed,
            result="Task completed successfully"
        )
        
        assert updated_task is not None
        assert updated_task.status == TaskStatusEnum.completed
        assert updated_task.result == "Task completed successfully"
        assert updated_task.updated_at is not None

    def test_update_task_status_with_error(self, db_session):
        """Test updating task status with error message."""
        # Create a project first
        project_data = ProjectBase(
            name="error-task-project",
            language="python",
            source_openapi_url="https://example.com/openapi.json",
            git_repo_url="https://github.com/test/repo.git"
        )
        
        project = crud_project.create_project(
            db=db_session,
            project=project_data,
            apikey="test-api-key"
        )
        
        # Create task
        task = crud_task.create_task(db=db_session, project_id=project.id)
        
        # Update task with error
        updated_task = crud_task.update_task_status(
            db=db_session,
            task_id=task.id,
            status=TaskStatusEnum.failed,
            error_message="Something went wrong"
        )
        
        assert updated_task is not None
        assert updated_task.status == TaskStatusEnum.failed
        assert updated_task.error_message == "Something went wrong"

    def test_update_task_status_not_found(self, db_session):
        """Test updating non-existent task returns None."""
        result = crud_task.update_task_status(
            db=db_session,
            task_id=999,
            status=TaskStatusEnum.completed
        )
        
        assert result is None