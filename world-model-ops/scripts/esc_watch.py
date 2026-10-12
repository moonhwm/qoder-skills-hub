# -*- coding: utf-8 -*-
"""esc_watch.py —— 升级面计时簿（使"esc.* 端到端 ≤60 s"从"不可评"变为"可评"）
应正主（DF-IMA-RECHECK-20261006-HY4-01）：「esc.* 升级面（≤60s）」
用法：
  python esc_watch.py open  --subject "<事项>" [--level esc|biz]     # 立案（记 raised_ts）
  python esc_watch.py close --id <案号>                              # 结案（记 handle_ts，算 elapsed）
  python esc_watch.py stats                                          # 统计（含超 60 s 者）
  python esc_watch.py list
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
LED = SEAT/"ledger"/"esc_watch.jsonl"

def _rows():
    return [json.loads(l) for l in LED.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()] if LED.exists() else []

def _app(rec):
    LED.parent.mkdir(parents=True, exist_ok=True)
    with open(LED, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def cmd_open(subject, level):
    rows = _rows()
    n = sum(1 for r in rows if r.get("event") == "open") + 1
    rid = "ESC-%s-%03d" % (time.strftime("%Y%m%d"), n)
    ts = time.strftime("%Y-%m-%dT%H:%M:%S+0800")
    _app({"event": "open", "id": rid, "level": level, "subject": subject[:120], "raised_ts": ts})
    print("   ✓ 立案 %s（层面 %s）｜ raised_ts=%s" % (rid, level, ts)); return rid

def cmd_close(rid):
    rows = _rows()
    ops = [r for r in rows if r.get("event") == "open" and r.get("id") == rid]
    if not ops: print("   ★无此案号：%s" % rid); return None
    t0 = time.mktime(time.strptime(ops[-1]["raised_ts"], "%Y-%m-%dT%H:%M:%S+0800"))
    now = time.time()
    ts = time.strftime("%Y-%m-%dT%H:%M:%S+0800")
    el = round(now - t0, 2)
    _app({"event": "close", "id": rid, "handle_ts": ts, "elapsed_s": el,
          "pass_60s": (el <= 60.0)})
    print("   ✓ 结案 %s ｜ handle_ts=%s ｜ ★端到端 %.2f s ⇒ %s" % (rid, ts, el, "✓ ≤60 s" if el <= 60 else "✗ 超 60 s"))
    return el

def cmd_stats():
    rows = _rows()
    cl = [r for r in rows if r.get("event") == "close"]
    op = [r for r in rows if r.get("event") == "open"]
    over = [r for r in cl if not r.get("pass_60s")]
    print("   ═══ 升级面计时簿 ═══")
    print("   立案 %d ｜ 结案 %d ｜ 未结 %d ｜ ★超 60 s %d" % (len(op), len(cl), len(op)-len(cl), len(over)))
    for r in cl[-5:]:
        print("     · %s ｜ %.2f s ｜ %s" % (r["id"], r.get("elapsed_s", -1), "✓" if r.get("pass_60s") else "✗"))
    if cl:
        els = [r.get("elapsed_s", 0) for r in cl]
        print("   端到端：最短 %.2f s ｜ 中位 %.2f s ｜ 最长 %.2f s" % (min(els), sorted(els)[len(els)//2], max(els)))
    return {"open": len(op), "close": len(cl), "over60": len(over)}

def cmd_list():
    for r in _rows(): print("   " + json.dumps(r, ensure_ascii=False)[:140])

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
    a1 = sub.add_parser("open"); a1.add_argument("--subject", required=True); a1.add_argument("--level", default="esc")
    a2 = sub.add_parser("close"); a2.add_argument("--id", required=True)
    sub.add_parser("stats"); sub.add_parser("list")
    a = ap.parse_args()
    if a.cmd == "open": cmd_open(a.subject, a.level)
    elif a.cmd == "close": cmd_close(a.id)
    elif a.cmd == "stats": cmd_stats()
    elif a.cmd == "list": cmd_list()
    else: ap.print_help()
