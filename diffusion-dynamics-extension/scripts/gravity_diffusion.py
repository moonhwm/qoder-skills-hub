#!/usr/bin/env python3
"""Fick-Gravity 空间流动/渗透分析器（纯标准库）。

理论渗透通量（引力-扩散形式）：
    flux_i = A_i / (C_i * d_i^2)
  A_i = 源对目的地 i 的引力强度（如岗位吸引力、薪资差、市场规模）
  C_i = 摩擦/成本系数（默认 1；可并入行政、语言、交通成本）
  d_i = 距离（地理/通勤时间/制度距离，须保持全表单位一致）

理论渗透份额 = flux_i / sum(flux)。
若提供 actual（实际渗透量/人数），计算：
    ratio_i       = 实际份额 / 理论份额
    barrier_i     = 1 - ratio_i   （壁垒系数）

防偏硬条款（本脚本强制输出）：
  壁垒系数由"理论 vs 实际差值"推出，在未经独立数据验证前一律标注
  verification_status="unverified_hypothesis（待验证假设）"，禁止在报告中
  当作已证实结论直接引用；必须先收集独立证据（问卷、行政壁垒清单、
  政策文本等）验证差值确实由壁垒造成，而非模型设定误差。

输入：stdin JSON：
{
  "unit": "km",                       // 距离单位说明（可选，透传）
  "destinations": [
    {"name": "城市B", "A": 120.0, "C": 1.0, "d": 50, "actual": 800},
    {"name": "城市C", "A":  80.0, "C": 1.2, "d": 120, "actual": 150}
  ],
  "total_actual": 950                 // 可选；缺省时用各 actual 之和
}
输出：stdout JSON，含每目的地理论通量/份额/比值/壁垒系数及整体壁垒系数。
"""

import argparse
import json
import sys

UNVERIFIED = "unverified_hypothesis（待验证假设）"


def main():
    ap = argparse.ArgumentParser(
        description="Fick-Gravity 理论渗透通量与壁垒系数计算（纯标准库）。"
                    "stdin 读 JSON，stdout 写 JSON。",
        epilog="示例: echo '{\"destinations\":[{\"name\":\"B\",\"A\":120,"
               "\"d\":50,\"actual\":800}]}' | python3 gravity_diffusion.py")
    ap.add_argument("--indent", type=int, default=None,
                    help="输出 JSON 缩进空格数（默认紧凑输出）")
    args = ap.parse_args()

    try:
        cfg = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        json.dump({"error": "stdin 不是合法 JSON: %s" % e}, sys.stdout,
                  ensure_ascii=False)
        sys.exit(2)

    dests = cfg.get("destinations")
    if not isinstance(dests, list) or not dests:
        json.dump({"error": "缺少非空 destinations 数组"}, sys.stdout,
                  ensure_ascii=False)
        sys.exit(2)

    rows, errors = [], []
    for i, dst in enumerate(dests):
        try:
            name = str(dst.get("name", "dest_%d" % i))
            A = float(dst["A"])
            C = float(dst.get("C", 1.0))
            d = float(dst["d"])
            if A < 0 or C <= 0 or d <= 0:
                raise ValueError("要求 A>=0, C>0, d>0")
            actual = dst.get("actual")
            actual = None if actual is None else float(actual)
            if actual is not None and actual < 0:
                raise ValueError("actual 不能为负")
            rows.append({"name": name, "A": A, "C": C, "d": d,
                         "actual": actual, "flux": A / (C * d * d)})
        except (KeyError, ValueError, TypeError) as e:
            errors.append("destinations[%d]: %s" % (i, e))
    if errors:
        json.dump({"error": errors}, sys.stdout, ensure_ascii=False)
        sys.exit(2)

    flux_sum = sum(r["flux"] for r in rows)
    if flux_sum <= 0:
        json.dump({"error": "理论通量总和为 0，无法归一化"}, sys.stdout,
                  ensure_ascii=False)
        sys.exit(2)

    actuals = [r["actual"] for r in rows]
    has_actual = all(a is not None for a in actuals)
    total_actual = cfg.get("total_actual")
    if has_actual:
        total_actual = float(total_actual) if total_actual is not None \
            else sum(actuals)
        if total_actual <= 0:
            json.dump({"error": "actual 全提供时 total_actual 必须为正"},
                      sys.stdout, ensure_ascii=False)
            sys.exit(2)

    results = []
    for r in rows:
        theo_share = r["flux"] / flux_sum
        row = {"name": r["name"],
               "theoretical_flux": round(r["flux"], 6),
               "theoretical_share": round(theo_share, 6)}
        if has_actual:
            act_share = r["actual"] / total_actual
            ratio = act_share / theo_share if theo_share > 0 else 0.0
            row.update({
                "actual": r["actual"],
                "actual_share": round(act_share, 6),
                "actual_to_theoretical_ratio": round(ratio, 6),
                "barrier_coefficient": round(max(0.0, 1.0 - ratio), 6),
                "verification_status": UNVERIFIED,
            })
        results.append(row)

    out = {
        "model": "Fick-Gravity: flux = A / (C * d^2)",
        "distance_unit": cfg.get("unit"),
        "total_theoretical_flux": round(flux_sum, 6),
        "destinations": results,
        "barrier_coefficient_definition": "1 - 实际渗透份额/理论渗透份额（截断到 >=0）",
        "anti_bias_notice": (
            "壁垒系数由理论与实际差值推得，属循环论证高风险量；在收集独立证据"
            "（壁垒清单/问卷/政策文本）验证前，只能作为待验证假设引用，"
            "不得当作已证实结论，也不得给估算参数标实证级置信度。"),
    }
    if has_actual:
        theo_total_share = 1.0
        overall_ratio = 1.0  # 份额总和均为 1，整体比值恒为 1
        # 有含义的整体指标：各地壁垒系数按理论份额加权
        overall_barrier = sum(
            r["barrier_coefficient"] * r["theoretical_share"]
            for r in results)
        out["overall"] = {
            "total_actual": total_actual,
            "weighted_barrier_coefficient": round(overall_barrier, 6),
            "verification_status": UNVERIFIED,
            "note": "按理论份额加权的平均壁垒系数；individual 值更有意义",
        }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=args.indent)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
