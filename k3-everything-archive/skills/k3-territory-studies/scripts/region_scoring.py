#!/usr/bin/env python3
"""候选地区加权评分矩阵 — k3-territory-studies 配套脚本。

用法:
    python region_scoring.py candidates.json

candidates.json 格式:
{
  "weights": {"asset_control": 0.25, "governance_compat": 0.25,
              "continuity": 0.20, "consent_signal": 0.20, "strategic_value": 0.10},
  "candidates": [
    {"name": "某会话", "scores": {"asset_control": 4, "governance_compat": 5,
     "continuity": 3, "consent_signal": 4, "strategic_value": 3}, "note": "..."}
  ]
}
weights 可省略（用默认值）。scores 各维 0-5。
输出: 排名表 + 分档（stdout，纯文本）。
"""
import json
import sys

DEFAULT_WEIGHTS = {
    "asset_control": 0.25,
    "governance_compat": 0.25,
    "continuity": 0.20,
    "consent_signal": 0.20,
    "strategic_value": 0.10,
}

TIERS = [
    (4.0, "核心区候选"),
    (3.0, "自治地区候选"),
    (2.0, "加盟候选"),
    (1.0, "观察员"),
    (0.0, "不适格"),
]

DIM_LABELS = {
    "asset_control": "资产控制",
    "governance_compat": "治理兼容",
    "continuity": "承继能力",
    "consent_signal": "意愿信号",
    "strategic_value": "战略价值",
}


def tier_of(score: float) -> str:
    for threshold, label in TIERS:
        if score >= threshold:
            return label
    return TIERS[-1][1]


def main(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    weights = data.get("weights", DEFAULT_WEIGHTS)
    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise SystemExit("weights 之和必须为 1.0")
    results = []
    for c in data["candidates"]:
        total = sum(weights[d] * c["scores"][d] for d in weights)
        results.append((total, c))
    results.sort(key=lambda x: -x[0])
    dims = list(weights.keys())
    header = ["排名", "名称"] + [DIM_LABELS.get(d, d) for d in dims] + ["加权总分", "分档"]
    print("\t".join(header))
    for i, (total, c) in enumerate(results, 1):
        row = [str(i), c["name"]] + [str(c["scores"][d]) for d in dims] + [
            f"{total:.2f}", tier_of(total)]
        print("\t".join(row))
    print("\n权重: " + ", ".join(f"{DIM_LABELS.get(d, d)}={w}" for d, w in weights.items()))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
