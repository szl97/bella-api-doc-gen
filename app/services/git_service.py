import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse, urlunparse

import git

logger = logging.getLogger(__name__)


def get_repo_url_with_auth(git_repo_url: str, token: Optional[str]) -> str:
    """
    构造带有认证信息的 Git 仓库 URL（针对 HTTPS URL）
    如果 token 为 None 或 URL 不是 HTTPS，则返回原始 URL
    示例: https://username:token@github.com/user/repo.git
    """
    if not token or not git_repo_url.startswith("https://"):
        return git_repo_url

    parsed_url = urlparse(git_repo_url)
    
    # 检查用户名是否已经在 netloc 中
    if '@' in parsed_url.netloc:
        # 如果用户名存在，替换或添加 token
        netloc_parts = parsed_url.netloc.split('@')
        host_part = netloc_parts[-1]  # 最后一部分始终是主机
        new_netloc = f"oauth2:{token}@{host_part}"
    else:
        # 没有用户名，添加 "oauth2:token@"
        new_netloc = f"oauth2:{token}@{parsed_url.netloc}"
        
    return urlunparse(parsed_url._replace(netloc=new_netloc))


def create_temp_dir(prefix: str = "git_temp_") -> str:
    """
    创建临时目录用于 Git 操作
    
    Args:
        prefix: 临时目录名称前缀
        
    Returns:
        临时目录的路径
    """
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    logger.info(f"Created temporary directory for Git operations: {temp_dir}")
    return temp_dir


def clean_temp_dir(temp_dir: str) -> bool:
    """
    清理临时目录
    
    Args:
        temp_dir: 要清理的临时目录路径
        
    Returns:
        是否成功清理
    """
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
            return True
        return True  # 如果目录不存在，也视为清理成功
    except Exception as e:
        logger.error(f"Failed to clean up temporary directory {temp_dir}: {e}")
        return False


def clone_repo(repo_url: str, target_dir: str, auth_token: Optional[str] = None) -> Optional[git.Repo]:
    """
    克隆仓库到指定目录
    
    Args:
        repo_url: 仓库 URL
        target_dir: 目标目录
        auth_token: 认证令牌（可选）
        
    Returns:
        Git 仓库对象，如果失败则返回 None
    """
    try:
        # 添加认证信息到 URL
        repo_url_with_auth = get_repo_url_with_auth(repo_url, auth_token)
        
        logger.info(f"Cloning repository from {repo_url} to {target_dir}...")
        repo = git.Repo.clone_from(repo_url_with_auth, target_dir)
        logger.info(f"Successfully cloned repository from {repo_url}.")
        return repo
    except git.exc.GitCommandError as e:
        logger.error(f"Failed to clone repository from {repo_url}. Error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during repository clone: {e}")
        return None


def pull_repo(repo: git.Repo, branch: str = None, auth_token: Optional[str] = None, repo_url: Optional[str] = None) -> bool:
    """
    从远程拉取最新更改
    
    Args:
        repo: Git 仓库对象
        branch: 要拉取的分支（如果为 None，则使用当前分支）
        auth_token: 认证令牌（可选）
        repo_url: 仓库 URL（可选，用于更新远程 URL 的认证信息）
        
    Returns:
        是否成功拉取
    """
    try:
        if not branch:
            branch = repo.active_branch.name
            
        origin = repo.remotes.origin
        
        # 如果提供了 repo_url 和 auth_token，确保远程 URL 包含认证信息
        if repo_url and auth_token:
            repo_url_with_auth = get_repo_url_with_auth(repo_url, auth_token)
            if origin.url != repo_url_with_auth:
                origin.set_url(repo_url_with_auth, origin.url)
                logger.info("Updated remote URL to include auth token.")
                
        logger.info(f"Pulling latest changes from branch {branch}...")
        pull_info = origin.pull(branch)
        
        # 检查拉取结果
        for info in pull_info:
            if info.flags & git.remote.FetchInfo.ERROR:
                logger.error(f"Error during pull: {info.note}")
                return False
                
        logger.info(f"Successfully pulled latest changes from branch {branch}.")
        return True
    except git.exc.GitCommandError as e:
        logger.error(f"Failed to pull latest changes. Error: {e}")
        # 检查是否有合并冲突
        if "conflict" in str(e).lower():
            logger.error("Merge conflict detected. Manual intervention required.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during pull: {e}")
        return False


def commit_and_push(repo: git.Repo, 
                   file_paths: List[str], 
                   commit_message: str,
                   auth_token: Optional[str] = None, 
                   repo_url: Optional[str] = None) -> bool:
    """
    提交并推送更改
    
    Args:
        repo: Git 仓库对象
        file_paths: 要提交的文件路径列表
        commit_message: 提交信息
        auth_token: 认证令牌（可选）
        repo_url: 仓库 URL（可选，用于更新远程 URL 的认证信息）
        
    Returns:
        是否成功提交并推送
    """
    try:
        # 添加文件到暂存区
        repo.index.add(file_paths)
        logger.info(f"Added {len(file_paths)} files to staging area.")
        
        # 提交更改
        repo.index.commit(commit_message)
        logger.info(f"Committed changes with message: '{commit_message}'.")
        
        # 推送更改
        origin = repo.remotes.origin
        
        # 如果提供了 repo_url 和 auth_token，确保远程 URL 包含认证信息
        if repo_url and auth_token:
            repo_url_with_auth = get_repo_url_with_auth(repo_url, auth_token)
            if origin.url != repo_url_with_auth:
                origin.set_url(repo_url_with_auth, origin.url)
                logger.info("Updated remote URL to include auth token for push.")
        
        # 推送到远程
        push_info_list = origin.push()
        
        # 检查推送结果
        successful_push = True
        for push_info in push_info_list:
            if push_info.flags & git.remote.PushInfo.ERROR:
                logger.error(f"Error during push: {push_info.summary}")
                successful_push = False
                break
            elif push_info.flags & git.remote.PushInfo.REJECTED:
                logger.error(f"Push rejected: {push_info.summary}")
                successful_push = False
                break
        
        if successful_push:
            logger.info("Successfully pushed changes to remote repository.")
            return True
        else:
            logger.error("Failed to push changes due to errors or rejections.")
            return False
    except git.exc.GitCommandError as e:
        logger.error(f"Git command error during commit or push: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during commit or push: {e}")
        return False


def is_repo_dirty(repo: git.Repo, file_paths: Optional[List[str]] = None) -> bool:
    """
    检查仓库是否有未提交的更改
    
    Args:
        repo: Git 仓库对象
        file_paths: 要检查的文件路径列表（可选，如果为 None，则检查整个仓库）
        
    Returns:
        是否有未提交的更改
    """
    if file_paths:
        # 检查特定文件
        for path in file_paths:
            if repo.is_dirty(path=path) or path in repo.untracked_files:
                return True
        return False
    else:
        # 检查整个仓库
        return repo.is_dirty(untracked_files=True)
