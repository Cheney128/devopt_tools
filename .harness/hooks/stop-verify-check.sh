#!/bin/bash
#
# stop-verify-check Hook
# 功能：Session 结束时验证检查清单
#
# 使用方式：
#   ./hooks/stop-verify-check.sh
#
# 返回值：
#   0 - 检查完成（无论通过与否，不阻断）
#
# 检查清单：
#   1. Hook 脚本是否有执行权限
#   2. 测试用例是否通过
#   3. 文档是否更新
#
# 输出：
#   验证报告到 stdout
#

set -euo pipefail

# 脚本所在目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
HOOKS_DIR="$PROJECT_ROOT/.harness/hooks"
DOCS_DIR="$PROJECT_ROOT/docs"

# 颜色输出
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查结果计数
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

# 存储检查结果
declare -a RESULTS=()

# 添加检查结果
add_result() {
    local status="$1"  # PASS, WARN, FAIL
    local check_name="$2"
    local message="$3"
    
    RESULTS+=("$status|$check_name|$message")
    
    case "$status" in
        PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
        WARN) WARN_COUNT=$((WARN_COUNT + 1)) ;;
        FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    esac
}

# 检查 1: Hook 脚本执行权限
check_hook_permissions() {
    echo -e "${BLUE}[CHECK 1]${NC} Checking Hook script permissions..."
    
    local all_executable=true
    local hook_files=()
    
    # 查找所有 .sh 文件
    while IFS= read -r -d '' file; do
        hook_files+=("$file")
    done < <(find "$HOOKS_DIR" -name "*.sh" -print0 2>/dev/null || true)
    
    if [ ${#hook_files[@]} -eq 0 ]; then
        add_result "WARN" "Hook Permissions" "No hook scripts found in $HOOKS_DIR"
        return
    fi
    
    for hook_file in "${hook_files[@]}"; do
        if [ ! -x "$hook_file" ]; then
            echo -e "${RED}✗${NC} Not executable: $(basename "$hook_file")"
            all_executable=false
        else
            echo -e "${GREEN}✓${NC} Executable: $(basename "$hook_file")"
        fi
    done
    
    if [ "$all_executable" = true ]; then
        add_result "PASS" "Hook Permissions" "All hook scripts are executable"
    else
        add_result "FAIL" "Hook Permissions" "Some hook scripts are not executable"
    fi
}

# 检查 2: 测试用例状态
check_test_status() {
    echo -e "${BLUE}[CHECK 2]${NC} Checking test status..."
    
    # 查找测试文件
    local test_files=()
    while IFS= read -r -d '' file; do
        test_files+=("$file")
    done < <(find "$PROJECT_ROOT" -name "*.test.ts" -o -name "*.spec.ts" -print0 2>/dev/null || true)
    
    if [ ${#test_files[@]} -eq 0 ]; then
        add_result "WARN" "Test Status" "No test files found (*.test.ts, *.spec.ts)"
        return
    fi
    
    echo "Found ${#test_files[@]} test file(s)"
    
    # 检查 vitest 是否可用
    if command -v vitest &> /dev/null || command -v npx &> /dev/null; then
        echo "Running tests..."
        local output
        local exit_code
        
        if command -v vitest &> /dev/null; then
            output=$(vitest run --passWithNoTests --reporter=verbose 2>&1) || exit_code=$?
        else
            output=$(npx vitest run --passWithNoTests --reporter=verbose 2>&1) || exit_code=$?
        fi
        
        if [ "${exit_code:-0}" -eq 0 ]; then
            add_result "PASS" "Test Status" "All tests passed"
            echo -e "${GREEN}✓${NC} Tests passed"
        else
            add_result "WARN" "Test Status" "Some tests failed or skipped"
            echo -e "${YELLOW}⚠${NC} Tests had failures (non-blocking)"
        fi
    else
        add_result "WARN" "Test Status" "Vitest not available, skipping test execution"
        echo -e "${YELLOW}⚠${NC} Vitest not available"
    fi
}

# 检查 3: 文档更新状态
check_docs_updated() {
    echo -e "${BLUE}[CHECK 3]${NC} Checking documentation status..."
    
    # 检查 docs 目录是否存在
    if [ ! -d "$DOCS_DIR" ]; then
        add_result "WARN" "Documentation" "Docs directory not found"
        return
    fi
    
    # 查找文档文件
    local doc_files=()
    while IFS= read -r -d '' file; do
        doc_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -print0 2>/dev/null || true)
    
    if [ ${#doc_files[@]} -eq 0 ]; then
        add_result "WARN" "Documentation" "No markdown files in docs directory"
        return
    fi
    
    # 检查最近修改的文档（24 小时内）
    local recent_docs=0
    local now=$(date +%s)
    local one_day_ago=$((now - 86400))
    
    for doc_file in "${doc_files[@]}"; do
        local mtime
        mtime=$(stat -c %Y "$doc_file" 2>/dev/null || echo "0")
        if [ "$mtime" -gt "$one_day_ago" ]; then
            recent_docs=$((recent_docs + 1))
            echo -e "${GREEN}✓${NC} Recently updated: $(basename "$doc_file")"
        fi
    done
    
    if [ $recent_docs -gt 0 ]; then
        add_result "PASS" "Documentation" "$recent_docs document(s) updated recently"
    else
        add_result "WARN" "Documentation" "No documents updated in the last 24 hours"
    fi
}

# 检查 4: 配置文件完整性
check_config_files() {
    echo -e "${BLUE}[CHECK 4]${NC} Checking configuration files..."
    
    local harness_dir="$PROJECT_ROOT/.harness"
    local all_present=true
    
    # 检查必要文件
    local required_files=(
        "$harness_dir/patterns-cache.json"
        "$harness_dir/config.json"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${GREEN}✓${NC} Present: $(basename "$file")"
        else
            echo -e "${RED}✗${NC} Missing: $(basename "$file")"
            all_present=false
        fi
    done
    
    if [ "$all_present" = true ]; then
        add_result "PASS" "Configuration" "All configuration files present"
    else
        add_result "FAIL" "Configuration" "Some configuration files are missing"
    fi
}

# 检查 5: error-journal 目录
check_error_journal() {
    echo -e "${BLUE}[CHECK 5]${NC} Checking error journal..."
    
    local journal_dir="$PROJECT_ROOT/.harness/error-journal"
    
    if [ ! -d "$journal_dir" ]; then
        echo "Creating error-journal directory..."
        mkdir -p "$journal_dir"
        # 创建 .gitkeep 文件
        touch "$journal_dir/.gitkeep"
        add_result "PASS" "Error Journal" "Directory created"
    else
        local log_count
        log_count=$(find "$journal_dir" -name "*.json" -type f 2>/dev/null | wc -l)
        echo "Found $log_count log entry/entries"
        add_result "PASS" "Error Journal" "Directory exists with $log_count entries"
    fi
}

# 输出验证报告
print_report() {
    echo ""
    echo "========================================"
    echo -e "${BLUE}[STOP-VERIFY-CHECK REPORT]${NC}"
    echo "========================================"
    echo "Timestamp: $(date -Iseconds)"
    echo "Project: $(basename "$PROJECT_ROOT")"
    echo ""
    echo "Summary:"
    echo -e "  ${GREEN}PASS:${NC} $PASS_COUNT"
    echo -e "  ${YELLOW}WARN:${NC} $WARN_COUNT"
    echo -e "  ${RED}FAIL:${NC} $FAIL_COUNT"
    echo ""
    echo "Details:"
    echo "----------------------------------------"
    
    for result in "${RESULTS[@]}"; do
        IFS='|' read -r status check_name message <<< "$result"
        
        case "$status" in
            PASS)
                echo -e "${GREEN}✓${NC} $check_name: $message"
                ;;
            WARN)
                echo -e "${YELLOW}⚠${NC} $check_name: $message"
                ;;
            FAIL)
                echo -e "${RED}✗${NC} $check_name: $message"
                ;;
        esac
    done
    
    echo "----------------------------------------"
    echo ""
    
    if [ $FAIL_COUNT -gt 0 ]; then
        echo -e "${RED}[ATTENTION]${NC} $FAIL_COUNT check(s) failed"
        echo "Please review and fix the issues above."
    elif [ $WARN_COUNT -gt 0 ]; then
        echo -e "${YELLOW}[NOTE]${NC} $WARN_COUNT warning(s) found"
        echo "Session completed with warnings (non-blocking)."
    else
        echo -e "${GREEN}[OK]${NC} All checks passed!"
    fi
    
    echo ""
    echo "Note: This check does not block session completion."
    echo "========================================"
}

# 主逻辑
main() {
    echo ""
    echo "========================================"
    echo -e "${BLUE}[STOP-VERIFY-CHECK]${NC} Session End Verification"
    echo "========================================"
    echo ""
    
    # 执行所有检查
    check_hook_permissions
    echo ""
    
    check_test_status
    echo ""
    
    check_docs_updated
    echo ""
    
    check_config_files
    echo ""
    
    check_error_journal
    echo ""
    
    # 输出报告
    print_report
    
    # 始终返回 0，不阻断
    exit 0
}

main
