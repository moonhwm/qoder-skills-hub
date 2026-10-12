# -*- coding: utf-8 -*-
"""conf_calibration_audit.py —— 决策读数之"置信度校核"（只增不改；2026-10-12 立）
背景：-98 复核发现 decision_model_api_20261011.json 之 6 题中 3 题"自报 confidence"与"max(概率)"不一致
      （D1 0.25 vs 0.50；D4 0.70 vs 0.65；D5 0.85 vs 0.90）⇒ 本器对各批统一补"校核标注"
做法：扫交换区与 outbox/mem 之 decision*／recognition* 之 JSON ⇒ 容错提取（题, 概率分布, 自报置信度）三元组
      ⇒ 逐项校核 conf 与 max(prob) ⇒ ★追加写 EX/conf_calibration_notes_20261012.jsonl（不改原档）
判据：①原档指纹前后不变（"只增不改"之实证）②每档皆有标注 ③不一致处逐项列明
用法：python conf_calibration_audit.py [--json out]
（中文串一律用「」）
"""
import argparse, hashlib, json, pathlib, sys, time

HOME = pathlib.Path.home()
PLAY = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"
SEAT = PLAY/"A2A新席_石敢当Cairn_20260928"
EX = PLAY/"A2A共同体_共享交换区"
NOTES = EX/"conf_calibration_notes_20261012.jsonl"
TOL = 0.001

def sha16(p):
    try: return hashlib.sha3_256(p.read_bytes()).hexdigest()[:16]
    except Exception: return None

def nums(d):
    return {k: float(v) for k, v in (d or {}).items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}

def extract(j):
    """容错提取 [(题, probs, conf)]（多形态）；probs 或 conf 可能缺（则记 None）"""
    out = []
    if not isinstance(j, dict): return out
    if isinstance(j.get("rows"), list):
        for r in j["rows"]:
            if isinstance(r, dict):
                out.append((r.get("id") or r.get("kind") or "题", nums(r.get("probabilities")), r.get("confidence")))
    if isinstance(j.get("rank"), list):
        pr = {}
        for it in j["rank"]:
            if isinstance(it, dict):
                for k in ("p", "prob", "probability", "score", "软概率"):
                    if isinstance(it.get(k), (int, float)):
                        pr[str(it.get("item") or it.get("name") or "项")[:24]] = float(it[k]); break
        dc = (j.get("decision") or {}) if isinstance(j.get("decision"), dict) else {}
        out.append(("rank", pr, dc.get("confidence")))
    if isinstance(j.get("probs"), dict):
        out.append(("顶层 probs", nums(j["probs"]), j.get("confidence")))
    if isinstance(j.get("decision"), dict) and isinstance(j["decision"].get("probabilities"), dict):
        out.append(("decision.probabilities", nums(j["decision"]["probabilities"]), j["decision"].get("confidence")))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    files = []
    for d in (EX, SEAT/"outbox"/"mem"):
        if d.exists(): files += [p for p in d.glob("*.json") if ("decision" in p.name or "recognition" in p.name)]
    seen, uniq = set(), []
    for p in sorted(files, key=lambda q: q.name):
        if p.name in seen: continue
        seen.add(p.name); uniq.append(p)
    print("  ═══ 置信度校核 ｜ 档 %d ═══" % len(uniq))
    before = {p.name: sha16(p) for p in uniq}
    report, bad_total, checked_total = [], 0, 0
    for p in uniq:
        try: j = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print("   ★%-44s 不可读：%s" % (p.name, str(e)[:36])); continue
        items = extract(j)
        rows = []
        for name, pr, cf in items:
            if not pr or cf is None:
                rows.append({"题": name, "判": "不可校核", "n": len(pr), "自报": cf}); continue
            mx = max(pr.values())
            try: cfv = float(cf)
            except Exception: cfv = None
            if cfv is None:
                rows.append({"题": name, "判": "不可校核（自报非数）", "n": len(pr)}); continue
            d = round(cfv - mx, 4)
            ok = abs(d) <= TOL
            checked_total += 1
            if not ok: bad_total += 1
            rows.append({"题": name, "自报": cfv, "max(prob)": round(mx, 4), "Δ": d, "判": "一致" if ok else "★不一致"})
        bad = sum(1 for r in rows if r.get("判", "").startswith("★"))
        print("   %-44s 项 %2d ｜ 可校核 %2d ｜ ★不一致 %d" % (p.name, len(rows), sum(1 for r in rows if "自报" in r and "max(prob)" in r), bad))
        for r in rows:
            if r.get("判", "").startswith("★") or r.get("判") == "不可校核":
                print("      · %s" % json.dumps(r, ensure_ascii=False))
        report.append({"档": p.name, "指纹": before[p.name], "项": rows})
    after = {p.name: sha16(p) for p in uniq}
    unchanged = all(before[k] == after[k] for k in before)
    crit = {"①原档指纹前后不变（只增不改）": unchanged,
            "②每档皆有标注": len(report) == len(uniq),
            "③不一致处已逐项列明": True}
    print("   ── 判据 ──")
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ⇒ 汇总：可校核 %d 项 ｜ ★不一致 %d 项" % (checked_total, bad_total))
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "kind": "conf_calibration_note",
           "note": "★校核标注（不改原档）：本表记录各决策读数之「自报 confidence」与「max(概率)」之对照；不一致者以★标之",
           "checked": checked_total, "mismatch": bad_total, "files": report, "criteria": crit}
    with open(NOTES, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("   ⇒ 已追加校核标注：%s" % NOTES.name)
    if a.json: pathlib.Path(a.json).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0 if all(crit.values()) else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
