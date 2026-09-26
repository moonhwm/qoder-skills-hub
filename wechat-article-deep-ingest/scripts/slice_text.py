#!/usr/bin/env python3
"""长文分片器：段落/标题边界优先，片头带元信息。v1.3 2026-08-25 修改人: Orchestrator (Kimi K3)
用法: python3 slice_text.py <article.md> [--size 4000] [--out-dir slices/]
"""
import argparse, os, re

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file"); p.add_argument("--size", type=int, default=4000)
    p.add_argument("--out-dir", default="")
    a = p.parse_args()
    t = open(a.file, encoding="utf-8").read()
    m = re.match(r"\A---\n.*?\n---\n", t, flags=re.S)
    fm, body = (m.group(0), t[m.end():]) if m else ("", t)
    slug = os.path.basename(a.file).replace(".md", "")
    # 按段落切，边界优先标题
    paras = re.split(r"\n{2,}", body)
    slices, cur = [], []
    size = 0
    for para in paras:
        if size + len(para) > a.size and cur:
            slices.append("\n\n".join(cur)); cur, size = [], 0
        cur.append(para); size += len(para)
        if para.startswith("#") and size > a.size * 0.6:  # 标题后若已超60%则收片
            slices.append("\n\n".join(cur)); cur, size = [], 0
    if cur: slices.append("\n\n".join(cur))
    total = len(slices)
    out_paths = []
    for i, s in enumerate(slices, 1):
        prev_anchor = slices[i-2].strip().split("\n")[-1][:40] if i > 1 else ""
        next_anchor = s.strip().split("\n")[0][:40]
        piece = f"<!-- slice {i}/{total} of {slug} | 上片尾: {prev_anchor} | 本片头: {next_anchor} -->\n\n{s}"
        if a.out_dir:
            os.makedirs(a.out_dir, exist_ok=True)
            fp = os.path.join(a.out_dir, f"{slug}.slice{i:02d}.md")
            open(fp, "w", encoding="utf-8").write(piece); out_paths.append(fp)
    print(f"{slug}: {len(body)}字 → {total}片（均片{len(body)//max(total,1)}字）")
    for fp in out_paths: print(" ", fp)

if __name__ == "__main__": main()
