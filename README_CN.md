# Bella API 文档生成服务

中文 | [English](./README.md)

Bella API 文档生成是一个自动生成和更新 OpenAPI 3.0 文档的 API 服务。它通过获取源 OpenAPI 规范，处理它，并将结果存储在数据库中。用户可以通过任务 ID 跟踪生成过程，并通过专用的 API 端点获取生成的 OpenAPI JSON。

## 功能特点

* **项目注册：** 配置项目的具体细节，包括源 OpenAPI URL 和私有源仓库的可选 Git 凭证。
* **API 触发生成：** 通过安全的 API 调用启动文档生成。
* **身份验证：** 项目特定操作通过 Bearer 令牌认证保护。
* **基于任务的生成：** 所有文档生成过程都作为异步任务处理。返回 `task_id` 用于跟踪。
* **任务状态跟踪：** API 端点用于检查生成任务的状态（待处理、处理中、成功、失败）并查看结果或错误消息。
* **数据库存储：** 生成的 OpenAPI 规范存储在数据库中。
* **直接 OpenAPI 访问：** API 端点用于获取项目最新成功生成的 OpenAPI JSON。
* **项目状态跟踪：** 监控项目的整体状态（`init`、`pending`、`active`、`failed`）。通过任务跟踪生成进度。
* **OpenAPI 规范对比：** 识别当前源规范与先前生成的规范之间的变化，以实现有针对性的处理。
* **目标描述补全：** 由 [Code-Aware-RAG](https://github.com/szl97/Code-Aware-RAG) 支持

## 依赖项

Bella API 文档生成服务依赖以下外部服务：

### **Code-Aware-RAG** 此服务是目标描述补全功能的先决条件。

**项目链接：** [Code-Aware-RAG](https://github.com/szl97/Code-Aware-RAG)
**说明：** 如果您打算使用描述补全功能，请确保在启动 Bella API 文档生成服务之前运行 Code-Aware-RAG 服务。
**重要提示：** 关于向量库更新的说明：
- 如果 Code-Aware-RAG 服务中项目的向量库不存在，系统会自动创建向量库。
- 如果 Code-Aware-RAG 服务中项目的向量库已存在，系统不会强制更新向量库。
- 如果需要更新向量库（例如代码有重大更新），需要手动调用 Code-Aware-RAG 服务的 `/v1/code-rag/repository/setup` 接口，并指定 `force_reindex` 和 `force_reclone` 参数为 `true`。
- 详细操作方法请参考 [Code-Aware-RAG 项目文档](https://github.com/szl97/Code-Aware-RAG)。

### Code-Aware-RAG使用说明
#### 使用API:
- 新项目或者重大更新后重新索引仓库:
    - 向 POST /v1/code-rag/repository/setup 端点发送请求。
    - 请求头: `Authorization: Bearer {apikey}` （仅在`未配置apikey模式`下需要）
      请求体示例:
      ```json
      {  
        "repo_id": "bella-issues-bot",  
        "repo_url_or_path": "https://github.com/szl97/bella-issues-bot.git",  
        "force_reclone": true,  
        "force_reindex": true  
      }  
      ```
        * 此操作在后台运行并立即返回任务ID。
        * `repo_id` 是你为这个仓库指定的唯一标识符。
        * `force_reclone`和`force_reindex`会重新索引。

- 查询仓库设置状态:
    - 向 GET /v1/code-rag/repository/status/{repo_id} 端点发送请求。
    - 请求头: `Authorization: Bearer {apikey}` （仅在`未配置apikey模式`下需要）
    * 响应示例:
       ```json
       {
      "repo_id": "bella-issues-bot",
      "status": "completed",  // "pending"(进行中), "completed"(完成), 或 "failed"(失败)
      "message": "Repository setup process completed", 
      "index_status": "Indexed Successfully",
      "repository_path": "/path/to/repository"
       }
       ```

## API 端点

所有 API 端点的基础 URL 为 `/v1/api-doc`。

### 身份验证

大多数项目特定端点（项目的 PUT、DELETE 和触发生成）需要在 `Authorization` 头中包含 Bearer 令牌：
`Authorization: Bearer <your_project_token>`，除了 GET openapi-docs

此令牌在创建项目时由您定义，并且对该项目是唯一的。

### 项目管理 (`/v1/api-doc/projects`)

* **`POST /v1/api-doc/projects`**
    * **描述：** 注册新的文档生成项目。自动启动初始文档生成任务。
    * **请求头：** `Authorization: Bearer {apikey}`（其中 `{apikey}` 是您用于创建项目的 API 密钥，不要与创建后生成的项目特定 bearer 令牌混淆）。
    * **请求体：**
        * `name`（字符串，必需）：项目的唯一名称。
        * `source_openapi_url`（字符串，必需）：获取源 OpenAPI 3.0 JSON 规范的 URL。可以是公共 URL 或 Git 仓库中文件的 URL。
        * `git_repo_url`（字符串，必需）：用于拉取代码的 Git 仓库 URL。
        * `git_auth_token`（字符串，可选）：如果 `git_repo_url` 是私有的，则需要认证令牌（如 GitHub PAT）。
    * **响应（成功：201 Created）：** 创建的项目详情和初始文档生成的 `task_id`。
        ```json
        {
          "project": {
            "id": 1,
            "name": "My Awesome API Project",
            "source_openapi_url": "https://api.example.com/v1/openapi.json",
            "git_repo_url": "https://git.example.com/my/repo.git",
            "created_at": "2025-05-28T12:00:00Z",
            "updated_at": "2025-05-28T12:00:00Z"
          },
          "task_id": "xyz123abc"
        }
        ```
    * **请求体示例：**
        ```json
        {
          "name": "My Awesome API Project",
          "source_openapi_url": "https://api.example.com/v1/openapi.json"
        }
        ```
    * **请求体示例（从私有 Git 获取源）：**
        ```json
        {
          "name": "Project From Private Git",
          "source_openapi_url": "path/to/openapi.json",
          "git_repo_url": "https://github.com/your_username/my-private-spec-repo.git",
          "git_auth_token": "your_github_pat"
        }
        ```

* **`GET /v1/api-doc/projects`**
    * **描述：** 列出所有注册的项目。（注意：在生产环境中，此端点可能受到限制或需要管理员权限）。
    * **响应：** 项目详情列表。排除敏感令牌。

* **`GET /v1/api-doc/projects/{project_id}`**
    * **描述：** 通过项目 ID 获取特定项目的详情。
    * **响应：** 项目详情。排除敏感令牌。

* **`PUT /v1/api-doc/projects/{project_id}`**
    * **描述：** 更新现有项目的配置。需要该项目的 Bearer 令牌认证。
    * **请求体：** 与项目创建类似（name、source_openapi_url、git_repo_url、git_auth_token），所有字段可选。也可以包含 `bearer_token` 来更新项目的 API 令牌。
    * **响应：** 更新后的项目详情。

* **`DELETE /v1/api-doc/projects/{project_id}`**
    * **描述：** 删除注册的项目。需要该项目的 Bearer 令牌认证。
    * **响应：** 被删除项目的详情。

### 手动文档生成 (`/v1/api-doc/gen`)

* **`POST /v1/api-doc/gen/{project_id}`**
    * **描述：** 为特定项目触发文档生成和处理工作流。需要该项目的 Bearer 令牌认证。
    * **响应（成功：202 Accepted）：** 确认消息和用于跟踪生成过程的 `task_id`。
        ```json
        {
          "message": "Documentation generation process initiated for project: ExampleProjectName",
          "task_id": "abc789def"
        }
        ```

### 任务管理 (`/v1/api-doc/tasks`)

* **`GET /v1/api-doc/tasks/{task_id}`**
    * **描述：** 检索特定文档生成任务的状态和结果。
    * **响应：**
        * `id`（字符串）：任务 ID。
        * `project_id`（整数）：此任务所属项目的 ID。
        * `status`（字符串）：任务的当前状态（例如，`pending`、`processing`、`success`、`failed`）。
        * `created_at`（日期时间）：任务创建时间戳。
        * `updated_at`（日期时间）：任务最后更新时间戳。
        * `result`（字符串/json，可选）：任务完成时包含成功消息或结构化错误详情。
        * `error_message`（字符串，可选）：如果任务失败，包含详细错误消息。
    * **示例响应（成功）：**
        ```json
        {
          "id": "xyz123abc",
          "project_id": 1,
          "status": "success",
          "created_at": "2023-10-28T12:00:00Z",
          "updated_at": "2023-10-28T12:05:00Z",
          "result": "{"message": "OpenAPI documentation generated successfully."}",
          "error_message": null
        }
        ```
    * **示例响应（失败）：**
        ```json
        {
          "id": "abc789def",
          "project_id": 2,
          "status": "failed",
          "created_at": "2023-10-28T11:00:00Z",
          "updated_at": "2023-10-28T11:01:00Z",
          "result": "{"error": "Failed to fetch OpenAPI spec from source."}",
          "error_message": "HTTPError: 404 Client Error: Not Found for url: https://invalid.url/openapi.json"
        }
        ```

### OpenAPI 文档检索 (`/v1/api-doc/openapi`)

* **`GET /v1/api-doc/{project_id}`**
    * **描述：** 检索指定项目最新成功生成的 OpenAPI JSON 文档。
    * **响应：** OpenAPI JSON 文档。
    * **示例响应：**
        ```json
        {
          "openapi": "3.0.0",
          "info": {
            "title": "Sample API",
            "version": "1.0.0"
          },
          "paths": {
            "/items": {
              "get": {
                "summary": "List all items"
              }
            }
          }
        }
        ```

## 项目配置字段

* `name`：（字符串，必需）项目的唯一名称。
* `bearer_token`：（字符串，创建/更新时必需）您定义的用于验证与此项目相关的 API 请求的密钥令牌。此令牌由 Bella 进行哈希处理并存储。
* `source_openapi_url`：（字符串，必需）Bella 将从中获取源 OpenAPI 3.0 JSON 规范的 URL。如果提供了 `git_repo_url`，可以是公共 URL 或 Git 仓库中的路径。
* `git_repo_url`：（字符串，可选）Git 仓库的 URL。如果 `source_openapi_url` 指向需要克隆的私有 Git 仓库中的资源，则必需。
* `git_auth_token`：（字符串，可选）如果是私有仓库，Bella 用于向 Git 仓库认证的令牌（例如，GitHub 个人访问令牌）。

## 工作流程概述

1. **注册项目：** 使用 `POST /v1/api-doc/projects` 注册您的 API 项目。提供其 `name` 和 `source_openapi_url`。如果源规范在私有 Git 仓库中，还需提供 `git_repo_url` 和 `git_auth_token`。定义 `bearer_token` 以保护您的项目与 Bella 的 API 交互。
2. **初始生成任务：** 注册成功后，Bella 自动触发初始文档生成任务。响应中返回 `task_id`。
3. **跟踪任务状态：** 使用收到的 `task_id` 通过 `GET /v1/api-doc/tasks/{task_id}` 监控生成进度（状态：`pending` -> `processing` -> `success` 或 `failed`）。完成时 `result` 和 `error_message` 字段提供详细信息。
4. **手动触发：** 要稍后更新文档，向 `/v1/api-doc/gen/{project_id}` 发送 `POST` 请求，使用项目的 `bearer_token` 进行认证。这也会返回一个 `task_id`。
5. **获取源规范：** Bella 从 `source_openapi_url` 获取最新的 OpenAPI 规范（如果提供了 Git 凭证，则用于私有仓库）。
6. **获取先前规范（用于对比）：** Bella 从其内部数据库中检索此项目最后成功生成的 OpenAPI 规范。
7. **处理规范：**
    * Bella Docs 计算新源规范与先前规范之间的差异。
    * 对于新的或修改的部分，它可以使用 LLM 应用描述补全。
    * 然后将更改合并到规范的新版本中。
8. **存储生成的规范：** 新处理的 OpenAPI 规范保存到 Bella 的数据库中，与项目和完成的任务关联。
9. **检索生成的规范：** 一旦任务状态为 `success`，您可以通过 `GET /v1/api-doc/openapi/projects/{project_id}/openapi-json` 访问最新生成的 OpenAPI 文档。
10. **状态更新：** 项目的主要状态（`active`、`failed`）反映其文档的整体健康状况。任务状态提供单个生成尝试的详细信息。

## 设置和运行（基础 - 概念性）

这概述了用于开发或测试的基本设置。生产部署需要进一步考虑 WSGI 服务器、容器化和数据库管理等方面。

1. **克隆仓库：**
    ```bash
    git clone <repository_url>
    cd bella-api-doc-gen # 或您的项目目录名
    ```
2. **安装依赖：**
    ```bash
    pip install -r requirements.txt
    ```
3. **配置环境：**
    * 应用程序使用 Pydantic 的 `BaseSettings` 进行配置，可以从环境变量或 `.env` 文件加载。
    * 关键设置包括 `DATABASE_URL`（例如，`sqlite:///./test.db` 或 `postgresql://user:pass@host:port/dbname`）。参考 `app/core/config.py`。
    * 如果您喜欢，可以在项目根目录创建 `.env` 文件，例如：
        ```env
        DATABASE_URL="sqlite:///./bella_doc_gen.db"
        ```
4. **初始化数据库：**
    * 应用程序配置为在启动时初始化数据库并创建表（通过 `app/main.py` 中的 `init_db(engine)`）。如果使用非 SQLite 数据库，请确保您的数据库服务器正在运行且可访问。
5. **运行应用程序：**
    ```bash
    uvicorn app.main:app --reload
    ```
   API 通常在 `http://127.0.0.1:8000` 可用。
6. **使用 Docker 启动：**
    ```bash
    docker build -t bella-api-doc-gen .
    docker run -d -p 8000:8000 --name bella-api-doc-gen bella-api-doc-gen
    ```

### 数据库配置

该服务使用 SQLAlchemy 和 Pydantic 设置，允许通过 `app/core/config.py` 或环境变量配置数据库连接。

**MySQL 配置：**

如果您使用 MySQL 数据库，`DATABASE_URL` 应按以下格式配置：

`mysql+mysqlconnector://USER:PASSWORD@HOST:PORT/DATABASE_NAME`

其中：
* `USER`：您的 MySQL 用户名。
* `PASSWORD`：您的 MySQL 密码。
* `HOST`：您的 MySQL 服务器的主机名或 IP 地址（例如，`localhost`）。
* `PORT`：MySQL 的端口号（默认为 `3306`）。
* `DATABASE_NAME`：您的数据库名称。

**示例：**
`mysql+mysqlconnector://bella_user:bella_pass@127.0.0.1:3306/bella_db`

您可以通过以下几种方式设置此 `DATABASE_URL`：

1. **通过环境变量（推荐）：**
   在运行应用程序之前设置 `DATABASE_URL` 环境变量：
    ```bash
    export DATABASE_URL="mysql+mysqlconnector://USER:PASSWORD@HOST:PORT/DATABASE_NAME"
    uvicorn app.main:app --reload
    ```
   这是推荐的方法，特别是在生产环境中，因为它具有安全性和灵活性。

2. **直接在 `app/core/config.py` 中：**
   您也可以在 `app/core/config.py` 中的 `Settings` 类中硬编码它（尽管这不太灵活，不推荐在生产环境中使用敏感凭证）：
    ```python
    # 在 app/core/config.py 中
    class Settings(BaseSettings):
        # ... 其他设置 ...
        DATABASE_URL: str = "mysql+mysqlconnector://USER:PASSWORD@HOST:PORT/DATABASE_NAME"
        # ...
    ```

如果未另行指定 `DATABASE_URL`，应用程序默认配置为使用 SQLite 数据库（`sqlite:///./test.db`），这对于快速本地测试很方便，但不适合生产环境。
