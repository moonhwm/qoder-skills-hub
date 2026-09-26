#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scoring_engine.py — 多维度加权评分引擎（纯标准库）

从 stdin 读取评分 JSON，输出加权总分、A–F 风险等级、置信度加权得分，
以及 ±20% 权重扰动下的排名/等级稳定性（敏感性分析，必做项）。

输入 JSON 结构（单个选项）：
{
  "option": "选项A",
  "dimensions": [
    {"name": "收益潜力", "score": 8.0, "weight": 0.3, "conf": "empirical"},
    ...
  ],
  "negative_items": [          # 可选，负权重风险扣分项
    {"name": "调剂窗口风险", "score": 6.0, "weight": -0.15, "conf": "estimated"}
  ]
}

批量模式：顶层 JSON 为数组，每个元素为上述结构；输出含排名与扰动稳定性。

conf 等级与数值映射：empirical(实证)=1.0, estimated(估算)=0.6, assumed(假设)=0.3

等级阈值（默认，可用 --thresholds 覆盖）：
  A >= 8.0  优质；B >= 6.5 可行；C >= 5.0 谨慎；D >= 3.5 高风险；F < 3.5 欺诈性或不可行

用法：
  echo '{...}' | python3 scoring_engine.py
  echo '[{...},{...}]' | python3 scoring_engine.py --perturb 0.2 --samples 200
  python3 scoring_engine.py --help
"""

import argparse
import json
import random
import sys

CONF_MAP = {"empirical": 1.0, "estimated": 0.6, "assumed": 0.3}

DEFAULT_THRESHOLDS = {"A": 8.0, "B": 6.5, "C": 5.0, "D": 3.5}  # 低于 D 下限即 F

GRADE_LABELS = {
    "A": "优质",
    "B": "可行",
    "C": "谨慎",
    "D": "高风险",
    "F": "欺诈性或不可行",
}


def parse_conf(value):
    """解析 conf 字段：接受等级名或 [0,1] 数值。"""
    if isinstance(value, (int, float)):
        v = float(value)
        if not 0.0 <= v <= 1.0:
            raise ValueError("conf 数值必须在 [0,1] 区间")
        return v
    key = str(value).strip().lower()
    if key not in CONF_MAP:
        raise ValueError(
            "conf 必须是 empirical/estimated/assumed 之一，或 [0,1] 数值，收到: %r" % value
        )
    return CONF_MAP[key]


def validate_item(item, kind, option_name):
    for field in ("name", "score", "weight", "conf"):
        if field not in item:
            raise ValueError("选项 %r 的 %s 缺少字段 %r" % (option_name, kind, field))
    score = float(item["score"])
    if not 0.0 <= score <= 10.0:
        raise ValueError("选项 %r 的 %s %r 分值须在 0-10，收到 %s" % (option_name, kind, item["name"], score))
    weight = float(item["weight"])
    if kind == "dimension" and weight < 0:
        raise ValueError("维度权重不能为负（负权重请放入 negative_items）: %r" % item["name"])
    if kind == "negative_item" and weight > 0:
        raise ValueError("负权重项 weight 必须为负: %r" % item["name"])
    conf = parse_conf(item["conf"])
    return {"name": str(item["name"]), "score": score, "weight": weight, "conf": conf}


def grade_of(total, thresholds):
    for g in ("A", "B", "C", "D"):
        if total >= thresholds[g]:
            return g
    return "F"


def compute_option(raw, thresholds):
    option_name = raw.get("option", raw.get("name", "未命名选项"))
    dims_raw = raw.get("dimensions")
    if not dims_raw:
        raise ValueError("选项 %r 缺少非空 dimensions" % option_name)
    dims = [validate_item(d, "dimension", option_name) for d in dims_raw]
    negs = [validate_item(n, "negative_item", option_name) for n in raw.get("negative_items", [])]

    pos_w = sum(d["weight"] for d in dims)
    if pos_w <= 0:
        raise ValueError("选项 %r 的正权重之和必须 > 0" % option_name)

    return score_with_weights(option_name, dims, negs, thresholds, scale=1.0)


def score_with_weights(option_name, dims, negs, thresholds, scale):
    """scale 为正维度权重的整体缩放系数（用于扰动后重归一化基准）。"""
    pos_w = sum(d["weight"] for d in dims) * scale
    base = sum(d["score"] * d["weight"] for d in dims) * scale
    penalty = sum(n["score"] * n["weight"] for n in negs)  # weight<0，故为扣分
    total = base / pos_w + penalty  # 负项按绝对分值直接扣分，不归一化
    conf_weighted = (
        sum(d["score"] * d["weight"] * d["conf"] for d in dims) * scale
        + sum(n["score"] * n["weight"] * n["conf"] for n in negs)
    ) / pos_w
    avg_conf = (
        sum(d["weight"] * d["conf"] for d in dims) * scale
        + sum(abs(n["weight"]) * n["conf"] for n in negs)
    ) / (pos_w + sum(abs(n["weight"]) for n in negs))
    total = max(0.0, min(10.0, total))
    return {
        "option": option_name,
        "total": round(total, 4),
        "grade": grade_of(total, thresholds),
        "grade_label": GRADE_LABELS[grade_of(total, thresholds)],
        "conf_weighted_score": round(max(0.0, min(10.0, conf_weighted)), 4),
        "avg_conf": round(avg_conf, 4),
    }


def sensitivity(options_raw, thresholds, perturb, samples, seed):
    """对每个正权重独立施加 U(-perturb, +perturb) 均匀扰动，统计排名与等级稳定性。"""
    rng = random.Random(seed)
    parsed = []
    for raw in options_raw:
        name = raw.get("option", raw.get("name", "未命名选项"))
        dims = [validate_item(d, "dimension", name) for d in raw["dimensions"]]
        negs = [validate_item(n, "negative_item", name) for n in raw.get("negative_items", [])]
        parsed.append((name, dims, negs))

    base_results = [score_with_weights(n, d, g, thresholds, 1.0) for n, d, g in parsed]
    base_rank = {r["option"]: i for i, r in enumerate(
        sorted(base_results, key=lambda r: -r["total"]))}

    rank_change_counts = {r["option"]: 0 for r in base_results}
    grade_change_counts = {r["option"]: 0 for r in base_results}
    rank_samples = {r["option"]: [] for r in base_results}

    for _ in range(samples):
        perturbed = []
        for name, dims, negs in parsed:
            new_dims = [
                dict(d, weight=d["weight"] * (1.0 + rng.uniform(-perturb, perturb)))
                for d in dims
            ]
            perturbed.append(score_with_weights(name, new_dims, negs, thresholds, 1.0))
        order = sorted(perturbed, key=lambda r: -r["total"])
        for i, r in enumerate(order):
            rank_samples[r["option"]].append(i)
            if i != base_rank[r["option"]]:
                rank_change_counts[r["option"]] += 1
            if r["grade"] != base_results[[b["option"] for b in base_results].index(r["option"])]["grade"]:
                grade_change_counts[r["option"]] += 1

    stability = []
    for r in base_results:
        n = r["option"]
        stability.append({
            "option": n,
            "rank_stability": round(1.0 - rank_change_counts[n] / samples, 4),
            "grade_stability": round(1.0 - grade_change_counts[n] / samples, 4),
            "worst_rank": max(rank_samples[n]) + 1,
            "best_rank": min(rank_samples[n]) + 1,
        })
    return base_results, stability


def build_output(raw_input, thresholds, perturb, samples, seed):
    is_batch = isinstance(raw_input, list)
    options_raw = raw_input if is_batch else [raw_input]
    base_results, stability = sensitivity(options_raw, thresholds, perturb, samples, seed)
    ranked = sorted(base_results, key=lambda r: -r["total"])
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    stab_by_name = {s["option"]: s for s in stability}
    for r in base_results:
        r["sensitivity"] = stab_by_name[r["option"]]
    out = {
        "meta": {
            "perturbation": perturb,
            "samples": samples,
            "thresholds": thresholds,
            "conf_map": CONF_MAP,
        },
        "results": sorted(base_results, key=lambda r: r["rank"]),
    }
    if not is_batch:
        out["results"] = out["results"][0]
    return out


def main():
    p = argparse.ArgumentParser(
        description="多维度加权评分引擎：stdin 读入评分 JSON，输出总分/等级/置信度与 ±扰动敏感性分析。"
    )
    p.add_argument("--perturb", type=float, default=0.2,
                   help="权重扰动幅度（默认 0.2 即 ±20%%）")
    p.add_argument("--samples", type=int, default=200,
                   help="蒙特卡洛扰动采样次数（默认 200）")
    p.add_argument("--seed", type=int, default=42, help="随机种子（默认 42，保证可复现）")
    p.add_argument("--thresholds", type=str, default=None,
                   help='自定义等级阈值 JSON，如 \'{"A":8.0,"B":6.5,"C":5.0,"D":3.5}\'')
    args = p.parse_args()

    if not 0 < args.perturb < 1:
        p.error("--perturb 必须在 (0,1) 区间")
    if args.samples < 1:
        p.error("--samples 必须 >= 1")

    thresholds = dict(DEFAULT_THRESHOLDS)
    if args.thresholds:
        try:
            custom = json.loads(args.thresholds)
            for g in ("A", "B", "C", "D"):
                if g in custom:
                    thresholds[g] = float(custom[g])
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            p.error("--thresholds 解析失败: %s" % e)
    if not (thresholds["A"] > thresholds["B"] > thresholds["C"] > thresholds["D"] > 0):
        p.error("阈值必须满足 A > B > C > D > 0")

    try:
        raw_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print("错误：stdin 不是合法 JSON: %s" % e, file=sys.stderr)
        sys.exit(2)

    try:
        out = build_output(raw_input, thresholds, args.perturb, args.samples, args.seed)
    except ValueError as e:
        print("输入校验失败: %s" % e, file=sys.stderr)
        sys.exit(2)

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
