#!/usr/bin/env python3
"""evidence_register.py

证据登记校验与复核清单生成工具（evidence-chain-verifier Step 1 的自动化部分）。

输入：从 stdin 读取 JSON 断言数组，每个元素为一条证据链登记条目。
输出：向 stdout 写入 JSON，包含四部分：
  - errors:          校验错误清单（每条含条目序号与缺失/非法字段说明）
  - warnings:        非阻断警告清单（如 check_date 为未来日期，疑似笔误）
  - review_checklist: 按 confidence 分组（Conflict > Low > Medium > High）的
                      markdown 复核清单字符串，每条附链接（或"不可公开复核"
                      及理由）与可证伪检验方法
  - stats:           统计（总数、各 confidence 计数、无公开 URL 数、错误数）

输入 JSON 格式（数组）：
[
  {
    "claim": "断言内容（可证伪陈述）",            // 必填，非空字符串
    "source_type": "官方底表|监管平台|官网|权威媒体|自媒体|记忆推断",  // 必填
    "url": "https://...",                        // 条件必填：公开可查 URL
    "no_public_url_reason": "理由",              // 条件必填：无 url 时必须填写
    "check_date": "YYYY-MM-DD",                  // 必填
    "falsifiable_test": "如何推翻这条断言",      // 必填，非空字符串
    "confidence": "High|Medium|Low|Conflict"     // 必填
  }
]

校验规则：
  - claim / source_type / check_date / falsifiable_test / confidence 必填，
    且必须是非空字符串（`claim: 123` 或 `{}` 这类非字符串值视为校验错误）；
  - url 与 no_public_url_reason 二选一必填其一，且不应同时出现；
  - url 必须是 http(s) 开头（仅做形态检查，不做网络访问，真伪由复核者点验）；
  - check_date 必须是合法 YYYY-MM-DD；为未来日期时给非阻断警告（warnings）；
  - source_type 非法时给出合法值清单。

仅使用 Python 标准库。退出码：0 正常（即使有校验错误，见 errors 字段）；2 输入错误。
"""

import argparse
import json
import sys
from collections import Counter
from datetime import date

VALID_SOURCE_TYPES = [
    "官方底表",
    "监管平台",
    "官网",
    "权威媒体",
    "自媒体",
    "记忆推断",
]
VALID_CONFIDENCE = ["High", "Medium", "Low", "Conflict"]
# 复核优先级：冲突与低置信排最前
REVIEW_ORDER = ["Conflict", "Low", "Medium", "High"]
REQUIRED_FIELDS = ["claim", "source_type", "check_date", "falsifiable_test", "confidence"]


def parse_args():
    p = argparse.ArgumentParser(
        description="证据登记校验：校验必填字段、按 confidence 分组生成 markdown 复核清单、输出统计。",
        epilog="从 stdin 读 JSON 断言数组，向 stdout 写 JSON。详见模块 docstring。",
    )
    p.add_argument(
        "--pretty", action="store_true", help="以缩进格式输出 JSON（默认紧凑输出）"
    )
    return p.parse_args()


def fail(msg):
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(2)


def is_valid_date(s):
    if not isinstance(s, str):
        return False
    try:
        date.fromisoformat(s)
    except ValueError:
        return False
    return len(s) == 10


def is_valid_url(s):
    return isinstance(s, str) and (
        s.startswith("http://") or s.startswith("https://")
    ) and len(s) > len("https://")


def validate(items):
    """返回 (errors, warnings)，均为字符串列表。warnings 非阻断。"""
    errors, warnings = [], []
    for i, it in enumerate(items):
        tag = f"items[{i}]"
        if not isinstance(it, dict):
            errors.append(f"{tag}: 必须是对象")
            continue
        for f in REQUIRED_FIELDS:
            v = it.get(f)
            if v is None:
                errors.append(f"{tag}: 必填字段 '{f}' 缺失")
            elif not isinstance(v, str):
                errors.append(
                    f"{tag}: 必填字段 '{f}' 必须是字符串，当前为 {type(v).__name__}：{v!r}"
                )
            elif not v.strip():
                errors.append(f"{tag}: 必填字段 '{f}' 为空字符串")
        st = it.get("source_type")
        if isinstance(st, str) and st and st not in VALID_SOURCE_TYPES:
            errors.append(
                f"{tag}: source_type '{st}' 非法，须为 {VALID_SOURCE_TYPES} 之一"
            )
        conf = it.get("confidence")
        if isinstance(conf, str) and conf and conf not in VALID_CONFIDENCE:
            errors.append(
                f"{tag}: confidence '{conf}' 非法，须为 {VALID_CONFIDENCE} 之一"
            )
        cd = it.get("check_date")
        if isinstance(cd, str) and cd:
            if not is_valid_date(cd):
                errors.append(f"{tag}: check_date '{cd}' 非法，须为 YYYY-MM-DD")
            elif date.fromisoformat(cd) > date.today():
                warnings.append(
                    f"{tag}: check_date '{cd}' 是未来日期，请确认是否笔误（不阻断）"
                )
        url = it.get("url")
        reason = it.get("no_public_url_reason")
        has_url = isinstance(url, str) and url.strip()
        has_reason = isinstance(reason, str) and reason.strip()
        if has_url and has_reason:
            errors.append(f"{tag}: url 与 no_public_url_reason 不应同时填写")
        elif not has_url and not has_reason:
            errors.append(
                f"{tag}: 无公开 URL 的关键判断必须填写 no_public_url_reason"
                "（显式标记'不可公开复核'并说明理由）"
            )
        elif has_url and not is_valid_url(url):
            errors.append(f"{tag}: url '{url}' 非法，须为 http(s) 开头的公开链接")
    return errors, warnings


def build_checklist(items):
    """按 confidence 分组生成 markdown 复核清单（复核优先级：Conflict > Low > Medium > High）。"""
    lines = ["# 证据复核清单", ""]
    for conf in REVIEW_ORDER:
        group = [
            (i, it)
            for i, it in enumerate(items)
            if isinstance(it, dict) and it.get("confidence") == conf
        ]
        if not group:
            continue
        lines.append(f"## {conf}（{len(group)} 条）")
        lines.append("")
        for i, it in group:
            claim = it.get("claim", "（claim 缺失）")
            lines.append(f"- [ ] **[{i}]** {claim}")
            lines.append(f"  - 信源类型: {it.get('source_type', '?')}")
            if it.get("url"):
                lines.append(f"  - 链接: {it['url']}")
            else:
                reason = it.get("no_public_url_reason", "未说明")
                lines.append(f"  - ⚠ 不可公开复核: {reason}")
            lines.append(f"  - 查证日期: {it.get('check_date', '?')}")
            lines.append(f"  - 证伪方法: {it.get('falsifiable_test', '?')}")
        lines.append("")
    if len(lines) == 2:
        lines.append("（无有效条目）")
    return "\n".join(lines)


def build_stats(items, errors):
    conf_counter = Counter(it.get("confidence", "?") for it in items if isinstance(it, dict))
    no_url = sum(
        1
        for it in items
        if isinstance(it, dict) and not (isinstance(it.get("url"), str) and it["url"].strip())
    )
    return {
        "total": len(items),
        "by_confidence": {c: conf_counter.get(c, 0) for c in VALID_CONFIDENCE},
        "no_public_url": no_url,
        "error_count": len(errors),
    }


def main():
    args = parse_args()
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        fail(f"stdin 不是合法 JSON：{e}")
    if not isinstance(data, list):
        fail("输入必须是 JSON 断言数组，例如 [{\"claim\": ...}, ...]")
    if not data:
        fail("断言数组为空")

    errors, warnings = validate(data)
    result = {
        "errors": errors,
        "warnings": warnings,
        "review_checklist": build_checklist(data),
        "stats": build_stats(data, errors),
    }
    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
