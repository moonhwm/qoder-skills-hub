#!/usr/bin/env python3
# consignment_ledger.py v1.0.2 — 函询交割台账（JSONL 追加式后端，方案1落地）
# 用法:
#   python3 consignment_ledger.py issue <函ID> <交割方> <接收方> <事项一句>
#   python3 consignment_ledger.py receive <函ID>
#   python3 consignment_ledger.py accept <函ID> <回执摘要>
#   python3 consignment_ledger.py reject <函ID> <退回理由>
#   python3 consignment_ledger.py status [函ID]
#   python3 consignment_ledger.py overdue [小时阈值, 默认24]
# 台账: <注册处>/交割台账.jsonl（行结构 ts/writer/item_id/event/note）
# v1.0.2：全量写入 JSON 改为 JSONL 追加模式（支持并发安全）；读取端重放处理（跳过异常行并计数）；数据压缩合并至主会话（04:00 cron 定时执行）
import json, sys, os, importlib.util
from datetime import datetime, timezone, timedelta

REG = "<注册处>"
LEDGER = os.path.join(REG, "交割台账.jsonl")
ENGINE = os.path.join(REG, "交割台账_jsonl.py")
STATES = ["发出", "已收", "验收中", "已交割", "退回"]
WRITER = "consignment-ledger"  # 调用方可改环境变量 LEDGER_WRITER 标识写者身份

_spec = importlib.util.spec_from_file_location("ledger_engine", ENGINE)
led = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(led)


def load():
    """replay JSONL → 兼容旧视图的 state dict。"""
    st, stats = led.replay(LEDGER)
    if stats["bad"]:
        print(f"[WARN] 坏行 {stats['bad']} 条已跳过：{stats['bad_lines'][:3]}")
    items = {}
    for iid, s in st.items():
        hist = [{"ts": h["ts"], "from": "-", "to": h["event"], "note": h.get("note", "")}
                for h in s["history"]]
        items[iid] = {"src": "", "dst": "", "matter": hist[0]["note"] if hist else "",
                      "state": s["state"], "history": hist}
    return {"version": "1.0.2", "items": items, "note": "函询交割台账（JSONL 追加式）"}


def append(cid, event, note=""):
    led.append_event(LEDGER, os.environ.get("LEDGER_WRITER", WRITER), cid, event, note)


def transit(s, cid, new_state, note=""):
    it = s["items"].get(cid)
    if not it:
        print(f"[FAIL] 函件不存在：{cid}"); return 2
    ok = (it["state"], new_state) in [("发出","已收"),("已收","验收中"),("验收中","已交割"),("验收中","退回"),("已收","退回"),("发出","退回")]  # 发出→退回=发件方撤回
    if not ok:
        print(f"[FAIL] 非法迁移 {it['state']}→{new_state}（合法：发出→已收/撤回→验收中→已交割/退回）"); return 2
    append(cid, new_state, note)
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
        append(cid, "issue", f"src={src} dst={dst} matter={matter[:120]}")
        append(cid, "发出", "issue")
        print(f"[OK] {cid} 已登记发出（{src}→{dst}）"); return 0
    if cmd == "receive" and len(sys.argv) >= 3:
        return transit(s, sys.argv[2], "已收")
    if cmd == "accept" and len(sys.argv) >= 3:
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
            print(f"{sys.argv[2]}: {it['state']} | {it['matter'][:60]}")
            for h in it["history"][-4:]: print(f"  {h['ts']} →{h['to']} {h.get('note','')[:50]}")
            return 0
        counts = {}
        for it in s["items"].values():
            counts[it["state"]] = counts.get(it["state"], 0) + 1
        print(f"交割总览（{len(s['items'])} 件）: " + " / ".join(f"{k}×{v}" for k, v in sorted(counts.items())))
        for cid, it in sorted(s["items"].items()):
            if it["state"] not in ("已交割",):
                print(f"  [{it['state']}] {cid} {it['matter'][:50]}")
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
