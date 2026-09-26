#!/usr/bin/env python3
# consignment_ledger.py v1.0.0 — 函询交割台账（发出/已收/验收中/已交割/退回 + 逾期扫描）
# 用法:
#   python3 consignment_ledger.py issue <函ID> <交割方> <接收方> <事项一句>
#   python3 consignment_ledger.py receive <函ID>
#   python3 consignment_ledger.py accept <函ID> <回执摘要>
#   python3 consignment_ledger.py reject <函ID> <退回理由>
#   python3 consignment_ledger.py status [函ID]
#   python3 consignment_ledger.py overdue [小时阈值, 默认24]
# 台账: <注册处>/交割台账.json
import json, sys, os
from datetime import datetime, timezone, timedelta

LEDGER = "<注册处>/交割台账.json"
STATES = ["发出", "已收", "验收中", "已交割", "退回"]

def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")

def load():
    if os.path.exists(LEDGER):
        try:
            return json.load(open(LEDGER, encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("[WARN] 台账损坏，按空账重建并备份")
            try: os.replace(LEDGER, LEDGER + ".corrupt.bak")
            except OSError: pass
    return {"version": "1.0.0", "items": {}, "note": "函询交割台账（consignment-intake-ops）"}

def save(s):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(s, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def transit(s, cid, new_state, note=""):
    it = s["items"].get(cid)
    if not it:
        print(f"[FAIL] 函件不存在：{cid}"); return 2
    i = STATES.index(it["state"]); j = STATES.index(new_state)
    # 合法迁移：发出→已收→验收中→已交割/退回；已收→退回；验收中→退回
    ok = (it["state"], new_state) in [("发出","已收"),("已收","验收中"),("验收中","已交割"),("验收中","退回"),("已收","退回"),("发出","退回")]  # 发出→退回=发件方撤回
    if not ok:
        print(f"[FAIL] 非法迁移 {it['state']}→{new_state}（合法：发出→已收/撤回→验收中→已交割/退回）"); return 2
    it["history"].append({"ts": now(), "from": it["state"], "to": new_state, "note": note})
    it["state"] = new_state
    save(s)
    print(f"[OK] {cid}: →{new_state}" + (f"（{note[:60]}）" if note else ""))
    return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    cmd = sys.argv[1]
    s = load()
    if cmd == "issue" and len(sys.argv) >= 6:
        cid, src, dst, matter = sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:])
        if cid in s["items"]:
            print(f"[FAIL] 函ID重复：{cid}"); return 2
        s["items"][cid] = {"src": src, "dst": dst, "matter": matter, "state": "发出",
                           "history": [{"ts": now(), "from": "-", "to": "发出", "note": "issue"}]}
        save(s); print(f"[OK] {cid} 已登记发出（{src}→{dst}）"); return 0
    if cmd == "receive" and len(sys.argv) >= 3:
        return transit(s, sys.argv[2], "已收")
    if cmd == "accept" and len(sys.argv) >= 3:
        # accept = 验收中→已交割 两步合并（验收摘要入 note）
        cid = sys.argv[2]; note = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        r = transit(s, cid, "验收中", "回执进入验收")
        if r != 0: return r
        return transit(s, cid, "已交割", note or "验收通过")
    if cmd == "reject" and len(sys.argv) >= 4:
        return transit(s, sys.argv[2], "退回", " ".join(sys.argv[3:]))
    if cmd == "status":
        if len(sys.argv) >= 3:
            it = s["items"].get(sys.argv[2])
            if not it: print(f"[FAIL] 函件不存在：{sys.argv[2]}"); return 2
            print(f"{sys.argv[2]}: {it['state']} | {it['src']}→{it['dst']} | {it['matter'][:60]}")
            for h in it["history"][-4:]: print(f"  {h['ts']} {h['from']}→{h['to']} {h.get('note','')[:50]}")
            return 0
        counts = {}
        for it in s["items"].values():
            counts[it["state"]] = counts.get(it["state"], 0) + 1
        print(f"交割总览（{len(s['items'])} 件）: " + " / ".join(f"{k}×{v}" for k, v in sorted(counts.items())))
        for cid, it in sorted(s["items"].items()):
            if it["state"] not in ("已交割",):
                print(f"  [{it['state']}] {cid} {it['src']}→{it['dst']} {it['matter'][:40]}")
        return 0
    if cmd == "overdue":
        hours = float(sys.argv[2]) if len(sys.argv) >= 3 else 24
        cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(hours=hours)
        hits = []
        for cid, it in s["items"].items():
            if it["state"] in ("发出", "已收", "验收中"):
                last = datetime.fromisoformat(it["history"][-1]["ts"])
                if last < cutoff:
                    hits.append((cid, it["state"], it["history"][-1]["ts"], it["matter"][:40]))
        if not hits:
            print(f"[OK] 无超 {hours}h 未闭环交割"); return 0
        print(f"[ALERT] 超 {hours}h 未闭环 {len(hits)} 件:")
        for h in hits: print("  ", h)
        return 1
    print(__doc__); return 2

if __name__ == "__main__":
    sys.exit(main())
