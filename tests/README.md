# 测试说明 (Test Documentation)

本项目包含了完整的测试套件，覆盖API层、服务层、数据层和核心模块。

## 测试结构 (Test Structure)

```
tests/
├── conftest.py           # 测试配置和共享fixtures
├── test_api/            # API端点测试
│   ├── test_health.py
│   ├── test_projects.py
│   ├── test_tasks.py
│   ├── test_generation.py
│   └── test_openapi_docs.py
├── test_services/       # 服务层测试
│   └── test_git_service.py
├── test_crud/          # 数据层CRUD测试
│   ├── test_crud_project.py
│   └── test_crud_task.py
├── test_models/        # 数据模型测试
│   └── test_project.py
├── test_core/          # 核心模块测试
│   └── test_security.py
└── test_integration/   # 集成测试
    └── test_project_workflow.py
```

## 运行测试 (Running Tests)

### 安装测试依赖 (Install Test Dependencies)

```bash
# 选项1：安装测试专用依赖
pip install -r requirements-test.txt

# 选项2：安装包含测试依赖的完整依赖
pip install -r requirements.txt
```

### 运行所有测试 (Run All Tests)

```bash
pytest
```

### 运行特定类型的测试 (Run Specific Test Types)

```bash
# API测试
pytest -m api

# 服务层测试
pytest -m service

# 数据库测试
pytest -m database

# 单元测试
pytest -m unit

# 集成测试
pytest -m integration
```

### 运行特定测试文件 (Run Specific Test Files)

```bash
# 运行项目API测试
pytest tests/test_api/test_projects.py

# 运行CRUD测试
pytest tests/test_crud/

# 运行集成测试
pytest tests/test_integration/
```

### 生成覆盖率报告 (Generate Coverage Report)

```bash
# 生成终端覆盖率报告
pytest --cov=app

# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html

# 查看HTML报告
open htmlcov/index.html
```

## 测试标记 (Test Markers)

- `@pytest.mark.api`: API端点测试
- `@pytest.mark.service`: 服务层测试
- `@pytest.mark.database`: 数据库相关测试
- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试

## 测试数据库 (Test Database)

测试使用独立的SQLite内存数据库，每个测试函数都会：
1. 创建干净的数据库表
2. 执行测试
3. 清理数据库

这确保了测试之间的隔离性。

## 模拟和Mock (Mocking)

测试中对外部依赖进行了适当的模拟：
- HTTP请求（使用`responses`库）
- 后台任务（mock `initiate_doc_generation_process`）
- 外部服务调用

## 测试覆盖范围 (Test Coverage)

当前测试覆盖：

### API层 (API Layer)
- ✅ 项目CRUD操作
- ✅ 任务状态查询
- ✅ 文档生成触发
- ✅ OpenAPI文档获取
- ✅ 健康检查
- ✅ 认证和授权

### 服务层 (Service Layer)
- ✅ Git服务基础功能
- ⚠️  代码RAG服务集成（需要外部服务，使用mock）
- ⚠️  文档生成服务（需要外部服务，使用mock）

### 数据层 (Data Layer)
- ✅ 项目CRUD操作
- ✅ 任务CRUD操作
- ✅ 数据模型验证

### 核心模块 (Core Modules)
- ✅ 安全功能（token hash/verify）
- ✅ 数据库连接配置

### 集成测试 (Integration Tests)
- ✅ 完整项目生命周期
- ✅ 多项目管理
- ✅ 令牌隔离

## 注意事项 (Notes)

1. 某些测试需要模拟外部服务（Code-RAG服务）
2. Git操作测试使用临时目录，测试完成后自动清理
3. 认证测试使用固定的测试令牌
4. 数据库连接在测试中被替换为内存SQLite数据库

## 持续改进 (Continuous Improvement)

随着项目功能的增加，建议：
1. 增加更多边界条件测试
2. 添加性能测试
3. 增加更复杂的集成测试场景
4. 考虑添加端到端测试