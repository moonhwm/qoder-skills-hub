#!/usr/bin/env python3
"""paper_direction_classifier.py

产出物方向分布核查工具（八轮核查中 R2/R3 的自动化部分）。

输入：从 stdin 读取 JSON，描述某机构/导师/项目的产出物清单。
输出：向 stdout 写入 JSON，包含：
  - 方向占比统计（direction_stats）
  - 入职/归属前后产出分离（owner_join_split）
  - 时间断档检测（gap_detection，断档 >5 年报 warning）
  - 标签型判定（label_only_verdict，目标方向占比 <30% 判为"标签型"）

输入 JSON 格式：
{
  "target_direction": "人工智能",              // 可选；对外宣传的核心方向
  "threshold": 0.30,                          // 可选；标签型判定阈值，默认 0.30
  "gap_warning_years": 5,                     // 可选；断档报警阈值（年），默认 5
  "items": [
    {
      "title": "论文或项目标题",
      "year": 2019,                            // 必填，整数
      "type": "paper|project|patent|other",    // 可选
      "direction": "人工智能",                 // 必填；该产出物的实际方向
      "owner_start_year": 2015                 // 可选；负责人入职/归属起始年
    }
  ]
}

仅使用 Python 标准库。退出码：0 正常；2 输入错误。
"""

import json
import sys
import argparse
from collections import Counter

VALID_TYPES = {"paper", "project", "patent", "other"}


def parse_args():
    p = argparse.ArgumentParser(
        description="产出物方向分布核查：方向占比 / 入职前后分离 / 时间断档 / 标签型判定。",
        epilog="从 stdin 读 JSON，向 stdout 写 JSON。详见模块 docstring。",
    )
    p.add_argument(
        "--pretty", action="store_true", help="以缩进格式输出 JSON（默认紧凑输出）"
    )
    return p.parse_args()


def fail(msg):
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(2)


def validate_items(items):
    if not isinstance(items, list) or not items:
        fail("'items' 必须是非空数组")
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            fail(f"items[{i}] 必须是对象")
        year = it.get("year")
        if not isinstance(year, int):
            fail(f"items[{i}].year 缺失或不是整数")
        if not it.get("direction"):
            fail(f"items[{i}].direction 缺失或为空")
        t = it.get("type")
        if t is not None and t not in VALID_TYPES:
            fail(f"items[{i}].type 必须是 {sorted(VALID_TYPES)} 之一")
        osy = it.get("owner_start_year")
        if osy is not None and not isinstance(osy, int):
            fail(f"items[{i}].owner_start_year 必须是整数")


def direction_stats(items, target, threshold):
    counter = Counter(it["direction"] for it in items)
    total = len(items)
    stats = [
        {
            "direction": d,
            "count": c,
            "ratio": round(c / total, 4),
            "is_target": (d == target) if target else False,
            "label_only": (c / total < threshold) if target and d == target else None,
        }
        for d, c in counter.most_common()
    ]
    return stats, total


def owner_join_split(items, target):
    """按 owner_start_year 将产出分为入职前/入职后两组，分别统计目标方向占比。"""
    groups = {"before_join": [], "after_join": [], "unknown_join_year": 0}
    for it in items:
        osy = it.get("owner_start_year")
        if osy is None:
            groups["unknown_join_year"] += 1
        elif it["year"] < osy:
            groups["before_join"].append(it)
        else:
            groups["after_join"].append(it)

    def summarize(lst):
        if not lst:
            return {"count": 0, "target_count": 0, "target_ratio": None}
        tc = sum(1 for x in lst if x["direction"] == target) if target else 0
        return {
            "count": len(lst),
            "target_count": tc,
            "target_ratio": round(tc / len(lst), 4) if target else None,
        }

    return {
        "before_join": summarize(groups["before_join"]),
        "after_join": summarize(groups["after_join"]),
        "unknown_join_year": groups["unknown_join_year"],
        "note": "入职前产出不应计入该主体当前方向实力；若 after_join 目标占比骤降，警惕'光环继承'。",
    }


def gap_detection(items, warning_years, target=None):
    """按年份排序，检测相邻产出间隔；目标方向序列单独检测。"""
    result = {}
    scope = {"all": items}
    if target:
        scope["target_direction"] = [it for it in items if it["direction"] == target]
    for name, lst in scope.items():
        years = sorted(it["year"] for it in lst)
        gaps = []
        for a, b in zip(years, years[1:]):
            if b - a > warning_years:
                gaps.append({"from": a, "to": b, "gap_years": b - a})
        result[name] = {
            "year_range": [years[0], years[-1]] if years else None,
            "warning_threshold_years": warning_years,
            "gaps": gaps,
            "has_shell_signal": bool(gaps),
        }
    result["note"] = (
        f"断档 >{warning_years} 年为空壳信号：实体可能已停运、报废或仅剩名义归属。"
    )
    return result


def label_only_verdict(items, target, threshold, stats):
    if not target:
        return {"verdict": "not_applicable", "reason": "未提供 target_direction，跳过标签型判定"}
    total = len(items)
    tc = sum(1 for it in items if it["direction"] == target)
    ratio = tc / total
    verdict = "label_only" if ratio < threshold else "substantive_candidate"
    return {
        "verdict": verdict,
        "target_direction": target,
        "target_count": tc,
        "total": total,
        "target_ratio": round(ratio, 4),
        "threshold": threshold,
        "interpretation": (
            f"目标方向占比 {ratio:.1%} < 阈值 {threshold:.0%}，判为'标签型'：有方向之名、缺方向之实。"
            if verdict == "label_only"
            else f"目标方向占比 {ratio:.1%} ≥ 阈值 {threshold:.0%}，通过初筛；仍需 R4-R8 核查配套与信源。"
        ),
    }


def main():
    args = parse_args()
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        fail(f"stdin 不是合法 JSON: {e}")
    if not isinstance(payload, dict):
        fail("输入必须是 JSON 对象")

    items = payload.get("items")
    validate_items(items)

    target = payload.get("target_direction")
    threshold = payload.get("threshold", 0.30)
    gap_years = payload.get("gap_warning_years", 5)
    if not (isinstance(threshold, (int, float)) and 0 < threshold < 1):
        fail("threshold 必须是 (0,1) 区间内的数")
    if not isinstance(gap_years, int) or gap_years < 1:
        fail("gap_warning_years 必须是正整数")

    stats, total = direction_stats(items, target, threshold)
    output = {
        "summary": {
            "total_items": total,
            "distinct_directions": len(stats),
            "target_direction": target,
        },
        "direction_stats": stats,
        "owner_join_split": owner_join_split(items, target),
        "gap_detection": gap_detection(items, gap_years, target),
        "label_only_verdict": label_only_verdict(items, target, threshold, stats),
        "confidence_note": "本输出为'估算'级证据：方向归类依赖输入数据的判定质量，需与 R1 官方文件交叉核对。",
    }

    if args.pretty:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
