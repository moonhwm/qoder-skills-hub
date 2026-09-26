#!/usr/bin/env python3
"""认罪认罚检测器（附和偏倚机检三指标）
用法:
  python3 acquittal_bias_detector.py check <opinion1.txt> [opinion2.txt ...] [--votes 5:0] [--threshold 0.6]
  python3 acquittal_bias_detector.py ledger <ledger.json> --case-id <id> --objections <n>
  python3 acquittal_bias_detector.py --self-test
指标: ①首轮≥4/5通过且反对理由<50字符(由调用方传入 votes 与意见文本长度判定)
      ②连续3案无反对票(ledger)
      ③评审意见 n-gram 重叠率>阈值(默认0.6, 设计初值)
退出码: 0=未命中(净), 1=命中(建议复审), 2=用法/自检错误
纯标准库。变更后先跑 --self-test。
"""
import json, re, sys, os

def ngrams(text, n=3):
    toks = re.findall(r"[一-鿿]|[A-Za-z0-9]+", text)
    return set(tuple(toks[i:i+n]) for i in range(len(toks)-n+1)) if len(toks) >= n else {tuple(toks)}

def overlap(a, b):
    A, B = ngrams(a), ngrams(b)
    return len(A & B) / max(1, min(len(A), len(B)))

def check(opinions, votes, threshold):
    hits = []
    if votes:
        try:
            agree, total = (int(x) for x in votes.split(":"))
        except ValueError:
            print("votes 格式应为 同意:总数", file=sys.stderr); sys.exit(2)
        if total > 0 and agree/total >= 0.8:
            short = [i for i, o in enumerate(opinions) if len(o.strip()) < 50]
            if short and agree > 0:
                hits.append(f"指标①: 首轮{agree}/{total}通过且席{short}反对理由<50字符")
    maxov, pair = 0.0, None
    for i in range(len(opinions)):
        for j in range(i+1, len(opinions)):
            ov = overlap(opinions[i], opinions[j])
            if ov > maxov: maxov, pair = ov, (i, j)
    if maxov > threshold:
        hits.append(f"指标③: 席{pair} n-gram重叠率{maxov:.2f}>{threshold}")
    return hits

def ledger(path, case_id, objections):
    data = json.load(open(path)) if os.path.exists(path) else {"cases": []}
    data["cases"].append({"case_id": case_id, "objections": objections})
    json.dump(data, open(path, "w"), ensure_ascii=False, indent=1)
    last3 = data["cases"][-3:]
    if len(last3) == 3 and all(c["objections"] == 0 for c in last3):
        return ["指标②: 连续3案无一反对票"]
    return []

def self_test():
    a = "反对放行。风雨无阻对老人构成可预见伤害路径，辩方证据充分。"
    b = "反对放行。风雨无阻对老人构成可预见伤害路径，辩方证据充分。"
    c = "我不同意这个方案，理由完全不同：成本太高且没有经过任何实测，应该先小规模试运行再决定推广。"
    assert check([a, b], "5:5", 0.6), "同构意见应命中指标③"
    assert not check([a, c], "1:5", 0.6), "互异意见+非首轮通过不应命中"
    h = check(["好。"]*5, "5:5", 0.6)
    assert any("指标①" in x for x in h), "全票+短理由应命中指标①"
    import tempfile
    p = os.path.join(tempfile.mkdtemp(), "l.json")
    assert not ledger(p, "c1", 2)
    assert not ledger(p, "c2", 0)
    assert not ledger(p, "c3", 0)
    assert ledger(p, "c4", 0) == ["指标②: 连续3案无一反对票"], "连续3案零反对应命中"
    print("self-test PASS"); sys.exit(0)

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--self-test" in args: self_test()
    if not args: print(__doc__); sys.exit(2)
    cmd = args[0]
    if cmd == "ledger":
        path = args[1]
        cid = args[args.index("--case-id")+1]
        obj = int(args[args.index("--objections")+1])
        hits = ledger(path, cid, obj)
    elif cmd == "check":
        files = [a for a in args[1:] if not a.startswith("--")]
        votes = args[args.index("--votes")+1] if "--votes" in args else None
        th = float(args[args.index("--threshold")+1]) if "--threshold" in args else 0.6
        hits = check([open(f, encoding="utf-8").read() for f in files], votes, th)
    else:
        print(__doc__); sys.exit(2)
    if hits:
        print("HIT 建议复审:"); [print(" -", h) for h in hits]; sys.exit(1)
    print("CLEAN"); sys.exit(0)
