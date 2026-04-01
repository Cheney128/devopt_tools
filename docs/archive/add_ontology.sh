#!/bin/bash
# 为归档文档添加 Ontology 元数据

DOC_BASE="/mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage/docs"

# 函数：添加 Ontology 元数据
add_ontology() {
    local file="$1"
    local id="$2"
    local type="$3"
    local problem="$4"
    local problem_id="$5"
    local date="$6"

    # 检查文件是否已有 ontology（前3行）
    if head -3 "$file" | grep -q "ontology:"; then
        echo "Skip (has ontology): $file"
        return 0
    fi

    # 创建临时文件
    local tmpfile=$(mktemp)

    # 写入元数据头部
    cat > "$tmpfile" << EOF
---
ontology:
  id: $id
  type: $type
  problem: $problem
  problem_id: $problem_id
  status: active
  created: $date
  updated: $date
  author: Claude
  tags:
    - documentation
---
EOF

    # 添加原文件内容
    cat "$file" >> "$tmpfile"

    # 替换原文件
    mv "$tmpfile" "$file"
    echo "Added ontology: $file"
}

# P001: ARP/MAC 调度器修复
P001="${DOC_BASE}/projects/P001-arp-mac-scheduler-fix"
add_ontology "${P001}/01-analysis-auto-collection-failure.md" "DOC-2026-03-001-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/02-analysis-startup-error.md" "DOC-2026-03-002-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/03-analysis-workflow.md" "DOC-2026-03-003-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/04-analysis-field-name-error.md" "DOC-2026-03-004-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/05-analysis-async-call-error.md" "DOC-2026-03-005-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/06-analysis-runtime-error.md" "DOC-2026-03-006-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/07-analysis-netmiko-readtimeout.md" "DOC-2026-03-007-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/08-analysis-expect-string-missing.md" "DOC-2026-03-008-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/09-analysis-vendor-format.md" "DOC-2026-03-009-ANAL" "analysis" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/10-plan-netmiko-final.md" "DOC-2026-03-010-PLAN" "plan" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/11-plan-immediate-collection.md" "DOC-2026-03-011-PLAN" "plan" "ARP/MAC 调度器修复" "P001" "2026-03-30"
add_ontology "${P001}/12-review-netmiko-final.md" "DOC-2026-03-012-REV" "review" "ARP/MAC 调度器修复" "P001" "2026-03-30"

echo "P001 ontology added"