import logging
import os
from pathlib import Path
from typing import Dict
import httpx
from . import git_service
from ..models import project as project_model  # To type hint Project model

logger = logging.getLogger(__name__)

def _write_file(file_path: str, content: str or Dict, is_json: bool = False) -> bool:
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 文件内容（字符串或字典）
        is_json: 是否以 JSON 格式写入（如果为 True，content 应为字典）

    Returns:
        是否成功写入
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 写入文件
        if is_json:
            import json
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
        else:
            with open(file_path, 'w') as f:
                f.write(content)

        logger.info(f"Successfully wrote to file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write to file {file_path}: {e}")
        return False


async def push_to_repo_callback(project: project_model.Project, openapi_spec: Dict) -> bool:
    """
    Handles the 'push_to_repo' callback: writes the OpenAPI spec to the project's Git repository
    and pushes the changes.
    
    Uses a temporary directory for Git operations, which is deleted after use.
    """
    logger.info(f"Initiating 'Push to Repo' callback for project: {project.name} (ID: {project.id})")

    temp_dir = git_service.create_temp_dir(prefix=f"bella_git_{project.id}_")
    
    try:
        repo = git_service.clone_repo(
            repo_url=project.git_repo_url,
            target_dir=temp_dir,
            auth_token=project.git_auth_token
        )
        
        if not repo:
            return False

        openapi_dir = Path(temp_dir) / ".openapi" / "v3.0"
        openapi_file_path = openapi_dir / "openapi.json"
        
        if not _write_file(
            file_path=str(openapi_file_path),
            content=openapi_spec,
            is_json=True
        ):
            return False

        if git_service.is_repo_dirty(repo, [".openapi/v3.0/openapi.json"]):
            logger.info(f"Changes detected in {openapi_file_path}. Proceeding with commit and push.")
            
            commit_message = f"Update OpenAPI spec for {project.name} via Bella API Doc Gen"
            
            if git_service.commit_and_push(
                repo=repo,
                file_paths=[str(openapi_file_path)],
                commit_message=commit_message,
                auth_token=project.git_auth_token,
                repo_url=project.git_repo_url
            ):
                return True
            else:
                return False
        else:
            logger.info(f"No changes detected in {openapi_file_path}. Nothing to commit or push for project {project.name}.")
            return True

    except Exception as e:
        logger.error(f"An unexpected error occurred in push_to_repo_callback for project {project.name}: {e}", exc_info=True)
        return False
    finally:
        git_service.clean_temp_dir(temp_dir)


async def custom_api_callback(project: project_model.Project, openapi_spec: Dict) -> bool:
    """
    Handles the 'custom_api' callback: sends the OpenAPI spec to a custom API endpoint.
    """
    logger.info(f"Initiating 'Custom API' callback for project: {project.name} (ID: {project.id})")

    if not project.custom_callback_url: # Updated field name
        logger.error(f"Project '{project.name}' (ID: {project.id}) is configured for 'custom_api' callback, but no custom_callback_url is set. Cannot proceed.")
        return False

    # TODO: Ensure custom_callback_token is securely handled/retrieved (e.g., decrypted if stored encrypted)
    
    # Construct JSON Body
    request_body = {
        "repo": project.git_repo_url,
        "openapi": openapi_spec # Key changed to "openapi" as per subtask description
    }

    # Prepare Headers
    headers = {
        "Content-Type": "application/json"
    }
    if project.custom_callback_token: # Updated field name
        # Assuming Bearer token for now. This could be made configurable if needed.
        headers["Authorization"] = f"Bearer {project.custom_callback_token}"
        logger.info(f"Custom callback token found for project {project.name}. Adding Authorization header.")
    else:
        logger.info(f"No custom callback token found for project {project.name}. Making request without Authorization header.")

    timeout_seconds = 30
    logger.info(f"Sending POST request to custom callback URL: {project.custom_callback_url} for project {project.name}.") # Updated log message

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                project.custom_callback_url, # Updated field name
                json=request_body,
                headers=headers,
                timeout=timeout_seconds
            )

        # Check response status code
        if 200 <= response.status_code < 300:
            logger.info(
                f"'Custom API' callback successful for project '{project.name}' (ID: {project.id}). "
                f"Status: {response.status_code}. Response: {response.text[:200]}..." # Log snippet of response
            )
            return True
        else:
            logger.error(
                f"'Custom API' callback failed for project '{project.name}' (ID: {project.id}). "
                f"Status: {response.status_code}. Response: {response.text[:200]}..." # Log snippet of response
            )
            return False
    except httpx.TimeoutException:
        logger.error(f"Timeout occurred while making custom API callback for project '{project.name}' (ID: {project.id}) after {timeout_seconds} seconds.")
        return False
    except httpx.RequestError as e:
        logger.error(f"An error occurred during the custom API callback request for project '{project.name}' (ID: {project.id}). Error: {e}")
        return False
    except Exception as e: # Catch-all for any other unexpected errors
        logger.error(f"An unexpected error occurred in custom_api_callback for project '{project.name}' (ID: {project.id}): {e}", exc_info=True)
        return False
