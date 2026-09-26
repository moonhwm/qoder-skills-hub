#!/usr/bin/env python3
"""score_panel.py — 轻量面板评分器（admission-panel-analytics，L1 原型级）

评分公式（权重可配，默认对齐档案 8 维修正因子的核心 6 项）：
  score = w_fc·一志愿率 + w_lk·录取可能性 + w_nm·不考数一
        + w_rp·复试通过率(修正项) + w_sf·必达分安全度 - w_tm·推免比(惩罚)
  录取可能性 = sigmoid((参照分-最低分)/跨度)，跨度=中位分-最低分（缺省 40）
  必达分安全度 = clamp((考生预估分-必达分)/安全跨度, 0, 1)；无考生分则中性 0.5 并标注
敏感性：每个权重单独 ±20% 扰动（其余不变、不归一化），报告得分波动区间。
用法：
    python3 score_panel.py --smoke                       # 合成三校自测，exit=0
    python3 score_panel.py schools.json                  # {"schools":[...], "candidate_score":?, "weights":?}
    python3 score_panel.py schools.json --weights '{"first_choice_rate":0.5}'
输出：JSON {ranking[], sensitivity{}, assumptions[], top3_likely_wrong[], honesty}
"""
import json
import math
import sys

DEFAULT_WEIGHTS = {
    "first_choice_rate": 0.40,   # 一志愿率
    "likelihood": 0.25,          # 录取可能性
    "no_math1": 0.15,            # 不考数一
    "retest_pass": 0.10,         # 复试通过率修正
    "safety": 0.10,              # 必达分安全度
    "tuimian_penalty": 0.10,     # 推免惩罚（减项）
}
REF_SCORE = 290.0      # 录取可能性参照分（档案 xdf_nn 教师标签口径）
SPAN_DEFAULT = 40.0    # 分数跨度缺省
SAFETY_SPAN = 40.0     # 必达分安全度跨度
NEUTRAL = 0.5


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def _latest_record(entry):
    """接受面板 {"records":[...]} 或扁平最新年字段对象；返回 (record, notes)。"""
    notes = []
    if isinstance(entry, dict) and isinstance(entry.get("records"), list) and entry["records"]:
        recs = [r for r in entry["records"] if isinstance(r, dict)
                and r.get("total_admit") is not None and r.get("first_choice_admit") is not None]
        dropped = len(entry["records"]) - len(recs)
        if dropped:
            notes.append("剔除 %d 条关键字段缺测的年份记录" % dropped)
        if not recs:
            return None, notes + ["无有效年份记录"]
        recs.sort(key=lambda r: r.get("year") or 0)
        return dict(recs[-1]), notes
    if isinstance(entry, dict):
        return dict(entry), notes
    return None, notes + ["学校条目不是对象"]


def _terms(rec, candidate_score, notes):
    """计算 6 项因子；缺测按中性/0 处理并登记 assumptions。"""
    ta, fc, rc = rec.get("total_admit"), rec.get("first_choice_admit"), rec.get("retest_count")
    fcr = rec.get("first_choice_rate")
    if fcr is None and isinstance(ta, (int, float)) and ta > 0 and isinstance(fc, (int, float)):
        fcr = fc / ta
    if fcr is None:
        notes.append("一志愿率缺测，按中性 0.5 计")
        fcr = NEUTRAL
    ms, md, mu = rec.get("min_score"), rec.get("median_score"), rec.get("must_score")
    if isinstance(ms, (int, float)):
        span = (md - ms) if isinstance(md, (int, float)) and md > ms else SPAN_DEFAULT
        lk = 1.0 / (1.0 + math.exp(-(REF_SCORE - ms) / span))
    else:
        notes.append("最低分缺测，录取可能性按中性 0.5 计")
        lk = NEUTRAL
    m1 = rec.get("math1")
    nm = {True: 0.0, False: 1.0}.get(m1) if isinstance(m1, bool) else None
    if nm is None:
        notes.append("数一标志未知，不考数一项按中性 0.5 计")
        nm = NEUTRAL
    rp = rec.get("retest_pass_rate")
    if rp is None and isinstance(rc, (int, float)) and rc > 0 and isinstance(fc, (int, float)):
        rp = fc / rc
    if rp is None:
        notes.append("复试通过率缺测，按中性 0.5 计")
        rp = NEUTRAL
    if isinstance(candidate_score, (int, float)) and isinstance(mu, (int, float)):
        sf = _clamp((candidate_score - mu) / SAFETY_SPAN)
    else:
        if not isinstance(candidate_score, (int, float)):
            notes.append("未提供考生预估分，必达分安全度按中性 0.5 计（提供 candidate_score 可提高精度）")
        elif not isinstance(mu, (int, float)):
            notes.append("必达分缺测，安全度按中性 0.5 计")
        sf = NEUTRAL
    tm = rec.get("tuimian_ratio")
    if tm is None:
        notes.append("推免比缺测，惩罚按 0 计（可能高估该校）")
        tm = 0.0
    return {"first_choice_rate": _clamp(fcr), "likelihood": lk, "no_math1": nm,
            "retest_pass": _clamp(rp), "safety": sf, "tuimian_penalty": _clamp(tm)}


def _score(terms, w):
    return (w["first_choice_rate"] * terms["first_choice_rate"]
            + w["likelihood"] * terms["likelihood"]
            + w["no_math1"] * terms["no_math1"]
            + w["retest_pass"] * terms["retest_pass"]
            + w["safety"] * terms["safety"]
            - w["tuimian_penalty"] * terms["tuimian_penalty"])


def score_panel(payload, weight_override=None):
    weights = dict(DEFAULT_WEIGHTS)
    if isinstance(payload.get("weights"), dict):
        weight_override = {**(weight_override or {}), **payload["weights"]}
    if weight_override:
        for k, v in weight_override.items():
            if k not in weights or not isinstance(v, (int, float)) or v < 0:
                return {"error": "非法权重项 %r=%r（允许键：%s，非负数）"
                        % (k, v, sorted(weights))}
            weights[k] = float(v)
    candidate_score = payload.get("candidate_score")
    schools = payload.get("schools")
    if not isinstance(schools, list) or not schools:
        return {"error": "输入缺少非空 schools 数组"}

    ranking, all_assumptions = [], []
    for entry in schools:
        name = entry.get("school", "未命名") if isinstance(entry, dict) else "未命名"
        rec, notes = _latest_record(entry)
        if rec is None:
            ranking.append({"school": name, "error": "; ".join(notes)})
            continue
        terms = _terms(rec, candidate_score, notes)
        s = _score(terms, weights)
        ranking.append({"school": name, "program": entry.get("program") or rec.get("program"),
                        "score": round(s, 4), "terms": {k: round(v, 4) for k, v in terms.items()},
                        "conf": rec.get("conf", "assumed"), "assumptions": notes})
        all_assumptions.extend("%s: %s" % (name, n) for n in notes)

    valid = [r for r in ranking if "score" in r]
    # 敏感性：每权重 ±20%（其余不变、不归一化）
    sens = {}
    for k in weights:
        w_up, w_dn = dict(weights), dict(weights)
        w_up[k], w_dn[k] = weights[k] * 1.2, weights[k] * 0.8
        deltas = []
        for entry, row in zip(schools, ranking):
            if "score" not in row:
                continue
            rec, notes = _latest_record(entry)
            terms = _terms(rec, candidate_score, [])
            deltas.append({"school": row["school"],
                           "down": round(_score(terms, w_dn) - row["score"], 4),
                           "up": round(_score(terms, w_up) - row["score"], 4)})
        sens[k] = deltas
    max_dev = max((max(abs(d["up"]), abs(d["down"])) for ds in sens.values() for d in ds),
                  default=0.0)
    valid.sort(key=lambda r: -r["score"])
    for i, r in enumerate(valid, 1):
        r["rank"] = i
    top3 = ["必达分≠录取线：必达分低仅代表复试线低，须另核录取实证",
            "缺测字段中性化可能高估/低估：见 assumptions 逐条复核",
            "本评分器为 L1 线性轻量模型，权重±20% 扰动下排名可能变化（见 sensitivity）"]
    if all_assumptions:
        top3[1] = "存在 %d 条缺测中性化假设，逐项复核后再交付" % len(all_assumptions)
    return {"weights": weights, "candidate_score": candidate_score,
            "ranking": ranking, "sensitivity": sens,
            "max_abs_deviation_under_20pct_perturbation": round(max_dev, 4),
            "assumptions": all_assumptions, "top3_likely_wrong": top3,
            "honesty": "L1 原型级轻量评分器；结论须经敏感性分析与三项偏见自查后方可交付；"
                       "跨域综合决策请交由 unified-decision-suite"}


def _smoke():
    schools = {"schools": [
        {"school": "示例乙（合成β·应最高）", "program": "070200", "records": [
            {"year": 2026, "total_admit": 75, "first_choice_admit": 75, "transfer_admit": 0,
             "retest_count": 82, "retest_pass_rate": 0.915, "min_score": 295,
             "median_score": 335, "must_score": 345, "math1": False, "first_choice_rate": 1.0,
             "transfer_rate": 0.0, "tuimian_ratio": 0.3, "conf": "empirical", "missing": []}]},
        {"school": "示例甲（合成α·居中）", "program": "082700", "records": [
            {"year": 2026, "total_admit": 38, "first_choice_admit": 20, "transfer_admit": 18,
             "retest_count": 20, "retest_pass_rate": 1.0, "min_score": 251,
             "median_score": 280, "must_score": 261, "math1": True, "first_choice_rate": 0.526,
             "transfer_rate": 0.474, "tuimian_ratio": 0.1, "conf": "empirical", "missing": []}]},
        {"school": "示例丙（合成γ·应最低）", "program": "070200", "records": [
            {"year": 2026, "total_admit": 25, "first_choice_admit": 5, "transfer_admit": 20,
             "retest_count": 25, "retest_pass_rate": 0.2, "min_score": 300,
             "median_score": 340, "must_score": 350, "math1": True, "first_choice_rate": 0.2,
             "transfer_rate": 0.8, "tuimian_ratio": 0.4, "conf": "estimated", "missing": []}]},
    ], "candidate_score": 330}
    res = score_panel(schools)
    ranks = [r["school"] for r in res["ranking"]]
    assert ranks[0].startswith("示例乙"), res
    assert ranks[-1].startswith("示例丙"), res
    assert all("score" in r for r in res["ranking"]), res
    assert res["max_abs_deviation_under_20pct_perturbation"] > 0, res
    # 权重可配：把一志愿率权重拉满，β 仍应第一
    res2 = score_panel(schools, {"first_choice_rate": 1.0, "likelihood": 0.0,
                                 "no_math1": 0.0, "retest_pass": 0.0, "safety": 0.0,
                                 "tuimian_penalty": 0.0})
    assert res2["ranking"][0]["school"].startswith("示例乙"), res2
    assert abs(res2["ranking"][0]["score"] - 1.0) < 1e-9, res2
    out = {"smoke": "score_panel",
           "ranking": [{"rank": r["rank"], "school": r["school"], "score": r["score"],
                        "conf": r["conf"]} for r in res["ranking"]],
           "max_abs_deviation_under_20pct_perturbation":
               res["max_abs_deviation_under_20pct_perturbation"],
           "assumptions": res["assumptions"],
           "weight_override_check": {"first_choice_rate=1.0 时榜首": res2["ranking"][0]["school"]}}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("SMOKE OK: score_panel 自测通过（β>α>γ 排序、权重可配、敏感性非零）")
    return 0


def main(argv):
    if "--smoke" in argv:
        return _smoke()
    weight_override = None
    args = []
    it = iter(argv[1:])
    for a in it:
        if a == "--weights":
            try:
                weight_override = json.loads(next(it))
            except (StopIteration, json.JSONDecodeError) as e:
                print(json.dumps({"error": "--weights 参数解析失败: %s" % e},
                                 ensure_ascii=False))
                return 2
        elif not a.startswith("--"):
            args.append(a)
    try:
        text = open(args[0], encoding="utf-8").read() if args else sys.stdin.read()
        payload = json.loads(text)
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"error": "输入读取/解析失败: %s" % e}, ensure_ascii=False))
        return 2
    res = score_panel(payload, weight_override)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 2 if "error" in res else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
