#!/bin/bash
#
# post-edit-verify Hook
# 功能：文件编辑后自动运行验证（tsc + vitest）
#
# 使用方式：
#   ./hooks/post-edit-verify.sh <file-path>
#
# 返回值：
#   0 - 验证完成（无论成功失败，不阻断）
#
# 配置：
#   超时阈值：30 秒（可配置）
#   支持项目级配置（哪些文件需要验证）
#
# 输出：
#   验证报告到 stdout
#

set -euo pipefail

# 脚本所在目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
HARNESS_DIR="$PROJECT_ROOT/.harness"
CONFIG_FILE="$HARNESS_DIR/config.json"

# 颜色输出
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_TIMEOUT=30

# 检查命令参数
if [ $# -lt 1 ]; then
    echo "Usage: $0 <file-path>"
    echo "Example: $0 \"src/index.ts\""
    exit 1
fi

FILE_PATH="$1"

# 检查文件是否存在
if [ ! -f "$FILE_PATH" ]; then
    echo -e "${YELLOW}[WARN]${NC} File not found: $FILE_PATH"
    exit 0
fi

# 读取配置
get_timeout() {
    if [ -f "$CONFIG_FILE" ]; then
        local timeout
        timeout=$(jq -r '.settings.postEditVerifyTimeout // 30' "$CONFIG_FILE" 2>/dev/null || echo "$DEFAULT_TIMEOUT")
        echo "$timeout"
    else
        echo "$DEFAULT_TIMEOUT"
    fi
}

TIMEOUT_SECONDS=$(get_timeout)

# 获取文件扩展名
get_extension() {
    local filename="$1"
    echo "${filename##*.}"
}

# 判断文件类型
get_file_type() {
    local filename="$1"
    local ext
    ext=$(get_extension "$filename")
    
    case "$ext" in
        ts)
            if [[ "$filename" == *".test.ts" ]] || [[ "$filename" == *".spec.ts" ]]; then
                echo "test"
            else
                echo "source"
            fi
            ;;
        tsx)
            if [[ "$filename" == *".test.tsx" ]] || [[ "$filename" == *".spec.tsx" ]]; then
                echo "test"
            else
                echo "source"
            fi
            ;;
        js|jsx)
            if [[ "$filename" == *".test.js" ]] || [[ "$filename" == *".test.jsx" ]] || \
               [[ "$filename" == *".spec.js" ]] || [[ "$filename" == *".spec.jsx" ]]; then
                echo "test"
            else
                echo "source"
            fi
            ;;
        *)
            echo "other"
            ;;
    esac
}

# 运行 TypeScript 编译检查
run_tsc() {
    local file="$1"
    local timeout_sec="$2"
    
    echo -e "${BLUE}[VERIFY]${NC} Running TypeScript check..."
    
    # 检查 tsc 是否可用
    if ! command -v tsc &> /dev/null; then
        # 尝试使用 npx tsc
        if command -v npx &> /dev/null; then
            echo -e "${BLUE}[VERIFY]${NC} Using npx tsc..."
            local output
            local exit_code
            output=$(timeout "$timeout_sec" npx tsc --noEmit "$file" 2>&1) || exit_code=$?
            
            if [ "${exit_code:-0}" -eq 124 ]; then
                echo -e "${YELLOW}[TIMEOUT]${NC} TypeScript check timed out after ${timeout_sec}s"
                return 124
            elif [ "${exit_code:-0}" -ne 0 ]; then
                echo -e "${RED}[TSC ERROR]${NC} TypeScript check failed:"
                echo "$output"
                return 1
            else
                echo -e "${GREEN}[PASS]${NC} TypeScript check passed"
                return 0
            fi
        else
            echo -e "${YELLOW}[SKIP]${NC} tsc not found, skipping TypeScript check"
            return 0
        fi
    fi
    
    # 直接使用 tsc
    local output
    local exit_code
    output=$(timeout "$timeout_sec" tsc --noEmit "$file" 2>&1) || exit_code=$?
    
    if [ "${exit_code:-0}" -eq 124 ]; then
        echo -e "${YELLOW}[TIMEOUT]${NC} TypeScript check timed out after ${timeout_sec}s"
        return 124
    elif [ "${exit_code:-0}" -ne 0 ]; then
        echo -e "${RED}[TSC ERROR]${NC} TypeScript check failed:"
        echo "$output"
        return 1
    else
        echo -e "${GREEN}[PASS]${NC} TypeScript check passed"
        return 0
    fi
}

# 运行 Vitest 测试
run_vitest() {
    local file="$1"
    local timeout_sec="$2"
    
    echo -e "${BLUE}[VERIFY]${NC} Running Vitest test..."
    
    # 检查 vitest 是否可用
    if ! command -v vitest &> /dev/null; then
        # 尝试使用 npx vitest
        if command -v npx &> /dev/null; then
            echo -e "${BLUE}[VERIFY]${NC} Using npx vitest..."
            local output
            local exit_code
            output=$(timeout "$timeout_sec" npx vitest run "$file" 2>&1) || exit_code=$?
            
            if [ "${exit_code:-0}" -eq 124 ]; then
                echo -e "${YELLOW}[TIMEOUT]${NC} Vitest timed out after ${timeout_sec}s"
                return 124
            elif [ "${exit_code:-0}" -ne 0 ]; then
                echo -e "${RED}[VITEST FAIL]${NC} Test failed:"
                echo "$output"
                return 1
            else
                echo -e "${GREEN}[PASS]${NC} All tests passed"
                return 0
            fi
        else
            echo -e "${YELLOW}[SKIP]${NC} vitest not found, skipping test"
            return 0
        fi
    fi
    
    # 直接使用 vitest
    local output
    local exit_code
    output=$(timeout "$timeout_sec" vitest run "$file" 2>&1) || exit_code=$?
    
    if [ "${exit_code:-0}" -eq 124 ]; then
        echo -e "${YELLOW}[TIMEOUT]${NC} Vitest timed out after ${timeout_sec}s"
        return 124
    elif [ "${exit_code:-0}" -ne 0 ]; then
        echo -e "${RED}[VITEST FAIL]${NC} Test failed:"
        echo "$output"
        return 1
    else
        echo -e "${GREEN}[PASS]${NC} All tests passed"
        return 0
    fi
}

# 主逻辑
main() {
    echo ""
    echo "========================================"
    echo -e "${BLUE}[POST-EDIT-VERIFY]${NC} Starting verification"
    echo "File: $FILE_PATH"
    echo "Timeout: ${TIMEOUT_SECONDS}s"
    echo "========================================"
    echo ""
    
    local file_type
    file_type=$(get_file_type "$FILE_PATH")
    
    local overall_status=0
    local verification_results=()
    
    case "$file_type" in
        source)
            # 源文件：运行 tsc
            if run_tsc "$FILE_PATH" "$TIMEOUT_SECONDS"; then
                verification_results+=("TypeScript: PASS")
            else
                verification_results+=("TypeScript: FAIL")
                overall_status=1
            fi
            ;;
        test)
            # 测试文件：运行 vitest
            if run_vitest "$FILE_PATH" "$TIMEOUT_SECONDS"; then
                verification_results+=("Vitest: PASS")
            else
                verification_results+=("Vitest: FAIL")
                overall_status=1
            fi
            ;;
        other)
            echo -e "${YELLOW}[SKIP]${NC} No verification configured for this file type"
            verification_results+=("Verification: SKIPPED")
            ;;
    esac
    
    # 输出验证报告
    echo ""
    echo "========================================"
    echo -e "${BLUE}[VERIFICATION REPORT]${NC}"
    echo "========================================"
    for result in "${verification_results[@]}"; do
        if [[ "$result" == *"PASS"* ]]; then
            echo -e "${GREEN}✓${NC} $result"
        elif [[ "$result" == *"FAIL"* ]]; then
            echo -e "${RED}✗${NC} $result"
        else
            echo -e "${YELLOW}○${NC} $result"
        fi
    done
    echo "========================================"
    
    if [ $overall_status -ne 0 ]; then
        echo -e "${YELLOW}[WARN]${NC} Verification completed with warnings"
        echo "Note: Verification failures do not block execution"
    else
        echo -e "${GREEN}[OK]${NC} Verification completed successfully"
    fi
    echo ""
    
    # 始终返回 0，不阻断执行
    exit 0
}

main
