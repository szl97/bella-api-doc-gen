import pytest
from fastapi import status
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestProjectWorkflow:
    """Integration tests for complete project workflows."""

    def test_full_project_lifecycle(self, client, auth_headers):
        """Test complete project lifecycle: create -> update -> generate -> delete."""
        # 1. Create project
        with patch('app.api.endpoints.projects.initiate_doc_generation_process') as mock_generate:
            create_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "lifecycle-test-project",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi.json",
                    "git_repo_url": "https://github.com/test/repo.git",
                    "git_auth_token": "auth-token"
                },
                headers=auth_headers
            )
            
            assert create_response.status_code == status.HTTP_201_CREATED
            project_data = create_response.json()
            project_id = project_data["id"]
            task_id = project_data["task_id"]
            mock_generate.assert_called_once()

        # 2. Check task status
        task_response = client.get(f"/v1/api-doc/tasks/{task_id}")
        assert task_response.status_code == status.HTTP_200_OK
        assert task_response.json()["id"] == task_id

        # 3. Get project details
        get_response = client.get(f"/v1/api-doc/projects/{project_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["name"] == "lifecycle-test-project"

        # 4. Update project
        update_response = client.put(
            f"/v1/api-doc/projects/{project_id}",
            json={
                "name": "updated-lifecycle-project",
                "language": "java"
            },
            headers=auth_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == "updated-lifecycle-project"
        assert update_response.json()["language"] == "java"

        # 5. Trigger manual generation
        with patch('app.api.endpoints.generation.initiate_doc_generation_process') as mock_manual_gen:
            gen_response = client.post(
                f"/v1/api-doc/gen/{project_id}",
                headers=auth_headers
            )
            assert gen_response.status_code == status.HTTP_202_ACCEPTED
            gen_data = gen_response.json()
            assert "task_id" in gen_data
            mock_manual_gen.assert_called_once()

        # 6. List projects (should include our project)
        list_response = client.get("/v1/api-doc/projects/list", headers=auth_headers)
        assert list_response.status_code == status.HTTP_200_OK
        projects = list_response.json()
        project_names = [p["name"] for p in projects]
        assert "updated-lifecycle-project" in project_names

        # 7. Delete project
        delete_response = client.delete(f"/v1/api-doc/projects/{project_id}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_200_OK

        # 8. Verify project is deleted
        get_deleted_response = client.get(f"/v1/api-doc/projects/{project_id}", headers=auth_headers)
        assert get_deleted_response.status_code == status.HTTP_404_NOT_FOUND

    def test_multiple_projects_same_token(self, client, auth_headers):
        """Test managing multiple projects with the same token."""
        project_names = ["multi-project-1", "multi-project-2", "multi-project-3"]
        created_projects = []

        # Create multiple projects
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            for name in project_names:
                response = client.post(
                    "/v1/api-doc/projects/",
                    json={
                        "name": name,
                        "language": "python",
                        "source_openapi_url": f"https://example.com/{name}.json",
                        "git_repo_url": f"https://github.com/test/{name}.git"
                    },
                    headers=auth_headers
                )
                assert response.status_code == status.HTTP_201_CREATED
                created_projects.append(response.json())

        # List all projects
        list_response = client.get("/v1/api-doc/projects/list", headers=auth_headers)
        assert list_response.status_code == status.HTTP_200_OK
        projects = list_response.json()
        
        assert len(projects) >= 3
        retrieved_names = [p["name"] for p in projects]
        for name in project_names:
            assert name in retrieved_names

        # Clean up - delete all created projects
        for project in created_projects:
            delete_response = client.delete(
                f"/v1/api-doc/projects/{project['id']}",
                headers=auth_headers
            )
            assert delete_response.status_code == status.HTTP_200_OK

    def test_project_isolation_between_tokens(self, client):
        """Test that projects are isolated between different tokens."""
        token1_headers = {"Authorization": "Bearer token-1"}
        token2_headers = {"Authorization": "Bearer token-2"}

        # Create project with token 1
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            project1_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "isolation-project-1",
                    "language": "python",
                    "source_openapi_url": "https://example.com/openapi1.json",
                    "git_repo_url": "https://github.com/test/repo1.git"
                },
                headers=token1_headers
            )
            assert project1_response.status_code == status.HTTP_201_CREATED
            project1_id = project1_response.json()["id"]

        # Create project with token 2
        with patch('app.api.endpoints.projects.initiate_doc_generation_process'):
            project2_response = client.post(
                "/v1/api-doc/projects/",
                json={
                    "name": "isolation-project-2",
                    "language": "java",
                    "source_openapi_url": "https://example.com/openapi2.json",
                    "git_repo_url": "https://github.com/test/repo2.git"
                },
                headers=token2_headers
            )
            assert project2_response.status_code == status.HTTP_201_CREATED
            project2_id = project2_response.json()["id"]

        # Token 1 can only see its own project
        list1_response = client.get("/v1/api-doc/projects/list", headers=token1_headers)
        assert list1_response.status_code == status.HTTP_200_OK
        projects1 = list1_response.json()
        project1_names = [p["name"] for p in projects1]
        assert "isolation-project-1" in project1_names
        assert "isolation-project-2" not in project1_names

        # Token 2 can only see its own project
        list2_response = client.get("/v1/api-doc/projects/list", headers=token2_headers)
        assert list2_response.status_code == status.HTTP_200_OK
        projects2 = list2_response.json()
        project2_names = [p["name"] for p in projects2]
        assert "isolation-project-2" in project2_names
        assert "isolation-project-1" not in project2_names

        # Token 1 cannot access project created by token 2
        access_response = client.get(f"/v1/api-doc/projects/{project2_id}", headers=token1_headers)
        assert access_response.status_code == status.HTTP_404_NOT_FOUND

        # Token 2 cannot access project created by token 1
        access_response = client.get(f"/v1/api-doc/projects/{project1_id}", headers=token2_headers)
        assert access_response.status_code == status.HTTP_404_NOT_FOUND