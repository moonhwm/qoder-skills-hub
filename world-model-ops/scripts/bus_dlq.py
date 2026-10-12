# -*- coding: utf-8 -*-
"""bus_dlq.py —— 总线死信队列与重试（应令条⑥：「在事件总线中引入死信队列与重试策略…自动触发回滚并记录审计日志」）
用法：
  python bus_dlq.py emit --path <件> [--kind artifact] [--seat a2a-node-local] [--tries 3]
  python bus_dlq.py retry [--tries 3]        # 续传死信队列中之待办
  python bus_dlq.py audit [--tail 20]        # 审计日志
  python bus_dlq.py status                   # 队列与审计之统计
  python bus_dlq.py selftest                 # 自检：故意用错总线目录 ⇒ 应入死信队列
★纪律：
  ①「回滚」只做"可安全回滚"者（以正本覆盖异常副本／撤销未推送之本地暂存）；
    ★凡破坏性回滚（重置提交、删除件）一律不自动执行，须主权人明示。
  ②死信队列与审计日志皆 append-only，不覆写、不删行。
  ③凭据零回显；任何网络失败须留 last_error 原文（截断）。
（中文串一律用「」）
"""
import argparse, json, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
BUS_DIR = EX/"bus"
DLQ = SEAT/"ledger"/"bus_dlq.jsonl"
AUDIT = SEAT/"ledger"/"bus_audit.jsonl"
EMIT = SEAT/"exp"/"lsbus_format_ops.py"


def _append(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")




def _already_emitted(path, bus):
    """★幂等闸：同 path ＋ 同内容哈希已在总线 ⇒ 返回 True（应跳过，勿重复投递）"""
    import hashlib
    b = pathlib.Path(bus)/"bus.jsonl"
    if not b.exists(): return False
    try:
        h = hashlib.sha3_256(pathlib.Path(path).read_bytes()).hexdigest()[:16]
    except Exception:
        return False
    name = pathlib.Path(path).name
    for l in b.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]:
        if name in l and h in l: return True
    return False

def _valid_bus(bus):
    """★总线合法性：目录已存在且其下有 bus.jsonl（否则拒绝，避免误造"假总线"而自认成功）"""
    b = pathlib.Path(bus)
    return b.is_dir() and (b/"bus.jsonl").exists()


def _readback_ok(path, bus):
    """★emit 后复验：该件名须确实出现在 bus.jsonl 之末 40 行内"""
    b = pathlib.Path(bus)/"bus.jsonl"
    if not b.exists(): return False
    lines = b.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
    return any(pathlib.Path(path).name in l for l in lines)

def _emit_once(path, kind, seat, bus):
    cmd = [sys.executable, str(EMIT), "emit", "--bus", str(bus), "--path", str(path), "--kind", kind, "--seat", seat]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    ok = ("已入总" in out) or (p.returncode == 0 and "ERR" not in out)
    return ok, out.strip().splitlines()[-1][:160] if out.strip() else "无输出"


def emit(path, kind, seat, tries, bus=None):
    bus = bus or BUS_DIR
    path = pathlib.Path(path)
    if not _valid_bus(bus):
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "dead_letter", "path": str(path),
               "name": path.name, "kind": kind, "seat": seat, "bus": str(bus), "attempts": 0,
               "last_error": "★总线目录非法（不存在或缺 bus.jsonl）⇒ 拒绝 emit，未写任何字节", "status": "pending"}
        _append(DLQ, rec); _append(AUDIT, {"ts": rec["ts"], "event": "dead_letter_reject_bus", "path": path.name, "bus": str(bus)})
        print("   ✗ ★总线目录非法 ⇒ 拒绝 emit（未写任何字节）｜已入死信队列")
        return False
    last = ""
    for k in range(1, tries + 1):
        if _already_emitted(path, bus):
            _append(AUDIT, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "duplicate_skip",
                            "path": pathlib.Path(path).name, "note": "★同 path 同哈希已在总线 ⇒ 幂等跳过"})
            print("   · 幂等跳过（同 path 同哈希已在总线）：%s" % pathlib.Path(path).name[:60])
            return True
        ok, last = _emit_once(path, kind, seat, bus)
        if ok and not _readback_ok(path, bus):
            ok, last = False, "★假成功：输出称已入总，但 bus.jsonl 末 40 行未见该件名"
        if ok:
            _append(AUDIT, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "emit_ok",
                            "path": path.name, "attempts": k, "bus": str(bus)})
            print("   ✓ 已入总（第 %d 次）｜ %s" % (k, last[:90]))
            return True
        print("   · 第 %d 次未成 ⇒ %s" % (k, last[:90]))
        time.sleep(2 * k)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "dead_letter", "path": str(path),
           "name": path.name, "kind": kind, "seat": seat, "bus": str(bus), "attempts": tries,
           "last_error": last, "status": "pending"}
    _append(DLQ, rec)
    _append(AUDIT, {"ts": rec["ts"], "event": "dead_letter", "path": path.name, "attempts": tries, "last_error": last[:120]})
    print("   ✗ 已入死信队列（%s）｜★未丢失，可 retry 续传" % DLQ.name)
    return False


def retry(tries=3):
    if not DLQ.exists():
        print("   死信队列为空"); return
    rows = [json.loads(l) for l in DLQ.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    pend = [r for r in rows if r.get("status") == "pending"]
    print("   死信队列：%d 条，其中待办 %d 条" % (len(rows), len(pend)))
    for r in pend:
        if not _valid_bus(r.get("bus", str(BUS_DIR))):
            _append(AUDIT, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "retry_skip_invalid_bus", "path": r.get("name", "")})
            print("   · 跳过（总线仍非法）：%s" % r.get("name", "")); continue
        ok, last = _emit_once(r["path"], r.get("kind", "artifact"), r.get("seat", "a2a-node-local"), r.get("bus", str(BUS_DIR)))
        if ok and not _readback_ok(r["path"], r.get("bus", str(BUS_DIR))):
            ok, last = False, "★假成功（复验未过）"
        if ok:
            _append(DLQ, {**r, "ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "retry_ok", "status": "resolved"})
            _append(AUDIT, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "retry_ok", "path": r.get("name", "")})
            print("   ✓ 续传成：%s" % r.get("name", ""))
        else:
            _append(AUDIT, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "retry_fail", "path": r.get("name", ""), "err": last[:100]})
            print("   · 续传仍未成：%s ｜ %s" % (r.get("name", ""), last[:70]))


def audit(tail=20):
    if not AUDIT.exists(): print("   审计日志为空"); return
    rows = AUDIT.read_text(encoding="utf-8", errors="replace").splitlines()
    print("   审计日志 %d 行 ⇒ 末 %d 行：" % (len(rows), min(tail, len(rows))))
    for l in rows[-tail:]: print("     " + l[:150])


def status():
    def cnt(p, pred=lambda r: True):
        if not p.exists(): return 0
        return sum(1 for l in p.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip() and pred(json.loads(l)))
    print("   死信队列 %s ⇒ 总 %d ｜ 待办 %d ｜ 已解 %d" % (DLQ.name, cnt(DLQ),
          cnt(DLQ, lambda r: r.get("status") == "pending"), cnt(DLQ, lambda r: r.get("status") == "resolved")))
    print("   审计日志 %s ⇒ 总 %d" % (AUDIT.name, cnt(AUDIT)))


def selftest():
    print("   ★ 自检：故意指向不存在之总线目录 ⇒ 应入死信队列")
    fake = SEAT/"exp"/"_no_such_bus_dir_"
    r = emit(SEAT/"exp"/"pub_safe.py", "artifact", "a2a-node-local", 1, bus=fake)
    print("   ⇒ 判：%s" % ("★自检通过（失败已入死信队列，未丢失）" if not r else "★异常：不该成功"))
    status()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
    p1 = sub.add_parser("emit"); p1.add_argument("--path", required=True); p1.add_argument("--kind", default="artifact")
    p1.add_argument("--seat", default="a2a-node-local"); p1.add_argument("--tries", type=int, default=3)
    p2 = sub.add_parser("retry"); p2.add_argument("--tries", type=int, default=3)
    p3 = sub.add_parser("audit"); p3.add_argument("--tail", type=int, default=20)
    sub.add_parser("status"); sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "emit": emit(a.path, a.kind, a.seat, a.tries)
    elif a.cmd == "retry": retry(a.tries)
    elif a.cmd == "audit": audit(a.tail)
    elif a.cmd == "status": status()
    elif a.cmd == "selftest": selftest()
    else: ap.print_help()
