#!/usr/bin/env python3
"""quota-ledger-ops · 额度账本 CLI（纯标准库，零凭证）
账本：/mnt/agents/temp/quota_ledger/<task>.jsonl（.tmp+os.replace 原子写；行级哈希链 lhash=md5(prev+canonical)[:16]）

用法：
  quota_ledger.py init <task> --budget 1.5 --unit cny|percent|tokens
  quota_ledger.py log <task> <phase> --in 40000 --out 6000 [--note "..."]
  quota_ledger.py status <task>
  quota_ledger.py report <task>
  quota_ledger.py estimate --in 50000 --out 8000
  quota_ledger.py --self-test
单价锚点：环境变量 QUOTA_RATE_IN / QUOTA_RATE_OUT（元/百万token）覆盖；默认=DeepSeek V4-Flash 谷时参考价（估算，非账单）。
"""
import argparse, hashlib, json, os, sys, time

DIR = os.environ.get("QUOTA_LEDGER_DIR", "/mnt/agents/temp/quota_ledger")
RATE_IN = float(os.environ.get("QUOTA_RATE_IN", "1.5"))    # 元/百万 input（谷时参考）
RATE_OUT = float(os.environ.get("QUOTA_RATE_OUT", "4.5"))  # 元/百万 output（谷时参考）
GENESIS = "0" * 16


def path(task):
    return os.path.join(DIR, task + ".jsonl")


def read_all(task):
    p = path(task)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def append_row(task, row):
    os.makedirs(DIR, exist_ok=True)
    rows = read_all(task)
    prev = rows[-1]["lhash"] if rows else GENESIS
    row["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    canon = json.dumps(row, sort_keys=True, ensure_ascii=False)
    row["lhash"] = hashlib.md5((prev + canon).encode()).hexdigest()[:16]
    tmp = path(task) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows + [row]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path(task))
    return row["lhash"]


def totals(task):
    rows = read_all(task)
    hdr = next((r for r in rows if r.get("type") == "init"), None)
    logs = [r for r in rows if r.get("type") == "log"]
    ti = sum(r.get("in_tokens", 0) for r in logs)
    to = sum(r.get("out_tokens", 0) for r in logs)
    return hdr, logs, ti, to


def cost_cny(ti, to):
    return ti / 1e6 * RATE_IN + to / 1e6 * RATE_OUT


def verdict(pct):
    if pct is None:
        return "N/A（percent/tokens 口径，自行对照池量）"
    if pct >= 100:
        return "OVER→止损结项，交接 quota-guard-ops"
    if pct >= 80:
        return "WARN80→降档或请示"
    if pct >= 50:
        return "WARN50→提示一次，继续"
    return "OK"


def cmd_init(a):
    h = append_row(a.task, {"type": "init", "task": a.task, "budget": a.budget,
                            "unit": a.unit, "rate_in": RATE_IN, "rate_out": RATE_OUT})
    print(f"init ok: {a.task} budget={a.budget}{a.unit} lhash={h}（单价锚点 {RATE_IN}/{RATE_OUT} 元/M，估算口径）")


def cmd_log(a):
    if not read_all(a.task):
        sys.exit("账本不存在，先 init")
    h = append_row(a.task, {"type": "log", "phase": a.phase, "in_tokens": a.in_tokens,
                            "out_tokens": a.out_tokens, "note": a.note or ""})
    _, _, ti, to = totals(a.task)
    print(f"log ok: {a.phase} in={a.in_tokens} out={a.out_tokens} lhash={h} | 累计 in={ti} out={to} ≈¥{cost_cny(ti, to):.4f}")


def cmd_status(a):
    hdr, logs, ti, to = totals(a.task)
    if not hdr:
        sys.exit("账本不存在")
    c = cost_cny(ti, to)
    pct = (c / hdr["budget"] * 100) if hdr["unit"] == "cny" and hdr["budget"] else None
    print(f"task={a.task} budget={hdr['budget']}{hdr['unit']} | 阶段数={len(logs)}")
    print(f"tokens: in={ti} out={to} 合计={ti + to} | 估算费用≈¥{c:.4f} | 占预算 {f'{pct:.1f}%' if pct is not None else 'N/A'} | {verdict(pct)}")


def cmd_report(a):
    hdr, logs, ti, to = totals(a.task)
    if not hdr:
        sys.exit("账本不存在")
    c = cost_cny(ti, to)
    pct = (c / hdr["budget"] * 100) if hdr["unit"] == "cny" and hdr["budget"] else None
    print(f"# 额度结项报告 · {a.task}\n")
    print(f"- 预算：{hdr['budget']}{hdr['unit']}（单价锚点 {hdr['rate_in']}/{hdr['rate_out']} 元/M，估算非账单）")
    print(f"- 合计：in={ti} out={to} ≈¥{c:.4f}（占预算 {f'{pct:.1f}%' if pct is not None else 'N/A'}）\n")
    print("| 阶段 | in | out | 估算¥ | 备注 |")
    print("|---|---|---|---|---|")
    for r in logs:
        print(f"| {r['phase']} | {r['in_tokens']} | {r['out_tokens']} | {cost_cny(r['in_tokens'], r['out_tokens']):.4f} | {r.get('note', '')} |")
    print(f"\n判决：{verdict(pct)}")
    print("落款：见 references/voices.md（萧红实引/尼采拟箴言/海德格尔缺藏拟体，≤2 行）")


def cmd_estimate(a):
    print(f"in={a.in_tokens} out={a.out_tokens} → ≈¥{cost_cny(a.in_tokens, a.out_tokens):.4f}"
          f"（锚点 {RATE_IN}/{RATE_OUT} 元/M，估算非账单）")


def self_test():
    os.environ["QUOTA_LEDGER_DIR"] = DIR = os.path.join("/mnt/agents/temp", "quota_ledger_selftest")
    globals()["DIR"] = DIR
    os.makedirs(DIR, exist_ok=True)
    t = "selftest"
    p = path(t)
    if os.path.exists(p):
        os.remove(p)
    append_row(t, {"type": "init", "task": t, "budget": 1.0, "unit": "cny",
                   "rate_in": RATE_IN, "rate_out": RATE_OUT})
    append_row(t, {"type": "log", "phase": "p1", "in_tokens": 100000, "out_tokens": 5000, "note": ""})
    append_row(t, {"type": "log", "phase": "p2", "in_tokens": 200000, "out_tokens": 8000, "note": ""})
    hdr, logs, ti, to = totals(t)
    assert ti == 300000 and to == 13000 and len(logs) == 2
    hs = [r["lhash"] for r in read_all(t)]
    assert len(set(hs)) == 3, "链哈希应互异"
    c = cost_cny(ti, to)
    assert abs(c - (0.3 * RATE_IN + 0.013 * RATE_OUT)) < 1e-9
    print(f"SELF-TEST PASS | 3 rows chained | cost≈¥{c:.4f}")
    os.remove(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("init"); p.add_argument("task"); p.add_argument("--budget", type=float, required=True)
    p.add_argument("--unit", choices=["cny", "percent", "tokens"], default="cny"); p.set_defaults(f=cmd_init)
    p = sub.add_parser("log"); p.add_argument("task"); p.add_argument("phase")
    p.add_argument("--in", dest="in_tokens", type=int, required=True)
    p.add_argument("--out", dest="out_tokens", type=int, required=True)
    p.add_argument("--note", default=""); p.set_defaults(f=cmd_log)
    p = sub.add_parser("status"); p.add_argument("task"); p.set_defaults(f=cmd_status)
    p = sub.add_parser("report"); p.add_argument("task"); p.set_defaults(f=cmd_report)
    p = sub.add_parser("estimate"); p.add_argument("--in", dest="in_tokens", type=int, default=0)
    p.add_argument("--out", dest="out_tokens", type=int, default=0); p.set_defaults(f=cmd_estimate)
    a = ap.parse_args()
    if a.self_test:
        self_test()
    elif hasattr(a, "f"):
        a.f(a)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
