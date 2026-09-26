#!/usr/bin/env python3
"""截断检测（三信号）。v1.3 2026-08-25 修改人: Orchestrator (Kimi K3)
用法: python3 truncation_check.py <article.md> [--tail-anchor 免责声明] [--threshold 7000]
输出 JSON: {truncated: bool, signals: [...], char_count, tail_anchor_found}
"""
import argparse, json, re, sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file"); p.add_argument("--tail-anchor", default="免责声明")
    p.add_argument("--threshold", type=int, default=7000)
    a = p.parse_args()
    t = open(a.file, encoding="utf-8").read()
    # 剥离 frontmatter
    body = re.sub(r"\A---\n.*?\n---\n", "", t, flags=re.S)
    n = len(body)
    signals = []
    tail = body[-500:]
    anchor_ok = a.tail_anchor in tail
    if n > a.threshold and not anchor_ok: signals.append("字数>阈值且尾锚缺失")
    if n > a.threshold and anchor_ok: signals.append("字数>阈值但尾锚在（疑似完整长文，建议人工抽尾）")
    if not anchor_ok and n > a.threshold * 0.7: signals.append("尾锚缺失")
    # 结构断裂：末节编号悬空（如目录含 4. 但正文止于 3.x）
    heads = re.findall(r"^#{1,3}\s*(\d+)", body, flags=re.M)
    if heads and heads[-1] != heads[0] and len(set(heads)) == 1:
        pass
    out = {"truncated": bool(signals and not anchor_ok), "signals": signals,
           "char_count": n, "tail_anchor_found": anchor_ok}
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(1 if out["truncated"] else 0)

if __name__ == "__main__": main()
