#!/usr/bin/env python3
"""
Initialize QA Project Structure

Creates complete QA testing infrastructure including documentation templates,
tracking CSVs, and baseline metrics for any software project.

Usage:
    python scripts/init_qa_project.py <project-name> [output-dir]

Example:
    python scripts/init_qa_project.py my-app ./tests
"""

import argparse
import os
import sys
import csv
from pathlib import Path
from datetime import datetime

def create_directory_structure(base_path):
    """Create QA project directory structure."""
    dirs = [
        "tests/docs",
        "tests/docs/templates",
        "tests/e2e",
        "tests/fixtures"
    ]

    for dir_path in dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {full_path}")

def create_test_execution_tracking(base_path, project_name):
    """Create TEST-EXECUTION-TRACKING.csv with headers."""
    csv_path = base_path / "tests/docs/templates/TEST-EXECUTION-TRACKING.csv"

    headers = [
        "Test Case ID", "Category", "Priority", "Test Name",
        "Estimated Time (min)", "Prerequisites", "Status",
        "Result", "Bug ID", "Execution Date", "Executed By",
        "Notes", "Screenshot/Log"
    ]

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        # Add example row
        writer.writerow([
            "TC-001", "Core", "P0", "Example Test Case",
            "5", "System running", "Not Started", "", "", "", "",
            "Replace with actual test cases", ""
        ])

    print(f"✅ Created: {csv_path}")

def create_bug_tracking_template(base_path):
    """Create BUG-TRACKING-TEMPLATE.csv."""
    csv_path = base_path / "tests/docs/templates/BUG-TRACKING-TEMPLATE.csv"

    headers = [
        "Bug ID", "Title", "Severity", "Component", "Test Case ID",
        "Status", "Reported Date", "Reported By", "Assigned To",
        "Description", "Steps to Reproduce", "Expected Result",
        "Actual Result", "Environment", "Screenshots/Logs",
        "Resolution", "Resolved Date", "Verified By", "Verification Date"
    ]

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        # Add example bug
        writer.writerow([
            "BUG-001", "Example Bug Title", "P1", "Component",
            "TC-001", "Open", datetime.now().strftime("%Y-%m-%d"),
            "QA Engineer", "Engineering Lead",
            "Description of the bug", "1. Step 1\n2. Step 2",
            "Expected behavior", "Actual behavior",
            "OS: macOS\nNode.js: v18.0.0", "",
            "", "", "", ""
        ])

    print(f"✅ Created: {csv_path}")

def create_baseline_metrics(base_path, project_name):
    """Create BASELINE-METRICS.md template."""
    content = f"""# Baseline Metrics - {project_name}

**日期**: {datetime.now().strftime("%Y-%m-%d")}
**目的**: 用于测试期间对比的预QA快照

---

## 1. 测试覆盖率（当前状态）

### 单元测试
- **Total Tests**: [NUMBER]
- **Passing**: [NUMBER] ([%]%)
- **Failing**: [NUMBER]
- **Coverage**: [%]% (statements/branches/functions)

### 集成测试
- **Total Tests**: [NUMBER]
- **Status**: [Passing/Failing/Not Implemented]

### 端到端测试
- **Total Tests**: [NUMBER]
- **Browsers Covered**: [List browsers]

---

## 2. 已知问题(Pre-QA)

### 关键问题
- [ ] Issue 1: Description
- [ ] Issue 2: Description

### 技术债务
- [ ] Debt 1: Description
- [ ] Debt 2: Description

---

## 3. 安全状态

### OWASP Top 10 覆盖范围
- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Authentication Failures
- [ ] A08: Data Integrity Failures
- [ ] A09: Logging Failures
- [ ] A10: SSRF

**当前覆盖率**: [X]/10 ([%]%)

---

## 4. 性能指标

- **Page Load Time**: [X]ms (average)
- **API Response Time**: [X]ms (p95)
- **Database Query Time**: [X]ms (average)

---

## 5. 代码质量

- **Linting Errors**: [NUMBER]
- **TypeScript Strict Mode**: [Yes/No]
- **Code Duplication**: [%]%
- **Cyclomatic Complexity**: [Average]

---

## 6. 预测问题

**CRITICAL-001**: [标题]
- **Predicted Severity**: P0/P1/P2
- **Root Cause**: [Analysis]
- **Test Case**: TC-XXX-YYY will verify
- **Mitigation**: [Recommendation]

---

**下一步**：基线确立后，开始第一周测试。
"""

    file_path = base_path / "tests/docs/BASELINE-METRICS.md"
    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✅ Created: {file_path}")

def create_weekly_report_template(base_path):
    """Create WEEKLY-PROGRESS-REPORT.md template."""
    content = """# Weekly QA Progress Report - Week [N]

**日期范围**: [Start Date] - [End Date]
**QA负责人**: [Name]
**项目**: [Project Name]

---

## 执行摘要

**状态**: 🟢 按计划进行 / 🟡 存在风险 / 🔴 受阻

### 关键指标
- **Tests Executed**: X / Y ([Z]%)
- **Pass Rate**: [%]%
- **Bugs Filed**: [N] (P0: [a], P1: [b], P2: [c], P3: [d])
- **Code Coverage**: [%]%

---

## 测试执行进度

| Category | Total | Executed | Pass | Fail | Pass Rate |
|----------|-------|----------|------|------|-----------|
| Component 1 | X | Y | Z | W | [%]% |
| Component 2 | X | Y | Z | W | [%]% |
| Security | X | Y | Z | W | [%]% |
| **TOTAL** | X | Y | Z | W | [%]% |

---

## 质量门禁状态

| Gate | Target | Current | Status |
|------|--------|---------|--------|
| Test Execution | 100% | [%]% | ✅/⚠️/❌ |
| Pass Rate | ≥80% | [%]% | ✅/⚠️/❌ |
| P0 Bugs | 0 | [N] | ✅/⚠️/❌ |
| P1 Bugs | ≤5 | [N] | ✅/⚠️/❌ |
| Code Coverage | ≥80% | [%]% | ✅/⚠️/❌ |
| Security Coverage | 90% | [%]% | ✅/⚠️/❌ |

---

## Bug 汇总

### P0 Bug（阻塞项）
1. **BUG-001**: [Title]
   - Status: [Open/In Progress/Blocked]
   - Assignee: [Name]
   - ETA: [Date]

### P1 缺陷（严重）
1. **BUG-XXX**: [Title]

---

## 基线对比

| Metric | Week 1 | This Week | Trend |
|--------|--------|-----------|-------|
| Pass Rate | [%]% | [%]% | ⬆️/⬇️/➡️ |
| P0 Bugs | [N] | [N] | ⬆️/⬇️/➡️ |
| Coverage | [%]% | [%]% | ⬆️/⬇️/➡️ |

---

## 阻塞项与风险

### 当前阻塞项
- [ ] Blocker 1: Description
- [ ] Blocker 2: Description

### 风险
- ⚠️ **Risk 1**: Description - Mitigation: [Action]
- ⚠️ **Risk 2**: Description - Mitigation: [Action]

---

## 下周计划

### 测试用例（第[N+1]周）
- [Category]: TC-XXX-YYY to TC-XXX-ZZZ ([N] tests)
- Estimated Time: [X] hours

### 前置条件
- [ ] Prerequisite 1
- [ ] Prerequisite 2

---

**编制人**：[Name]
**日期**：[Date]
"""

    file_path = base_path / "tests/docs/templates/WEEKLY-PROGRESS-REPORT.md"
    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✅ Created: {file_path}")

def create_master_qa_prompt(base_path, project_name):
    """Create MASTER-QA-PROMPT.md for autonomous execution."""
    content = f"""# Master QA Prompt - {project_name}

**目的**：用于自主 QA 测试执行的单次复制粘贴提示词。

---

## ⭐ 主提示词（复制粘贴此内容）

```
You are a senior QA engineer with 20+ years of experience at Google.
Execute the {project_name} QA test plan.

**关键说明：**

1. Read tests/docs/QA-HANDOVER-INSTRUCTIONS.md
2. Read tests/docs/BASELINE-METRICS.md
3. Read tests/docs/templates/TEST-EXECUTION-TRACKING.csv

**确定当前状态**：
- If no tests executed: Start Day 1 onboarding
- If tests in progress: Resume from last completed test case

**对于每个测试用例：**
1. Read test specification
2. Execute test steps
3. Update TEST-EXECUTION-TRACKING.csv IMMEDIATELY (no batching)
4. If FAILED: File bug in BUG-TRACKING-TEMPLATE.csv
5. If P0 bug: STOP and escalate

**每日例行事项**：
- Morning: Check blockers, plan today's tests
- During: Execute tests, update CSV after EACH test
- End-of-day: Provide summary (tests executed, pass rate, bugs filed)

**每周例行工作**（周五）：
- Generate WEEKLY-PROGRESS-REPORT.md
- Compare against BASELINE-METRICS.md
- Assess quality gates

**强制规则**：
- ❌ DO NOT skip tests
- ❌ DO NOT batch CSV updates
- ❌ DO NOT deviate from documented test cases
- ✅ STOP immediately if P0 bug discovered

**现在开始**：告诉我当前状态以及你今天正在做的事情。
```

---

## 自动恢复能力

The master prompt automatically:
1. Reads TEST-EXECUTION-TRACKING.csv
2. Finds last "Completed" test
3. Resumes from next test
4. No manual tracking needed

---

## 每周执行计划

**第1周**：关键路径测试（最高优先级）
**第2周**：用户工作流（常见旅程）
**第3周**：数据完整性（数据库、API）
**第4周**：安全审计（OWASP Top 10）
**第5周**：回归测试（重新执行P0测试）

---

**用法**：复制上方的主提示词并粘贴，以启动自主 QA 执行。
"""

    file_path = base_path / "tests/docs/MASTER-QA-PROMPT.md"
    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✅ Created: {file_path}")

def create_readme(base_path, project_name):
    """Create README.md for QA docs."""
    content = f"""# QA Documentation - {project_name}

**状态**：🟢 准备就绪
**创建时间**：{datetime.now().strftime("%Y-%m-%d")}
**QA 框架**：Google Testing Standards

---

## 📋 快速开始

### 选项 1：自主执行（推荐）
```bash
# 从 MASTER-QA-PROMPT.md 复制主提示词，并粘贴至你的 LLM
```

### 选项 2：手动执行
1. Read `QA-HANDOVER-INSTRUCTIONS.md`
2. Complete Day 1 onboarding checklist
3. Execute test cases from category-specific documents
4. Update tracking CSVs after each test

---

## 文档索引

### 核心策略
- **QA-HANDOVER-INSTRUCTIONS.md** - Master handover guide
- **BASELINE-METRICS.md** - Pre-QA snapshot

### 测试用例
- **01-[CATEGORY]-TEST-CASES.md** - Component tests
- **02-SECURITY-TEST-CASES.md** - OWASP Top 10 tests

### 模板
- **TEST-EXECUTION-TRACKING.csv** - Progress tracker
- **BUG-TRACKING-TEMPLATE.csv** - Bug log
- **WEEKLY-PROGRESS-REPORT.md** - Status reporting

### 自动化
- **MASTER-QA-PROMPT.md** - Autonomous execution

---

## 🎯 质量门禁

| Gate | Target | Status |
|------|--------|--------|
| Test Execution | 100% | ⏳ Not Started |
| Pass Rate | ≥80% | ⏳ Not Started |
| P0 Bugs | 0 | ✅ No blockers |
| Code Coverage | ≥80% | ⏳ Baseline TBD |
| Security | 90% | ⏳ Week 4 |

---

## 🚀 快速开始

**第 1 天设置** (5 小时)：
1. Environment setup
2. Test data seeding
3. Execute first test case
4. Verify tracking systems

**第1-5周执行**：
- Follow test case documents
- Update CSV after EACH test
- File bugs for failures
- Weekly progress reports

---

**联系人**: QA负责人 - [Your Name]
"""

    file_path = base_path / "tests/docs/README.md"
    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✅ Created: {file_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Initialize QA project structure: documentation templates, "
                    "tracking CSVs, and baseline metrics.",
        epilog="Example: python init_qa_project.py my-app ./tests",
    )
    parser.add_argument("project_name", help="Name of the project to initialize QA infrastructure for")
    parser.add_argument("output_dir", nargs="?", default=".",
                        help="Output directory (default: current directory)")
    args = parser.parse_args()

    project_name = args.project_name
    output_dir = args.output_dir

    base_path = Path(output_dir).resolve()

    print(f"\n🚀 Initializing QA Project: {project_name}")
    print(f"   Location: {base_path}\n")

    # Create directory structure
    create_directory_structure(base_path)

    # Create tracking files
    create_test_execution_tracking(base_path, project_name)
    create_bug_tracking_template(base_path)

    # Create documentation
    create_baseline_metrics(base_path, project_name)
    create_weekly_report_template(base_path)
    create_master_qa_prompt(base_path, project_name)
    create_readme(base_path, project_name)

    print(f"\n✅ QA Project '{project_name}' initialized successfully!")
    print(f"\n📝 Next Steps:")
    print(f"   1. Review {base_path}/tests/docs/README.md")
    print(f"   2. Fill in BASELINE-METRICS.md with current project state")
    print(f"   3. Write test cases in category-specific documents")
    print(f"   4. Start testing with MASTER-QA-PROMPT.md")

if __name__ == "__main__":
    main()
