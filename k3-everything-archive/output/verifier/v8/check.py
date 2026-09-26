#!/usr/bin/env python3
# verifier v8 —「烧」批次收尾核验（I1-I5），纯标准库
import json, re, os, sys

REG = "<注册处>"
RECEIPTS = ["<输出区>/蜂群回执/P0review_GLM52%s.md" % s
            for s in ["条文席", "逃逸面席", "用户代言席", "核算席", "ACK席"]]
RESULTS = "<输出区>/burn_20260902/results.json"
LEDGER = REG + "/蜂群消耗台账.jsonl"
BOOK = REG + "/表决记录册_S2026L3-01.jsonl"
SECRETS = ["REDACTED20"]  # 扩展项：api_key 前缀（其余六项沿用 v1 check.py 定义，此处只测本批产物最常接触项）
DAILY_CAP = 50.0

def fail(msg): print("FAIL:", msg); return False
def ok(msg): print("PASS:", msg); return True

r = []

# I1 回执齐
missing = [p for p in RECEIPTS if not (os.path.exists(p) and os.path.getsize(p) > 10)]
r.append(ok("I1 五席回执在盘非空") if not missing else fail("I1 缺/空: %s" % missing))

# I2 票型可解析
try:
    data = json.load(open(RESULTS, encoding="utf-8"))
    seats = {d["seat"]: d for d in data}
    bad = [s for s, d in seats.items() if d.get("http") != 200]
    votes = {}
    for s in ["GLM52-条文席", "GLM52-逃逸面席", "GLM52-用户代言席"]:
        c = seats[s]["content"]
        v = dict(re.findall(r'\{"item":\s*"(R\d)",\s*"vote":\s*"([^"}]+)"', c))
        votes[s] = v
        if set(v) != {"R1", "R2", "R3"}: bad.append(s + "票型不全:%s" % v)
    r.append(ok("I2 http=200 且票型可解析: %s" % json.dumps(votes, ensure_ascii=False)) if not bad else fail("I2 %s" % bad))
except Exception as e:
    r.append(fail("I2 异常 %s" % e))

# I3 入账与闸
try:
    today, cnt, total = "2026-09-02", 0, 0.0
    day_total = 0.0
    for ln in open(LEDGER, encoding="utf-8"):
        try: rec = json.loads(ln)
        except Exception: continue
        if rec.get("date") == today:
            c = float(rec.get("cost", 0) or 0); day_total += c
            if rec.get("skill") == "GLM燃烧工单W123":
                cnt += 1; total += c
    good = cnt >= 5 and day_total < DAILY_CAP
    r.append(ok("I3 W123 入账 %d 条 ¥%.4f；当日总额 ¥%.4f < ¥%.0f" % (cnt, total, day_total, DAILY_CAP)) if good
             else fail("I3 cnt=%d day_total=%.4f" % (cnt, day_total)))
except Exception as e:
    r.append(fail("I3 异常 %s" % e))

# I4 票册落册
try:
    lines = [json.loads(l) for l in open(BOOK, encoding="utf-8") if l.strip()]
    md5ok = all(re.fullmatch(r"[0-9a-f]{32}", l.get("md5", "")) for l in lines)
    types = [l.get("type") for l in lines]
    good = len(lines) >= 5 and md5ok and types.count("票型落册") == 3 and "票型归并" in types
    r.append(ok("I4 票册 %d 行 md5 齐 类型=%s" % (len(lines), types)) if good else fail("I4 lines=%d md5ok=%s types=%s" % (len(lines), md5ok, types)))
except Exception as e:
    r.append(fail("I4 异常 %s" % e))

# I5 零明文（本批产物：回执五件+票册+results.json；check.py 本体豁免）
hits = []
for p in RECEIPTS + [BOOK, RESULTS]:
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    for s in SECRETS:
        if s in t: hits.append((p, s[:6] + "..."))
r.append(ok("I5 零明文（SECRETS 扩展项零命中）") if not hits else fail("I5 命中 %s" % hits))

print("== v8 汇总 ==", "ALL PASS" if all(r) else "HAS FAIL")
sys.exit(0 if all(r) else 1)
