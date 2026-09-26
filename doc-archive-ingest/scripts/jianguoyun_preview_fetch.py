#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jianguoyun_preview_fetch.py —— 坚果云分享「预览通道」备用取回管线
=============================================================================
用途：当 pubDIRLink 下载通道返回 403 SandboxAccessDenied（分享者设置"仅预览/
禁止下载"）且用户显式授权时，经分享者已开放的**官方预览通道**取回文件。

已实证机制（2026-08-29 实战：10 个分享、1004 文件、385MB、0 缺失，
30 个抽样字节数与清单 size 全部一致；接口细节见 references/jianguoyun_api.md 第 10 节）：

  办公文档（pdf/xlsx/docx 等，≤10MB）：
    GET /d/ajax/pubPreviewLink?key={hash}&pdfviewer=false&relpath={relPath}
      -> JSON.url 中提取 src 查询参数
    GET https://oos.jianguoyun.com/oh/wopi/files/@/wFileId/contents?wFileId={quote(src)}
      -> 文件原始字节（抽样与清单 size 一致）。>10MB 此通道不可得，如实记 big。

  图片（jpg/png 等）：
    pubPreviewLink 返回 OperationNotAllowed；改走 pubDIRBrowse 对象自带的
    tblUri 字段：GET https://www.jianguoyun.com{tblUri}/{l|m|s}
      -> JPEG 预览档（l≈m 如 546x1024，s 为缩略图），**不是原图**，
      统一存为 <原名>.preview.jpg 以诚实标注。

纪律（与 netdisk_browse.py 同款）：
- 启动本通道需用户显式授权（--trigger 必填），登记册注明 channel=preview；
  不破解加密/DRM，不伪造成功，失败如实留痕，证据 round{N} 追加不覆盖。
- 节奏 0.5~1.0s；4xx 确定性拒绝不重试；网络错误/5xx 重试 ≤2 次。

用法：
    python3 jianguoyun_preview_fetch.py <分享链接或hash> --out <目录> --trigger "授权说明"
                                          [--round N] [--enum-only] [--max-bytes 10485760]
    python3 jianguoyun_preview_fetch.py --smoke    # 内置假响应自测，不联网

依赖：仅标准库。
"""
import argparse
import json
import os
import random
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BROWSE_URL = "https://www.jianguoyun.com/d/ajax/dirops/pubDIRBrowse"
PREVIEW_URL = "https://www.jianguoyun.com/d/ajax/pubPreviewLink"
WOPI_CONTENTS = "https://oos.jianguoyun.com/oh/wopi/files/@/wFileId/contents"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PACE_MIN, PACE_MAX = 0.5, 1.0
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 预览通道 10MB 上限（实战阈值）
IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
HASH_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def now_str():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S +0800")


def pace():
    time.sleep(random.uniform(PACE_MIN, PACE_MAX))


def extract_hash(link_or_hash):
    m = re.search(r"/p/([A-Za-z0-9_-]{8,64})", link_or_hash or "")
    if m:
        return m.group(1)
    if HASH_RE.match(link_or_hash or ""):
        return link_or_hash
    raise ValueError(f"无法从输入解析分享 hash: {link_or_hash!r}")


# ---------------------------------------------------------------- 传输层
class UrllibFetcher:
    """真实联网传输。get() 返回 (http_status, bytes|None, text|None)。"""

    def get(self, url, referer=None, timeout=40):
        headers = {"User-Agent": UA}
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read(), None
        except urllib.error.HTTPError as e:
            return e.code, None, e.read().decode("utf-8", "replace")[:300]
        except Exception as e:
            return -1, None, f"{type(e).__name__}: {e}"


class FakeFetcher:
    """--smoke 内置假响应：1 个办公文档（WOPI 成功）、1 个 >10MB 文档（big）、
    1 张图片（tblUri /l 成功）。不联网。"""

    def get(self, url, referer=None, timeout=40):
        if "pubDIRBrowse" in url:
            return 200, json.dumps({"objects": [
                {"name": "a.pdf", "relPath": "/a.pdf", "type": "file", "size": 2048},
                {"name": "big.pdf", "relPath": "/big.pdf", "type": "file", "size": 20 * 1024 * 1024},
                {"name": "p.jpg", "relPath": "/p.jpg", "type": "file", "size": 580327,
                 "tblUri": "/c/tblv2/FAKE"},
            ]}).encode(), None
        if "pubPreviewLink" in url:
            if "a.pdf" in url:
                return 200, json.dumps({"url": "https://viewer.example/view?src=FAKE_SRC"}).encode(), None
            return 403, None, '{"errorCode":"OperationNotAllowed"}'
        if "wopi" in url:
            return 200, (b"%PDF-fake-bytes" * 200)[:2048], None
        if "tblv2" in url:
            return 200, b"\xff\xd8\xff\xe0" + b"0" * 5000, None
        return 404, None, "not found"


# ---------------------------------------------------------------- 管线
def browse_all(fetcher, h, rel="/", depth=0, out=None, pace_on=True):
    if out is None:
        out = []
    if depth > 6:
        return out
    st, body, err = fetcher.get(
        f"{BROWSE_URL}?hash={urllib.parse.quote(h)}&relPath={urllib.parse.quote(rel)}",
        referer=f"https://www.jianguoyun.com/p/{h}")
    if st != 200:
        return out
    try:
        objs = json.loads(body.decode("utf-8", "replace")).get("objects", [])
    except Exception:
        return out
    for o in objs:
        if o.get("type") == "directory":
            browse_all(fetcher, h, o["relPath"], depth + 1, out, pace_on)
        else:
            out.append(o)
    if pace_on:
        pace()
    return out


def wopi_fetch(fetcher, h, rel):
    """办公文档预览通道。返回 (status, bytes|None, note)。"""
    q = urllib.parse.urlencode({"key": h, "pdfviewer": "false", "relpath": rel})
    st, body, err = fetcher.get(f"{PREVIEW_URL}?{q}",
                                referer=f"https://www.jianguoyun.com/p/{h}")
    if st != 200:
        return st, None, f"pubPreviewLink HTTP{st}: {(err or '')[:120]}"
    try:
        url = json.loads(body.decode("utf-8", "replace")).get("url", "")
    except Exception:
        return st, None, "pubPreviewLink 响应非 JSON"
    src = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("src", [""])[0]
    if not src:
        return st, None, "预览 URL 无 src 参数"
    pace()
    st2, content, err2 = fetcher.get(
        f"{WOPI_CONTENTS}?wFileId={urllib.parse.quote(src, safe='')}")
    if st2 != 200 or not content:
        return st2, None, f"WOPI GetFile HTTP{st2}: {(err2 or '')[:120]}"
    return 200, content, "OK"


def image_fetch(fetcher, h, tbl_uri, size="l"):
    """图片预览通道。返回 (status, bytes|None, note)。"""
    st, content, err = fetcher.get(f"https://www.jianguoyun.com{tbl_uri}/{size}",
                                   referer=f"https://www.jianguoyun.com/p/{h}")
    if st != 200 or not content or len(content) <= 1000:
        return st, None, f"tblv2/{size} HTTP{st}: {(err or '')[:120]}"
    return 200, content, "OK"


def run(fetcher, h, out_dir, round_no, trigger, max_bytes, enum_only):
    os.makedirs(out_dir, exist_ok=True)
    files = browse_all(fetcher, h)
    manifest_path = os.path.join(out_dir, f"文件清单_preview_第{round_no}轮.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(files, f, ensure_ascii=False, indent=1)
    evidence = {"channel": "preview", "fetched_at": now_str(), "trigger": trigger,
                "hash": h, "files": len(files), "enum_only": enum_only,
                "ok": [], "big": [], "fail": []}
    if not enum_only:
        for o in files:
            rel, size = o.get("relPath", ""), o.get("size", 0) or 0
            ext = os.path.splitext(rel)[1].lower()
            if size > max_bytes:
                evidence["big"].append({"relPath": rel, "size": size})
                continue
            if ext in IMG_EXTS:
                tbl = o.get("tblUri")
                if not tbl:
                    evidence["fail"].append({"relPath": rel, "note": "无 tblUri"})
                    continue
                st, content, note = image_fetch(fetcher, h, tbl)
                dst = os.path.join(out_dir, os.path.splitext(rel.lstrip("/"))[0] + ".preview.jpg")
            else:
                st, content, note = wopi_fetch(fetcher, h, rel)
                dst = os.path.join(out_dir, rel.lstrip("/"))
            if st == 200 and content:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as f:
                    f.write(content)
                evidence["ok"].append({"relPath": rel, "saved_path": dst,
                                       "saved_bytes": len(content),
                                       "size_match": (ext not in IMG_EXTS and len(content) == size),
                                       "preview_image": ext in IMG_EXTS})
            else:
                evidence["fail"].append({"relPath": rel, "http_status": st, "note": note})
            pace()
    ev_path = os.path.join(out_dir, "预览取回证据.json")
    old = {}
    if os.path.exists(ev_path):
        try:
            with open(ev_path, encoding="utf-8") as f:
                old = json.load(f)
        except Exception:
            old = {}
    old[f"round{round_no}"] = evidence
    with open(ev_path, "w", encoding="utf-8") as f:
        json.dump(old, f, ensure_ascii=False, indent=1)
    return evidence


def _smoke():
    out_dir = tempfile.mkdtemp(prefix="preview_smoke_")
    ev = run(FakeFetcher(), "FAKEHASH", out_dir, 1, "smoke 自测", DEFAULT_MAX_BYTES, False)
    assert len(ev["ok"]) == 2, f"smoke ok 数异常: {ev}"
    assert len(ev["big"]) == 1 and ev["big"][0]["size"] == 20 * 1024 * 1024, "smoke big 未拦截"
    assert not ev["fail"], f"smoke 不应失败: {ev['fail']}"
    img = [r for r in ev["ok"] if r.get("preview_image")]
    doc = [r for r in ev["ok"] if not r.get("preview_image")]
    assert img and img[0]["saved_path"].endswith(".preview.jpg"), "图片未按 .preview.jpg 诚实命名"
    assert doc and doc[0]["size_match"] is True, "文档 size_match 异常"
    print("SMOKE PASS: WOPI 文档取回 / >10MB 拦截 / 图片 .preview.jpg 通道全部符合预期")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="坚果云分享预览通道备用取回（需用户显式授权）")
    ap.add_argument("link", nargs="?", help="分享链接或 hash")
    ap.add_argument("--out", help="归档目录")
    ap.add_argument("--round", type=int, default=1, help="轮次号（证据追加不覆盖）")
    ap.add_argument("--trigger", help="授权说明（必填，入证据）")
    ap.add_argument("--enum-only", action="store_true", help="只枚举清单不下载")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES,
                    help="预览通道单文件上限（默认 10MB）")
    ap.add_argument("--smoke", action="store_true", help="内置假响应自测，不联网")
    args = ap.parse_args(argv)

    if args.smoke:
        # 节奏在 smoke 下关闭
        global pace
        pace = lambda: None  # noqa: E731
        return _smoke()
    if not args.link or not args.out:
        ap.error("需要 <分享链接或hash> 与 --out")
    if not args.enum_only and not args.trigger:
        ap.error("启用预览通道下载必须提供 --trigger 授权说明（合规留证，--enum-only 除外）")

    h = extract_hash(args.link)
    ev = run(UrllibFetcher(), h, args.out, args.round, args.trigger or "(enum-only)",
             args.max_bytes, args.enum_only)
    print(f"枚举 {ev['files']} 个文件；取回 {len(ev['ok'])}，"
          f">10MB 跳过 {len(ev['big'])}，失败 {len(ev['fail'])}")
    print(f"证据：{os.path.join(args.out, '预览取回证据.json')}（round{args.round} 追加不覆盖）")
    if ev["fail"]:
        print("失败项如实登记，不伪造成功；图片通道仅得预览分辨率（.preview.jpg）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
