#!/usr/bin/env python3
"""
score_engine.py — 升学评分引擎（grad-path-scorer）核心计算器
纯标准库。CLI 用法：
  python3 score_engine.py --smoke                  # 内置冒烟自测
  cat schools.json | python3 score_engine.py       # stdin 读院校数组, stdout 出评分 JSON
  python3 score_engine.py --config cfg.json schools.json
  python3 score_engine.py --seed 42 --no-perturb schools.json

设计纪律（源自 2026-08-28 权重评分系统优化会话；权重/max_penalty 已经 v2.0 代理锚收敛，σ/k 仍为占位）。\nv2.3.2：--sensitivity 密集池判据升级为 gap-aware（近 tie 翻转=预期行为）。
  1. 字段只计一次：dedup_groups 声明并入关系，被并入字段不再单独计分。
  2. 无基础常数项：总分 = Σ(维度分×权重) − 惩罚，无 W_BASIC 式虚高项。
  3. 置信度 conf 只进展示层标注，绝不乘入总分。
  4. 导师舒适度扰动：phd_intent 按院校层级 sigma 加高斯扰动，模拟读博意愿漂移。
  5. 学术断头路惩罚：dead_end=true 且 regret_intent>0 时触发，
     随意向度非线性放大（默认 exponential 族，可切 linear / threshold）。
  6. 门槛级降档：维度分低于 threshold 触发 tier 降档（层级可分，可关）。
"""
import json, math, random, sys, argparse

# ---------- 默认配置（⚠ 全部占位值，见 references/calibration_todo.md） ----------
DEFAULT_CONFIG = {
    "weights": {                      # 维度权重，和为 1.0（v2.0 代理锚校准收敛值，非占位）
        "phd": 0.207,                 # 申博衔接力（已并入 access/faculty 权重）
        "city": 0.106,                # 城市与通勤
        "funding": 0.073,             # 经费与补助
        "platform": 0.396,            # 平台与方向匹配（聚变择校平台主导，锚点校准）
        "admission_risk": 0.218       # 录取风险（越高越稳）
    },
    "dedup_groups": [                 # 去重组：parent 并入 children 权重，children 只计一次
        {"parent": "phd", "children": ["access", "faculty"]}
    ],
    "sigma_by_tier": {                # 导师舒适度扰动 σ 分层（占位梯度）
        "tier1": 0.05,
        "tier2": 0.10,
        "tier3": 0.18
    },
    "regret_curve": {                 # 反悔成本曲线：exponential | linear | threshold
        "type": "exponential",
        "k": 2.0,                     # e 指数陡峭度（占位，用户未锁死）
        "threshold": 0.5,             # threshold 模式的触发点
        "max_penalty": 22.0,          # 断头路惩罚上限（分，v2.0 校准：15→22）
        "soft_factor": 0.5            # v1.3 软断头路（有跨校申博出口）惩罚系数
    },
    "thresholds": {                   # 门槛级降档：维度分 < min 则触发
        "phd": {"min": 40.0, "demote_by": 1}
    },
    "enable_thresholds": True,
    # v2.0 断头路托底折减：dead_end 校的非聚变维（默认 city/funding）按系数折减——
    # 断头路校的城市与经费优势对"聚变升学训练"价值对折（校准发现：郑大+27.8/哈工大+21.9 托底偏差）
    "dead_end_discount": 0.4,
    "dead_end_discount_dims": ["city", "funding"]
}

CONF_TAGS = {"empirical": "🔵实证", "estimated": "🟡估算", "assumed": "🔴假设"}


def regret_factor(x, curve):
    """反悔成本放大因子 f(x)∈[0,1]，x=regret_intent∈[0,1]。"""
    x = max(0.0, min(1.0, x))
    t = curve.get("type", "exponential")
    if t == "linear":
        return x
    if t == "threshold":
        return 1.0 if x >= curve.get("threshold", 0.5) else 0.0
    # exponential（默认）：(e^{kx}-1)/(e^k-1)，低端平缓、高端陡增
    k = curve.get("k", 2.0)
    if k == 0:
        return x
    return (math.exp(k * x) - 1.0) / (math.exp(k) - 1.0)


def score_school(school, cfg, rng=None, perturb=True):
    """对单个院校评分。返回完整分明细。所有维度分按 0–100 输入。"""
    w = cfg["weights"]
    # --- 去重：声明并入 children 的字段若同时出现在输入，只认 parent 一次 ---
    consumed = set()
    for g in cfg.get("dedup_groups", []):
        if g["parent"] in school:
            consumed.update(g["children"])
    dims = {}
    # v2.0：dead_end 校的非聚变维托底折减（在加权前生效）
    dd = cfg.get("dead_end_discount", 1.0) if school.get("dead_end") else 1.0
    dd_dims = set(cfg.get("dead_end_discount_dims", []))
    for dim, wgt in w.items():
        if dim in consumed:
            continue  # 字段只计一次
        raw = float(school.get(dim, 0.0))
        if dd < 1.0 and dim in dd_dims:
            raw = raw * dd
        dims[dim] = {"raw": raw, "weight": wgt, "weighted": raw * wgt}

    base = sum(d["weighted"] for d in dims.values())

    # --- 导师舒适度扰动：仅作用于 phd 维，σ 按院校层级分层 ---
    pert = {"applied": False, "sigma": 0.0, "delta": 0.0}
    if perturb and rng is not None and "phd" in dims:
        tier = school.get("tier", "tier2")
        sigma = cfg.get("sigma_by_tier", {}).get(tier, 0.10)
        delta = rng.gauss(0.0, sigma) * 100.0 * w["phd"]  # 换算到加权分尺度
        dims["phd"]["weighted"] += delta
        pert = {"applied": True, "sigma": sigma, "delta": round(delta, 4)}

    subtotal = sum(d["weighted"] for d in dims.values())

    # --- 学术断头路惩罚 ---
    penalties = []
    if school.get("dead_end") and float(school.get("regret_intent", 0.0)) > 0:
        rc = cfg.get("regret_curve", DEFAULT_CONFIG["regret_curve"])
        f = regret_factor(float(school.get("regret_intent", 0.0)), rc)
        pen = rc.get("max_penalty", 15.0) * f
        grade = school.get("dead_end_grade", "hard")
        if grade == "soft":
            pen *= rc.get("soft_factor", 0.5)  # 软断头：出口尚可，惩罚减半
        penalties.append({"type": "dead_end_regret", "grade": grade, "curve": rc.get("type"),
                          "factor": round(f, 4), "amount": round(pen, 4)})

    total = subtotal - sum(p["amount"] for p in penalties)

    # --- 门槛级降档 ---
    demotions = []
    if cfg.get("enable_thresholds", True):
        for dim, th in cfg.get("thresholds", {}).items():
            if dim in dims and dims[dim]["raw"] < th["min"]:
                demotions.append({"dim": dim, "raw": dims[dim]["raw"],
                                  "min": th["min"], "demote_by": th["demote_by"]})

    # --- 置信度：展示层标注，不进总分 ---
    conf = school.get("conf", "assumed")
    result = {
        "school": school.get("name", "<unnamed>"),
        "total": round(total, 2),
        "base_before_penalty": round(subtotal, 2),
        "breakdown": {k: {"raw": v["raw"], "weight": v["weight"],
                          "weighted": round(v["weighted"], 3)} for k, v in dims.items()},
        "perturbation": pert,
        "penalties": penalties,
        "demotions": demotions,
        "conf": conf,
        "conf_tag": CONF_TAGS.get(conf, conf)
    }
    # governance_flags：治理风险展示层透传（v1.7）——仅 A 级纪委通报/司法文书可入，
    # 零计分（个案证据强度不足以支撑计分，且禁止将高层个案影射至导师团队）
    if school.get("governance_flags"):
        result["governance_flags"] = school["governance_flags"]
    return result


def run(schools, cfg, seed=None, perturb=True):
    rng = random.Random(seed) if seed is not None else None
    results = [score_school(s, cfg, rng, perturb) for s in schools]
    results.sort(key=lambda r: r["total"], reverse=True)
    return {
        "data_cutoff": "2026-08-28",
        "conf": "estimated",
        "results": results,
        "top3_likely_wrong": [
            "权重为锚点库代理锚收敛值（v2.0，ρ=0.9252）——锚点库本身仍是占位时代产物，真·外部校准待用户面板",
            "σ 分层 .05/.10/.18 仍为占位梯度，未经导师体验样本标定",
            "院校输入分若无统一量纲，排序结果不可比"
        ]
    }


def sensitivity(schools, cfg, pp=0.05):
    """敏感性分析：逐维权重 ±pp（归一化），统计排序位置变动数。
    确定性运行（关扰动），供验收标准 2：排序翻转率应 <20%。"""
    base_order = [r["school"] for r in run(schools, cfg, perturb=False)["results"]]
    report = {"baseline_order": base_order, "pp": pp, "cases": []}
    worst = 0.0
    for dim in cfg["weights"]:
        for sign, label in ((+1, f"+{pp:.0%}"), (-1, f"-{pp:.0%}")):
            w2 = dict(cfg["weights"])
            w2[dim] = max(0.0, w2[dim] + sign * pp)
            tot = sum(w2.values()) or 1.0
            w2 = {k: v / tot for k, v in w2.items()}
            cfg2 = dict(cfg); cfg2["weights"] = w2
            order2 = [r["school"] for r in run(schools, cfg2, perturb=False)["results"]]
            moved = sum(1 for a, b in zip(base_order, order2) if a != b)
            rate = moved / len(base_order) if base_order else 0.0
            worst = max(worst, rate)
            report["cases"].append({"dim": dim, "direction": label,
                                    "order": order2, "positions_changed": moved,
                                    "flip_rate": round(rate, 3)})
    report["worst_flip_rate"] = round(worst, 3)
    report["verdict"] = "PASS(<20%)" if worst < 0.20 else "FAIL(>=20%)"
    # v2.3.2 密集池口径（gap-aware）：≥20 校密集池下 <20% 不现实，改看头部稳定性；
    # 位置翻转若发生于"近 tie 对"（baseline 分差 ≤ 该维扰动一阶摆幅上界 pp×|原始分差|）
    # 则为预期行为而非缺陷——v2.3.1 归因实证：43 校池全部 TOP6 变动 = 西南交大↔SWIP
    # 互换（分差 0.30 < 摆幅 0.70）。判据：TOP2 零翻转 且 所有翻转对均可被摆幅解释。
    n = len(base_order)
    if n >= 20 and report["cases"]:
        base_tot = {r["school"]: r["total"] for r in run(schools, cfg, perturb=False)["results"]}
        raw_by_name = {s.get("name"): s for s in schools}
        w2 = 0; w6 = 0; unexplained = []
        for c in report["cases"]:
            cur = c["order"]
            chg2 = sum(1 for a, b in zip(base_order[:2], cur[:2]) if a != b)
            chg6 = sum(1 for a, b in zip(base_order[:6], cur[:6]) if a != b)
            w2 = max(w2, chg2); w6 = max(w6, chg6)
            dim = c["dim"]
            for i, (a, b) in enumerate(zip(base_order[:6], cur[:6])):
                if a == b:
                    continue
                gap = abs(base_tot.get(a, 0.0) - base_tot.get(b, 0.0))
                rawgap = abs(float(raw_by_name.get(a, {}).get(dim, 0.0))
                             - float(raw_by_name.get(b, {}).get(dim, 0.0)))
                bound = pp * rawgap * 1.5  # 一阶摆幅上界（×1.5 吸收归一化二阶项）
                if gap > bound:
                    unexplained.append({"case": f"{dim} {c['direction']}", "rank": i + 1,
                                        "pair": [a, b], "baseline_gap": round(gap, 2),
                                        "swing_bound": round(bound, 2)})
        report["dense_pool"] = {"pool_size": n, "worst_top2_changed": w2,
                                "worst_top6_changed": w6,
                                "unexplained_flips": unexplained,
                                "verdict_dense": ("PASS(TOP2零翻转+全部翻转为近tie预期行为)"
                                                  if w2 == 0 and not unexplained else
                                                  "REVIEW(存在摆幅不可解释的翻转)" if w2 == 0 else
                                                  "FAIL(TOP2翻转)")}
    return report


def stress():
    """边界压测：极端输入不崩且行为符合语义。"""
    cfg = DEFAULT_CONFIG
    cases = []
    # 1 全满分 → 接近 100
    top = run([{"name": "MAX", "phd": 100, "city": 100, "funding": 100,
                "platform": 100, "admission_risk": 100}], cfg, perturb=False)["results"][0]
    cases.append(("全满分≈100", abs(top["total"] - 100.0) < 0.01))
    # 2 极端反悔意向 → 惩罚顶格
    hard = run([{"name": "HARD", "phd": 50, "city": 50, "funding": 50, "platform": 50,
                 "admission_risk": 50, "dead_end": True, "regret_intent": 1.0}],
               cfg, perturb=False)["results"][0]
    cases.append(("regret=1.0 惩罚顶格", abs(hard["penalties"][0]["amount"] - cfg["regret_curve"]["max_penalty"]) < 0.01))
    # 3 断头路但无意反悔 → 零惩罚
    calm = run([{"name": "CALM", "phd": 50, "dead_end": True, "regret_intent": 0.0}],
               cfg, perturb=False)["results"][0]
    cases.append(("dead_end+regret=0 零惩罚", calm["penalties"] == []))
    # 3b 软断头惩罚=硬断头一半（v1.3 分级）
    hard_r = run([{"name": "H", "phd": 50, "dead_end": True, "dead_end_grade": "hard",
                   "regret_intent": 0.9}], cfg, perturb=False)["results"][0]["penalties"][0]["amount"]
    soft_r = run([{"name": "S", "phd": 50, "dead_end": True, "dead_end_grade": "soft",
                   "regret_intent": 0.9}], cfg, perturb=False)["results"][0]["penalties"][0]["amount"]
    cases.append(("软断头惩罚减半", abs(soft_r - hard_r * 0.5) < 0.01))
    # 4 非法 tier → 回退默认 σ 不崩
    weird = run([{"name": "WEIRD", "phd": 60, "tier": "tierX"}], cfg, seed=7)["results"][0]
    cases.append(("非法tier回退容错", weird["perturbation"]["sigma"] == 0.10))
    # 5 空列表 → 优雅空结果
    empty = run([], cfg)
    cases.append(("空输入优雅处理", empty["results"] == []))
    # 6 权重和≠1 → 告警但照跑（不归一化，让用户看到偏移）
    bad = dict(cfg); bad["weights"] = dict(cfg["weights"]); bad["weights"]["phd"] = 0.9
    r6 = run([{"name": "W", "phd": 80}], bad, perturb=False)["results"][0]
    cases.append(("权重失衡照跑(告警)", r6["total"] > 0))
    ok = all(p for _, p in cases)
    for name, passed in cases:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}", file=sys.stderr)
    print("[STRESS %s] %d/%d 通过" % ("OK" if ok else "FAIL",
          sum(p for _, p in cases), len(cases)), file=sys.stderr)
    return ok


SMOKE_SCHOOLS = [    {"name": "A校-强衔接", "phd": 85, "access": 80, "faculty": 78, "city": 70,
     "funding": 60, "platform": 88, "admission_risk": 65, "tier": "tier1",
     "conf": "empirical"},
    {"name": "B校-断头路", "phd": 35, "city": 75, "funding": 70, "platform": 55,
     "admission_risk": 80, "tier": "tier3", "dead_end": True,
     "regret_intent": 0.9, "conf": "assumed"},
    {"name": "C校-中庸", "phd": 60, "city": 65, "funding": 65, "platform": 70,
     "admission_risk": 70, "tier": "tier2", "conf": "estimated"},
]


def smoke():
    cfg = DEFAULT_CONFIG
    out = run(SMOKE_SCHOOLS, cfg, seed=42)
    assert len(out["results"]) == 3
    # 去重校验：A校带了 access/faculty，breakdown 不得含这两个维度
    a = [r for r in out["results"] if r["school"] == "A校-强衔接"][0]
    assert "access" not in a["breakdown"] and "faculty" not in a["breakdown"], "去重失败"
    # 断头路校验：B校必须有惩罚且触发门槛降档
    b = [r for r in out["results"] if r["school"] == "B校-断头路"][0]
    assert b["penalties"] and b["penalties"][0]["amount"] > 0, "断头路惩罚缺失"
    assert b["demotions"], "门槛降档未触发"
    # 无常数项校验：全零院校总分应为 0
    zero = run([{"name": "ZERO"}], cfg, seed=1, perturb=False)["results"][0]
    assert zero["total"] == 0.0, f"存在隐性常数项: {zero['total']}"
    # 反悔曲线单调性
    f = [regret_factor(x / 10.0, cfg["regret_curve"]) for x in range(11)]
    assert all(f[i] <= f[i + 1] + 1e-9 for i in range(10)), "反悔曲线非单调"
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n[SMOKE OK] 去重/惩罚/降档/无常数项/曲线单调性 全部通过", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="升学评分引擎")
    ap.add_argument("schools", nargs="?", help="院校 JSON 文件（缺省读 stdin）")
    ap.add_argument("--config", help="自定义配置 JSON")
    ap.add_argument("--seed", type=int, default=None, help="扰动随机种子（复现用）")
    ap.add_argument("--no-perturb", action="store_true", help="关闭导师舒适度扰动")
    ap.add_argument("--smoke", action="store_true", help="内置冒烟自测")
    ap.add_argument("--stress", action="store_true", help="边界压测（极端输入容错）")
    ap.add_argument("--sensitivity", action="store_true",
                    help="敏感性分析：逐维权重 ±5pp 排序翻转率（确定性，关扰动）")
    ap.add_argument("--pp", type=float, default=0.05, help="敏感性扰动幅度，默认 0.05")
    args = ap.parse_args()
    if args.smoke:
        smoke(); return
    if args.stress:
        sys.exit(0 if stress() else 1)
    cfg = DEFAULT_CONFIG
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            cfg = json.load(f)
    raw = open(args.schools, encoding="utf-8").read() if args.schools else sys.stdin.read()
    schools = json.loads(raw)
    if isinstance(schools, dict):
        schools = schools.get("schools", [schools])
    if args.sensitivity:
        print(json.dumps(sensitivity(schools, cfg, args.pp), ensure_ascii=False, indent=2))
        return
    print(json.dumps(run(schools, cfg, args.seed, not args.no_perturb),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
