#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transition_scoring_bridge.py — 医学转行候选 → 评分引擎桥接器

纯标准库。stdin 读转行候选 JSON，stdout 出 multi-dimensional-option-scoring
兼容的 dimensions JSON（顶层含 data_cutoff，dimensions 每项含
name/score/weight/conf，conf 为 empirical/estimated/assumed 字符串等级），
并对硬约束未达标的候选打一票否决标记（vetoed=true，喂入评分引擎前剔除）。

输入格式（顶层为数组，或 {"data_cutoff": "YYYY-MM-DD", "candidates": [...]}）：

[
  {
    "名称": "医学写作",                 # 必填
    "门槛达标度": 0.8,                  # 0-1，证书/学历/经验的达标比例
    "预期年收入下限": 8,                # 万元/年，必填
    "预期年收入上限": 12,               # 万元/年，必填，>=下限
    "三年成长空间": 7,                  # 0-10
    "风险": 3,                          # 0-10，越大越危险（负权重扣分项）
    "沉没成本": 4,                      # 0-10，转行放弃的既有投入（负权重扣分项）
    "城市约束匹配": 1.0,                # 0-1，1=完全不受城市限制（可远程）
    "硬约束达标": true,                 # 可选，默认 true；false 即一票否决
    "硬约束未达标项": ["年龄超限"],      # 可选；非空列表同样触发一票否决
    "conf": "estimated"                # 可选，覆盖自动判级
  }, ...
]

字段同时接受英文键：name / threshold_fit / income_low / income_high /
growth_3y / risk / sunk_cost / city_match / hard_ok / hard_violations / conf。
收入 conf 可用 "收入conf" / income_conf 单独指定（默认跟随候选 conf；
行业收入区间通常应标 estimated）。

输出：{"schema": ..., "data_cutoff": ..., "options": [{"option": ...,
"dimensions": [...], "negative_items": [...], "vetoed": bool,
"veto_reasons": [...], "derived": {...}}, ...]}

端到端用法（提取 .options 中未否决项喂入 scoring_engine.py）：
  cat candidates.json | python3 transition_scoring_bridge.py > bridge_out.json
  python3 - <<'EOF'
  import json
  d = json.load(open("bridge_out.json"))
  opts = [{"option": o["option"], "dimensions": o["dimensions"],
           "negative_items": o["negative_items"]}
          for o in d["options"] if not o["vetoed"]]
  json.dump(opts, open("engine_input.json", "w"), ensure_ascii=False)
  EOF
  cat engine_input.json | python3 scoring_engine.py   # multi-dimensional-option-scoring 侧

  python3 transition_scoring_bridge.py --help
"""
import sys
import json
import datetime

VERSION = "1.0.0"

CONF_LEVELS = ("empirical", "estimated", "assumed")

# 默认权重（正权重之和 = 1，可在评分侧覆盖）
DEFAULT_WEIGHTS = {
    "门槛可达性": 0.25,   # 门槛达标度直接决定转行可行性，权重次高
    "收益水平": 0.30,     # 转行决策首要目标通常是收入底线与提升
    "成长空间": 0.20,     # 3 年成长空间反映赛道中期价值
    "城市适配": 0.25,     # 城市约束是硬约束之外的软性位置匹配
}

NEGATIVE_WEIGHTS = {
    "职业风险": -0.15,    # |weight*score| 上限 1.5 分，不超总分 30%
    "沉没成本": -0.10,    # |weight*score| 上限 1.0 分
}

# 收益锚点：按预期年收入区间中点（万元/年）映射 0-10 分，档内线性插值
# (中点下限万元, 分值下限, 锚点描述)；分档参照 option_library.md 收入量级
INCOME_ANCHORS = [
    (0, 0, "年收入中点<8万：低于多数转行候选的收入底线"),
    (8, 3, "年收入中点8-15万：转行起步常规量级"),
    (15, 6, "年收入中点15-25万：资深/高门槛岗位量级"),
    (25, 9, "年收入中点≥25万：头部岗位量级"),
]
INCOME_TIER_HI = [2, 4, 7, 10]  # 各档分值上限

ALIASES = {
    "name": ["名称", "name"],
    "threshold_fit": ["门槛达标度", "threshold_fit"],
    "income_low": ["预期年收入下限", "income_low"],
    "income_high": ["预期年收入上限", "income_high"],
    "growth_3y": ["三年成长空间", "growth_3y"],
    "risk": ["风险", "risk"],
    "sunk_cost": ["沉没成本", "sunk_cost"],
    "city_match": ["城市约束匹配", "city_match"],
    "hard_ok": ["硬约束达标", "hard_ok"],
    "hard_violations": ["硬约束未达标项", "hard_violations"],
    "conf": ["conf"],
    "income_conf": ["收入conf", "income_conf"],
}

REQUIRED = ["name", "threshold_fit", "income_low", "income_high",
            "growth_3y", "risk", "sunk_cost", "city_match"]


def get_field(item, key, default=None):
    for alias in ALIASES[key]:
        if alias in item and item[alias] is not None:
            return item[alias]
    return default


def income_score(mid):
    """按收入锚点表把年收入中点（万元）映射为 0-10 分，档内线性插值。"""
    for i, (lo_lim, lo_score, desc) in enumerate(INCOME_ANCHORS):
        hi_lim = (INCOME_ANCHORS[i + 1][0]
                  if i + 1 < len(INCOME_ANCHORS) else float("inf"))
        if lo_lim <= mid < hi_lim or (hi_lim == float("inf") and mid >= lo_lim):
            hi_score = INCOME_TIER_HI[i]
            if hi_lim == float("inf"):
                return float(hi_score), desc
            frac = (mid - lo_lim) / (hi_lim - lo_lim)
            return round(lo_score + frac * (hi_score - lo_score), 2), desc
    return 0.0, INCOME_ANCHORS[0][2]


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
    if rec["conf"] not in CONF_LEVELS:
        raise ValueError("候选 #%d 的 conf 必须为 %s 之一" % (idx, "/".join(CONF_LEVELS)))
    rec["income_conf"] = get_field(item, "income_conf", rec["conf"])
    if rec["income_conf"] not in CONF_LEVELS:
        raise ValueError("候选 #%d 的 income_conf 必须为 %s 之一" % (idx, "/".join(CONF_LEVELS)))

    for k in ("threshold_fit", "income_low", "income_high", "growth_3y",
              "risk", "sunk_cost", "city_match"):
        rec[k] = float(rec[k])
    for k in ("threshold_fit", "city_match"):
        if not 0 <= rec[k] <= 1:
            raise ValueError("候选 #%d 字段 %s 须在 0-1（收到 %s）" % (idx, k, rec[k]))
    for k in ("growth_3y", "risk", "sunk_cost"):
        if not 0 <= rec[k] <= 10:
            raise ValueError("候选 #%d 字段 %s 须在 0-10（收到 %s）" % (idx, k, rec[k]))
    if rec["income_low"] < 0 or rec["income_high"] < 0:
        raise ValueError("候选 #%d 收入不能为负" % idx)
    if rec["income_high"] < rec["income_low"]:
        raise ValueError("候选 #%d 预期年收入上限(%s)不能低于下限(%s)"
                         % (idx, rec["income_high"], rec["income_low"]))

    hard_ok = get_field(item, "hard_ok", True)
    if isinstance(hard_ok, str):
        hard_ok = hard_ok.strip().lower() not in ("false", "0", "否", "no")
    rec["hard_ok"] = bool(hard_ok)
    violations = get_field(item, "hard_violations", []) or []
    if isinstance(violations, str):
        violations = [violations]
    rec["hard_violations"] = list(violations)
    return rec


def build_option(rec):
    """把转行候选转成评分引擎兼容结构，含一票否决标记。"""
    mid = (rec["income_low"] + rec["income_high"]) / 2.0
    inc_score, inc_anchor = income_score(mid)

    dims = [
        {"name": "门槛可达性",
         "score": round(rec["threshold_fit"] * 10, 2),
         "weight": DEFAULT_WEIGHTS["门槛可达性"],
         "conf": rec["conf"],
         "anchor": "门槛达标度 %.2f × 10（证书/学历/经验达标比例）" % rec["threshold_fit"],
         "key_metric": "门槛可达性分 = 门槛达标度 %.2f × 10" % rec["threshold_fit"]},
        {"name": "收益水平",
         "score": inc_score,
         "weight": DEFAULT_WEIGHTS["收益水平"],
         "conf": rec["income_conf"],
         "anchor": inc_anchor,
         "key_metric": "收入中点 = (%.1f + %.1f)/2 = %.1f 万元/年，按锚点档内插值"
                       % (rec["income_low"], rec["income_high"], mid)},
        {"name": "成长空间",
         "score": rec["growth_3y"],
         "weight": DEFAULT_WEIGHTS["成长空间"],
         "conf": rec["conf"],
         "anchor": "3 年成长空间自评 %.1f/10（评分侧须按锚点表复核）" % rec["growth_3y"],
         "key_metric": "成长空间分 = 三年成长空间 %.1f（直接采用 0-10 输入）" % rec["growth_3y"]},
        {"name": "城市适配",
         "score": round(rec["city_match"] * 10, 2),
         "weight": DEFAULT_WEIGHTS["城市适配"],
         "conf": rec["conf"],
         "anchor": "城市约束匹配 %.2f × 10（1=可远程/不受限）" % rec["city_match"],
         "key_metric": "城市适配分 = 城市约束匹配 %.2f × 10" % rec["city_match"]},
    ]

    negative_items = [
        {"name": "职业风险",
         "score": rec["risk"],
         "weight": NEGATIVE_WEIGHTS["职业风险"],
         "conf": rec["conf"],
         "score_means": "风险严重度 0-10，越大越危险（行业周期/岗位稳定性/合规风险）"},
        {"name": "沉没成本",
         "score": rec["sunk_cost"],
         "weight": NEGATIVE_WEIGHTS["沉没成本"],
         "conf": rec["conf"],
         "score_means": "转行放弃的既有投入 0-10（规培年限/执业积累/编制），越大越痛"},
    ]

    vetoed = (not rec["hard_ok"]) or bool(rec["hard_violations"])
    veto_reasons = list(rec["hard_violations"])
    if not rec["hard_ok"] and not veto_reasons:
        veto_reasons.append("硬约束达标=false（未逐条列明，须回第 3 步补录否决原因）")

    return {
        "option": rec["name"],
        "dimensions": dims,
        "negative_items": negative_items,
        "vetoed": vetoed,
        "veto_reasons": veto_reasons,
        "derived": {
            "收入中点_万元每年": round(mid, 2),
            "收益锚点分": inc_score,
        },
        "rating_endpoint_payload": {
            "option": rec["name"],
            "transition": {
                "threshold_fit": rec["threshold_fit"],
                "income_range_wan": [rec["income_low"], rec["income_high"]],
                "growth_3y": rec["growth_3y"],
                "risk": rec["risk"],
                "sunk_cost": rec["sunk_cost"],
                "city_match": rec["city_match"],
                "vetoed": vetoed,
                "conf": rec["conf"],
            },
        },
    }


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

    n_vetoed = sum(1 for o in options if o["vetoed"])
    out = {
        "schema": "multi-dimensional-option-scoring.dimensions.v1",
        "generator": "transition_scoring_bridge.py v%s" % VERSION,
        "data_cutoff": data_cutoff,
        "weight_defaults": DEFAULT_WEIGHTS,
        "negative_weight_defaults": NEGATIVE_WEIGHTS,
        "note": ("dimensions 可直接并入 multi-dimensional-option-scoring 的 "
                 "scoring_engine.py 输入（喂入前剔除 vetoed=true 的候选）；"
                 "weight 为默认值，可在评分侧用 --weights 覆盖。"
                 "收入类维度 conf 默认跟随候选 conf，行业收入区间应标 estimated。"),
        "stats": {"候选数": len(options), "一票否决数": n_vetoed,
                  "进入评分数": len(options) - n_vetoed},
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
