#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
netdisk_browse.py —— 坚果云分享链接「枚举 + 下载」一体化管线
=============================================================================
管线（接口用法详见 references/jianguoyun_api.md）：
  1. 目录枚举 GET /d/ajax/dirops/pubDIRBrowse?hash={分享ID}&relPath={路径}（BFS 全量）
  2. 清单落盘 文件清单_{名称}_第{N}轮.json（按轮次命名，不覆盖历史清单）
  3. 逐文件下载 GET /d/ajax/dirops/pubDIRLink?k={分享ID}&dn={根目录名}&p={relPath}
     -> 允许时返回 {"payload": <下载URL或其包装>}，再 GET 该 URL 取字节落盘；
     -> 禁止时返回 403 {"errorCode": "SandboxAccessDenied", ...}，如实留痕。

纪律（硬性，源自两轮 403 实战教训）：
- 不绕过任何权限设置；403 如实记录，绝不伪造下载成功。
- 请求节奏 0.5~1.0s；确定性 4xx 不重试，网络错误/5xx 最多重试 2 次。
- 证据追加写入 下载尝试证据.json 的 round{N} 节点：跨轮次只追加不覆盖；
  同轮次重跑仅替换本链接的旧记录（幂等），其余轮次原样保留。
- 每完成一个链接即落盘一次证据，防长任务中断后证据丢失。

用法：
    python3 netdisk_browse.py <分享链接或hash> [--out 归档目录] [--dn 根目录名]
                              [--round N] [--enum-only] [--trigger "触发说明"]
    python3 netdisk_browse.py --smoke        # 内置假响应自测，不联网

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
LINK_URL = "https://www.jianguoyun.com/d/ajax/dirops/pubDIRLink"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PACE_MIN, PACE_MAX = 0.5, 1.0  # 节奏纪律：每次请求间隔
HASH_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def now_str():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S +0800")


def pace():
    time.sleep(random.uniform(PACE_MIN, PACE_MAX))


# ---------------------------------------------------------------- 传输层
class UrllibFetcher:
    """真实联网传输。get() 返回 (http_status, content)；网络异常返回 (-1, 描述)。"""

    def get(self, url, timeout=40, binary=False):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                return resp.status, (data if binary else data.decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            body = e.read()
            if binary:
                return e.code, body
            try:
                return e.code, body.decode("utf-8", "replace")
            except Exception:
                return e.code, repr(body)
        except Exception as e:
            return -1, f"{type(e).__name__}: {e}"


class FakeFetcher:
    """--smoke 内置假响应：1 个目录 + 2 个文件（1 个允许下载、1 个 403）。不联网。"""

    TREE = {
        "/": [{"name": "docs", "relPath": "/docs", "type": "directory",
               "size": 0, "mtime": "2026-08-12"},
              {"name": "readme.txt", "relPath": "/readme.txt", "type": "file",
               "size": 19, "mtime": "2026-08-12"}],
        "/docs": [{"name": "a.pdf", "relPath": "/docs/a.pdf", "type": "file",
                   "size": 1024, "mtime": "2026-08-12"}],
    }
    PAYLOAD_URL = "https://dl.fake.invalid/readme.txt"
    PAYLOAD_BYTES = b"fake readme content"

    def get(self, url, timeout=40, binary=False):
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path.endswith("/pubDIRBrowse"):
            rel = qs.get("relPath", ["/"])[0]
            objs = self.TREE.get(rel)
            if objs is None:
                return 404, json.dumps({"errorCode": "NotFound",
                                        "detailMsg": f"no such relPath: {rel}"})
            return 200, json.dumps({"objects": objs}, ensure_ascii=False)
        if parsed.path.endswith("/pubDIRLink"):
            p = qs.get("p", [""])[0]
            if p == "/readme.txt":
                return 200, json.dumps({"payload": self.PAYLOAD_URL})
            return 403, json.dumps({"errorCode": "SandboxAccessDenied",
                                    "detailMsg": "Can not download it"})
        if url == self.PAYLOAD_URL:
            return 200, (self.PAYLOAD_BYTES if binary
                         else self.PAYLOAD_BYTES.decode("utf-8"))
        return 404, json.dumps({"errorCode": "NotFound", "detailMsg": url})


# ---------------------------------------------------------------- 管线核心
def get_json(fetcher, url, tries=2):
    """带重试的 JSON GET。返回 (status, obj_or_rawtext)。4xx 为确定性响应不重试。"""
    status, text = -1, ""
    for attempt in range(tries + 1):
        status, text = fetcher.get(url)
        if status == 200:
            try:
                return status, json.loads(text)
            except Exception as e:
                return status, {"_parse_error": f"{type(e).__name__}: {e}",
                                "_raw": str(text)[:500]}
        if status != -1 and not (500 <= status < 600):
            break
        if attempt < tries:
            pace()
    return status, text


def browse_all(fetcher, hash_):
    """从根目录 BFS 枚举全部对象。返回 (objects, enum_errors)。"""
    objects, errors = [], []
    queue, seen = ["/"], set()
    while queue:
        rel = queue.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        url = BROWSE_URL + "?" + urllib.parse.urlencode({"hash": hash_, "relPath": rel})
        status, obj = get_json(fetcher, url)
        if status != 200 or not isinstance(obj, dict) or "objects" not in obj:
            errors.append({"relPath": rel, "http_status": status,
                           "response_head": str(obj)[:300]})
            pace()
            continue
        for o in obj["objects"]:
            objects.append(o)
            if o.get("type") == "directory":
                queue.append(o["relPath"])
        pace()
    objects.sort(key=lambda o: o.get("relPath", ""))
    return objects, errors


def extract_download_url(payload):
    """从 pubDIRLink 的 payload 提取真实下载 URL（兼容字符串/字典包装）。"""
    if isinstance(payload, str) and payload.startswith("http"):
        return payload
    if isinstance(payload, dict):
        for key in ("url", "link", "downloadUrl", "href"):
            v = payload.get(key)
            if isinstance(v, str) and v.startswith("http"):
                return v
    return None


def safe_join(root, rel_path):
    """按 relPath 落盘，防路径穿越。"""
    rel = rel_path.lstrip("/")
    dest = os.path.normpath(os.path.join(root, rel))
    root_n = os.path.normpath(root)
    if dest != root_n and not (dest + os.sep).startswith(root_n + os.sep):
        raise ValueError(f"非法路径: {rel_path}")
    return dest


def try_download_one(fetcher, link_key, hash_, dn, fobj, dest_root):
    """对单个文件执行 pubDIRLink -> (若允许) 落盘。返回尝试记录（证据留痕格式）。"""
    rel = fobj["relPath"]
    rec = {"link": link_key, "relPath": rel,
           "endpoint": "/d/ajax/dirops/pubDIRLink?k=%s&dn=%s&p=%s" % (hash_, dn, rel),
           "attempts": 0, "http_status": None, "saved_path": None,
           "saved_bytes": None, "expected_size": fobj.get("size"),
           "errorCode": None, "detailMsg": None}
    for attempt in range(3):  # 首次 + 最多 2 次重试
        rec["attempts"] = attempt + 1
        url = LINK_URL + "?" + urllib.parse.urlencode({"k": hash_, "dn": dn, "p": rel})
        status, obj = get_json(fetcher, url, tries=0)
        rec["http_status"] = status
        if isinstance(obj, str):  # 非 200 时 get_json 返回原文，尽量解析出 errorCode
            try:
                obj = json.loads(obj)
            except Exception:
                pass
        if status == 200 and isinstance(obj, dict):
            dl = extract_download_url(obj.get("payload"))
            if not dl:
                rec["detailMsg"] = f"200 但未能从 payload 解析下载URL: {str(obj)[:200]}"
                break
            dst_status, content = fetcher.get(dl, timeout=120, binary=True)
            rec["download_url_status"] = dst_status
            if dst_status == 200 and isinstance(content, (bytes, bytearray)):
                dest = safe_join(dest_root, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(content)
                rec["saved_path"] = os.path.relpath(dest, dest_root)
                rec["saved_bytes"] = len(content)
                exp = fobj.get("size")
                rec["size_match"] = (exp is None or exp == len(content))
                rec["detailMsg"] = "OK"
            else:
                rec["detailMsg"] = f"下载URL响应异常: {str(content)[:200]}"
            break
        # 失败分支：记录错误信息
        if isinstance(obj, dict):
            rec["errorCode"] = obj.get("errorCode")
            rec["detailMsg"] = obj.get("detailMsg") or str(obj)[:200]
        else:
            rec["detailMsg"] = str(obj)[:200]
        # 确定性 403/4xx 权限拒绝：不重试、不绕过
        if isinstance(status, int) and 400 <= status < 500:
            break
        if attempt < 2:
            pace()
    return rec


def parse_share(share):
    """从分享链接或裸 hash 解析分享 ID。"""
    share = share.strip()
    m = re.search(r"jianguoyun\.com/p/([A-Za-z0-9_-]+)", share)
    if m:
        return m.group(1)
    if HASH_RE.match(share):
        return share
    raise ValueError(f"无法解析坚果云分享 ID: {share!r}（应为 /p/{'{hash}'} 链接或裸 hash）")


def run_pipeline(args, fetcher):
    hash_ = parse_share(args.share)
    dn = args.dn or "share"  # 地域分流拿不到根目录名时用占位名；权限判定与 dn 无关
    link_key = hash_
    out_root = os.path.abspath(args.out)
    ldir = os.path.join(out_root, link_key)
    os.makedirs(ldir, exist_ok=True)
    evidence_path = os.path.join(out_root, "下载尝试证据.json")
    round_key = f"round{args.round}"

    if os.path.exists(evidence_path):
        with open(evidence_path, encoding="utf-8") as f:
            evidence = json.load(f)
    else:
        evidence = {}
    node = evidence.get(round_key) or {
        "interface": ("pubDIRBrowse(hash,relPath) 枚举；pubDIRLink(k,dn,p) 取下载URL "
                      "（签名核自分享页前端 pubobject_page.min-*.js）"),
        "enumeration": {}, "download_attempts": [], "summary": {},
    }
    node["fetched_at"] = now_str()
    if args.trigger:
        node["trigger"] = args.trigger

    objects, enum_errors = browse_all(fetcher, hash_)
    files = [o for o in objects if o.get("type") == "file"]
    dirs = [o for o in objects if o.get("type") == "directory"]

    manifest_name = f"文件清单_{dn}_第{args.round}轮.json"
    manifest_path = os.path.join(ldir, manifest_name)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"source": f"https://www.jianguoyun.com/p/{hash_}",
                   "fetched_at": now_str(), "round": args.round,
                   "objects": objects}, f, ensure_ascii=False, indent=1)

    node["enumeration"][link_key] = {
        "dirs": len(dirs), "files": len(files), "enum_errors": enum_errors,
        "manifest": os.path.relpath(manifest_path, out_root),
    }
    print(f"[{link_key}] 枚举完成：{len(dirs)} 目录 / {len(files)} 文件 "
          f"-> {os.path.relpath(manifest_path, out_root)}", flush=True)

    ok = fail = 0
    if not args.enum_only:
        # 同轮次重跑：仅替换本链接旧记录，保证幂等；其他轮次节点不受影响
        node["download_attempts"] = [
            r for r in node["download_attempts"] if r.get("link") != link_key]
        for fo in files:
            rec = try_download_one(fetcher, link_key, hash_, dn, fo, ldir)
            node["download_attempts"].append(rec)
            if rec["saved_bytes"] is not None:
                ok += 1
                print(f"  [OK] {rec['relPath']} -> {rec['saved_bytes']}B", flush=True)
            else:
                fail += 1
                print(f"  [FAIL] {rec['relPath']} HTTP {rec['http_status']} "
                      f"{rec.get('errorCode')}: {rec.get('detailMsg')}", flush=True)
            pace()
    node["summary"][link_key] = {"success": ok, "failed": fail, "total": len(files)}
    evidence[round_key] = node
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, ensure_ascii=False, indent=1)
    print(f"[{link_key}] 完成：成功 {ok} / 失败 {fail} / 共 {len(files)}"
          f"（证据追加至 {round_key}，未覆盖历史轮次）", flush=True)
    return 0


# ---------------------------------------------------------------- 冒烟自测
def smoke():
    """用 FakeFetcher 走完整管线：验证清单 JSON 结构、成功/403 双路径留痕。"""
    with tempfile.TemporaryDirectory(prefix="netdisk_smoke_") as tmp:
        args = argparse.Namespace(share="SmokeHash123", out=tmp, dn="冒烟测试",
                                  round=1, enum_only=False,
                                  trigger="--smoke 内置自测（不联网）")
        rc = run_pipeline(args, FakeFetcher())
        assert rc == 0, "管线返回非零"

        manifest = os.path.join(tmp, "SmokeHash123", "文件清单_冒烟测试_第1轮.json")
        with open(manifest, encoding="utf-8") as f:
            m = json.load(f)
        assert m["round"] == 1 and m["source"].endswith("/p/SmokeHash123")
        files = [o for o in m["objects"] if o["type"] == "file"]
        dirs = [o for o in m["objects"] if o["type"] == "directory"]
        assert len(files) == 2 and len(dirs) == 1, f"清单结构异常: {len(files)}f/{len(dirs)}d"

        with open(os.path.join(tmp, "下载尝试证据.json"), encoding="utf-8") as f:
            ev = json.load(f)
        node = ev["round1"]
        attempts = {r["relPath"]: r for r in node["download_attempts"]}
        ok_rec = attempts["/readme.txt"]
        assert ok_rec["saved_bytes"] == len(FakeFetcher.PAYLOAD_BYTES)
        assert ok_rec["size_match"] is True and ok_rec["detailMsg"] == "OK"
        saved = os.path.join(tmp, "SmokeHash123", ok_rec["saved_path"])
        assert open(saved, "rb").read() == FakeFetcher.PAYLOAD_BYTES
        fail_rec = attempts["/docs/a.pdf"]
        assert fail_rec["http_status"] == 403
        assert fail_rec["errorCode"] == "SandboxAccessDenied"
        assert fail_rec["saved_bytes"] is None and fail_rec["attempts"] == 1, \
            "确定性 403 不应重试"
        assert node["summary"]["SmokeHash123"] == {"success": 1, "failed": 1, "total": 2}

        # 第 2 轮重跑：验证 round 追加不覆盖第 1 轮
        args.round = 2
        run_pipeline(args, FakeFetcher())
        with open(os.path.join(tmp, "下载尝试证据.json"), encoding="utf-8") as f:
            ev = json.load(f)
        assert "round1" in ev and "round2" in ev, "轮次必须追加不覆盖"
        assert len(ev["round1"]["download_attempts"]) == 2

    print("[SMOKE OK] netdisk_browse: 枚举/下载/403留痕/轮次追加 全部通过（未联网）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="坚果云分享链接枚举+下载一体化管线")
    ap.add_argument("share", nargs="?", help="分享链接 https://www.jianguoyun.com/p/<hash> 或裸 hash")
    ap.add_argument("--out", default=".", help="归档根目录（默认当前目录）")
    ap.add_argument("--dn", default=None, help="分享根目录名（地域分流拿不到时省略，用占位名）")
    ap.add_argument("--round", type=int, default=1, help="轮次编号（证据节点 round{N}，默认 1）")
    ap.add_argument("--enum-only", action="store_true", help="只枚举出清单，不尝试下载")
    ap.add_argument("--trigger", default="", help="本轮触发说明（写入证据，便于留痕）")
    ap.add_argument("--smoke", action="store_true", help="内置假响应自测，不联网")
    args = ap.parse_args()
    if args.smoke:
        return smoke()
    if not args.share:
        ap.error("缺少分享链接；或使用 --smoke 自测")
    return run_pipeline(args, UrllibFetcher())


if __name__ == "__main__":
    sys.exit(main())
