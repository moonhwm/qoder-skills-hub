# -*- coding: utf-8 -*-
"""daily_statement.py —— 每日四维对账单（应《跨生态A2A协作网络体系建设方案》：「以日志埋点与调用链追踪数据为基础，
建立成功率、延迟、配额、审计四维监测；对账单可重跑复现，每日形成对账单归档」）
四维：①成功率（总线投递／死信）②延迟（本轮实测之关键路径耗时）③配额（token 与花费）④审计（台账链／署名／落地率／留痕率／四仓一致）
★可重跑复现：同一输入重复运行，除时点与耗时段外读数应一致
用法：python daily_statement.py [--json out.json] [--no-net]
（中文串一律用「」）
"""
import argparse, json, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
WPS = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"
SEAT = WPS/"A2A新席_石敢当Cairn_20260928"
EX = WPS/"A2A共同体_共享交换区"
BUS = EX/"bus"/"bus.jsonl"
REPOS = {"cairn": HOME/"openplanlink-cairn", "mirror": HOME/"openplanlink-mirror",
         "hub": HOME/"qoder-skills-hub", "k3": HOME/"sleepless-flower-under-sealevel"}

def line(**kw): print("   " + "｜".join("%s=%s" % (k, v) for k, v in kw.items()))

def dim1_success():
    n = uid = dlq_p = dup = 0
    if BUS.exists():
        rows = [json.loads(l) for l in BUS.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        n = len(rows); uid = len({r.get("id") for r in rows})
    dlq = SEAT/"ledger"/"bus_dlq.jsonl"
    if dlq.exists():
        recs = [json.loads(l) for l in dlq.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        closed = {r.get("name") for r in recs if r.get("status") == "closed_selftest"}
        dlq_p = sum(1 for r in recs if r.get("status") == "pending" and r.get("name") not in closed)
    aud = SEAT/"ledger"/"bus_audit.jsonl"
    if aud.exists():
        dup = sum(1 for l in aud.read_text(encoding="utf-8", errors="replace").splitlines()
                  if l.strip() and json.loads(l).get("event") == "duplicate_skip")
    ok = n > 0 and dlq_p == 0
    line(维度="成功率", 总线条目=n, 唯一id=uid, 死信待办=dlq_p, 幂等跳过=dup, 判=("✓" if ok else "✗"))
    return {"bus_entries": n, "unique_ids": uid, "dlq_pending": dlq_p, "idempotent_skips": dup, "pass": ok}

def dim2_latency():
    t0 = time.time(); r = subprocess.run([sys.executable, str(SEAT/"ledger"/"cairn_ledger.py"), "verify"],
                                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    dt = time.time()-t0
    line(维度="延迟", 台账复核秒=round(dt, 2), 判=("✓" if dt < 30 else "·"))
    return {"ledger_verify_s": round(dt, 2)}

def dim3_quota():
    q = SEAT/"ledger"/"quota_ledger"
    tin = tout = 0; api = res = 0.0; ri = ro = 0.0
    files = list(q.glob("*.jsonl")) if q.exists() else []
    for f in files:
        for l in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not l.strip(): continue
            try: j = json.loads(l)
            except Exception: continue
            tin += int(j.get("in_tokens", 0) or 0); tout += int(j.get("out_tokens", 0) or 0)
            if j.get("type") == "init": ri, ro = float(j.get("rate_in", 0) or 0), float(j.get("rate_out", 0) or 0)
            if j.get("cost_cny"): api += float(j["cost_cny"])
            if j.get("kind") == "res_cost_correction": res += float(j.get("subtotal_cny", 0) or 0)
    api = (tin*ri + tout*ro)/1e6 if (ri or ro) else api
    line(维度="配额", 台账文件=len(files), 入token=tin, 出token=tout, 费率="%s/%s" % (ri, ro),
         API花费元=round(api, 4), 资源花费元=round(res, 2), 合计元=round(api+res, 2))
    return {"ledger_files": len(files), "tokens_in": tin, "tokens_out": tout, "api_cny": round(api, 4), "res_cny": round(res, 2)}

def dim2b_esc():
    """升级面端到端（读 ledger/esc_watch.jsonl）"""
    ew = SEAT/"ledger"/"esc_watch.jsonl"
    if not ew.exists():
        line(维度="升级面端到端", 状态="无计时簿", 判="·"); return {"n": 0}
    op = cl = over = 0; els = []
    for l in ew.read_text(encoding="utf-8", errors="replace").splitlines():
        if not l.strip(): continue
        j = json.loads(l)
        if j.get("event") == "open": op += 1
        elif j.get("event") == "close":
            cl += 1; els.append(float(j.get("elapsed_s", 0)))
            if not j.get("pass_60s"): over += 1
    line(维度="升级面端到端", 立案=op, 结案=cl, 未结=op-cl, 超60s=over,
         最长=("%.2f s" % max(els)) if els else "—", 判=("✓" if over == 0 else "✗"))
    return {"open": op, "close": cl, "over60": over, "max_s": (max(els) if els else None)}


def dim4_audit(no_net=False):
    fl = SEAT/"ledger"/"frontier_ledger.jsonl"
    entries = len(fl.read_text(encoding="utf-8", errors="replace").splitlines()) if fl.exists() else 0
    r = subprocess.run([sys.executable, str(SEAT/"ledger"/"cairn_ledger.py"), "verify"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    chain = "PASS" in ((r.stdout or "") + (r.stderr or ""))
    sig = None
    sv = SEAT/"exp"/"sig_verify.py"
    if sv.exists():
        o = subprocess.run([sys.executable, str(sv), "--dir", str(SEAT), "--glob", "**/*CAIRN-*.otl"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        txt = (o.stdout or "") + (o.stderr or "")
        import re
        m = re.search(r"相符\s*(\d+).*?不符\s*(\d+)", txt, re.S)
        if m: sig = {"ok": int(m.group(1)), "bad": int(m.group(2))}
    repos = {}
    for k, v in REPOS.items():
        if not (v/".git").exists(): repos[k] = "不在"; continue
        lo = subprocess.run(["git", "-C", str(v), "rev-parse", "--short=12", "HEAD"], capture_output=True, text=True).stdout.strip()
        if no_net: repos[k] = lo
        else:
            o = subprocess.run(["git", "-C", str(v), "ls-remote", "origin", "main"], capture_output=True, text=True).stdout.strip()
            rem = o.split()[0][:12] if o else "不可达"
            repos[k] = ("★一致 " if rem == lo else "★待补推 ") + lo
    line(维度="审计", 台账条目=entries, 链=("PASS" if chain else "★断"), 署名=("%d/%d" % (sig["ok"], sig["ok"]+sig["bad"])) if sig else "未测",
         四仓=" ｜ ".join("%s %s" % (k, v) for k, v in repos.items()))
    return {"entries": entries, "chain_pass": chain, "signature": sig, "repos": repos}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); ap.add_argument("--no-net", action="store_true")
    ap.add_argument("--close-selftest-dlq", action="store_true")
    a = ap.parse_args()
    if a.close_selftest_dlq:
        import json as _j
        dlq = SEAT/"ledger"/"bus_dlq.jsonl"
        recs = [_j.loads(l) for l in dlq.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        with open(dlq, "a", encoding="utf-8", newline="\n") as f:
            for r in recs:
                if r.get("status") == "pending" and "自检" in str(r.get("last_error", "")) or (
                   r.get("status") == "pending" and "_no_such_bus_dir_" in str(r.get("bus", ""))):
                    f.write(_j.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "close_selftest",
                                      "name": r.get("name"), "status": "closed_selftest",
                                      "note": "★自检样本（非法总线之拒绝路径）⇒ 结案，不计待办"}, ensure_ascii=False) + "\n")
                    print("   ✓ 已结案自检样本：%s" % r.get("name"))
    print("  ═══ 每日四维对账单（可重跑复现）｜ %s ═══" % time.strftime("%Y-%m-%d %H:%M:%S+0800"))
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "seat": "a2a-node-local"}
    out["success"] = dim1_success(); out["latency"] = dim2_latency(); out["esc"] = dim2b_esc(); out["quota"] = dim3_quota(); out["audit"] = dim4_audit(a.no_net)
    p = pathlib.Path(a.json) if a.json else SEAT/"ledger"/("daily_statement_%s.json" % time.strftime("%Y%m%d"))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   ✓ 已归档：%s" % p.name)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
