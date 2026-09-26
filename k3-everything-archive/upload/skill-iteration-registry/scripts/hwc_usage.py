#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hwc_usage.py — 华为云用量全局指标工具 v1.0（2026-08-31 立法配套件）

全局指标定义（《华为云用量全局指标规程 v1.0》技术件）：
  每一次外部模型调用必录：ts/model/seat/project/skill/conversation/
  prompt_tokens/completion_tokens/reasoning_tokens/cost/ok/md5。
  台账=<注册处>/蜂群消耗台账.jsonl（追加式，永不清零）。

用法：
  record --model glm-5.2 --seat GLM52-A --project 项目名 --skill 技能名 \
         --conv 会话标识 --usage '{"prompt_tokens":..,"completion_tokens":..,"completion_tokens_details":{"reasoning_tokens":..}}' [--md5 ..]
  gate            日闸检查：今日累计≥¥50 → 输出 ALARM 并 exit 1（调用前必过）；本月累计≥¥800 输出 WARN 软警（不停闸）
  report [--day YYYY-MM-DD]   总量/分模型/分日/分项目汇总
"""
import json, sys, time, os

LEDGER = "<注册处>/蜂群消耗台账.jsonl"
DAILY_CAP = 50.0  # 新闸 ¥50/日（2026-09-02 用户口令「全面提高相关用量，放开跑」；三件套在册：用量参数变更三件套_日闸_v1.0_20260902.md；旧闸 ¥5 备份 archive/hwc_usage.py.bak_20260902_pre_gate50；五常否决可一字回滚）
MONTHLY_SOFT_CAP = 800.0  # 月度软警 ¥800（对齐用户 Kimi 本平台日烧观察值；触及只报警不停闸）
# 勘误(2026-09-02 逃逸#21)：本行原注「服务甲」系「提米」语音映射误判，用户更正=Kimi；数值不变
PRICE = {  # 刊例 元/百万token（输入, 输出；reasoning 计入输出）
    "glm-5.2": (5.6, 19.6), "glm-5.1": (5.6, 19.6),
    "deepseek-v4-pro": (8.4, 16.8), "deepseek-v4-flash": (1.4, 2.8),
}

def calc_cost(model, u):
    pin, pout = PRICE.get(model, (0, 0))
    return (u.get("prompt_tokens", 0) * pin + u.get("completion_tokens", 0) * pout) / 1e6

def load():
    if not os.path.exists(LEDGER):
        return []
    out = []
    for ln in open(LEDGER, encoding="utf-8"):
        ln = ln.strip()
        if ln:
            try: out.append(json.loads(ln))
            except json.JSONDecodeError: pass
    return out

def today_spend():
    t = time.strftime("%Y-%m-%d")
    return sum(e.get("cost", 0) for e in load() if e.get("date") == t)

def cmd_record(a):
    u = json.loads(a["usage"])
    cost = a.get("cost")
    if cost is None:
        cost = calc_cost(a["model"], u)
    rec = {
        "date": time.strftime("%Y-%m-%d"), "ts": time.strftime("%Y%m%d_%H%M%S"),
        "seat": a.get("seat", "?"), "model": a["model"],
        "project": a.get("project", "未归属"), "skill": a.get("skill", "未归属"),
        "conv": a.get("conv", "未归属"),
        "cost": round(cost, 4), "ok": True, "usage": u,
        "md5": a.get("md5", ""),
    }
    open(LEDGER, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"recorded: {rec['model']} ¥{rec['cost']} | 今日累计 ¥{today_spend():.4f}")
    if today_spend() >= DAILY_CAP:
        print(f"ALARM: 日闸 ¥{DAILY_CAP} 触及，L1 即报用户")

def month_spend():
    m = time.strftime("%Y-%m")
    return sum(e.get("cost", 0) for e in load() if str(e.get("date","")).startswith(m))

def cmd_gate():
    s = today_spend()
    ms = month_spend()
    print(f"今日累计 ¥{s:.4f} / 闸 ¥{DAILY_CAP} ｜ 本月累计 ¥{ms:.4f} / 软警 ¥{MONTHLY_SOFT_CAP}")
    if ms >= MONTHLY_SOFT_CAP:
        print("WARN: 月度软警触及，报告用户（不停闸）")
    if s >= DAILY_CAP:
        print("ALARM: 日闸触及，禁止继续扣费调用，L1 即报用户"); sys.exit(1)
    print("PASS")

def cmd_report(a):
    rows = load()
    day = a.get("day")
    if day: rows = [r for r in rows if r.get("date") == day]
    tot = sum(r.get("cost", 0) for r in rows)
    tok = sum(r.get("usage", {}).get("total_tokens", 0) for r in rows)
    print(f"条目 {len(rows)} | 总成本 ¥{tot:.4f} | 总tokens {tok:,}")
    for key in ("model", "date", "project", "skill"):
        agg = {}
        for r in rows:
            k = r.get(key, "未归属"); agg.setdefault(k, [0, 0.0])
            agg[k][0] += 1; agg[k][1] += r.get("cost", 0)
        print(f"-- 按{key} --")
        for k, (n, c) in sorted(agg.items(), key=lambda x: -x[1][1]):
            print(f"   {k}: {n}次 ¥{c:.4f}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    cmd = args[0]
    kv = {}
    i = 1
    while i < len(args):
        if args[i].startswith("--"):
            kv[args[i][2:]] = args[i + 1]; i += 2
        else:
            i += 1
    {"record": cmd_record, "gate": lambda _: cmd_gate(), "report": cmd_report}[cmd](kv)
