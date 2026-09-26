#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
commute_scoring_bridge.py — 通勤成本核算与评分桥接器

纯标准库。stdin 读 JSON，stdout 出 multi-dimensional-option-scoring 兼容的
dimensions JSON（每项含 score/weight/conf/锚点说明/data_cutoff 与成本构成）。

输入格式（顶层为数组，或 {"data_cutoff": "YYYY-MM-DD", "candidates": [...]}）：

[
  {
    "名称": "方案A：公交+地铁",
    "单程分钟": 55,          # 门到门（含候车/换乘/步行），非仅车程
    "换乘次数": 2,
    "单程票价": 6.0,          # 元
    "月出行次数": 22,         # 往返次数/月（脚本按 ×2 折算单程次数）
    "可利用时间比例": 0.1,    # 0-1；高铁整段 0.5-0.8，换乘/拥挤段取 0
    "时薪": 60,               # 元/小时，用于机会成本
    "可靠性": 0.9,            # 0-1，准点/稳定程度
    "conf": "estimated"      # 可选，覆盖自动判级
  }, ...
]

字段同时接受英文键：name / one_way_minutes / transfers / fare /
monthly_trips / usable_ratio / hourly_wage / reliability / conf。

输出：{"data_cutoff": ..., "options": [{"option": ..., "dimensions": [...],
"negative_items": [...], "cost_breakdown": {...}, "dominated": bool,
"rating_endpoint_payload": {...}}, ...]}

用法：
  cat candidates.json | python3 commute_scoring_bridge.py
  python3 commute_scoring_bridge.py --help
"""
import sys
import json
import datetime

VERSION = "1.0.0"

# 维度锚点（0-10 分，遵循 multi-dimensional-option-scoring 锚点规范）
TIME_ANCHORS = [  # (单程门到门分钟上限, 分值下限, 锚点描述)
    (30, 9, "单程≤30分钟：步行/短途接驳量级，近乎无通勤负担"),
    (60, 6, "单程31-60分钟：城市内常规通学量级"),
    (90, 3, "单程61-90分钟：长距离通学，疲劳显著"),
    (float("inf"), 0, "单程>90分钟：超长途，通常触及 L1 时长红线"),
]
MONEY_ANCHORS = [  # (月交通成本元上限, 分值下限, 锚点描述)
    (200, 9, "月≤200元：学生月票/短距公交量级"),
    (600, 6, "月201-600元：常规城市通勤量级"),
    (1500, 3, "月601-1500元：高频跨城/高铁通学量级"),
    (float("inf"), 0, "月>1500元：高成本，通常触及 L1 预算红线"),
]
OPP_ANCHORS = [  # (月机会成本元上限, 分值下限, 锚点描述)
    (500, 9, "月机会成本≤500元：通勤时间大多可利用或时耗极低"),
    (2000, 6, "月501-2000元：有可见的时间价值损失"),
    (5000, 3, "月2001-5000元：显著时间价值损失"),
    (float("inf"), 0, "月>5000元：通勤吞噬大量可支配时间"),
]

DEFAULT_WEIGHTS = {
    "时间成本": 0.30,
    "金钱成本": 0.25,
    "机会成本": 0.25,
    "可靠性": 0.20,
}

ALIASES = {
    "name": ["名称", "name"],
    "one_way_minutes": ["单程分钟", "one_way_minutes"],
    "transfers": ["换乘次数", "transfers"],
    "fare": ["单程票价", "fare"],
    "monthly_trips": ["月出行次数", "monthly_trips"],
    "usable_ratio": ["可利用时间比例", "usable_ratio"],
    "hourly_wage": ["时薪", "hourly_wage"],
    "reliability": ["可靠性", "reliability"],
    "conf": ["conf"],
}

REQUIRED = ["name", "one_way_minutes", "transfers", "fare",
            "monthly_trips", "usable_ratio", "hourly_wage", "reliability"]


def get_field(item, key, default=None):
    for alias in ALIASES[key]:
        if alias in item and item[alias] is not None:
            return item[alias]
    return default


def anchor_score(value, anchors):
    """按锚点表把数值映射为 0-10 分，并在档内线性插值。"""
    tiers = [(9, 10), (6, 7), (3, 4), (0, 2)]
    prev_limit = 0.0
    for i, (limit, lo, desc) in enumerate(anchors):
        if value <= limit:
            hi = tiers[i][1]
            if limit == float("inf"):
                return lo, desc
            # 档内线性插值：越接近档上限分越低
            span = limit - prev_limit
            frac = (value - prev_limit) / span if span > 0 else 0.0
            score = hi - frac * (hi - lo)
            return round(score, 2), desc
        prev_limit = limit
    return 0, anchors[-1][2]


def normalize(item, idx):
    rec = {}
    missing = []
    for key in REQUIRED:
        val = get_field(item, key)
        if val is None:
            missing.append(key)
        rec[key] = val
    if missing:
        raise ValueError(
            "候选 #%d 缺必填字段：%s（接受中文或英文键）" % (idx, ", ".join(missing)))
    rec["conf"] = get_field(item, "conf", "estimated")
    if rec["conf"] not in ("empirical", "estimated", "assumed"):
        raise ValueError("候选 #%d 的 conf 必须为 empirical/estimated/assumed" % idx)
    for k in ("one_way_minutes", "transfers", "fare", "monthly_trips",
              "usable_ratio", "hourly_wage", "reliability"):
        rec[k] = float(rec[k])
    for k in ("one_way_minutes", "transfers", "fare", "monthly_trips",
              "hourly_wage"):
        if rec[k] < 0:
            raise ValueError(
                "候选 #%d 字段 %s 不能为负数（收到 %s）；负分钟/负票价会产出 >10 的越界分数"
                % (idx, k, rec[k]))
    if not (0 <= rec["usable_ratio"] <= 1):
        raise ValueError("候选 #%d 可利用时间比例须在 0-1" % idx)
    if not (0 <= rec["reliability"] <= 1):
        raise ValueError("候选 #%d 可靠性须在 0-1" % idx)
    return rec


def build_option(rec):
    """核算四类成本并生成评分引擎兼容结构。"""
    m = rec["one_way_minutes"]
    trips = rec["monthly_trips"]          # 往返次数/月
    single_trips = trips * 2              # 单程次数/月
    monthly_hours = m * single_trips / 60.0
    monthly_money = rec["fare"] * single_trips
    usable_hours = monthly_hours * rec["usable_ratio"]
    wasted_hours = monthly_hours - usable_hours
    monthly_opp = rec["hourly_wage"] * wasted_hours
    monthly_total = monthly_money + monthly_opp

    t_score, t_anchor = anchor_score(m, TIME_ANCHORS)
    m_score, m_anchor = anchor_score(monthly_money, MONEY_ANCHORS)
    o_score, o_anchor = anchor_score(monthly_opp, OPP_ANCHORS)
    r_score = round(rec["reliability"] * 10, 2)
    r_anchor = "可靠性 %.2f：按准点/稳定程度直接映射 0-10" % rec["reliability"]

    dims = [
        {"name": "时间成本", "score": t_score, "weight": DEFAULT_WEIGHTS["时间成本"],
         "conf": rec["conf"], "anchor": t_anchor,
         "key_metric": "单程门到门分钟 = %.0f（含候车/换乘/步行，换乘 %d 次）"
                       % (m, int(rec["transfers"]))},
        {"name": "金钱成本", "score": m_score, "weight": DEFAULT_WEIGHTS["金钱成本"],
         "conf": rec["conf"], "anchor": m_anchor,
         "key_metric": "月交通费 = 单程票价 %.2f × 2 × 月往返 %.0f 次 = %.2f 元（优惠前）"
                       % (rec["fare"], trips, monthly_money)},
        {"name": "机会成本", "score": o_score, "weight": DEFAULT_WEIGHTS["机会成本"],
         "conf": rec["conf"], "anchor": o_anchor,
         "key_metric": "月机会成本 = 时薪 %.2f × 不可利用通勤小时 %.1f = %.2f 元"
                       % (rec["hourly_wage"], wasted_hours, monthly_opp)},
        {"name": "可靠性", "score": r_score, "weight": DEFAULT_WEIGHTS["可靠性"],
         "conf": rec["conf"], "anchor": r_anchor,
         "key_metric": "可靠性评分 = 可靠性 %.2f × 10" % rec["reliability"]},
    ]

    negative_items = []
    if m > 75:
        negative_items.append({
            "name": "疲劳惩罚",
            "score": min(10, round((m - 75) / 15, 2)),
            "weight": -0.10,
            "conf": "assumed",
            "score_means": "单程>75分钟的疲劳严重度 0-10，越大越危险",
        })

    cost_breakdown = {
        "时间成本": {
            "单程门到门分钟": m,
            "换乘次数": int(rec["transfers"]),
            "月通勤小时": round(monthly_hours, 2),
            "其中可利用小时": round(usable_hours, 2),
            "其中不可利用小时": round(wasted_hours, 2),
        },
        "金钱成本": {
            "单程票价元": rec["fare"],
            "月往返次数": trips,
            "月交通费元_优惠前": round(monthly_money, 2),
            "备注": "学生票/月票/计次票优惠需在 L1 门槛处另行核减",
        },
        "机会成本": {
            "时薪元": rec["hourly_wage"],
            "可利用时间比例": rec["usable_ratio"],
            "月机会成本元": round(monthly_opp, 2),
        },
        "月综合成本元_金钱加机会": round(monthly_total, 2),
    }

    return {
        "option": rec["name"],
        "dimensions": dims,
        "negative_items": negative_items,
        "cost_breakdown": cost_breakdown,
        "rating_endpoint_payload": {
            "option": rec["name"],
            "commute": {
                "one_way_minutes": m,
                "transfers": int(rec["transfers"]),
                "monthly_money_cost": round(monthly_money, 2),
                "monthly_opportunity_cost": round(monthly_opp, 2),
                "reliability": rec["reliability"],
                "conf": rec["conf"],
            },
        },
    }


def mark_dominated(options):
    """L2 帕累托：在 (时间↓, 金钱↓, 机会↓) 三目标上标记被支配方案。"""
    def vec(o):
        cb = o["cost_breakdown"]
        return (cb["时间成本"]["单程门到门分钟"],
                cb["金钱成本"]["月交通费元_优惠前"],
                cb["机会成本"]["月机会成本元"])
    for o in options:
        o["dominated"] = False
    for i, a in enumerate(options):
        va = vec(a)
        for j, b in enumerate(options):
            if i == j:
                continue
            vb = vec(b)
            if all(x <= y for x, y in zip(vb, va)) and any(x < y for x, y in zip(vb, va)):
                a["dominated"] = True
                a["dominated_by"] = b["option"]
                break
    return options


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return 0
    weights_override = None
    if "--weights" in sys.argv:
        i = sys.argv.index("--weights")
        weights_override = json.loads(sys.argv[i + 1])

    raw = sys.stdin.read().strip()
    if not raw:
        print("错误：stdin 为空。用 --help 查看输入格式。", file=sys.stderr)
        return 1
    payload = json.loads(raw)
    if isinstance(payload, dict):
        data_cutoff = payload.get("data_cutoff")
        candidates = payload.get("candidates", [])
    else:
        data_cutoff = None
        candidates = payload
    if not data_cutoff:
        data_cutoff = datetime.date.today().isoformat()
    if not candidates:
        print("错误：候选数组为空。", file=sys.stderr)
        return 1

    options = []
    for idx, item in enumerate(candidates):
        rec = normalize(item, idx)
        opt = build_option(rec)
        if weights_override:
            for d in opt["dimensions"]:
                if d["name"] in weights_override:
                    d["weight"] = float(weights_override[d["name"]])
        options.append(opt)
    options = mark_dominated(options)

    out = {
        "schema": "multi-dimensional-option-scoring.dimensions.v1",
        "generator": "commute_scoring_bridge.py v%s" % VERSION,
        "data_cutoff": data_cutoff,
        "weight_defaults": DEFAULT_WEIGHTS,
        "note": ("dimensions 可直接并入 multi-dimensional-option-scoring 的 "
                 "scoring_engine.py 输入；weight 为默认值，可在评分侧覆盖。"
                 "dominated=true 的方案已被帕累托支配，建议先淘汰。"),
        "options": options,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, json.JSONDecodeError) as e:
        print("错误：%s" % e, file=sys.stderr)
        sys.exit(1)
