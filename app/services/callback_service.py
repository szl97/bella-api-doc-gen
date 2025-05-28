import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlparse, urlunparse

import git # GitPython

from ..models import project as project_model # To type hint Project model
from ..core.config import settings

logger = logging.getLogger(__name__)

def _get_repo_url_with_auth(git_repo_url: str, token: Optional[str]) -> str:
    """
    Constructs a Git repository URL with embedded token for HTTPS URLs.
    If token is None or URL is not HTTPS, returns the original URL.
    Example: https://username:token@github.com/user/repo.git
    """
    if not token or not git_repo_url.startswith("https://"):
        return git_repo_url

    parsed_url = urlparse(git_repo_url)
    
    # Check if username is already in the netloc
    if '@' in parsed_url.netloc:
        # If username is present, replace it or add token
        # Example: current_user@host -> token@host or current_user:token@host
        # For simplicity, let's assume the token replaces any existing user/pass
        # A more robust solution would be needed for complex scenarios.
        netloc_parts = parsed_url.netloc.split('@')
        host_part = netloc_parts[-1] # last part is always the host
        # Use the token as the username, or as 'oauth2' for some services if token is the password
        # For GitHub, using the token as password with a dummy username like 'x-access-token' or actual username works.
        # Let's use a common pattern: <token>@host or <user>:<token>@host.
        # If we assume the token is a PAT, it often replaces the password.
        # Let's try a simple username:token pattern. If username is in the project model, use it.
        # For now, using 'oauth2' as username and token as password.
        # Alternative: parsed_url = parsed_url._replace(netloc=f"{token}@{host_part}")
        # This depends on the Git provider.
        # Let's assume the token is a PAT that can act as a password.
        # If project has a username field, it could be used. For now, use 'git' or 'oauth2'.
        new_netloc = f"oauth2:{token}@{host_part}"
    else:
        # No username, prepend "oauth2:token@"
        new_netloc = f"oauth2:{token}@{parsed_url.netloc}"
        
    return urlunparse(parsed_url._replace(netloc=new_netloc))


async def push_to_repo_callback(project: project_model.Project, openapi_spec: Dict) -> bool:
    """
    Handles the 'push_to_repo' callback: writes the OpenAPI spec to the project's Git repository
    and pushes the changes.
    """
    logger.info(f"Initiating 'Push to Repo' callback for project: {project.name} (ID: {project.id})")

    # Define local repository path
    project_slug = project.name.lower().replace(" ", "-").replace("_", "-") # Basic slugification
    local_repo_path = Path(settings.GIT_REPOS_BASE_PATH) / f"{project.id}_{project_slug}"
    
    # Ensure parent directory for local_repo_path exists
    try:
        os.makedirs(local_repo_path.parent, exist_ok=True)
        logger.info(f"Base directory for repos ensured: {local_repo_path.parent}")
    except OSError as e:
        logger.error(f"Error creating base directory {local_repo_path.parent}: {e}")
        return False

    repo_url_with_auth = _get_repo_url_with_auth(project.git_repo_url, project.git_auth_token)
    
    repo: Optional[git.Repo] = None

    try:
        # 1. Clone or Open Repo
        try:
            logger.info(f"Attempting to open existing repository at: {local_repo_path}")
            repo = git.Repo(local_repo_path)
            logger.info(f"Successfully opened existing repository for project {project.name}.")
            
            # Pull latest changes
            # TODO: Add more sophisticated branch handling / configuration
            current_branch = repo.active_branch
            logger.info(f"Current branch: {current_branch.name}. Pulling latest changes from origin/{current_branch.name}...")
            try:
                origin = repo.remotes.origin
                # Ensure remote URL is up-to-date, especially if token changed
                if origin.url != repo_url_with_auth:
                     origin.set_url(repo_url_with_auth, origin.url) # set_url(new_url, old_url)
                     logger.info(f"Updated remote URL for origin to include auth token if necessary.")

                origin.pull(current_branch.name) # Pull specific branch
                logger.info(f"Successfully pulled latest changes for {project.name} on branch {current_branch.name}.")
            except git.exc.GitCommandError as e:
                logger.error(f"Error pulling latest changes for {project.name}: {e}")
                if "conflict" in str(e).lower():
                    logger.error("Merge conflict detected. Manual intervention required. Skipping commit and push.")
                    # TODO: Add conflict notification mechanism
                    return False 
                # Other pull errors might be recoverable or might need specific handling
                # For now, we'll try to proceed but this might fail at push
        
        except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):
            logger.info(f"Repository not found at {local_repo_path} or invalid. Cloning new one for project {project.name}...")
            try:
                repo = git.Repo.clone_from(repo_url_with_auth, str(local_repo_path))
                logger.info(f"Successfully cloned repository for {project.name} from {project.git_repo_url}.")
            except git.exc.GitCommandError as e:
                logger.error(f"Failed to clone repository for {project.name} from {project.git_repo_url}. Error: {e}")
                return False
        
        if repo is None: # Should not happen if logic above is correct
            logger.error(f"Repository object not initialized for project {project.name}.")
            return False

        # 2. Write OpenAPI JSON file
        openapi_dir = local_repo_path / ".openapi" / "v3.0"
        os.makedirs(openapi_dir, exist_ok=True)
        openapi_file_path = openapi_dir / "openapi.json"

        logger.info(f"Writing OpenAPI spec to: {openapi_file_path}")
        try:
            with open(openapi_file_path, 'w') as f:
                json.dump(openapi_spec, f, indent=2)
            logger.info(f"Successfully wrote OpenAPI spec to {openapi_file_path}.")
        except IOError as e:
            logger.error(f"Failed to write OpenAPI spec to {openapi_file_path}. Error: {e}")
            return False

        # 3. Commit and Push
        if repo.is_dirty(untracked_files=True, path=str(openapi_file_path)):
            logger.info(f"Changes detected in {openapi_file_path}. Proceeding with commit and push.")
            repo.index.add([str(openapi_file_path)])
            commit_message = f"Update OpenAPI spec for {project.name} via Bella API Doc Gen"
            try:
                repo.index.commit(commit_message)
                logger.info(f"Successfully committed changes for {project.name} with message: '{commit_message}'.")
            except git.exc.GitCommandError as e: # Can happen if nothing to commit after add (e.g. git config filters)
                 logger.error(f"Failed to commit changes for {project.name}. Error: {e}")
                 return False


            try:
                origin = repo.remotes.origin
                # Ensure remote URL is up-to-date again before push, if not already set in pull
                if origin.url != repo_url_with_auth:
                     origin.set_url(repo_url_with_auth, origin.url)
                
                push_info_list = origin.push()
                
                # Check push results
                # push_info can be a list of PushInfo objects
                # A successful push might have flags like PushInfo.UP_TO_DATE or PushInfo.NEW_HEAD
                # An error might have PushInfo.ERROR set.
                successful_push = True
                for push_info in push_info_list:
                    if push_info.flags & git.remote.PushInfo.ERROR:
                        logger.error(f"Error during push for project {project.name}: {push_info.summary}")
                        successful_push = False
                        break # One error is enough to mark failure
                    elif push_info.flags & git.remote.PushInfo.REJECTED:
                        logger.error(f"Push rejected for project {project.name}: {push_info.summary}")
                        successful_push = False
                        break
                
                if successful_push:
                    logger.info(f"Successfully pushed changes for {project.name} to origin.")
                    return True
                else:
                    logger.error(f"Failed to push changes for {project.name} due to errors or rejections.")
                    return False

            except git.exc.GitCommandError as e:
                logger.error(f"Failed to push changes for {project.name}. Error: {e}")
                return False
        else:
            logger.info(f"No changes detected in {openapi_file_path}. Nothing to commit or push for project {project.name}.")
            return True # Considered success as the file is already up-to-date

    except git.exc.GitCommandError as e:
        logger.error(f"A Git command failed during callback for project {project.name}. Error: {e}")
        return False
    except Exception as e: # Catch-all for any other unexpected errors
        logger.error(f"An unexpected error occurred in push_to_repo_callback for project {project.name}: {e}", exc_info=True)
        return False
    finally:
        # Consider if repo object needs explicit closing if using external resources not managed by GitPython's context
        # For GitPython, typically not needed unless specific resources are manually acquired.
        pass


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

    # Make HTTP POST Request
    # Using httpx which should already be imported if fetch_openapi_spec is in another service file
    # but good practice to ensure imports are where they're used or explicitly managed.
    # For now, assume httpx is available (as it's used in orchestration_service)
    # If this were a standalone file, 'import httpx' would be at the top.
    # Since this file does not use httpx yet, we need to add it.
    import httpx # Added import for httpx

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
                f"Status: {response.status_code}. Response: {response.text[:500]}..." # Log more for errors
            )
            return False
    except httpx.TimeoutException:
        logger.error(
            f"Timeout occurred after {timeout_seconds}s while sending to custom callback for project '{project.name}' (ID: {project.id}) " # Updated log message
            f"at URL: {project.custom_callback_url}" # Updated field name
        )
        return False
    except httpx.RequestError as e:
        logger.error(
            f"HTTP request error for 'Custom API' callback for project '{project.name}' (ID: {project.id}). " # Log message context is fine
            f"URL: {project.custom_callback_url}. Error: {e}" # Updated field name
        )
        return False
    except Exception as e: # Catch any other unexpected errors
        logger.error(
            f"An unexpected error occurred during 'Custom API' callback for project '{project.name}' (ID: {project.id}). Error: {e}",
            exc_info=True
        )
        return False
