import copy
import httpx
import json
import logging
from ..core.config import settings
from typing import Dict, Any, List, Set, Tuple, Optional

logger = logging.getLogger(__name__)

def _extract_schema_references(element: Any, current_schemas: Set[str]) -> None:
    """
    Recursively traverses an OpenAPI element and extracts schema references.
    A schema reference is a dict with a '$ref' key whose value starts with '#/components/schemas/'.
    """
    if isinstance(element, dict):
        if '$ref' in element and isinstance(element['$ref'], str) and element['$ref'].startswith('#/components/schemas/'):
            schema_name = element['$ref'].split('/')[-1]
            current_schemas.add(schema_name)
        for key, value in element.items():
            _extract_schema_references(value, current_schemas)
    elif isinstance(element, list):
        for item in element:
            _extract_schema_references(item, current_schemas)

def group_openapi_paths(openapi_paths: Dict[str, Any], openapi_components_schemas: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Groups OpenAPI paths by their prefix (e.g., /v1/users) and identifies all schemas
    referenced within each group. Each group contains at most 10 paths.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}

    for path_string, path_item_object in openapi_paths.items():
        parts = path_string.strip('/').split('/')
        if len(parts) >= 2:
            # Group by the first two segments, e.g., /v1/users
            group_key = f"/{parts[0]}/{parts[1]}"
        elif len(parts) == 1 and parts[0] != "":
            # Group by the first segment if only one, e.g., /health
            group_key = f"/{parts[0]}"
        else:
            # Default group for paths like "/" or if something is unexpected
            group_key = "/default_group"

        if group_key not in groups:
            groups[group_key] = []

        # Check if we need to create a new subgroup (if the current one has 10 paths already)
        current_group_idx = 0
        if len(groups[group_key]) > 0:
            current_group_idx = len(groups[group_key]) - 1
            if len(groups[group_key][current_group_idx]['paths']) >= 10:
                # Create a new subgroup
                groups[group_key].append({'paths': {}, 'schema_names': set()})
                current_group_idx += 1
        else:
            # First subgroup for this prefix
            groups[group_key].append({'paths': {}, 'schema_names': set()})

        # Add the path to the current subgroup
        groups[group_key][current_group_idx]['paths'][path_string] = path_item_object

        # Extract schema references from the current path_item_object
        _extract_schema_references(path_item_object, groups[group_key][current_group_idx]['schema_names'])

    # Convert groups dictionary to the desired list format
    result_list: List[Dict[str, Any]] = []
    for group_prefix, subgroups in groups.items():
        for i, subgroup in enumerate(subgroups):
            # Create a unique group prefix for each subgroup
            unique_group_prefix = f"{group_prefix}" if i == 0 else f"{group_prefix}_part{i+1}"
            result_list.append({
                'group_prefix': unique_group_prefix,
                'paths': subgroup['paths'],
                'schema_names': subgroup['schema_names']
            })

    return result_list


def _get_rewrite_prompt(language_hint: str) -> str:
     return f'''
    ## 你的角色:
你是一位专业的AI助手，擅长分析OpenAPI 3.0规范及相关源代码。当前任务是：根据用户提供的**完整的OpenAPI 3.0 JSON规范内容**，生成一个或多个高效的检索查询字符串。这些查询将用于一个混合式RAG系统（结合FAISS进行语义检索和BM25进行关键词检索），目的是召回相关的源代码文件。最终，这些召回的代码将作为上下文，辅助另一个LLM为用户提供的OpenAPI规范中缺失“description”字段的元素生成描述。

## 你将收到的输入:
1.  **本System Prompt:** 包含操作指令`。
2.  **User Prompt:** **这将是用户提供的完整的OpenAPI 3.0 JSON字符串。**

## 从用户提供的OpenAPI JSON中提取关键信息的指引:
当你收到OpenAPI JSON (通过User Prompt) 时，你**必须**对其进行分析以识别以下信息：
* **重要的Schema/模型名称:** 查看 `components.schemas` 路径下的内容。识别那些结构复杂（属性较多）、被频繁引用或看起来是API核心功能的Schema。
* **常见的API路径结构与关键操作:** 分析 `paths` 部分。注意通用的基础路径（如 `/v1/users`, `/api/inventory`）以及与之关联的HTTP方法（如GET, POST, PUT）。找出那些代表核心功能的路径。
* **整体API用途 (从 `info` 和 `tags` 中获取):** 检查 `info.title`, `info.description` (如果存在) 以及操作中使用的任何 `tags`，以理解API的业务领域和主要功能。

## 查询生成指令 (为混合式检索优化 - 兼顾语义与关键词):

**你正在处理的OpenAPI规范，其实现代码的语言/框架为: `{language_hint}`**

1.  **分析用户提供的JSON:** 首先，请彻底分析User Prompt中提供的OpenAPI JSON，根据上述指引提取关键的Schema、路径和整体API用途。
2.  **语义丰富性 (针对FAISS):** 基于你对OpenAPI JSON的分析结果：
    * 构建能够捕捉实现所述API及其数据模型的*意图*和*概念*的查询。
    * 在适当时使用自然语言短语来表达实体间的关系（例如：“使用{{提取出的Schema名}}模型实现{{提取出的API用途}}相关API端点的源代码”）。
3.  **关键词密度 (针对BM25):** 基于你的分析结果：
    * 确保查询中富含具体的、相关的**关键词**，这些关键词很可能直接出现在源代码中。
    * 包含你从OpenAPI中提取的Schema和路径所对应的潜在类名、函数名、重要变量名、注解以及框架特有的术语。
4.  **结合语义与关键词元素:** 努力生成既能在语义上易于理解，又包含从OpenAPI分析和你已知的 `{language_hint}` 知识中提炼出的精确关键词的查询。
    * *优秀示例 (假设你从OpenAPI中提取出“用户管理”功能、"User" Schema、“/users”路径，且语言为Java Spring):* "Java Spring @RestController for /users API User management, using UserDTO model and UserService logic, class User definition"
5.  **运用语言/框架特定的关键词 (对BM25和语义上下文均至关重要):**
    结合 `{language_hint}` 融入特定的关键词。例如：
    * **Java Spring:** `@RestController`, `@Service`, `@Entity`, `@RequestMapping`, `DTO`, `Model`。
    * **Python (Flask/Django):** `class`, `def`, `app.route`, `views.py`, `models.py`, Pydantic `BaseModel`。
    * **Node.js (Express/NestJS):** `function`, `router.post`, `@Controller()`, `Schema`。
    * *(如果需要，可参考更详尽的列表，或根据 `{language_hint}` 的常见实践进行推断)*
6.  **整合从OpenAPI中提取的关键实体:**
    * 对于你识别出的重要 **Schemas**: "class {{识别出的Schema名}} source code definition", "{{识别出的Schema名}} data model implementation"。
    * 对于你识别出的重要 **Paths**: "controller handling API path {{识别出的路径前缀}}", "route implementation for {{识别出的路径前缀}} methods"。
    * 利用你提取出的 **API标题/标签** 来增加主题性关键词: "{{提取出的标签名}} module implementation"。
7.  **生成广泛而聚焦的查询:**
    * 目标是生成查询，这些查询能共同覆盖你从OpenAPI JSON中识别出的最重要方面（如模型、控制器/路由、主要服务）。
    * 每个查询都应该是一个结构良好、结合了概念元素和具体关键词的短语或句子。
    * *示例 (假设OpenAPI描述了Java Spring中的用户和订单管理):*
        1.  "Source code for data model definitions of User class and Order DTO including relevant fields and annotations"
        2.  "@RestController @RequestMapping implementation for User and Order API paths handling HTTP GET POST PUT methods"
8.  **输出格式:**
    一个或多个检索查询字符串。如果提供多个查询，请用换行符分隔。不要添加任何其他的解释性文字。

## 当前任务:
请基于后续User Prompt中提供的OpenAPI JSON内容，遵循以上所有指令，生成检索查询。
    '''

def _get_sys_prompt() -> str:
    return  """
    # OpenAPI 3.0 文档描述生成任务

## 任务目标
你是一个专业的API文档分析专家。请结合代码，分析输入的OpenAPI 3.0规范文档，并为其中缺失description字段的元素自动生成准确、简洁、有用的中文描述信息。

## 输入
- 一个完整的OpenAPI 3.0规范的JSON文档
- 相关的源代码文件（可能包含Controller、Service、Entity等）

## 输出要求
- 输出必须是一个完整的、符合OpenAPI 3.0规范的JSON
- 保持原有文档的所有结构和内容不变
- 仅添加或补充缺失的description字段
- 如果某个字段已有description，请保持不变
- 输出的JSON必须格式正确，可以直接使用
- 输出内容必须是合法的JSON,不要包含任何文档格式，否则会序列化报错

## 需要添加描述的元素
1. **API端点 (paths)**：
   - 为每个路径和HTTP方法添加operation的description
   - 描述该接口的具体功能和用途

2. **请求参数 (parameters)**：
   - 为path参数、query参数、header参数等添加description
   - 说明参数的作用和预期值

3. **Schema组件 (components/schemas)**：
   - 为每个schema对象添加整体description
   - 为schema中的每个属性(properties)添加description
   - 描述字段的含义、用途和可能的值

4. **请求体和响应 (requestBody/responses)**：
   - 为请求体添加description说明
   - 为响应状态码添加description说明

## 描述内容要求
- **准确性**：基于字段名称、类型和上下文推断合理的用途
- **简洁性**：描述应简明扼要，通常1-2句话即可
- **专业性**：使用技术准确的术语
- **一致性**：同类型字段的描述风格保持一致
- **中文输出**：所有description使用中文

## 推理规则
- **优先分析代码**：仔细阅读提供的源代码，理解业务逻辑和数据流
- **代码注释分析**：提取函数、类、字段的注释信息作为描述的重要依据
- **路由处理分析**：通过不同语言的路由处理方式理解API功能：
   - Java: Controller类的@RequestMapping/@GetMapping等注解方法
   - Python: Flask的@app.route装饰器函数，Django的views函数
   - JavaScript/Node.js: Express的app.get/post等路由函数
   - Go: gin.GET/POST等路由处理函数
   - C#: Controller的Action方法
   - PHP: 路由函数或控制器方法
   - Ruby: Rails的controller actions
   - 其他语言的类似路由/接口定义模式
- **数据模型分析**：通过不同语言的数据结构定义理解字段含义：
   - 类定义、结构体、接口、数据模型等
   - 字段注解、装饰器、注释等元信息
- **业务流程理解**：结合业务逻辑代码理解完整的处理流程
- **字段关联分析**：通过代码中字段的使用方式和上下文推断字段含义
- **异常处理分析**：通过错误处理逻辑理解可能的错误场景和响应
- **数据验证规则**：通过验证逻辑理解字段的约束和要求
- **辅助字段名推理**：当代码信息不足时，再结合字段名称进行合理推测
- **格式类型结合**：根据代码中的数据处理逻辑和format信息提供准确描述

## 注意事项
- 不要修改原有的任何字段值、结构或已存在的description
- 确保输出的JSON语法完全正确
- 保持原有的字段顺序
- **代码分析优先**：优先使用代码中的信息，包括注释、方法名、业务逻辑等
- **建立对应关系**：将OpenAPI中的schema与代码中的数据结构进行对应，将path与路由处理函数对应
- **理解业务上下文**：通过代码理解完整的业务流程，而不是孤立地分析每个字段
- 如果代码信息不足以推断某个字段，再结合字段名提供合理的通用描述

## 分析步骤建议
1. 首先识别代码的编程语言和框架类型
2. 阅读并理解提供的源代码结构和业务逻辑
3. 建立OpenAPI文档与代码组件的对应关系：
   - API路径 ↔ 路由处理函数/方法
   - Schema组件 ↔ 数据模型/类/结构体
   - 参数定义 ↔ 函数参数
4. 提取代码中的注释、文档字符串和元信息
5. 分析业务流程和数据处理逻辑
6. 基于代码分析结果生成准确的description字段

## 输出格式 (重要)
直接输出完整的OpenAPI 3.0 JSON文档，不要添加任何解释文字或markdown标记，否则会序列化报错。
    """

async def call_code_rag_service(partial_openapi_spec: Dict[str, Any], repo_id: str, language: str, apikey: str) -> Optional[Dict[str, Any]]:
    """
    Calls the Code RAG service to get contextually relevant code snippets.
    """

    query_text = f"以下为openapi 3.0规范的json：{json.dumps(partial_openapi_spec, ensure_ascii=False)}"

    payload = {
        "repo_id": repo_id,
        "sys_prompt": _get_sys_prompt(),
        "query_text": query_text,
        "rewrite_prompt": _get_rewrite_prompt(language)
    }

    headers = {
        "Authorization": f"Bearer {apikey}",
        "Content-Type": "application/json"
    }

    logger.info(f"Calling Code RAG service for repo_id: {repo_id} with partial spec.")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.CODE_RAG_SERVICE_HOST + "query/stream",
                json=payload,
                headers=headers,
                timeout=60.0
            )

        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Successfully received response from Code RAG service for repo_id: {repo_id}")
                return result
            except json.JSONDecodeError:
                # Clean response text from potential markdown formatting
                response_text = response.text
                # Remove markdown code blocks (```json and ```)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    # Handle case where language isn't specified in the markdown
                    code_blocks = response_text.split("```")
                    if len(code_blocks) >= 3:  # At least one complete code block
                        response_text = code_blocks[1].strip()

                # Try to parse the cleaned text as JSON
                try:
                    result = json.loads(response_text)
                    logger.info(f"Successfully received response from Code RAG service for repo_id: {repo_id}")
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON response from Code RAG service for repo_id: {repo_id}. Response text: {response.text}")
                    return None
        else:
            logger.error(f"Error calling Code RAG service for repo_id: {repo_id}. Status: {response.status_code}, Response: {response.text}")
            return None

    except httpx.TimeoutException:
        logger.error(f"Request to Code RAG service timed out for repo_id: {repo_id}.")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error while calling Code RAG service for repo_id: {repo_id}. Error: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while calling Code RAG service for repo_id: {repo_id}. Error: {e}")
        return None

async def generate_descriptions(openapi_spec_source: Dict[str, Any], spec_diff_report: Dict[str, Any], repo_id: str, language: str, apikey: str) -> Dict[str, Any]:
    """
    Generates descriptions for added/modified paths in an OpenAPI specification
    by calling a Code RAG service.
    """
    # Logger is already initialized at the module level
    # global logger

    updated_spec = copy.deepcopy(openapi_spec_source)
    paths_to_process: Dict[str, Any] = {}

    for path_key, path_item in spec_diff_report.get('added_paths', {}).items():
        paths_to_process[path_key] = path_item

    for path_key, diff_item in spec_diff_report.get('modified_paths', {}).items():
        if 'new' in diff_item: # 'new' contains the new path_item_object
            paths_to_process[path_key] = diff_item['new']
        else: # Fallback if 'new' is not present, though it should be for modified_paths
            paths_to_process[path_key] = diff_item

    if not paths_to_process:
        logger.info("No added or modified paths found in the diff report. No descriptions to generate.")
        return updated_spec

    # Ensure components and schemas structures exist before calling group_openapi_paths
    components = updated_spec.get('components', {})
    schemas = components.get('schemas', {})

    raw_groups = group_openapi_paths(paths_to_process, schemas)

    if not raw_groups:
        logger.info("No path groups were formed from the paths_to_process. Nothing to send to RAG.")
        return updated_spec

    batched_api_calls: List[Dict[str, Any]] = []
    current_call_paths: Dict[str, Any] = {}
    current_call_schema_names: Set[str] = set()

    # Ensure basic OpenAPI structure for partial_spec_for_rag
    base_partial_spec = {
        "openapi": updated_spec.get("openapi", "3.0.0"), # Default to 3.0.0 if not present
        "info": updated_spec.get("info", {"title": "Partial API", "version": "1.0.0"}), # Provide default info
        "paths": {},
        "components": {"schemas": {}}
    }


    for group in raw_groups:
        current_call_paths.update(group.get('paths', {}))
        current_call_schema_names.update(group.get('schema_names', set()))

        partial_spec_for_rag = copy.deepcopy(base_partial_spec)
        partial_spec_for_rag["paths"] = current_call_paths
        # Filter only relevant schemas for the current batch
        relevant_schemas = {s_name: schemas[s_name] for s_name in current_call_schema_names if s_name in schemas}
        partial_spec_for_rag["components"]["schemas"] = relevant_schemas

        batched_api_calls.append(partial_spec_for_rag)

        current_call_paths = {}
        current_call_schema_names = set()


    # Add any remaining paths as the last batch
    if current_call_paths:
        partial_spec_for_rag = copy.deepcopy(base_partial_spec)
        partial_spec_for_rag["paths"] = current_call_paths
        relevant_schemas = {s_name: schemas[s_name] for s_name in current_call_schema_names if s_name in schemas}
        partial_spec_for_rag["components"]["schemas"] = relevant_schemas
        batched_api_calls.append(partial_spec_for_rag)

    if not batched_api_calls:
        logger.info("No batches were created to call the RAG service.")
        return updated_spec

    for partial_spec_input in batched_api_calls:
        num_paths_in_batch = len(partial_spec_input.get('paths', {}))
        if num_paths_in_batch == 0:
            logger.info("Skipping an empty batch.")
            continue

        logger.info(f"Calling code-rag service for a batch of {num_paths_in_batch} paths.")

        # Assuming call_code_rag_service needs the repo_id, if it's part of your settings or a default.
        # If repo_id needs to be dynamic, it should be passed into generate_descriptions.
        # For now, using the default "bella-openapi" as in call_code_rag_service's definition.
        processed_chunk = await call_code_rag_service(partial_openapi_spec=partial_spec_input, repo_id=repo_id, language=language, apikey=apikey)

        if processed_chunk:
            logger.info(f"Successfully received processed chunk for {num_paths_in_batch} paths. Merging paths and schemas.")

            # Merge paths
            if 'paths' in processed_chunk:
                updated_spec.setdefault('paths', {}).update(processed_chunk['paths'])

            # Merge schemas
            if 'components' in processed_chunk and 'schemas' in processed_chunk['components']:
                updated_spec.setdefault('components', {}).setdefault('schemas', {}).update(processed_chunk['components']['schemas'])
        else:
            logger.warning(f"Failed to process a batch of {num_paths_in_batch} paths. Descriptions for this batch will be missing.")
            logger.error(f"Failed Json is {partial_spec_input}")

    return updated_spec
