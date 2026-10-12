# -*- coding: utf-8 -*-
"""memory_change_log.py —— 记忆变更日志（★借 letta-code `hooks/memory_logger.py` 之思路，2026-10-12）
所监之"记忆面"（各取其可核之指纹／计数值）：
  ①指针 exp/.cache/index_pointer.json（值＋其指纹）②索引档 exp/.cache/section_index*.json（名＋指纹）
  ③台账 ledger/frontier_ledger.jsonl（条数＋链末 hash）④档案 archive/docs/index.json（两 watch 件之最新版＋字数）
  ⑤登记表 ledger/index_registry.jsonl（条数）⑥总线 bus.jsonl（条数）
做法：读 state（上次快照）⇒ 与当前比对 ⇒ 变更逐条追加 ledger/memory_changes.jsonl（含 before／after）⇒ 写回 state
用法：python memory_change_log.py [--state <path>] [--selftest]
（中文串一律用「」）
"""
import argparse, hashlib, json, pathlib, sys, time

HOME = pathlib.Path.home()
PLAY = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"
SEAT = PLAY/"A2A新席_石敢当Cairn_20260928"
EX = PLAY/"A2A共同体_共享交换区"
STATE = SEAT/"ledger"/"memory_state.json"
CHG = SEAT/"ledger"/"memory_changes.jsonl"

def sha16(p):
    try: return hashlib.sha3_256(p.read_bytes()).hexdigest()[:16]
    except Exception: return None

def snapshot():
    s = {}
    ptr = SEAT/"exp"/".cache"/"index_pointer.json"
    s["pointer"] = {"exists": ptr.exists(), "sha16": sha16(ptr),
                    "index": (json.loads(ptr.read_text(encoding="utf-8")).get("index") if ptr.exists() else None)}
    idxs = {}
    for q in sorted((SEAT/"exp"/".cache").glob("section_index*.json")):
        idxs[q.name] = sha16(q)
    s["indexes"] = idxs
    led = SEAT/"ledger"/"frontier_ledger.jsonl"
    if led.exists():
        lines = [l for l in led.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        s["ledger"] = {"n": len(lines), "last_hash": (json.loads(lines[-1]).get("hash") if lines else None)}
    reg = SEAT/"ledger"/"index_registry.jsonl"
    if reg.exists():
        s["registry_n"] = len([l for l in reg.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()])
    di = SEAT/"archive"/"docs"/"index.json"
    if di.exists():
        try:
            j = json.loads(di.read_text(encoding="utf-8"))
            s["docs"] = {k: {"ver": (j.get(k) or {}).get("latest", {}).get("ver"),
                             "chars": (j.get(k) or {}).get("latest", {}).get("chars")} for k in ("outline", "polish")}
        except Exception: pass
    bus = EX/"bus"/"bus.jsonl"
    if bus.exists():
        s["bus_n"] = len([l for l in bus.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()])
    return s

def diff(old, new):
    out = []
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k), new.get(k)
        if a != b: out.append({"field": k, "before": a, "after": b})
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--state", default=""); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    st = pathlib.Path(a.state) if a.state else STATE
    cur = snapshot()
    if a.selftest:
        print("  ═══ 记忆变更日志 自测（注入合成旧态 ⇒ 须检出变更）═══")
        fake = dict(cur)
        fake["ledger"] = {"n": (cur.get("ledger") or {}).get("n", 0) - 3, "last_hash": "★合成的旧链末"}
        fake["bus_n"] = (cur.get("bus_n") or 0) - 2
        d = diff(fake, cur)
        print("   合成旧态 ⇒ 检出变更 %d 条：%s" % (len(d), "、".join(x["field"] for x in d)))
        # ★自纠（2026-10-12）：原期望含 pointer，然当前本无指针 ⇒ "无差异"才是正确行为
        #   ⇒ 改以"当前必有值之两项"（ledger 与 bus_n）为必检项
        ok = any(x["field"] == "ledger" for x in d) and any(x["field"] == "bus_n" for x in d)
        print("   ⇒ 自测判：%s" % ("✓ 能检出（含 ledger 与 bus_n）" if ok else "★未检出 ⇒ 须修"))
        return 0 if ok else 1
    old = {}
    if st.exists():
        try: old = json.loads(st.read_text(encoding="utf-8"))
        except Exception: old = {}
    first = not old
    d = [] if first else diff(old, cur)
    print("  ═══ 记忆变更日志 ｜ %s ═══" % ("★首跑（建基线）" if first else "%d 条变更" % len(d)))
    if not first:
        for x in d[:12]:
            print("   ★%s ｜ 前：%s ⇒ 后：%s" % (x["field"], json.dumps(x["before"], ensure_ascii=False)[:56],
                                              json.dumps(x["after"], ensure_ascii=False)[:56]))
        if d:
            with open(CHG, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "changes": d}, ensure_ascii=False) + "\n")
    st.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   记忆面读数：指针 %s ｜ 索引档 %d ｜ 台账 %s ｜ 登记表 %s ｜ 文档 %s ｜ 总线 %s" % (
        (cur.get("pointer") or {}).get("index") or "无",
        len(cur.get("indexes") or {}), (cur.get("ledger") or {}).get("n"), cur.get("registry_n"),
        json.dumps(cur.get("docs"), ensure_ascii=False)[:44], cur.get("bus_n")))
    print("   ⇒ 判：%s" % ("✓ 基线已建（无变更可报）" if first else ("✓ 已记 %d 条变更" % len(d) if d else "✓ 无变更")))
    return 0

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
