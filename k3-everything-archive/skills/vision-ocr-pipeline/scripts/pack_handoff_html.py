#!/usr/bin/env python3
"""跨AI交接打包器 v1.1：把一组文件打成单个自包含 HTML（任何模型可读，绕开压缩包兼容问题）。
v1.1 2026-08-27 修改人: Orchestrator (Kimi K3)｜仅标准库（PIL 可选：仅用于读取图片尺寸，缺失时降级为"尺寸未知"）
  修复：v1.0 把图片按 UTF-8 文本转义成乱码 <pre>，跨AI传图必丢——现图片一律 base64
  内联为 <img>（data URI）；其它非文本二进制内联为可下载 <a download> 链接；文本仍走 <pre>。
  已知边界：非 UTF-8 文本（GBK 等）会按解码失败处理、降级为下载链接而不尝试其它编码。
  （<技能安装位> 只读挂载期间，本文件暂存 <输出区>/，挂载恢复后回填技能目录）
v1.0 2026-08-26 修改人: Orchestrator (Kimi K3)｜仅标准库
用法: python3 pack_handoff_html.py --out handoff.html file1.md file2.csv pic1.png ...
"""
import argparse, base64, html, os, datetime

IMG_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp"}

def img_dims(fp):
    try:
        from PIL import Image
        with Image.open(fp) as im:
            return f"{im.size[0]}x{im.size[1]}"
    except Exception:
        return "尺寸未知(无PIL)"

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
.meta{{color:#888;font-size:.85em}}img{{max-width:100%;border:1px solid #ddd;border-radius:4px}}</style></head><body>"""]
    parts.append(f"<h1>{html.escape(a.title)}</h1><p class='meta'>打包：Orchestrator（Kimi K3）｜{datetime.date.today().isoformat()}｜共 {len(a.files)} 件｜v1.1 图片已内联</p>")
    total = 0
    for fp in a.files:
        try:
            raw = open(fp, "rb").read(); total += len(raw)
            name = html.escape(os.path.basename(fp))
            ext = os.path.splitext(fp)[1].lower()
            kb = f"{len(raw)/1024:.1f} KB"
            if ext in IMG_MIME:
                b64 = base64.b64encode(raw).decode()
                parts.append(f"<div class='file'><h2>🖼 {name}</h2><p class='meta'>{html.escape(fp)} ｜ {img_dims(fp)} ｜ {kb} ｜ base64内联</p>"
                             f"<img src='data:{IMG_MIME[ext]};base64,{b64}' alt='{name}'></div>")
            else:
                txt = raw.decode("utf-8")
                parts.append(f"<div class='file'><h2>📄 {name}</h2><p class='meta'>{html.escape(fp)} ｜ {kb}</p><pre>{html.escape(txt)}</pre></div>")
        except UnicodeDecodeError:
            b64 = base64.b64encode(raw).decode()
            parts.append(f"<div class='file'><h2>📦 {name}</h2><p class='meta'>{html.escape(fp)} ｜ {kb} ｜ 二进制→下载链接</p>"
                         f"<a download='{name}' href='data:application/octet-stream;base64,{b64}'>下载 {name}</a></div>")
        except Exception as e:
            parts.append(f"<div class='file'><h2>⚠ {name}</h2><pre>读取失败: {html.escape(str(e))}</pre></div>")
    parts.append("</body></html>")
    open(a.out, "w", encoding="utf-8").write("\n".join(parts))
    print(f"[OK] {a.out} ｜ 源文件 {total/1e6:.2f}MB → HTML {os.path.getsize(a.out)/1e6:.2f}MB")
    if os.path.getsize(a.out) > 100e6:
        print("[WARN] 超 100MB——单文件上限，请分片或走 COS 预签名（cos_upload.py，注意24h有效期）")

if __name__ == "__main__":
    main()
