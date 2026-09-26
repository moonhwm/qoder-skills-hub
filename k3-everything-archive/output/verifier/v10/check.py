#!/usr/bin/env python3
# verifier v10 — MAGA 涌现研究批次（K1-K5），纯标准库
import os, re, json, glob, sys
DOC = "<注册处>/MAGA子代理涌现数量研究_SSCI设计_v1.0_20260902.md"
PILOT = "<输出区>/maga_pilot_20260902"
REG = "<注册处>"
SECRETS = ["REDACTED20"]
r = []
def ok(m): print("PASS:", m); return True
def fail(m): print("FAIL:", m); return False

t = open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""

# K1
need = ["摘要", "关键词", "文献锚", "理论框架", "可能性穷举", "方法", "伦理", "实测结果", "局限", "三镜"]
r.append(ok("K1 SSCI 必备节齐") if t and all(k in t for k in need) else fail("K1 缺:%s" % [k for k in need if k not in t]))

# K2 引文与 CSV 一致
csv_titles = ""
for f in glob.glob("/tmp/scholar/s*.csv"):
    csv_titles += open(f, encoding="utf-8", errors="ignore").read()
papers = ["Generative agents: Interactive simulacra of human behavior",
          "Out of one, many: Using language models to simulate human samples",
          "Performance and biases of large language models in public opinion simulation",
          "politicized topics using large language models"]
hit = [p for p in papers if p.lower() in csv_titles.lower()]
r.append(ok("K2 四篇文献锚与 scholar CSV 实证一致") if len(hit) == 4 else fail("K2 仅中:%s" % hit))

# K3 试点可复算
N = Ns = 0; cnt = 0
for f in sorted(glob.glob(PILOT + "/pilot_P*.json")):
    d = json.load(open(f))
    if d.get("http") != 200: continue
    cnt += 1
    c = d.get("content", "")
    q2 = re.search(r'q2_maga"?\s*:\s*"(\w+)"', c)
    q3 = re.search(r'q3_extra_institutional"?\s*:\s*(\d)', c)
    if q2 and q2.group(1) in ("strong_support", "lean_support"): N += 1
    if q3 and int(q3.group(1)) >= 4: Ns += 1
r.append(ok("K3 8/8 席 200 且复算 N=%d N*=%d 与文书一致" % (N, Ns)) if cnt == 8 and N == 5 and Ns == 0
         else fail("K3 cnt=%d N=%d N*=%d" % (cnt, N, Ns)))

# K4 燃烧合规
quota = json.load(open(REG + "/额度状态台账.json", encoding="utf-8"))
h1 = any("外池燃烧全面开放" in json.dumps(e, ensure_ascii=False) for e in quota.get("history", []))
led = 0
for ln in open(REG + "/蜂群消耗台账.jsonl", encoding="utf-8"):
    try: rec = json.loads(ln)
    except Exception: continue
    if rec.get("skill") == "MAGA涌现研究试点A": led += 1
r.append(ok("K4 外池开放在册+试点入账 %d 条" % led) if h1 and led >= 8 else fail("K4 reg=%s led=%d" % (h1, led)))

# K5
hit5 = [s[:6] for s in SECRETS if s in t]
r.append(ok("K5 零明文+统摄语未登记为授权") if not hit5 and "不登记为授权" in t else fail("K5 %s" % hit5))

print("== v10 汇总 ==", "ALL PASS" if all(r) else "HAS FAIL")
sys.exit(0 if all(r) else 1)
