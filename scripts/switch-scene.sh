#!/bin/bash
# switch_manage 场景切换脚本
# 用法：./switch-scene.sh <场景 ID 或名称>
# 场景：1=本地开发，2=测试环境，3=生产环境

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_DIR/config"
SCENES_FILE="$PROJECT_DIR/.test-scenes.json"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用帮助
show_help() {
    echo "用法：$0 <场景 ID 或名称>"
    echo ""
    echo "场景列表："
    echo "  1, local, dev, 本地，开发     - 本地开发环境"
    echo "  2, test, staging, 测试        - 测试环境"
    echo "  3, prod, production, 生产     - 生产环境（需确认）"
    echo ""
    echo "示例："
    echo "  $0 1          # 切换到本地开发环境"
    echo "  $0 test       # 切换到测试环境"
    echo "  $0 production # 切换到生产环境（需确认）"
    echo ""
    echo "快捷命令："
    echo "  sm-local      # 切换到本地开发环境"
    echo "  sm-test       # 切换到测试环境"
    echo "  sm-prod       # 切换到生产环境"
}

# 解析场景名称
parse_scene() {
    local input="$1"
    case "$input" in
        1|local|dev|本地 | 开发)
            echo "1"
            ;;
        2|test|staging|测试)
            echo "2"
            ;;
        3|prod|production|生产)
            echo "3"
            ;;
        *)
            echo ""
            ;;
    esac
}

# 获取场景信息
get_scene_info() {
    local scene_id="$1"
    if command -v jq &> /dev/null; then
        jq -r ".scenes[] | select(.id == $scene_id)" "$SCENES_FILE"
    else
        grep -A 20 "\"id\": $scene_id" "$SCENES_FILE"
    fi
}

# 确认函数
confirm() {
    local message="$1"
    local risk_level="$2"
    
    if [ "$risk_level" == "high" ]; then
        echo -e "${RED}⚠️  警告：生产环境操作${NC}"
        echo "$message"
        echo ""
        echo "请输入 'CONFIRM' 确认："
        read -r confirm_input
        if [ "$confirm_input" != "CONFIRM" ]; then
            log_error "操作已取消"
            exit 1
        fi
    else
        echo "$message"
        read -r -p "确认吗？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "操作已取消"
            exit 1
        fi
    fi
}

# 备份当前配置
backup_config() {
    local backup_dir="$PROJECT_DIR/.backup"
    mkdir -p "$backup_dir"
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        cp "$PROJECT_DIR/.env" "$backup_dir/.env.backup.$timestamp"
        log_info "已备份当前配置：.env.backup.$timestamp"
    fi
}

# 切换场景
switch_scene() {
    local scene_id="$1"
    local scene_name="$2"
    local risk_level="$3"
    
    log_info "切换到场景 $scene_id: $scene_name"
    
    # 生产环境需要确认
    if [ "$risk_level" == "high" ]; then
        confirm "即将切换到生产环境（10.23.65.95），请确认操作！" "$risk_level"
    fi
    
    # 备份当前配置
    backup_config
    
    # 复制对应的配置文件
    local config_file="$CONFIG_DIR/db-$scene_name.env"
    if [ -f "$config_file" ]; then
        cp "$config_file" "$PROJECT_DIR/.env"
        log_info "已加载配置：$config_file"
    else
        log_error "配置文件不存在：$config_file"
        exit 1
    fi
    
    # 显示场景信息
    echo ""
    log_info "=== 当前场景 ==="
    echo "场景 ID:   $scene_id"
    echo "场景名称：$scene_name"
    
    # 从配置文件读取并显示
    if [ -f "$PROJECT_DIR/.env" ]; then
        grep -E "^DB_HOST|^DB_PORT|^APP_URL" "$PROJECT_DIR/.env" | while read line; do
            echo "$line"
        done
    fi
    
    echo ""
    log_info "切换完成！"
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi
    
    local input="$1"
    local scene_id=$(parse_scene "$input")
    
    if [ -z "$scene_id" ]; then
        log_error "未知场景：$input"
        show_help
        exit 1
    fi
    
    # 获取场景信息
    local scene_name=""
    local risk_level=""
    
    case "$scene_id" in
        1)
            scene_name="local"
            risk_level="low"
            ;;
        2)
            scene_name="test"
            risk_level="medium"
            ;;
        3)
            scene_name="prod"
            risk_level="high"
            ;;
    esac
    
    # 执行切换
    switch_scene "$scene_id" "$scene_name" "$risk_level"
}

# 执行主函数
main "$@"
