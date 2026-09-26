#!/usr/bin/env python3
"""跨AI交接打包器：把一组文件打成单个自包含 HTML（任何模型可读，绕开压缩包兼容问题）。
v1.0 2026-08-26 修改人: Orchestrator (Kimi K3)｜仅标准库
用法: python3 pack_handoff_html.py --out handoff.html file1.md file2.csv ...
"""
import argparse, html, os, datetime

def main():
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+"); p.add_argument("--out", required=True)
    p.add_argument("--title", default="跨AI交接包")
    a = p.parse_args()
    parts = [f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>{html.escape(a.title)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:960px;margin:2em auto;padding:0 1em;line-height:1.6}}
.file{{border:1px solid #ccc;border-radius:8px;margin:1.5em 0;padding:1em}}
h2{{font-size:1.1em;color:#8a6d3b}}pre{{white-space:pre-wrap;word-wrap:break-word;background:#f7f5f0;padding:1em;border-radius:6px;font-size:.9em}}
.meta{{color:#888;font-size:.85em}}</style></head><body>"""]
    parts.append(f"<h1>{html.escape(a.title)}</h1><p class='meta'>打包：Orchestrator（Kimi K3）｜{datetime.date.today().isoformat()}｜共 {len(a.files)} 件</p>")
    total = 0
    for fp in a.files:
        try:
            raw = open(fp, "rb").read(); total += len(raw)
            txt = raw.decode("utf-8", errors="replace")
            parts.append(f"<div class='file'><h2>📄 {html.escape(os.path.basename(fp))}</h2><p class='meta'>{fp} ｜ {len(raw)/1024:.1f} KB</p><pre>{html.escape(txt)}</pre></div>")
        except Exception as e:
            parts.append(f"<div class='file'><h2>⚠ {html.escape(os.path.basename(fp))}</h2><pre>读取失败: {html.escape(str(e))}</pre></div>")
    parts.append("</body></html>")
    open(a.out, "w", encoding="utf-8").write("\n".join(parts))
    print(f"[OK] {a.out} ｜ 源文件 {total/1e6:.2f}MB → HTML {os.path.getsize(a.out)/1e6:.2f}MB")
    if os.path.getsize(a.out) > 100e6:
        print("[WARN] 超 100MB——Kimi/助手甲单文件上限，请分片或走 COS 预签名（cos_upload.py，注意24h有效期）")

if __name__ == "__main__": main()
