#!/usr/bin/env python3
"""公众号链接规范化+去重+批次切分。v1.0 2026-08-25 修改人: Orchestrator (Kimi K3)
输入: 文本(每行一链接或短码) 或 JSON [{"url","note"}]；输出规范清单+重复报告。
用法: python3 link_dedup.py links.txt [--batch-size 10] [--out clean.json]
"""
import argparse, json, re, sys

PREFIX = "https://mp.weixin.qq.com/s/"

def norm(raw):
    raw = raw.strip().strip("；;，,")
    if not raw: return None
    m = re.search(r"mp\.weixin\.qq\.com/s/([A-Za-z0-9_\-]+)", raw)
    if m: return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_\-]{10,40}", raw): return raw
    return None  # 非公众号域/无法识别

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input"); p.add_argument("--batch-size", type=int, default=10)
    p.add_argument("--out")
    a = p.parse_args()
    txt = open(a.input, encoding="utf-8").read()
    raws = []
    if a.input.endswith(".json"):
        raws = [it.get("url","") for it in json.loads(txt)]
    else:
        raws = re.split(r"[\n\r]+", txt)
    seen, clean, dup, bad = {}, [], [], []
    for r in raws:
        code = norm(r)
        if not code:
            if r.strip(): bad.append(r.strip()[:60])
            continue
        if code in seen: dup.append(code); continue
        seen[code] = 1; clean.append({"url": PREFIX+code, "code": code})
    batches = [clean[i:i+a.batch_size] for i in range(0, len(clean), a.batch_size)]
    rep = {"total_in": len([r for r in raws if r.strip()]), "unique": len(clean),
           "duplicates": dup, "unrecognized": bad, "batches": len(batches)}
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if a.out:
        json.dump({"report": rep, "items": clean, "batches": batches},
                  open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[OK] -> {a.out}", file=sys.stderr)

if __name__ == "__main__": main()
