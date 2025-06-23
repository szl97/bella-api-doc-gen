#!/usr/bin/env python3
"""
Bella API Documentation Generator - API Demo Scripts
完整的API端点调用演示

这个脚本演示了如何调用Bella API文档生成器的所有API端点。
包含了完整的认证、错误处理和响应解析示例。
"""

import requests
import json
import time
from typing import Optional, Dict, Any


class BellaAPIDemo:
    """Bella API文档生成器的演示客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化API客户端
        
        Args:
            base_url: API服务器的基础URL
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/v1/api-doc"
        self.session = requests.Session()
    
    def set_auth_token(self, token: str):
        """设置认证令牌"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发起HTTP请求的通用方法"""
        url = f"{self.api_base}{endpoint}" if endpoint.startswith('/') else f"{self.api_base}/{endpoint}"
        response = self.session.request(method, url, **kwargs)
        print(f"{method} {url}")
        print(f"Status: {response.status_code}")
        if response.content:
            try:
                print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            except:
                print(f"Response: {response.text}")
        print("-" * 50)
        return response

    # ==================== 健康检查 ====================
    
    def health_check(self) -> Dict[str, Any]:
        """检查API服务健康状态"""
        print("=== 健康检查 ===")
        response = requests.get(f"{self.base_url}/health")
        print(f"GET {self.base_url}/health")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print("-" * 50)
        return result

    # ==================== 项目管理 ====================
    
    def create_project(self, name: str, source_openapi_url: str, language: str, 
                      git_repo_url: str, git_auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        创建新项目
        
        Args:
            name: 项目名称
            source_openapi_url: OpenAPI规范的源URL
            language: 编程语言
            git_repo_url: Git仓库URL
            git_auth_token: Git认证令牌（可选）
        """
        print("=== 创建项目 ===")
        data = {
            "name": name,
            "source_openapi_url": source_openapi_url,
            "language": language,
            "git_repo_url": git_repo_url
        }
        if git_auth_token:
            data["git_auth_token"] = git_auth_token
            
        response = self._make_request("POST", "/projects/", json=data)
        return response.json() if response.content else {}
    
    def list_projects(self) -> Dict[str, Any]:
        """获取项目列表"""
        print("=== 获取项目列表 ===")
        response = self._make_request("GET", "/projects/list")
        return response.json() if response.content else {}
    
    def get_project(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目详情
        
        Args:  
            project_id: 项目ID
        """
        print(f"=== 获取项目详情 (ID: {project_id}) ===")
        response = self._make_request("GET", f"/projects/{project_id}")
        return response.json() if response.content else {}
    
    def update_project(self, project_id: int, **updates) -> Dict[str, Any]:
        """
        更新项目信息
        
        Args:
            project_id: 项目ID
            **updates: 要更新的字段
        """
        print(f"=== 更新项目 (ID: {project_id}) ===")
        # 过滤掉None值
        data = {k: v for k, v in updates.items() if v is not None}
        response = self._make_request("PUT", f"/projects/{project_id}", json=data)
        return response.json() if response.content else {}
    
    def delete_project(self, project_id: int) -> Dict[str, Any]:
        """
        删除项目
        
        Args:
            project_id: 项目ID
        """
        print(f"=== 删除项目 (ID: {project_id}) ===")
        response = self._make_request("DELETE", f"/projects/{project_id}")
        return response.json() if response.content else {}

    # ==================== 文档生成 ====================
    
    def generate_docs(self, project_id: int) -> Dict[str, Any]:
        """
        触发文档生成
        
        Args:
            project_id: 项目ID
        """
        print(f"=== 触发文档生成 (项目ID: {project_id}) ===")
        response = self._make_request("POST", f"/gen/{project_id}")
        return response.json() if response.content else {}

    # ==================== 任务管理 ====================
    
    def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        """
        print(f"=== 获取任务状态 (任务ID: {task_id}) ===")
        response = self._make_request("GET", f"/tasks/{task_id}")
        return response.json() if response.content else {}
    
    def wait_for_task_completion(self, task_id: int, timeout: int = 300, interval: int = 5) -> Dict[str, Any]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
        """
        print(f"=== 等待任务完成 (任务ID: {task_id}) ===")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            task_status = self.get_task_status(task_id)
            status = task_status.get('status', 'unknown')
            
            if status in ['completed', 'failed']:
                print(f"任务 {task_id} 已完成，状态: {status}")
                return task_status
            
            print(f"任务 {task_id} 状态: {status}，等待 {interval} 秒后重试...")
            time.sleep(interval)
        
        print(f"任务 {task_id} 在 {timeout} 秒内未完成")
        return self.get_task_status(task_id)

    # ==================== OpenAPI文档 ====================
    
    def get_openapi_spec(self, project_id: int) -> Dict[str, Any]:
        """
        获取生成的OpenAPI规范
        
        Args:
            project_id: 项目ID
        """
        print(f"=== 获取OpenAPI规范 (项目ID: {project_id}) ===")
        response = self._make_request("GET", f"/openapi/{project_id}")
        return response.json() if response.content else {}


def demo_complete_workflow():
    """完整工作流程演示"""
    print("=" * 60)
    print("Bella API文档生成器 - 完整工作流程演示")
    print("=" * 60)
    
    # 初始化客户端
    client = BellaAPIDemo("http://localhost:8000")
    
    # 1. 健康检查
    health = client.health_check()
    
    # 2. 设置认证令牌（请替换为实际的令牌）
    demo_token = "demo_token_12345"
    client.set_auth_token(demo_token)
    
    # 3. 创建项目
    project_data = client.create_project(
        name="演示项目",
        source_openapi_url="https://api.example.com/openapi.json",
        language="Python",
        git_repo_url="https://github.com/example/demo-api.git",
        git_auth_token=None  # 公开仓库不需要认证
    )
    
    if 'task_id' not in project_data:
        print("项目创建失败，停止演示")
        return
    
    task_id = project_data['task_id']
    print(f"项目创建任务ID: {task_id}")
    
    # 4. 等待项目创建完成
    task_result = client.wait_for_task_completion(task_id)
    
    if task_result.get('status') != 'completed':
        print("项目创建任务未成功完成，停止演示")
        return
    
    # 假设从任务结果中获取项目ID
    project_id = 1  # 实际应该从task_result中获取
    
    # 5. 获取项目列表
    projects = client.list_projects()
    
    # 6. 获取项目详情
    project_details = client.get_project(project_id)
    
    # 7. 更新项目信息
    updated_project = client.update_project(
        project_id,
        name="更新后的演示项目",
        language="FastAPI"
    )
    
    # 8. 手动触发文档生成
    gen_result = client.generate_docs(project_id)
    
    if 'task_id' in gen_result:
        gen_task_id = gen_result['task_id']
        
        # 9. 等待文档生成完成
        gen_task_result = client.wait_for_task_completion(gen_task_id)
        
        if gen_task_result.get('status') == 'completed':
            # 10. 获取生成的OpenAPI规范
            openapi_spec = client.get_openapi_spec(project_id)
            print("文档生成成功！")
        else:
            print("文档生成失败")
    
    # 11. 清理 - 删除演示项目（可选）
    # client.delete_project(project_id)
    
    print("演示完成！")


def demo_individual_endpoints():
    """单独端点演示"""
    print("=" * 60)
    print("Bella API文档生成器 - 单独端点演示")
    print("=" * 60)
    
    client = BellaAPIDemo("http://localhost:8000")
    
    # 演示健康检查（无需认证）
    print("1. 健康检查端点演示")
    client.health_check()
    
    # 设置认证令牌
    client.set_auth_token("demo_token_12345")
    
    # 演示项目创建
    print("2. 项目创建端点演示")
    client.create_project(
        name="测试项目",
        source_openapi_url="https://petstore.swagger.io/v2/swagger.json",
        language="Java",
        git_repo_url="https://github.com/swagger-api/swagger-petstore.git"
    )
    
    # 演示项目列表查询
    print("3. 项目列表查询端点演示")
    client.list_projects()
    
    # 演示任务状态查询
    print("4. 任务状态查询端点演示")
    client.get_task_status(1)  # 假设任务ID为1
    
    # 演示OpenAPI规范获取（无需认证）
    print("5. OpenAPI规范获取端点演示")
    # 临时移除认证令牌来演示无需认证的端点
    original_headers = client.session.headers.copy()
    if 'Authorization' in client.session.headers:
        del client.session.headers['Authorization']
    
    client.get_openapi_spec(1)  # 假设项目ID为1
    
    # 恢复认证令牌
    client.session.headers.update(original_headers)
    
    print("单独端点演示完成！")


if __name__ == "__main__":
    print("选择演示模式:")
    print("1. 完整工作流程演示")
    print("2. 单独端点演示")
    print("3. 两者都运行")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == "1":
        demo_complete_workflow()
    elif choice == "2":
        demo_individual_endpoints()
    elif choice == "3":
        demo_individual_endpoints()
        print("\n" + "=" * 80 + "\n")
        demo_complete_workflow()
    else:
        print("无效选择，运行单独端点演示")
        demo_individual_endpoints()