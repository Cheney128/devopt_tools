#!/bin/bash
#
# dangerous-cmd-guard Hook
# 功能：拦截危险命令（rm -rf、chmod 777、git push --force 等）
#
# 使用方式：
#   ./hooks/dangerous-cmd-guard.sh "命令字符串"
#
# 返回值：
#   0 - 命令安全，允许执行
#   1 - 命令危险，已阻断
#
# 配置：
#   读取 .harness/patterns-cache.json 中的规则
#   支持项目级白名单配置
#
# 日志：
#   违规记录写入 .harness/error-journal/*.json
#

set -euo pipefail

# 脚本所在目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
HARNESS_DIR="$PROJECT_ROOT/.harness"
PATTERNS_FILE="$HARNESS_DIR/patterns-cache.json"
ERROR_JOURNAL_DIR="$HARNESS_DIR/error-journal"

# 颜色输出
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 检查命令参数
if [ $# -lt 1 ]; then
    echo "Usage: $0 <command-string>"
    echo "Example: $0 \"rm -rf /tmp/test\""
    exit 1
fi

COMMAND="$1"

# 检查配置文件是否存在
if [ ! -f "$PATTERNS_FILE" ]; then
    echo -e "${YELLOW}[WARN]${NC} Patterns file not found: $PATTERNS_FILE"
    echo "Allowing command by default: $COMMAND"
    exit 0
fi

# 检查 jq 是否可用
if ! command -v jq &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} jq is required but not installed."
    echo "Please install jq: sudo apt-get install jq"
    exit 1
fi

# 确保 error-journal 目录存在
mkdir -p "$ERROR_JOURNAL_DIR"

# 标记：是否发现违规
VIOLATION_FOUND=false
VIOLATION_LEVEL="warn"
VIOLATION_RULE=""
VIOLATION_REASON=""

# 读取规则并检查
check_pattern() {
    local pattern_id="$1"
    local pattern_name="$2"
    local pattern_level="$3"
    local forbidden_list="$4"
    local whitelist="$5"
    
    # 检查是否在 forbidden 列表中
    local is_forbidden=false
    while IFS= read -r forbidden; do
        if [ -n "$forbidden" ]; then
            # 简单匹配：检查命令是否包含 forbidden 字符串
            if [[ "$COMMAND" == *"$forbidden"* ]]; then
                # 特殊处理 git push --force
                if [[ "$forbidden" == "git push --force" ]]; then
                    # 检查是否在白名单中（宽松策略）
                    local is_whitelisted=false
                    while IFS= read -r white; do
                        if [ -n "$white" ] && [[ "$COMMAND" == *"$white"* ]]; then
                            is_whitelisted=true
                            break
                        fi
                    done <<< "$whitelist"
                    
                    if [ "$is_whitelisted" = true ]; then
                        # 在白名单中，跳过此规则
                        continue
                    fi
                    
                    # 检查是否是推送到 main/master 分支
                    if [[ "$COMMAND" == *"main"* ]] || [[ "$COMMAND" == *"master"* ]]; then
                        is_forbidden=true
                    fi
                else
                    is_forbidden=true
                fi
                
                if [ "$is_forbidden" = true ]; then
                    VIOLATION_FOUND=true
                    VIOLATION_LEVEL="$pattern_level"
                    VIOLATION_RULE="$pattern_id: $pattern_name"
                    VIOLATION_REASON="$forbidden"
                    return 1
                fi
            fi
        fi
    done <<< "$forbidden_list"
    
    return 0
}

# 遍历所有规则
pattern_count=$(jq '.patterns | length' "$PATTERNS_FILE")
for ((i=0; i<pattern_count; i++)); do
    pattern_id=$(jq -r ".patterns[$i].id" "$PATTERNS_FILE")
    pattern_name=$(jq -r ".patterns[$i].name" "$PATTERNS_FILE")
    pattern_level=$(jq -r ".patterns[$i].level" "$PATTERNS_FILE")
    pattern_type=$(jq -r ".patterns[$i].type" "$PATTERNS_FILE")
    
    # 只处理 command 类型的规则
    if [ "$pattern_type" != "command" ]; then
        continue
    fi
    
    # 获取 forbidden 列表
    forbidden_list=$(jq -r ".patterns[$i].pattern.forbidden[]" "$PATTERNS_FILE" 2>/dev/null || echo "")
    
    # 获取 whitelist
    whitelist=$(jq -r ".patterns[$i].pattern.whitelist[]" "$PATTERNS_FILE" 2>/dev/null || echo "")
    
    # 检查规则
    if ! check_pattern "$pattern_id" "$pattern_name" "$pattern_level" "$forbidden_list" "$whitelist"; then
        break
    fi
done

# 处理违规
if [ "$VIOLATION_FOUND" = true ]; then
    timestamp=$(date -Iseconds)
    log_file="$ERROR_JOURNAL_DIR/$(date +%Y%m%d_%H%M%S)_$(echo "$COMMAND" | md5sum | cut -c1-8).json"
    
    # 记录违规日志
    cat > "$log_file" << EOF
{
  "timestamp": "$timestamp",
  "rule": "$VIOLATION_RULE",
  "level": "$VIOLATION_LEVEL",
  "command": "$COMMAND",
  "reason": "$VIOLATION_REASON",
  "action": "blocked",
  "project": "$(basename "$PROJECT_ROOT")"
}
EOF
    
    # 输出警告/错误信息
    if [ "$VIOLATION_LEVEL" = "error" ]; then
        echo -e "${RED}[ERROR]${NC} Dangerous command detected and BLOCKED!"
        echo -e "${RED}Rule:${NC} $VIOLATION_RULE"
        echo -e "${RED}Command:${NC} $COMMAND"
        echo -e "${RED}Reason:${NC} $VIOLATION_REASON"
        echo ""
        echo "This command violates project safety rules. Execution denied."
        echo "Log saved to: $log_file"
        exit 1
    else
        echo -e "${YELLOW}[WARN]${NC} Potentially dangerous command detected!"
        echo -e "${YELLOW}Rule:${NC} $VIOLATION_RULE"
        echo -e "${YELLOW}Command:${NC} $COMMAND"
        echo -e "${YELLOW}Reason:${NC} $VIOLATION_REASON"
        echo ""
        echo "Proceeding with caution. Log saved to: $log_file"
        # warn 级别不阻断，但记录日志
        exit 0
    fi
else
    echo -e "${GREEN}[OK]${NC} Command passed safety check: $COMMAND"
    exit 0
fi
