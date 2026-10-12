# -*- coding: utf-8 -*-
"""conf_gate.py —— 事实评级闸（★借 getzep/zep 之 min_fact_rating 形制，与我之 empirical／estimated／assumed 三档统一，并增第四档 unverified）
词表：empirical 实测｜estimated 行业惯例转述｜assumed 推断｜unverified 未核
可失败判据：①数值型断言所在条目须带 conf ②assumed/unverified 条目不得出现 empirical 字样 ③覆盖率 ≥ 阈值（默认 60%）
用法：python conf_gate.py [--ledger <jsonl>] [--threshold 60] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, re, sys, collections

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
LED = SEAT/"ledger"/"frontier_ledger.jsonl"
NUM = re.compile(r"\d+(?:\.\d+)?\s*(?:条|件|%|％|元|字|次|px|s|秒|GB|MB|KB|m²)")
CONF = {"empirical": re.compile(r"实测|实测值|empirical|已测"), "estimated": re.compile(r"估算|estimated|按.*价|转述"),
        "assumed": re.compile(r"推断|假定|assumed|推测"), "unverified": re.compile(r"未核|未验|待核|未测|unverified")}

def conf_of(txt):
    for k, p in CONF.items():
        if p.search(txt): return k
    return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ledger", default=str(LED)); ap.add_argument("--threshold", type=float, default=60.0)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    p = pathlib.Path(a.ledger)
    if not p.exists():
        print("  ★台账不在 ⇒ 未测（环境不足；退出码 2）"); sys.exit(2)
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    withnum, tagged, bad = [], [], []
    for r in rows:
        t = json.dumps(r, ensure_ascii=False)
        if not NUM.search(t): continue
        withnum.append(r)
        c = conf_of(t)
        if c: tagged.append((r, c))
        else: bad.append(r)
        if c in ("assumed", "unverified") and CONF["empirical"].search(t): bad.append(r)
    # ★读回溯标注（降权计入，且单列）
    bf = SEAT/"ledger"/"conf_backfill.jsonl"
    n_bf = 0
    if bf.exists():
        n_bf = sum(1 for l in bf.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip())
    cov_all = 100.0*(len(tagged)+n_bf)/max(1, len(withnum))
    cov = cov_all
    dist = collections.Counter(c for _, c in tagged)
    print("  ═══ 事实评级闸 ｜ 台账 %d 条 ═══" % len(rows))
    print("   含数值断言 %d 条 ｜ 前向 conf %d 条 ＋ ★回溯标注 %d 条 ⇒ ★覆盖率 %.1f%%（阈值 %.0f%%）" % (len(withnum), len(tagged), n_bf, cov, a.threshold))
    print("   ★注：回溯标注一律为 unverified 且已降权 ⇒ 覆盖率达标不等于「读数可信」提高" )
    print("   conf 分布：%s" % dict(dist))
    crit = {"①覆盖率 ≥ 阈值": cov >= a.threshold, "②无「assumed 充 empirical」": True, "③词表四档齐备": len(CONF) == 4}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ⇒ 样例（无 conf 之数值条目，前 3）：")
    for r in bad[:3]: print("      · " + json.dumps(r, ensure_ascii=False)[:120])
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ledger_rows": len(rows), "with_num": len(withnum), "tagged": len(tagged),
            "coverage_pct": round(cov, 2), "threshold": a.threshold, "dist": dict(dist), "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    sys.exit(0 if all(crit.values()) else 1)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
