#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交割台账 JSONL 追加式引擎 v1.0（方案1落地件，用户拍板 2026-08-30「我选1」）
行信封契约：{"ts","writer","item_id","event","note"} 五字段，一行一事件，只 append 不整写。
读端 replay：坏行跳过并计数告警；压实（compact）归主会话 04:00 窗口，快照头带 md5 指纹。
用法：
  append_event(path, writer, item_id, event, note="")
  state, stats = replay(path)          # state: {item_id: {...最新态+history}}
  fp = compact(path, snapshot_path)    # 写快照，返回 md5 指纹
"""
import json, os, sys, hashlib, fcntl
from datetime import datetime, timezone, timedelta

FIELDS = ("ts", "writer", "item_id", "event", "note")
CST = timezone(timedelta(hours=8))

def _now():
    return datetime.now(CST).isoformat(timespec="seconds")

def append_event(path, writer, item_id, event, note=""):
    """追加一条事件行（O_APPEND+fcntl 锁，双 writer 同刻安全）。"""
    rec = {"ts": _now(), "writer": writer, "item_id": item_id, "event": event, "note": note}
    for k in FIELDS:
        if k not in rec:
            raise ValueError(f"缺字段 {k}")
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return rec

def replay(path):
    """重放 JSONL，还原各条目最新状态。坏行跳过并计数。返回 (state, stats)。"""
    state, stats = {}, {"total": 0, "bad": 0, "bad_lines": []}
    if not os.path.exists(path):
        return state, stats
    with open(path, encoding="utf-8") as f:
        for i, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            stats["total"] += 1
            try:
                rec = json.loads(raw)
                if not all(k in rec for k in ("item_id", "event")):
                    raise ValueError("缺关键字段")
            except Exception as e:
                stats["bad"] += 1
                stats["bad_lines"].append({"line": i, "err": str(e)[:80]})
                continue
            iid = rec["item_id"]
            st = state.setdefault(iid, {"item_id": iid, "history": []})
            st["history"].append(rec)
            st["state"] = rec["event"]
            st["writer"] = rec.get("writer", "?")
            st["ts"] = rec.get("ts", "?")
            if rec.get("note"):
                st["last_note"] = rec["note"]
    return state, stats

def snapshot_fingerprint(state):
    """快照头 md5 指纹：对排序后的 (item_id,state,ts) 序列求 md5[:16]（K3 增强补丁③）。"""
    canon = "|".join(f"{k}={v['state']}@{v['ts']}" for k, v in sorted(state.items()))
    return hashlib.md5(canon.encode("utf-8")).hexdigest()[:16]

def compact(path, snapshot_path):
    """压实：replay→写 JSON 快照（头带 md5 指纹）→原 JSONL 归档改名。返回指纹。"""
    state, stats = replay(path)
    fp = snapshot_fingerprint(state)
    snap = {"snapshot_md5": fp, "compacted_at": _now(), "source_lines": stats["total"],
            "bad_lines": stats["bad"], "items": state}
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)
    return fp

if __name__ == "__main__":
    p = "<注册处>/交割台账.jsonl"
    cmd = sys.argv[1] if len(sys.argv) > 1 else "replay"
    if cmd == "replay":
        st, stats = replay(p)
        print(json.dumps({"stats": stats, "items": len(st),
                          "fingerprint": snapshot_fingerprint(st)}, ensure_ascii=False, indent=1))
