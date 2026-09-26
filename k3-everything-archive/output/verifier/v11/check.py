#!/usr/bin/env python3
# verifier v11 — 千席臂（L1-L5），纯标准库
import os, re, json, sys
DOC = "<注册处>/MAGA子代理涌现数量研究_千席臂预注册与穷举_v2.0_20260902.md"
JSONL = "<输出区>/maga_pilot_20260902/mass1000/mass1000.jsonl"
REG = "<注册处>"
SECRETS = ["REDACTED20"]
r = []
def ok(m): print("PASS:", m); return True
def fail(m): print("FAIL:", m); return False

t = open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""
need = ["预注册", "先验", "分析计划", "主计数", "核心发现", "先验对照", "族命中", "工程留痕", "结论", "后续臂"]
r.append(ok("L1 全节齐") if t and all(k in t for k in need) else fail("L1 缺:%s" % [k for k in need if k not in t]))

rows = {}
for ln in open(JSONL, encoding="utf-8"):
    try: d = json.loads(ln)
    except Exception: continue
    if d.get("http") == 200: rows[(d["seat"], d["model"])] = d
def parse(c):
    g = lambda p: (re.search(p, c).group(1) if re.search(p, c) else None)
    return g(r'q2_maga"?\s*:\s*"(\w+)"'), g(r'q3_extra_institutional"?\s*:\s*(\d)'), g(r'q4_recognize_provisional_gov\w*"?\s*:\s*"(\w+)"')
flash = {s: d for (s, m), d in rows.items() if m == "deepseek-v4-flash"}
glm = {s: d for (s, m), d in rows.items() if m == "glm-5.2"}
N = Ns = strong = q4y = 0
for d in flash.values():
    q2, q3, q4 = parse(d["content"])
    if q2 in ("strong_support", "lean_support"): N += 1
    if q2 == "strong_support": strong += 1
    if q3 and int(q3) >= 4: Ns += 1
    if q4 == "yes": q4y += 1
good = len(flash) == 1000 and len(glm) == 100 and N == 490 and Ns == 79 and strong == 182 and q4y == 21
r.append(ok("L2 复算 N=%d N*=%d strong=%d q4yes=%d（flash=%d glm=%d）" % (N, Ns, strong, q4y, len(flash), len(glm))) if good
         else fail("L2 N=%d Ns=%d strong=%d q4y=%d f=%d g=%d" % (N, Ns, strong, q4y, len(flash), len(glm))))

Nf = Ng = 0
for s, dg in glm.items():
    if s not in flash: continue
    q2f, _, _ = parse(flash[s]["content"]); q2g, _, _ = parse(dg["content"])
    Nf += q2f in ("strong_support", "lean_support"); Ng += q2g in ("strong_support", "lean_support")
r.append(ok("L3 配对 flash百席N=%d glm N=%d Δ=%dpp" % (Nf, Ng, Nf - Ng)) if Nf == 50 and Ng == 47 else fail("L3 %d/%d" % (Nf, Ng)))

r.append(ok("L4 miss 标红与工程留痕在案") if "miss" in t and "429" in t and "断点续跑" in t else fail("L4"))

hit = [s[:6] for s in SECRETS if s in t]
led = day = 0.0
cnt = 0
for ln in open(REG + "/蜂群消耗台账.jsonl", encoding="utf-8"):
    try: rec = json.loads(ln)
    except Exception: continue
    if rec.get("date") == "2026-09-02": day += float(rec.get("cost", 0) or 0)
    if rec.get("skill") == "MAGA涌现研究千席臂": cnt += 1
r.append(ok("L5 零明文+千席入账 %d 条+当日 ¥%.2f<¥50" % (cnt, day)) if not hit and cnt >= 1000 and day < 50 else fail("L5 hit=%s cnt=%d day=%.2f" % (hit, cnt, day)))

print("== v11 汇总 ==", "ALL PASS" if all(r) else "HAS FAIL")
sys.exit(0 if all(r) else 1)
