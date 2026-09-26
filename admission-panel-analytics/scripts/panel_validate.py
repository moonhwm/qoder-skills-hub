#!/usr/bin/env python3
"""panel_validate.py — 录取面板 JSON 校验器（admission-panel-analytics）

依据 references/panel_schema.md 逐字段校验：类型/范围/跨字段一致性(C1-C6)/缺测登记。
用法：
    python3 panel_validate.py --smoke            # 合成样例自测，exit=0
    python3 panel_validate.py panel.json         # 校验文件
    cat panel.json | python3 panel_validate.py   # 校验 stdin
输出：JSON {ok, n_records, n_checks, n_errors, n_warnings, pass_rate, issues[], excluded_years[]}
"""
import json
import sys

# 字段规范: name -> (允许类型, min, max) ；None 表示无界
NUM = (int, float)
FIELDS = {
    "year": ((int,), 2000, 2100),
    "plan": ((int,), 0, None),
    "total_admit": ((int,), 0, None),
    "first_choice_admit": ((int,), 0, None),
    "transfer_admit": ((int,), 0, None),
    "retest_count": ((int,), 0, None),
    "retest_pass_rate": (NUM, 0.0, 1.0),
    "min_score": (NUM, 0.0, 500.0),
    "median_score": (NUM, 0.0, 500.0),
    "must_score": (NUM, 0.0, 500.0),
    "math1": ((bool,), None, None),
    "first_choice_rate": (NUM, 0.0, 1.0),
    "transfer_rate": (NUM, 0.0, 1.0),
    "tuimian_ratio": (NUM, 0.0, 1.0),
    "first_try_weight": (NUM, 0.0, 1.0),
    "window_hours": (NUM, 0.0, None),
}
CRITICAL = ["total_admit", "first_choice_admit"]  # 关键字段：缺测则该年禁入模式判别
CONF_VALUES = {"empirical", "estimated", "assumed"}
TOL_RATE = 0.02   # C4 比率复算容差
TOL_PASS = 0.05   # C3 通过率复算容差


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _num_ok(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_panel(panel):
    issues = []  # (level, year, field, message)
    checks = [0, 0]  # [passed, total]

    def add(level, year, field, msg):
        issues.append({"level": level, "year": year, "field": field, "message": msg})

    def check(ok, level, year, field, msg):
        checks[1] += 1
        if ok:
            checks[0] += 1
        else:
            add(level, year, field, msg)

    if not isinstance(panel, dict):
        return {"ok": False, "issues": [{"level": "error", "year": None, "field": None,
                "message": "面板顶层必须是 JSON 对象"}], "n_records": 0,
                "n_checks": 1, "n_errors": 1, "n_warnings": 0, "pass_rate": 0.0,
                "excluded_years": []}
    for key in ("school", "program", "data_cutoff"):
        check(isinstance(panel.get(key), str) and panel.get(key).strip() != "",
              "error", None, key, "顶层字段 %s 缺失或不是非空字符串" % key)
    records = panel.get("records")
    if not isinstance(records, list) or not records:
        add("error", None, "records", "records 缺失、不是数组或为空")
        return {"ok": False, "issues": issues, "n_records": 0, "n_checks": checks[1],
                "n_errors": sum(1 for i in issues if i["level"] == "error"),
                "n_warnings": sum(1 for i in issues if i["level"] == "warning"),
                "pass_rate": checks[0] / checks[1] if checks[1] else 0.0,
                "excluded_years": []}

    seen_years = set()
    excluded = []
    for rec in records:
        yr = rec.get("year") if isinstance(rec, dict) else None
        if not isinstance(rec, dict):
            add("error", None, "record", "记录不是 JSON 对象")
            continue
        # 类型与范围
        for name, (types, lo, hi) in FIELDS.items():
            v = rec.get(name)
            if v is None:
                continue  # 缺测留给缺测登记检查
            checks[1] += 1
            t_ok = (_is_int(v) if types == (int,) else
                    isinstance(v, bool) if types == (bool,) else _num_ok(v))
            r_ok = t_ok and (lo is None or v >= lo) and (hi is None or v <= hi)
            if t_ok and r_ok:
                checks[0] += 1
            else:
                add("error", yr, name, "类型或取值范围违规: %r (约束 %s, [%s, %s])"
                    % (v, types, lo, hi))
        # 年份重复
        if yr in seen_years:
            add("error", yr, "year", "年份重复: %s" % yr)
        else:
            checks[0] += 1
        checks[1] += 1
        seen_years.add(yr)
        # conf 合法性
        check(rec.get("conf") in CONF_VALUES, "error", yr, "conf",
              "conf 必须是 empirical/estimated/assumed，实得 %r" % rec.get("conf"))
        # 缺测登记一致性
        missing = rec.get("missing")
        check(isinstance(missing, list), "error", yr, "missing", "missing 必须是数组")
        missing = missing if isinstance(missing, list) else []
        for name in FIELDS:
            if name == "year":
                continue
            if rec.get(name) is None and name not in missing:
                add("warning", yr, name, "字段缺测(null)但未登记入 missing")
            if rec.get(name) is not None and name in missing:
                add("warning", yr, name, "字段登记在 missing 但有值 %r" % rec.get(name))
        # 关键字段缺测 → excluded
        if any(rec.get(f) is None for f in CRITICAL):
            excluded.append(yr)
            add("info", yr, None, "关键字段缺测，该年记录禁入模式判别（excluded）")
        ta, fc, tr = rec.get("total_admit"), rec.get("first_choice_admit"), rec.get("transfer_admit")
        rc, rp = rec.get("retest_count"), rec.get("retest_pass_rate")
        fcr, trr = rec.get("first_choice_rate"), rec.get("transfer_rate")
        # C1 总账
        if all(_is_int(x) for x in (ta, fc, tr)):
            check(fc + tr == ta, "error", yr, "total_admit",
                  "C1 总账不平: 一志愿%d + 调剂%d ≠ 总录取%d" % (fc, tr, ta))
            check(fc <= ta and tr <= ta, "error", yr, "first_choice_admit",
                  "一志愿/调剂录取超过总录取")
        # C2 复试账
        if _is_int(fc) and _is_int(rc):
            check(fc <= rc, "error", yr, "retest_count",
                  "C2 一志愿录取%d > 复试人数%d" % (fc, rc))
        # C3 通过率复算
        if _is_int(rc) and rc == 0:
            check(rp is None, "error", yr, "retest_pass_rate", "复试人数为0时通过率必须为 null")
        elif _is_int(rc) and _is_int(fc) and _num_ok(rp):
            expect = fc / rc
            check(abs(rp - expect) <= TOL_PASS, "warning", yr, "retest_pass_rate",
                  "C3 通过率复算 %.3f vs 记录 %.3f 超容差" % (expect, rp))
        # C4 比率复算
        if _is_int(ta) and ta == 0:
            check(fcr is None and trr is None, "error", yr, "first_choice_rate",
                  "总录取为0时一志愿率/调剂率必须为 null")
        elif _is_int(ta) and ta > 0:
            if _is_int(fc) and _num_ok(fcr):
                check(abs(fcr - fc / ta) <= TOL_RATE, "error", yr, "first_choice_rate",
                      "C4 一志愿率复算 %.3f vs 记录 %.3f 超容差" % (fc / ta, fcr))
            if _is_int(tr) and _num_ok(trr):
                check(abs(trr - tr / ta) <= TOL_RATE, "error", yr, "transfer_rate",
                      "C4 调剂率复算 %.3f vs 记录 %.3f 超容差" % (tr / ta, trr))
            if _num_ok(fcr) and _num_ok(trr):
                check(abs(fcr + trr - 1.0) <= TOL_RATE, "error", yr, "transfer_rate",
                      "C4 一志愿率+调剂率应≈1，实得 %.3f" % (fcr + trr))
        # C5 分数序（软约束）
        ms, md, mu = rec.get("min_score"), rec.get("median_score"), rec.get("must_score")
        if _num_ok(ms) and _num_ok(md):
            check(md >= ms, "warning", yr, "median_score",
                  "C5 中位分 %.1f < 最低分 %.1f，需人工确认" % (md, ms))
        if _num_ok(ms) and _num_ok(mu):
            check(mu >= ms, "warning", yr, "must_score",
                  "C5 必达分 %.1f < 最低分 %.1f，需人工确认" % (mu, ms))
        # C6 计划 vs 实际（info）
        pl = rec.get("plan")
        if _is_int(pl) and _is_int(ta) and ta > pl:
            add("info", yr, "plan", "C6 实际录取%d > 计划%d（扩招/调剂补录信号）" % (ta, pl))

    n_err = sum(1 for i in issues if i["level"] == "error")
    n_warn = sum(1 for i in issues if i["level"] == "warning")
    return {
        "ok": n_err == 0,
        "school": panel.get("school"),
        "n_records": len(records),
        "n_checks": checks[1],
        "n_errors": n_err,
        "n_warnings": n_warn,
        "pass_rate": round(checks[0] / checks[1], 4) if checks[1] else 0.0,
        "excluded_years": excluded,
        "issues": issues,
    }


def _smoke():
    good = {
        "school": "示例大学（合成·冒烟）", "program": "070200", "data_cutoff": "2026-08-24",
        "records": [
            {"year": 2025, "plan": 62, "total_admit": 72, "first_choice_admit": 72,
             "transfer_admit": 0, "retest_count": 80, "retest_pass_rate": 0.9,
             "min_score": 292, "median_score": 332, "must_score": 342, "math1": True,
             "first_choice_rate": 1.0, "transfer_rate": 0.0, "tuimian_ratio": 0.3,
             "first_try_weight": 0.6, "conf": "empirical", "missing": []},
            {"year": 2026, "plan": 65, "total_admit": 75, "first_choice_admit": 75,
             "transfer_admit": 0, "retest_count": 82, "retest_pass_rate": 0.915,
             "min_score": 295, "median_score": 335, "must_score": 345, "math1": True,
             "first_choice_rate": 1.0, "transfer_rate": 0.0, "tuimian_ratio": 0.32,
             "first_try_weight": 0.6, "window_hours": None, "conf": "empirical",
             "missing": ["window_hours"]},
        ],
    }
    bad = {
        "school": "坏例校（合成·冒烟）", "program": "082700", "data_cutoff": "2026-08-24",
        "records": [
            {"year": 2026, "plan": 33, "total_admit": 42, "first_choice_admit": 22,
             "transfer_admit": 25, "retest_count": 20, "retest_pass_rate": 1.0,
             "min_score": 251, "median_score": 240, "must_score": 261, "math1": "yes",
             "first_choice_rate": 0.9, "transfer_rate": 0.476, "tuimian_ratio": 1.5,
             "first_try_weight": 0.6, "conf": "empirical", "missing": []},
            {"year": 2026, "plan": 33, "total_admit": 40, "first_choice_admit": None,
             "transfer_admit": 18, "retest_count": 22, "retest_pass_rate": None,
             "min_score": 255, "median_score": 300, "must_score": 265, "math1": True,
             "first_choice_rate": 0.55, "transfer_rate": 0.45, "tuimian_ratio": 0.2,
             "first_try_weight": 0.6, "conf": "guess", "missing": []},
        ],
    }
    rg = validate_panel(good)
    rb = validate_panel(bad)
    # 坏例应至少捕获：C1不平、C2(22>20)、math1类型、tuimian超界、年份重复、conf非法、
    # first_choice_rate复算超差、缺测未登记 等 ≥6 个 error
    assert rg["ok"], rg
    assert rg["pass_rate"] == 1.0, rg
    assert not rg["excluded_years"], rg
    assert not rb["ok"], rb
    assert rb["n_errors"] >= 6, rb
    assert 2026 in rb["excluded_years"], rb
    assert any(i["field"] == "total_admit" and "C1" in i["message"] for i in rb["issues"]), rb
    assert any(i["field"] == "year" and "重复" in i["message"] for i in rb["issues"]), rb
    print(json.dumps({"smoke": "panel_validate", "good_case": {"ok": rg["ok"],
                      "pass_rate": rg["pass_rate"], "n_checks": rg["n_checks"]},
                      "bad_case": {"ok": rb["ok"], "n_errors": rb["n_errors"],
                      "n_warnings": rb["n_warnings"], "pass_rate": rb["pass_rate"],
                      "excluded_years": rb["excluded_years"],
                      "sample_issues": rb["issues"][:4]}},
                     ensure_ascii=False, indent=2))
    print("SMOKE OK: panel_validate 自测通过（好例全过、坏例捕获 %d 个 error）" % rb["n_errors"])
    return 0


def main(argv):
    if "--smoke" in argv:
        return _smoke()
    args = [a for a in argv[1:] if not a.startswith("--")]
    try:
        text = open(args[0], encoding="utf-8").read() if args else sys.stdin.read()
        panel = json.loads(text)
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": "输入读取/解析失败: %s" % e},
                         ensure_ascii=False))
        return 2
    result = validate_panel(panel)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
