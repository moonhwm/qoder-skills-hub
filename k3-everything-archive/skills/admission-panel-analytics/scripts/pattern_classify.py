#!/usr/bin/env python3
"""pattern_classify.py — 三录取模式判别 + 调剂窗口风险评级（admission-panel-analytics）

判别规则依据 references/admission_patterns.md：
  β 零调剂堡垒：连续≥3年零调剂(或调剂率≤0.05) 且 一志愿率≥0.90
  γ 高调剂陷阱：最新年一志愿率<0.30 且 (复试通过率<0.50 或 调剂率>0.70)
  α 过线即录：  最新年一志愿复试通过率≥0.98 且 进复试者全录(调剂为补录非竞争)
  优先级 β → γ → α → 未定型
窗口风险三因子：窗口时长 / 优先级档位 / 一志愿保护度（§3.6 合成规则）。
用法：
    python3 pattern_classify.py --smoke           # 合成 α/β/γ 三校自测，exit=0
    python3 pattern_classify.py school.json
    cat school.json | python3 pattern_classify.py
输出：JSON {pattern, window_risk, confidence, reason_chain[], warnings[], factors{}}
"""
import json
import sys

PASS_ALPHA = 0.98      # α 通过率阈值
BETA_MIN_YEARS = 3     # β 连续年数
BETA_FC_RATE = 0.90    # β 一志愿率
BETA_TR_RATE = 0.05    # β 调剂率容差
GAMMA_FC_RATE = 0.30   # γ 一志愿率
GAMMA_PASS = 0.50      # γ 复试通过率
GAMMA_TR_RATE = 0.70   # γ 调剂率
TIER_RISK = {"A&B": "低", "A": "低", "B": "低", "C": "中", "D": "高", "E": "高"}


def _derive(rec):
    """补全可派生字段；返回 (first_choice_rate, transfer_rate, retest_pass_rate)。"""
    ta, fc, tr, rc = (rec.get(k) for k in
                      ("total_admit", "first_choice_admit", "transfer_admit", "retest_count"))
    fcr = rec.get("first_choice_rate")
    trr = rec.get("transfer_rate")
    rp = rec.get("retest_pass_rate")
    if isinstance(ta, (int, float)) and ta > 0:
        if fcr is None and isinstance(fc, (int, float)):
            fcr = fc / ta
        if trr is None and isinstance(tr, (int, float)):
            trr = tr / ta
    if rp is None and isinstance(rc, (int, float)) and rc > 0 and isinstance(fc, (int, float)):
        rp = fc / rc
    return fcr, trr, rp


def classify(panel):
    reasons, warnings = [], []
    records = [r for r in panel.get("records", []) if isinstance(r, dict)]
    records.sort(key=lambda r: r.get("year") or 0)
    # 剔除关键字段缺测的记录
    valid = []
    for r in records:
        if r.get("total_admit") is None or r.get("first_choice_admit") is None:
            reasons.append("年份 %s 关键字段缺测，按规范剔除出模式判别" % r.get("year"))
        else:
            valid.append(r)
    if not valid:
        return {"pattern": "undetermined", "pattern_label": "无法判别",
                "window_risk": None, "confidence": "low", "reason_chain":
                reasons + ["无有效年份记录（total_admit/first_choice_admit 全缺测）"],
                "warnings": ["补齐关键字段后重判"], "factors": {}}
    recent = valid[-3:]
    latest = valid[-1]
    fcr_l, trr_l, rp_l = _derive(latest)
    reasons.append("有效年份：%s（最新 %s，采用最近 %d 年）"
                   % ([r.get("year") for r in valid], latest.get("year"), len(recent)))

    # ---- β：连续≥3年零调剂 且 一志愿率≥0.90 ----
    pattern, label = None, None
    if len(recent) >= BETA_MIN_YEARS:
        zero_tr, fc_rates = True, []
        for r in recent:
            fcr, trr, _ = _derive(r)
            tr_a = r.get("transfer_admit")
            is_zero = (tr_a == 0) or (trr is not None and trr <= BETA_TR_RATE)
            zero_tr = zero_tr and bool(is_zero)
            if fcr is not None:
                fc_rates.append(fcr)
        mean_fcr = sum(fc_rates) / len(fc_rates) if fc_rates else None
        if zero_tr and mean_fcr is not None and mean_fcr >= BETA_FC_RATE:
            pattern, label = "beta", "β 零调剂堡垒"
            reasons.append("β 命中：连续%d年零调剂(或调剂率≤%.2f)，期间一志愿率均值 %.3f ≥ %.2f"
                           % (len(recent), BETA_TR_RATE, mean_fcr, BETA_FC_RATE))
        else:
            reasons.append("β 未命中：零调剂连续性=%s，一志愿率均值=%s"
                           % (zero_tr, ("%.3f" % mean_fcr) if mean_fcr is not None else "缺测"))
    else:
        reasons.append("β 无法判定：有效年数 %d < %d（置信度降级）" % (len(recent), BETA_MIN_YEARS))

    # ---- γ：最新年一志愿率<0.30 且 (通过率<0.50 或 调剂率>0.70) ----
    if pattern is None:
        if fcr_l is not None and fcr_l < GAMMA_FC_RATE and (
                (rp_l is not None and rp_l < GAMMA_PASS) or
                (trr_l is not None and trr_l > GAMMA_TR_RATE)):
            pattern, label = "gamma", "γ 高调剂陷阱"
            reasons.append("γ 命中：最新年一志愿率 %.3f < %.2f，且复试通过率=%s、调剂率=%s 触发刷人判据"
                           % (fcr_l, GAMMA_FC_RATE,
                              ("%.3f" % rp_l) if rp_l is not None else "缺测",
                              ("%.3f" % trr_l) if trr_l is not None else "缺测"))
        else:
            reasons.append("γ 未命中：最新年一志愿率=%s（阈值<%.2f 且需刷人证据）"
                           % (("%.3f" % fcr_l) if fcr_l is not None else "缺测", GAMMA_FC_RATE))

    # ---- α：通过率≥0.98 且 进复试者全录 ----
    if pattern is None:
        rc_l = latest.get("retest_count")
        fc_l = latest.get("first_choice_admit")
        full_admit = isinstance(rc_l, (int, float)) and isinstance(fc_l, (int, float)) \
            and rc_l > 0 and fc_l == rc_l
        if rp_l is not None and rp_l >= PASS_ALPHA and full_admit:
            pattern, label = "alpha", "α 一志愿过线即录"
            tr_l = latest.get("transfer_admit") or 0
            reasons.append("α 命中：一志愿复试通过率 %.3f ≥ %.2f，且进复试 %d 人全录"
                           "（调剂 %d 人为计划未满的补录，非竞争）"
                           % (rp_l, PASS_ALPHA, rc_l, tr_l))
        else:
            reasons.append("α 未命中：通过率=%s（阈值≥%.2f），进复试全录=%s"
                           % ((("%.3f" % rp_l) if rp_l is not None else "缺测"),
                              PASS_ALPHA, full_admit))
    if pattern is None:
        pattern, label = "mixed", "未定型 mixed"
        reasons.append("三模式均未命中 → 未定型；禁止强行归类，列观察名单补数据后重判")

    # ---- 模式警示（偏见自查挂钩）----
    if pattern == "alpha":
        warnings.append("偏见2自查：通过率≈100% 可能是筛选前置（进复试人少）；"
                        "核查进复试线是否=国家线、一志愿未进复试者的去向")
    elif pattern == "beta":
        warnings.append("β 校风险全部前置到初试：重点核查必达分硬门槛；无调剂退路")
    elif pattern == "gamma":
        warnings.append("γ 陷阱：一志愿考生=备胎，切勿误判为保底校；原则上从保底链剔除")
    else:
        warnings.append("未定型：交付时显式标注，并给补数据清单")
    if (latest.get("transfer_admit") or 0) > 0 or (trr_l or 0) > 0:
        warnings.append("偏见1自查：存在调剂即核查——调剂去向丰富≠正面信号（学校主动选调剂=一志愿保护弱）")

    # ---- 调剂窗口风险三因子 ----
    wh = latest.get("window_hours", panel.get("window_hours"))
    tier = latest.get("priority_tier", panel.get("priority_tier"))
    f_dur = ("未知" if wh is None else "高" if wh <= 24 else "中" if wh <= 48 else "低")
    tier_key = (str(tier).strip().upper() if tier is not None else None)
    f_tier = TIER_RISK.get(tier_key, "未知") if tier_key else "未知"
    f_prot = {"beta": "低", "alpha": "中", "gamma": "高"}.get(pattern, "中")
    factors = {"window_hours": wh, "duration_risk": f_dur,
               "priority_tier": tier, "tier_risk": f_tier,
               "protection_risk": f_prot}
    known = [f_dur, f_tier, f_prot]
    if f_dur == "未知" and f_tier == "未知":
        window_risk = "中"
        warnings.append("窗口未知（时长与优先级档位均缺测），按中风险保守处理")
    elif f_dur == "未知" or f_tier == "未知":
        window_risk = "中"  # 规范：任一因子缺测，综合评级不得高于中
        warnings.append("窗口部分未知（缺测因子按未知处理，综合评级封顶为中）")
    else:
        if "高" in known and f_prot != "低":
            window_risk = "高"
        elif all(f == "低" for f in known):
            window_risk = "低"
        else:
            window_risk = "中"
    reasons.append("窗口三因子：时长=%s档 / 优先级=%s档 / 一志愿保护=%s → 风险=%s"
                   % (f_dur, f_tier, f_prot, window_risk))
    if pattern == "beta" and window_risk == "中" and f_dur == "未知":
        reasons.append("β 校零调剂=天然无窗口暴露；窗口字段缺测仅影响调剂情景评估")

    # ---- 置信度 ----
    year_conf = "high" if len(recent) >= 3 else ("medium" if len(recent) == 2 else "low")
    conf_map = {"empirical": "high", "estimated": "medium", "assumed": "low"}
    rec_conf = min((conf_map.get(r.get("conf"), "low") for r in recent),
                   key=lambda c: {"high": 0, "medium": 1, "low": 2}[c]) \
        if all(r.get("conf") in conf_map for r in recent) else "low"
    order = {"high": 0, "medium": 1, "low": 2}
    confidence = year_conf if order[year_conf] >= order[rec_conf] else rec_conf
    reasons.append("置信度：年份覆盖=%s，记录conf=%s → %s" % (year_conf, rec_conf, confidence))

    return {"school": panel.get("school"), "program": panel.get("program"),
            "pattern": pattern, "pattern_label": label,
            "window_risk": window_risk, "confidence": confidence,
            "reason_chain": reasons, "warnings": warnings, "factors": factors,
            "latest_year": latest.get("year"),
            "latest_metrics": {"first_choice_rate": fcr_l, "transfer_rate": trr_l,
                               "retest_pass_rate": rp_l}}


def _smoke():
    alpha = {"school": "示例甲（合成α）", "program": "082700", "records": [
        {"year": 2024, "plan": 30, "total_admit": 36, "first_choice_admit": 18,
         "transfer_admit": 18, "retest_count": 18, "retest_pass_rate": 1.0,
         "first_choice_rate": 0.5, "transfer_rate": 0.5, "conf": "empirical", "missing": []},
        {"year": 2025, "plan": 32, "total_admit": 38, "first_choice_admit": 19,
         "transfer_admit": 19, "retest_count": 19, "retest_pass_rate": 1.0,
         "first_choice_rate": 0.5, "transfer_rate": 0.5, "conf": "empirical", "missing": []},
        {"year": 2026, "plan": 35, "total_admit": 38, "first_choice_admit": 20,
         "transfer_admit": 18, "retest_count": 20, "retest_pass_rate": 1.0,
         "first_choice_rate": 0.526, "transfer_rate": 0.474, "min_score": 251,
         "must_score": 261, "window_hours": 14, "priority_tier": "D",
         "conf": "empirical", "missing": []}]}
    beta = {"school": "示例乙（合成β）", "program": "070200", "records": [
        {"year": y, "total_admit": n, "first_choice_admit": n, "transfer_admit": 0,
         "retest_count": n + 8, "retest_pass_rate": round(n / (n + 8), 3),
         "first_choice_rate": 1.0, "transfer_rate": 0.0, "conf": "empirical", "missing": []}
        for y, n in ((2024, 70), (2025, 72), (2026, 75))]}
    gamma = {"school": "示例丙（合成γ）", "program": "070200", "records": [
        {"year": 2026, "total_admit": 25, "first_choice_admit": 5, "transfer_admit": 20,
         "retest_count": 25, "retest_pass_rate": 0.2, "first_choice_rate": 0.2,
         "transfer_rate": 0.8, "conf": "empirical", "missing": []}]}
    ra, rb, rg = classify(alpha), classify(beta), classify(gamma)
    assert ra["pattern"] == "alpha", ra
    assert ra["window_risk"] == "高", ra   # 14h + D档 + α保护中 → 高
    assert rb["pattern"] == "beta", rb
    assert rb["window_risk"] == "中", rb   # 窗口字段缺测 → 封顶中
    assert any("窗口" in w for w in rb["warnings"]), rb
    assert rg["pattern"] == "gamma", rg
    assert rg["window_risk"] == "中", rg   # γ保护高但时长/档位缺测 → 封顶中
    out = {"smoke": "pattern_classify",
           "alpha_case": {"pattern": ra["pattern"], "window_risk": ra["window_risk"],
                          "confidence": ra["confidence"],
                          "first_reason": ra["reason_chain"][1] if len(ra["reason_chain"]) > 1 else ""},
           "beta_case": {"pattern": rb["pattern"], "window_risk": rb["window_risk"],
                         "confidence": rb["confidence"]},
           "gamma_case": {"pattern": rg["pattern"], "window_risk": rg["window_risk"],
                          "confidence": rg["confidence"],
                          "warning": rg["warnings"][0]}}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("SMOKE OK: pattern_classify 自测通过（α/β/γ 三校判别 + 窗口风险评级正确）")
    return 0


def main(argv):
    if "--smoke" in argv:
        return _smoke()
    args = [a for a in argv[1:] if not a.startswith("--")]
    try:
        text = open(args[0], encoding="utf-8").read() if args else sys.stdin.read()
        panel = json.loads(text)
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"error": "输入读取/解析失败: %s" % e}, ensure_ascii=False))
        return 2
    print(json.dumps(classify(panel), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
