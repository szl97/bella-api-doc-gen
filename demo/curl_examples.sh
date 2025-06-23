#!/bin/bash
# Bella API Documentation Generator - cURL Examples
# 完整的API端点cURL调用示例

# API服务器地址
BASE_URL="http://localhost:8000"
API_BASE="${BASE_URL}/v1/api-doc"

# 认证令牌（请替换为实际的令牌）
AUTH_TOKEN="demo_token_12345"

# 颜色输出函数
print_header() {
    echo -e "\033[1;34m=== $1 ===\033[0m"
}

print_success() {
    echo -e "\033[1;32m✓ $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m✗ $1\033[0m"
}

print_info() {
    echo -e "\033[1;33m→ $1\033[0m"
}

# ==================== 健康检查 ====================

demo_health_check() {
    print_header "健康检查"
    print_info "检查API服务是否正常运行"
    
    curl -X GET "${BASE_URL}/health" \
         -H "Content-Type: application/json" \
         -w "\nHTTP状态码: %{http_code}\n" \
         -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    
    echo
}

# ==================== 项目管理 ====================

demo_create_project() {
    print_header "创建项目"
    print_info "创建一个新的API文档项目"
    
    curl -X POST "${API_BASE}/projects/" \
         -H "Content-Type: application/json" \
         -H "Authorization: Bearer ${AUTH_TOKEN}" \
         -w "\nHTTP状态码: %{http_code}\n" \
         -d '{
             "name": "演示项目",
             "source_openapi_url": "https://petstore.swagger.io/v2/swagger.json",
             "language": "Java",
             "git_repo_url": "https://github.com/swagger-api/swagger-petstore.git",
             "git_auth_token": null
         }' \
         -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    
    echo
}

demo_list_projects() {
    print_header "获取项目列表"
    print_info "获取当前用户的所有项目"
    
    curl -X GET "${API_BASE}/projects/list" \
         -H "Content-Type: application/json" \
         -H "Authorization: Bearer ${AUTH_TOKEN}" \
         -w "\nHTTP状态码: %{http_code}\n" \
         -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    
    echo
}

demo_get_project() {
    local project_id=${1:-1}
    print_header "获取项目详情"
    print_info "获取项目ID ${project_id} 的详细信息"
    
    curl -X GET "${API_BASE}/projects/${project_id}" \
         -H "Content-Type: application/json" \
         -H "Authorization: Bearer ${AUTH_TOKEN}" \
         -w "\nHTTP状态码: %{http_code}\n" \
         -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    
    echo
}

demo_update_project() {
    local project_id=${1:-1}
    print_header "更新项目"
    print_info "更新项目ID ${project_id} 的信息"
    
    curl -X PUT "${API_BASE}/projects/${project_id}" \
         -H "Content-Type: application/json" \
         -H "Authorization: Bearer ${AUTH_TOKEN}" \
         -w "\nHTTP状态码: %{http_code}\n" \
         -d '{
             "name": "更新后的演示项目",
             "language": "Python",
             "status": "active"
         }' \
         -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    
    echo
}

demo_delete_project() {
    local project_id=${1:-1}
    print_header "删除项目"
    print_info "删除项目ID ${project_id}"
    
    read -p "确认要删除项目 ${project_id} 吗？(y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        curl -X DELETE "${API_BASE}/projects/${project_id}" \
             -H "Content-Type: application/json" \
             -H "Authorization: Bearer ${AUTH_TOKEN}" \
             -w "\nHTTP状态码: %{http_code}\n" \
             -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    else
        echo "取消删除操作"
    fi
    
    echo
}

# ==================== 文档生成 ====================

demo_generate_docs() {
    local project_id=${1:-1}
    print_header "触发文档生成"
    print_info "为项目ID ${project_id} 生成API文档"
    
    curl -X POST "${API_BASE}/gen/${project_id}" \
         -H "Content-Type: application/json" \
         -H "Authorization: Bearer ${AUTH_TOKEN}" \
         -w "\nHTTP状态码: %{http_code}\n" \
         -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    
    echo
}

# ==================== 任务管理 ====================

demo_get_task_status() {
    local task_id=${1:-1}
    print_header "获取任务状态"
    print_info "检查任务ID ${task_id} 的执行状态"
    
    curl -X GET "${API_BASE}/tasks/${task_id}" \
         -H "Content-Type: application/json" \
         -w "\nHTTP状态码: %{http_code}\n" \
         -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    
    echo
}

demo_wait_for_task() {
    local task_id=${1:-1}
    local max_attempts=${2:-20}
    local interval=${3:-5}
    
    print_header "等待任务完成"
    print_info "等待任务ID ${task_id} 完成，最多等待 $((max_attempts * interval)) 秒"
    
    for ((i=1; i<=max_attempts; i++)); do
        echo "检查第 ${i} 次..."
        
        response=$(curl -X GET "${API_BASE}/tasks/${task_id}" \
                       -H "Content-Type: application/json" \
                       -s)
        
        status=$(echo "$response" | jq -r '.status' 2>/dev/null)
        
        echo "任务状态: $status"
        
        if [[ "$status" == "completed" || "$status" == "failed" ]]; then
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
            break
        fi
        
        if [[ $i -lt $max_attempts ]]; then
            print_info "等待 ${interval} 秒后重试..."
            sleep $interval
        fi
    done
    
    echo
}

# ==================== OpenAPI文档获取 ====================

demo_get_openapi_spec() {
    local project_id=${1:-1}
    print_header "获取OpenAPI规范"
    print_info "获取项目ID ${project_id} 生成的OpenAPI规范"
    
    curl -X GET "${API_BASE}/openapi/${project_id}" \
         -H "Content-Type: application/json" \
         -w "\nHTTP状态码: %{http_code}\n" \
         -s | jq '.' 2>/dev/null || echo "响应不是有效的JSON格式"
    
    echo
}

# ==================== 批量测试所有端点 ====================

demo_all_endpoints() {
    print_header "所有端点演示"
    print_info "按顺序演示所有API端点"
    
    # 1. 健康检查
    demo_health_check
    
    # 2. 创建项目
    demo_create_project
    
    # 3. 获取项目列表
    demo_list_projects
    
    # 4. 获取项目详情（假设项目ID为1）
    demo_get_project 1
    
    # 5. 更新项目
    demo_update_project 1
    
    # 6. 触发文档生成
    demo_generate_docs 1
    
    # 7. 获取任务状态（假设任务ID为1）
    demo_get_task_status 1
    
    # 8. 获取OpenAPI规范
    demo_get_openapi_spec 1
    
    # 注意：删除项目放在最后，因为会删除数据
    echo "如需测试删除项目功能，请单独运行: $0 delete 1"
}

# ==================== 完整工作流程演示 ====================

demo_complete_workflow() {
    print_header "完整工作流程演示"
    print_info "演示从创建项目到获取生成文档的完整流程"
    
    # 1. 健康检查
    echo "步骤 1: 检查服务健康状态"
    demo_health_check
    
    # 2. 创建项目
    echo "步骤 2: 创建新项目"
    create_response=$(curl -X POST "${API_BASE}/projects/" \
                          -H "Content-Type: application/json" \
                          -H "Authorization: Bearer ${AUTH_TOKEN}" \
                          -d '{
                              "name": "工作流程演示项目",
                              "source_openapi_url": "https://petstore.swagger.io/v2/swagger.json",
                              "language": "Java",
                              "git_repo_url": "https://github.com/swagger-api/swagger-petstore.git"
                          }' \
                          -s)
    
    echo "$create_response" | jq '.' 2>/dev/null || echo "$create_response"
    
    # 提取任务ID
    task_id=$(echo "$create_response" | jq -r '.task_id' 2>/dev/null)
    if [[ "$task_id" != "null" && "$task_id" != "" ]]; then
        echo
        echo "步骤 3: 等待项目创建完成"
        demo_wait_for_task "$task_id" 10 3
        
        # 假设项目创建成功，项目ID为1（实际应该从任务结果中获取）
        project_id=1
        
        echo "步骤 4: 获取项目详情"
        demo_get_project "$project_id"
        
        echo "步骤 5: 触发文档生成"
        gen_response=$(curl -X POST "${API_BASE}/gen/${project_id}" \
                           -H "Content-Type: application/json" \
                           -H "Authorization: Bearer ${AUTH_TOKEN}" \
                           -s)
        
        echo "$gen_response" | jq '.' 2>/dev/null || echo "$gen_response"
        
        # 提取生成任务ID
        gen_task_id=$(echo "$gen_response" | jq -r '.task_id' 2>/dev/null)
        if [[ "$gen_task_id" != "null" && "$gen_task_id" != "" ]]; then
            echo
            echo "步骤 6: 等待文档生成完成"
            demo_wait_for_task "$gen_task_id" 15 5
            
            echo "步骤 7: 获取生成的OpenAPI文档"
            demo_get_openapi_spec "$project_id"
        fi
    else
        print_error "项目创建失败，无法继续工作流程演示"
    fi
    
    print_success "完整工作流程演示完成！"
}

# ==================== 主函数 ====================

show_usage() {
    echo "Bella API文档生成器 - cURL演示脚本"
    echo
    echo "用法: $0 [命令] [参数]"
    echo
    echo "可用命令:"
    echo "  health                    - 健康检查"
    echo "  create                   - 创建项目"
    echo "  list                     - 获取项目列表"
    echo "  get [project_id]         - 获取项目详情"
    echo "  update [project_id]      - 更新项目"
    echo "  delete [project_id]      - 删除项目"
    echo "  generate [project_id]    - 触发文档生成"
    echo "  task [task_id]           - 获取任务状态"
    echo "  wait [task_id]           - 等待任务完成"
    echo "  openapi [project_id]     - 获取OpenAPI规范"
    echo "  all                      - 演示所有端点"
    echo "  workflow                 - 完整工作流程演示"
    echo "  help                     - 显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 health                # 检查服务健康状态"
    echo "  $0 create                # 创建新项目"
    echo "  $0 get 1                 # 获取项目ID为1的详情"
    echo "  $0 workflow              # 运行完整工作流程演示"
    echo
    echo "环境变量:"
    echo "  BASE_URL                 - API服务器地址 (默认: http://localhost:8000)"
    echo "  AUTH_TOKEN               - 认证令牌 (默认: demo_token_12345)"
}

# 检查是否安装了jq
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        print_error "错误: 需要安装 jq 来格式化JSON输出"
        echo "在Ubuntu/Debian上安装: sudo apt-get install jq"
        echo "在CentOS/RHEL上安装: sudo yum install jq"
        echo "在macOS上安装: brew install jq"
        exit 1
    fi
}

main() {
    # 检查依赖
    check_dependencies
    
    # 处理环境变量
    if [[ -n "$BELLA_API_BASE_URL" ]]; then
        BASE_URL="$BELLA_API_BASE_URL"
        API_BASE="${BASE_URL}/v1/api-doc"
    fi
    
    if [[ -n "$BELLA_API_AUTH_TOKEN" ]]; then
        AUTH_TOKEN="$BELLA_API_AUTH_TOKEN"
    fi
    
    echo "使用API服务器: $BASE_URL"
    echo "使用认证令牌: ${AUTH_TOKEN:0:10}..."
    echo
    
    # 解析命令行参数
    case "${1:-help}" in
        "health")
            demo_health_check
            ;;
        "create")
            demo_create_project
            ;;
        "list")
            demo_list_projects
            ;;
        "get")
            demo_get_project "$2"
            ;;
        "update")
            demo_update_project "$2"
            ;;
        "delete")
            demo_delete_project "$2"
            ;;
        "generate")
            demo_generate_docs "$2"
            ;;
        "task")
            demo_get_task_status "$2"
            ;;
        "wait")
            demo_wait_for_task "$2" "$3" "$4"
            ;;
        "openapi")
            demo_get_openapi_spec "$2"
            ;;
        "all")
            demo_all_endpoints
            ;;
        "workflow")
            demo_complete_workflow
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "未知命令: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"