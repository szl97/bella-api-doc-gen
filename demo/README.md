# Bella API文档生成器 - API调用演示

这个目录包含了完整的API端点调用演示，帮助开发者快速了解如何使用Bella API文档生成器的所有功能。

## 📁 文件说明

### `api_demo.py`
- **语言**: Python 3.7+
- **描述**: 完整的Python API客户端演示脚本
- **特性**: 
  - 面向对象的API客户端封装
  - 完整的错误处理和响应解析
  - 两种演示模式：单独端点演示和完整工作流程演示
  - 中文注释和输出
  - 支持自定义API服务器地址和认证令牌

### `curl_examples.sh`
- **语言**: Bash shell脚本
- **描述**: 使用cURL的API调用示例集合
- **特性**:
  - 所有API端点的cURL命令示例
  - 彩色输出和格式化JSON响应
  - 交互式命令行工具
  - 支持单独调用和批量演示
  - 完整工作流程演示

### `README.md`
- **描述**: 本文档，提供使用指南和API端点详细说明

## 🚀 快速开始

### 前置要求

1. **Python演示** (api_demo.py):
   ```bash
   pip install requests
   ```

2. **cURL演示** (curl_examples.sh):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install jq curl
   
   # CentOS/RHEL
   sudo yum install jq curl
   
   # macOS
   brew install jq curl
   ```

### 运行Python演示

```bash
# 进入demo目录
cd demo

# 运行交互式演示
python3 api_demo.py

# 选择演示模式:
# 1. 完整工作流程演示
# 2. 单独端点演示  
# 3. 两者都运行
```

### 运行cURL演示

```bash
# 进入demo目录
cd demo

# 给脚本添加执行权限
chmod +x curl_examples.sh

# 查看可用命令
./curl_examples.sh help

# 运行完整工作流程演示
./curl_examples.sh workflow

# 运行所有端点演示
./curl_examples.sh all

# 运行单个端点演示
./curl_examples.sh health
./curl_examples.sh create
./curl_examples.sh list
```

## 🔧 配置说明

### 环境变量

**Python演示**:
```bash
# 可在脚本中直接修改
BASE_URL = "http://localhost:8000"  # API服务器地址
AUTH_TOKEN = "your_token_here"      # 认证令牌
```

**cURL演示**:
```bash
# 设置环境变量
export BELLA_API_BASE_URL="http://localhost:8000"
export BELLA_API_AUTH_TOKEN="your_token_here"

# 或者在脚本中修改
BASE_URL="http://localhost:8000"
AUTH_TOKEN="your_token_here"
```

### 认证令牌

- 大多数API端点需要Bearer token认证
- 令牌应该与项目关联
- 在演示中使用的是示例令牌，实际使用时请替换为真实令牌

## 📚 API端点详细说明

### 1. 健康检查

**端点**: `GET /health`  
**认证**: 不需要  
**描述**: 检查API服务的健康状态

```bash
# cURL示例
curl -X GET "http://localhost:8000/health"

# Python示例
client.health_check()
```

### 2. 项目管理

#### 创建项目
**端点**: `POST /v1/api-doc/projects/`  
**认证**: 需要Bearer token  
**描述**: 创建新的API文档项目，自动触发初始文档生成

```bash
# cURL示例
curl -X POST "http://localhost:8000/v1/api-doc/projects/" \
     -H "Authorization: Bearer your_token" \
     -H "Content-Type: application/json" \
     -d '{
         "name": "演示项目",
         "source_openapi_url": "https://api.example.com/openapi.json",
         "language": "Python",
         "git_repo_url": "https://github.com/example/demo-api.git",
         "git_auth_token": null
     }'

# Python示例
client.create_project(
    name="演示项目",
    source_openapi_url="https://api.example.com/openapi.json",
    language="Python",
    git_repo_url="https://github.com/example/demo-api.git"
)
```

**请求参数**:
- `name` (必需): 项目名称 (1-255字符)
- `source_openapi_url` (必需): OpenAPI规范源URL (最大512字符)
- `language` (必需): 编程语言 (最大32字符)
- `git_repo_url` (必需): Git仓库URL (最大512字符)
- `git_auth_token` (可选): Git认证令牌 (最大512字符)

**响应示例**:
```json
{
    "message": "项目创建成功，正在生成初始文档",
    "task_id": 1,
    "project_id": 1
}
```

#### 获取项目列表
**端点**: `GET /v1/api-doc/projects/list`  
**认证**: 需要Bearer token  
**描述**: 获取当前用户的所有项目

```bash
# cURL示例
curl -X GET "http://localhost:8000/v1/api-doc/projects/list" \
     -H "Authorization: Bearer your_token"

# Python示例
client.list_projects()
```

#### 获取项目详情
**端点**: `GET /v1/api-doc/projects/{project_id}`  
**认证**: 需要Bearer token (必须匹配项目的令牌)  
**描述**: 获取指定项目的详细信息

```bash
# cURL示例
curl -X GET "http://localhost:8000/v1/api-doc/projects/1" \
     -H "Authorization: Bearer your_token"

# Python示例
client.get_project(1)
```

#### 更新项目
**端点**: `PUT /v1/api-doc/projects/{project_id}`  
**认证**: 需要Bearer token (必须匹配项目的令牌)  
**描述**: 更新项目信息

```bash
# cURL示例
curl -X PUT "http://localhost:8000/v1/api-doc/projects/1" \
     -H "Authorization: Bearer your_token" \
     -H "Content-Type: application/json" \
     -d '{
         "name": "更新后的项目名称",
         "language": "Java"
     }'

# Python示例
client.update_project(1, name="更新后的项目名称", language="Java")
```

#### 删除项目
**端点**: `DELETE /v1/api-doc/projects/{project_id}`  
**认证**: 需要Bearer token (必须匹配项目的令牌)  
**描述**: 删除指定项目

```bash
# cURL示例
curl -X DELETE "http://localhost:8000/v1/api-doc/projects/1" \
     -H "Authorization: Bearer your_token"

# Python示例
client.delete_project(1)
```

### 3. 文档生成

#### 触发文档生成
**端点**: `POST /v1/api-doc/gen/{project_id}`  
**认证**: 需要Bearer token (必须匹配项目的令牌)  
**描述**: 手动触发指定项目的文档生成过程

```bash
# cURL示例
curl -X POST "http://localhost:8000/v1/api-doc/gen/1" \
     -H "Authorization: Bearer your_token"

# Python示例
client.generate_docs(1)
```

**响应示例**:
```json
{
    "message": "文档生成任务已启动",
    "task_id": 2
}
```

### 4. 任务管理

#### 获取任务状态
**端点**: `GET /v1/api-doc/tasks/{task_id}`  
**认证**: 不需要  
**描述**: 获取任务的执行状态和结果

```bash
# cURL示例
curl -X GET "http://localhost:8000/v1/api-doc/tasks/1"

# Python示例
client.get_task_status(1)
```

**响应示例**:
```json
{
    "id": 1,
    "project_id": 1,
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "result": {
        "generated_docs_count": 15,
        "enhanced_endpoints": 8
    },
    "error_message": null
}
```

**任务状态说明**:
- `pending`: 等待执行
- `in_progress`: 正在执行
- `completed`: 执行完成
- `failed`: 执行失败

### 5. OpenAPI文档获取

#### 获取OpenAPI规范
**端点**: `GET /v1/api-doc/openapi/{project_id}`  
**认证**: 不需要  
**描述**: 获取项目生成的完整OpenAPI规范

```bash
# cURL示例
curl -X GET "http://localhost:8000/v1/api-doc/openapi/1"

# Python示例
client.get_openapi_spec(1)
```

**响应**: 完整的OpenAPI 3.0规范JSON文档

## 🔄 完整工作流程示例

### 1. 典型使用流程

```bash
# 1. 检查服务健康状态
./curl_examples.sh health

# 2. 创建项目（会返回task_id）
./curl_examples.sh create

# 3. 等待项目创建完成
./curl_examples.sh wait <task_id>

# 4. 查看项目列表
./curl_examples.sh list

# 5. 获取项目详情
./curl_examples.sh get <project_id>

# 6. 手动触发文档生成（可选）
./curl_examples.sh generate <project_id>

# 7. 等待文档生成完成
./curl_examples.sh wait <generation_task_id>

# 8. 获取生成的OpenAPI文档
./curl_examples.sh openapi <project_id>
```

### 2. 错误处理

演示脚本包含了完整的错误处理示例：

- HTTP状态码检查
- JSON响应验证
- 任务状态监控
- 超时处理
- 认证失败处理

## 🛠️ 常见问题

### Q: 如何获取认证令牌？
A: 认证令牌通常在创建项目时生成，或者由系统管理员提供。每个项目都有独立的令牌。

### Q: 为什么项目创建后需要等待？
A: 项目创建是异步过程，包括Git仓库克隆、代码分析和初始文档生成，需要一定时间完成。

### Q: 如何处理私有Git仓库？
A: 在创建项目时提供`git_auth_token`参数，使用GitHub Personal Access Token或其他Git认证令牌。

### Q: 文档生成失败怎么办？
A: 检查任务状态的`error_message`字段，常见原因包括：
- Git仓库访问失败
- OpenAPI规范格式错误
- Code-RAG服务不可用

### Q: 支持哪些编程语言？
A: 目前支持Spring、FastAPI、Node.js等主流框架，具体支持的语言在项目配置中指定。

## 📝 扩展开发

如果需要基于这些演示开发自己的客户端：

1. **认证处理**: 所有需要认证的请求都要在Header中包含`Authorization: Bearer <token>`
2. **异步任务**: 创建和生成操作都是异步的，需要通过task_id轮询状态
3. **错误处理**: 检查HTTP状态码和响应内容中的错误信息
4. **速率限制**: 在生产环境中注意API调用频率限制

## 🔗 相关链接

- [Bella API文档生成器项目主页](https://github.com/szl97/bella-api-doc-gen)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [OpenAPI 3.0规范](https://swagger.io/specification/)

---

如果在使用过程中遇到问题，请查看项目的Issue页面或创建新的Issue报告问题。