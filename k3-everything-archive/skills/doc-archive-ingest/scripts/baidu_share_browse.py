#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
baidu_share_browse.py —— 百度网盘（百度云）「官方 xpan + 分享页逆向」双通道枚举管线
=============================================================================
通道（接口事实详见 references/baidu_netdisk_api.md，data_cutoff=2026-08-24，
conf=estimated）：
  1. 官方 xpan（用户本人网盘，--token 由用户自行在开放平台 OAuth 获取，
     脚本绝不代申请）：
       --token T --dir 路径        列目录（GET xpan/file?method=list，start/limit
                                   分页，limit≤1000，BFS 下钻子目录）
       --token T --fsids "[..]" --dlink
                                   取直链（GET xpan/multimedia?method=filemetas，
                                   fsids 数组上限 100，dlink=1）
  2. 分享页（逆向，不稳定，每次开跑前重新核对页面）：
       --share https://pan.baidu.com/s/{surl} --pwd 提取码 [--dir 路径]
                                   verify 置 cookie → share/list 分页枚举

纪律（硬性，沿用本技能三条铁律与五件套立场）：
- 不伪造：errno 非 0 / HTTP 非 200 / 网络失败一律如实留痕，诚实退出非零；
  证据 JSON 按 round{N} 追加，跨轮次只追加不覆盖，同轮次重跑幂等替换本链接记录。
- 不绕过：403/权限类失败是确定性结论，不重试（仅网络错误/5xx 重试 ≤2 次）。
- 限速如实提示：非会员实测约 96-170KB/s（2025-03 媒体实测，conf=estimated），
  禁止暗示可突破限速；第三方"不限速解析工具"只作风险提示，绝不集成。
- dlink 为临时链接（约 600s 失效）；下载 dlink 必须带 header
  `User-Agent: pan.baidu.com`，否则大文件（>20M）报错 31362 "sign error"。

退出码：0 成功；2 本地环境/落盘失败；3 参数或授权缺失（缺 --token/--pwd 等）；
        4 网络/接口失败（HTTP 非 200、errno 非 0、超时；证据已落盘）。

用法：
    python3 baidu_share_browse.py --token T --dir /资料 --out 归档目录 --round 1
    python3 baidu_share_browse.py --token T --fsids "[123,456]" --dlink
    python3 baidu_share_browse.py --share https://pan.baidu.com/s/xxxx --pwd abcd
    python3 baidu_share_browse.py --smoke      # 内置 FakeFetcher 全离线自测

依赖：仅标准库。
"""
import argparse
import http.cookiejar
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

XPAN_LIST_URL = "https://pan.baidu.com/rest/2.0/xpan/file"
XPAN_FILEMETAS_URL = "https://pan.baidu.com/rest/2.0/xpan/multimedia"
SHARE_PAGE_HOST = "https://pan.baidu.com"
SHARE_VERIFY_URL = "https://pan.baidu.com/share/verify"
SHARE_LIST_URL = "https://pan.baidu.com/share/list"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
DLink_UA = "pan.baidu.com"  # 下载 dlink 必须携带，否则大文件 31362 sign error
FSIDS_CHUNK = 100           # filemetas fsids 数组上限
PACE_MIN, PACE_MAX = 0.5, 1.0

EXIT_OK, EXIT_ENV, EXIT_REFUSED, EXIT_NET = 0, 2, 3, 4

CATEGORY_NAMES = {1: "视频", 2: "音乐", 3: "图片", 4: "文档",
                  5: "应用", 6: "其他", 7: "种子"}
LICENSE_NOTE = ("仅限用户本人文件或获授权分享；由用户提供的百度网盘通道获取，"
                "仅供用户个人学习使用，出处见链接；如涉第三方版权，权利归原权利"
                "人所有")
SPEED_NOTE = ("限速提示：非会员实测约 96-170KB/s（2025-03 媒体实测，"
              "conf=estimated），SVIP 约 7-10MB/s，2025 年起按资源热度调度；"
              "本管线如实记录速率事实，不提供也不暗示任何突破限速的手段")
DLINK_NOTE = ("dlink 为临时链接（约 600 秒失效），取到后应立即使用，过期需重新"
              "走 filemetas 取链；下载时必须携带 header User-Agent: pan.baidu.com，"
              "否则大文件（>20M）报错 31362 sign error")


def now_str():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S +0800")


def pace():
    time.sleep(random.uniform(PACE_MIN, PACE_MAX))


def epoch_to_str(ts):
    try:
        dt = datetime.fromtimestamp(int(ts), timezone(timedelta(hours=8)))
        return dt.strftime("%Y-%m-%d %H:%M:%S +0800")
    except Exception:
        return str(ts)


# ---------------------------------------------------------------- 传输层
class UrllibFetcher:
    """真实联网传输。get/post 返回 (http_status, content)；网络异常 (-1, 描述)。
    自带 CookieJar（分享页 verify 置 cookie 后 share/list 需要携带）。"""

    def __init__(self):
        self.calls = 0
        cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj))

    def _open(self, req, timeout, binary):
        self.calls += 1
        try:
            with self.opener.open(req, timeout=timeout) as resp:
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

    def get(self, url, timeout=40, headers=None):
        h = {"User-Agent": BROWSER_UA}
        h.update(headers or {})
        return self._open(urllib.request.Request(url, headers=h), timeout, False)

    def post(self, url, form, timeout=40, headers=None):
        h = {"User-Agent": BROWSER_UA}
        h.update(headers or {})
        data = urllib.parse.urlencode(form).encode("utf-8")
        return self._open(urllib.request.Request(url, data=data, headers=h),
                          timeout, False)


class FakeFetcher:
    """--smoke 内置假响应，不联网。覆盖：分页、递归子目录、dlink 组装、
    403 确定性拒绝、提取码验证成功/失败、分享页参数提取。"""

    # dir -> 该目录全量条目（xpan filemeta 风格）
    XPAN_TREE = {
        "/": [
            {"fsid": 11, "path": "/docs", "server_filename": "docs", "isdir": 1,
             "size": 0, "server_mtime": 1786600000, "category": 6},
            {"fsid": 12, "path": "/readme.txt", "server_filename": "readme.txt",
             "isdir": 0, "size": 19, "server_mtime": 1786600001, "category": 4},
            {"fsid": 13, "path": "/notes.md", "server_filename": "notes.md",
             "isdir": 0, "size": 33, "server_mtime": 1786600002, "category": 4},
        ],
        "/docs": [
            {"fsid": 14, "path": "/docs/a.pdf", "server_filename": "a.pdf",
             "isdir": 0, "size": 1024, "server_mtime": 1786600003, "category": 4},
        ],
    }
    SHARE_PARAMS = {"shareid": 9001, "uk": 8002, "sign": "fakesign", "timestamp": 1786600100}
    SHARE_LIST = [
        {"fs_id": 21, "path": "/资料/b.docx", "server_filename": "b.docx",
         "isdir": 0, "size": 2048, "server_mtime": 1786600200, "category": 4},
        {"fs_id": 22, "path": "/资料", "server_filename": "资料",
         "isdir": 1, "size": 0, "server_mtime": 1786600201, "category": 6},
    ]

    def __init__(self):
        self.calls = 0
        self.url_calls = {}

    def _count(self, url):
        self.calls += 1
        key = url.split("?")[0] + "?" + "&".join(
            sorted(p for p in urllib.parse.urlparse(url).query.split("&")
                   if not p.startswith("start=")))
        self.url_calls[key] = self.url_calls.get(key, 0) + 1

    def get(self, url, timeout=40, headers=None):
        self._count(url)
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/rest/2.0/xpan/file" and qs.get("method") == ["list"]:
            dir_ = qs.get("dir", ["/"])[0]
            if dir_ == "/forbidden":
                return 403, json.dumps({"errno": -6, "errmsg": "No permission to access"})
            entries = self.XPAN_TREE.get(dir_)
            if entries is None:
                return 200, json.dumps({"errno": 31061, "errmsg": "file not exist",
                                        "list": []})
            limit = int(qs.get("limit", ["200"])[0])
            start = int(qs.get("start", ["0"])[0])
            return 200, json.dumps({"errno": 0, "request_id": 1,
                                    "list": entries[start:start + limit]})
        if parsed.path == "/rest/2.0/xpan/multimedia" and qs.get("method") == ["filemetas"]:
            try:
                fsids = json.loads(qs.get("fsids", ["[]"])[0])
            except Exception:
                return 200, json.dumps({"errno": 42211, "errmsg": "invalid fsids"})
            if not isinstance(fsids, list) or len(fsids) > FSIDS_CHUNK:
                return 200, json.dumps({"errno": 42212, "errmsg": "fsids out of range"})
            return 200, json.dumps({"errno": 0, "list": [
                {"fsid": f, "path": f"/fake/{f}.bin", "server_filename": f"{f}.bin",
                 "size": 10, "dlink": f"https://d.pcs.baidu.com/fake/{f}?sign=x"}
                for f in fsids]})
        m = re.match(r"^/s/([A-Za-z0-9_-]+)$", parsed.path)
        if m:
            p = self.SHARE_PARAMS
            html = ("<html><script>locals.mset({\"shareid\": %s, \"uk\": %s, "
                    "\"sign\": \"%s\", \"timestamp\": %s});</script></html>"
                    % (p["shareid"], p["uk"], p["sign"], p["timestamp"]))
            return 200, html
        if parsed.path == "/share/list":
            page = int(qs.get("page", ["1"])[0])
            num = int(qs.get("num", ["100"])[0])
            entries = self.SHARE_LIST
            chunk = entries[(page - 1) * num: page * num]
            return 200, json.dumps({"errno": 0, "list": chunk})
        return 404, json.dumps({"errno": 31034, "errmsg": f"unknown url {url}"})

    def post(self, url, form, timeout=40, headers=None):
        self._count(url)
        parsed = urllib.parse.urlparse(url)
        if parsed.path == "/share/verify":
            if (form or {}).get("pwd") == "abcd":
                return 200, json.dumps({"errno": 0})
            return 200, json.dumps({"errno": -9, "errmsg": "提取码错误"})
        return 404, json.dumps({"errno": 31034, "errmsg": f"unknown url {url}"})


# ---------------------------------------------------------------- 公共助手
def get_json(fetcher, url, tries=2, headers=None):
    """带重试的 JSON GET。返回 (status, obj_or_rawtext, attempts)。
    4xx 为确定性响应不重试；仅网络错误(-1)/5xx 重试 ≤tries 次。"""
    status, text, attempts = -1, "", 0
    for attempt in range(tries + 1):
        attempts = attempt + 1
        status, text = fetcher.get(url, headers=headers)
        if status == 200:
            try:
                return status, json.loads(text), attempts
            except Exception as e:
                return status, {"_parse_error": f"{type(e).__name__}: {e}",
                                "_raw": str(text)[:500]}, attempts
        if status != -1 and not (500 <= status < 600):
            break
        if attempt < tries:
            pace()
    return status, text, attempts


def map_entry(e):
    """xpan filemeta / share list 条目 → 与 source_register 兼容的清单对象。"""
    isdir = int(e.get("isdir", 0)) == 1
    cat = e.get("category")
    obj = {"name": e.get("server_filename") or os.path.basename(e.get("path", "")),
           "relPath": e.get("path", ""),
           "type": "directory" if isdir else "file",
           "size": e.get("size"),
           "mtime": epoch_to_str(e.get("server_mtime")) if e.get("server_mtime") else None,
           "fsid": e.get("fsid", e.get("fs_id"))}
    if cat in CATEGORY_NAMES:
        obj["category"] = cat
        obj["category_name"] = CATEGORY_NAMES[cat]
    return obj


def write_manifest(out_root, link_key, source_url, rnd, objects, channel, extra=None):
    """清单落盘：schema 与 source_register.py 输入兼容，追加轮次命名不覆盖。"""
    ldir = os.path.join(out_root, link_key)
    os.makedirs(ldir, exist_ok=True)
    files = [o for o in objects if o.get("type") == "file"]
    dirs = [o for o in objects if o.get("type") == "directory"]
    manifest = {"source_url": source_url, "fetched_at": now_str(), "round": rnd,
                "round_ts": {f"round{rnd}": now_str()},
                "channel": channel, "license_note": LICENSE_NOTE,
                "summary": {"dirs": len(dirs), "files": len(files)},
                "objects": objects}
    if extra:
        manifest.update(extra)
    path = os.path.join(ldir, f"文件清单_{link_key}_第{rnd}轮.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    return path


def append_evidence(out_root, rnd, link_key, patch, trigger=""):
    """证据 JSON 按 round{N} 追加：跨轮次只追加不覆盖；同轮次重跑幂等替换
    本链接的 enumeration/summary 记录。返回证据路径。"""
    evidence_path = os.path.join(out_root, "下载尝试证据.json")
    round_key = f"round{rnd}"
    if os.path.exists(evidence_path):
        with open(evidence_path, encoding="utf-8") as f:
            evidence = json.load(f)
    else:
        evidence = {}
    node = evidence.get(round_key) or {
        "interface": ("百度网盘双通道：xpan file?method=list 分页枚举 / "
                      "multimedia?method=filemetas 取 dlink / 分享页 verify+list"
                      "（逆向，不稳定；事实见 references/baidu_netdisk_api.md）"),
        "enumeration": {}, "download_attempts": [], "dlink_attempts": [],
        "summary": {}}
    node["fetched_at"] = now_str()
    if trigger:
        node["trigger"] = trigger
    node.setdefault("enumeration", {})[link_key] = patch.get("enumeration")
    node.setdefault("dlink_attempts", [])
    # 同轮次重跑：幂等替换本链接 dlink 记录
    node["dlink_attempts"] = [r for r in node["dlink_attempts"]
                              if r.get("link") != link_key] + patch.get("dlinks", [])
    node.setdefault("summary", {})[link_key] = patch.get("summary")
    if patch.get("speed_note"):
        node["speed_note"] = patch["speed_note"]
    evidence[round_key] = node
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, ensure_ascii=False, indent=1)
    return evidence_path


def dedup(objects):
    """按 relPath 去重（防分页重叠/递归重复进入），保持排序后顺序。"""
    seen, out = set(), []
    for o in sorted(objects, key=lambda x: x.get("relPath", "")):
        rp = o.get("relPath", "")
        if rp and rp not in seen:
            seen.add(rp)
            out.append(o)
    return out


def ensure_out(out):
    root = os.path.abspath(out)
    try:
        os.makedirs(root, exist_ok=True)
    except Exception as e:
        sys.stderr.write(f"无法创建输出目录 {root}: {e}\n")
        sys.exit(EXIT_ENV)
    return root


# ---------------------------------------------------------------- 通道 1：官方 xpan
def xpan_list(fetcher, token, dir_, limit):
    """分页枚举单目录。返回 (entries, error_record_or_None, attempts)。"""
    entries, start, attempts = [], 0, 0
    while True:
        url = XPAN_LIST_URL + "?" + urllib.parse.urlencode({
            "method": "list", "dir": dir_, "access_token": token,
            "start": start, "limit": limit, "order": "name"})
        status, obj, at = get_json(fetcher, url)
        attempts += at
        if status != 200 or not isinstance(obj, dict):
            return entries, {"dir": dir_, "http_status": status,
                             "response_head": str(obj)[:300]}, attempts
        if obj.get("errno") != 0:
            return entries, {"dir": dir_, "http_status": status,
                             "errno": obj.get("errno"),
                             "errmsg": str(obj.get("errmsg"))[:200]}, attempts
        batch = obj.get("list") or []
        entries.extend(batch)
        if len(batch) < limit:
            return entries, None, attempts
        start += limit
        pace()


def run_xpan_enum(args, fetcher):
    if not args.token:
        sys.stderr.write("缺少 --token：access_token 须由用户本人在百度网盘开放"
                         "平台创建应用并走 OAuth 获取，脚本不代申请。\n")
        return EXIT_REFUSED
    out_root = ensure_out(args.out)
    link_key = "baidu-xpan"
    source_url = f"baidu-xpan://dir={args.dir}"
    objects, errors, attempts = [], [], 0
    queue, seen = [args.dir], set()
    while queue:
        d = queue.pop(0)
        if d in seen:
            continue
        seen.add(d)
        entries, err, at = xpan_list(fetcher, args.token, d, args.limit)
        attempts += at
        if err:
            errors.append(err)
            if err.get("http_status") and 400 <= err["http_status"] < 500:
                # 403 等权限类失败是确定性结论：整轮止步，如实留痕退出 4
                break
        for e in entries:
            o = map_entry(e)
            objects.append(o)
            if o["type"] == "directory":
                queue.append(o["relPath"])
        pace()
    objects = dedup(objects)
    manifest_path = write_manifest(out_root, link_key, source_url, args.round,
                                   objects, "xpan",
                                   extra={"enum_errors": errors})
    files = [o for o in objects if o["type"] == "file"]
    ev = append_evidence(out_root, args.round, link_key, {
        "enumeration": {"dir": args.dir, "dirs": len(objects) - len(files),
                        "files": len(files), "enum_errors": errors,
                        "manifest": os.path.relpath(manifest_path, out_root)},
        "summary": {"success": 0 if errors else len(files),
                    "failed": len(files) if errors else 0,
                    "total": len(files), "http_attempts": attempts},
        "speed_note": SPEED_NOTE}, trigger=args.trigger)
    print(SPEED_NOTE, flush=True)
    print(f"[{link_key}] 枚举 {args.dir}：{len(files)} 文件，错误 {len(errors)} 处 "
          f"-> {os.path.relpath(manifest_path, out_root)}（证据 {ev}）", flush=True)
    if errors:
        for e in errors:
            print(f"  [FAIL] {e.get('dir')} HTTP {e.get('http_status')} "
                  f"errno={e.get('errno')}: {e.get('errmsg') or e.get('response_head')}",
                  flush=True)
        return EXIT_NET
    return EXIT_OK


def run_dlink(args, fetcher):
    if not args.token:
        sys.stderr.write("缺少 --token：脚本不代申请 access_token。\n")
        return EXIT_REFUSED
    try:
        fsids = json.loads(args.fsids)
        assert isinstance(fsids, list) and all(isinstance(x, int) for x in fsids)
    except Exception:
        sys.stderr.write("--fsids 须为整数 JSON 数组，如 \"[123,456]\"\n")
        return EXIT_REFUSED
    if not fsids or len(fsids) > FSIDS_CHUNK:
        sys.stderr.write(f"fsids 数组须为 1~{FSIDS_CHUNK} 个（filemetas 接口上限）\n")
        return EXIT_REFUSED
    out_root = ensure_out(args.out)
    link_key = "baidu-xpan"
    url = XPAN_FILEMETAS_URL + "?" + urllib.parse.urlencode({
        "method": "filemetas", "fsids": json.dumps(fsids), "dlink": 1,
        "access_token": token_of(args)})
    status, obj, attempts = get_json(fetcher, url)
    dlinks, failed = [], None
    if status == 200 and isinstance(obj, dict) and obj.get("errno") == 0:
        for item in obj.get("list") or []:
            dlinks.append({"link": link_key, "fsid": item.get("fsid"),
                           "path": item.get("path"), "dlink": item.get("dlink"),
                           "fetched_at": now_str(),
                           "expires_note": "约 600 秒失效，请立即使用，过期重新取链",
                           "ua_note": f"下载必须携带 header User-Agent: {DLink_UA}",
                           "http_status": status, "attempts": attempts})
    else:
        failed = {"link": link_key, "http_status": status,
                  "errno": obj.get("errno") if isinstance(obj, dict) else None,
                  "response_head": str(obj)[:300], "attempts": attempts}
    ev = append_evidence(out_root, args.round, link_key, {
        "enumeration": None,
        "dlinks": dlinks or ([failed] if failed else []),
        "summary": {"dlink_ok": len(dlinks), "dlink_failed": 0 if failed is None else 1,
                    "total": len(fsids)},
        "speed_note": SPEED_NOTE}, trigger=args.trigger)
    print(DLINK_NOTE, flush=True)
    print(SPEED_NOTE, flush=True)
    if failed:
        print(f"[FAIL] filemetas HTTP {failed['http_status']} "
              f"errno={failed.get('errno')}: {failed['response_head'][:200]}"
              f"（证据已落盘 {ev}）", flush=True)
        return EXIT_NET
    print(f"[baidu-xpan] 取得 {len(dlinks)} 条 dlink（证据 {ev}）", flush=True)
    for d in dlinks:
        print(f"  fsid={d['fsid']} {d['path']} -> {d['dlink'][:80]}…", flush=True)
    return EXIT_OK


def token_of(args):
    return args.token


# ---------------------------------------------------------------- 通道 2：分享页（逆向）
def parse_share(url):
    """解析 pan.baidu.com/s/{surl}[?pwd=XXXX]。返回 (surl, pwd_or_None)。"""
    m = re.search(r"pan\.baidu\.com/s/(1?[A-Za-z0-9_-]+)", url or "")
    if not m:
        raise ValueError(f"无法解析百度分享链接: {url!r}")
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    pwd = (qs.get("pwd") or [None])[0]
    return m.group(1), pwd


def extract_share_params(html):
    """从分享页 HTML 内嵌 JS 提取 shareid/uk/sign/timestamp（逆向，页面结构
    常变；取不到即如实返回 None，不臆造）。"""
    def grab(key, numeric=False):
        pat = r'"%s"\s*:\s*(%s)' % (key, r"(\d+)" if numeric else r'"([^"]+)"')
        m = re.search(pat, html)
        if not m:
            return None
        return m.group(1)
    params = {"shareid": grab("shareid", True), "uk": grab("uk", True),
              "sign": grab("sign"), "timestamp": grab("timestamp", True)}
    return params if all(params.values()) else None


def run_share_enum(args, fetcher):
    try:
        surl, pwd_in_url = parse_share(args.share)
    except ValueError as e:
        sys.stderr.write(str(e) + "\n")
        return EXIT_REFUSED
    pwd = args.pwd or pwd_in_url
    if not pwd:
        sys.stderr.write("缺少提取码：用 --pwd 传入，或链接中携带 ?pwd=XXXX。\n")
        return EXIT_REFUSED
    out_root = ensure_out(args.out)
    link_key = f"baidu-share-{surl}"
    source_url = f"https://pan.baidu.com/s/{surl}"

    page_url = f"{SHARE_PAGE_HOST}/s/{surl}"
    status, html = fetcher.get(page_url)  # 分享页是 HTML，不走 JSON 解析
    if status != 200:
        ev = append_evidence(out_root, args.round, link_key, {
            "enumeration": {"surl": surl, "enum_errors": [
                {"step": "share_page", "http_status": status,
                 "response_head": str(html)[:300]}]},
            "summary": {"success": 0, "failed": 0, "total": 0},
            "speed_note": SPEED_NOTE}, trigger=args.trigger)
        print(f"[FAIL] 分享页 HTTP {status}（证据已落盘 {ev}）", flush=True)
        return EXIT_NET
    params = extract_share_params(html)
    if not params:
        ev = append_evidence(out_root, args.round, link_key, {
            "enumeration": {"surl": surl, "enum_errors": [
                {"step": "extract_params",
                 "response_head": "页面 JS 中未取得 shareid/uk/sign/timestamp，"
                                  "逆向通道当前可能已失效（如实报告，不臆造）"}]},
            "summary": {"success": 0, "failed": 0, "total": 0},
            "speed_note": SPEED_NOTE}, trigger=args.trigger)
        print(f"[FAIL] 分享页参数提取失败，逆向通道可能已失效（证据 {ev}）", flush=True)
        return EXIT_NET

    verify_url = SHARE_VERIFY_URL + "?" + urllib.parse.urlencode({
        "surl": surl, "t": int(time.time() * 1000), "channel": "chunlei",
        "web": 1, "clienttype": 0})
    status, text = fetcher.post(verify_url, {"pwd": pwd, "vcode": "", "vcode_str": ""})
    verr = None
    try:
        vobj = json.loads(text) if isinstance(text, str) else {}
    except Exception:
        vobj = {}
    if status != 200 or vobj.get("errno") != 0:
        verr = {"step": "verify", "http_status": status,
                "errno": vobj.get("errno"), "response_head": str(text)[:300]}
    if verr:
        ev = append_evidence(out_root, args.round, link_key, {
            "enumeration": {"surl": surl, "enum_errors": [verr]},
            "summary": {"success": 0, "failed": 0, "total": 0},
            "speed_note": SPEED_NOTE}, trigger=args.trigger)
        print(f"[FAIL] 提取码验证失败 errno={verr.get('errno')} "
              f"HTTP {status}（如实留痕 {ev}）", flush=True)
        return EXIT_NET

    # share/list 分页枚举（BFS 下钻子目录）
    objects, errors = [], []
    queue, seen = [args.dir], set()
    while queue:
        d = queue.pop(0)
        if d in seen:
            continue
        seen.add(d)
        page = 1
        while True:
            q = {"shareid": params["shareid"], "uk": params["uk"],
                 "sign": params["sign"], "timestamp": params["timestamp"],
                 "dir": d, "page": page, "num": 100, "order": "name"}
            status, obj, _ = get_json(fetcher, SHARE_LIST_URL + "?" +
                                      urllib.parse.urlencode(q))
            if status != 200 or not isinstance(obj, dict) or obj.get("errno") != 0:
                errors.append({"dir": d, "page": page, "http_status": status,
                               "errno": obj.get("errno") if isinstance(obj, dict) else None,
                               "response_head": str(obj)[:300]})
                break
            batch = obj.get("list") or []
            for e in batch:
                o = map_entry(e)
                objects.append(o)
                if o["type"] == "directory" and o["relPath"] != d:
                    queue.append(o["relPath"])
            if len(batch) < 100:
                break
            page += 1
            pace()
        pace()
    objects = dedup(objects)
    manifest_path = write_manifest(out_root, link_key, source_url, args.round,
                                   objects, "share-reverse",
                                   extra={"enum_errors": errors})
    files = [o for o in objects if o["type"] == "file"]
    ev = append_evidence(out_root, args.round, link_key, {
        "enumeration": {"surl": surl, "dirs": len(objects) - len(files),
                        "files": len(files), "enum_errors": errors,
                        "manifest": os.path.relpath(manifest_path, out_root)},
        "summary": {"success": 0 if errors else len(files),
                    "failed": len(files) if errors else 0, "total": len(files)},
        "speed_note": SPEED_NOTE}, trigger=args.trigger)
    print(SPEED_NOTE, flush=True)
    print(f"[{link_key}] 分享枚举：{len(files)} 文件，错误 {len(errors)} 处 "
          f"-> {os.path.relpath(manifest_path, out_root)}（证据 {ev}）", flush=True)
    return EXIT_NET if errors else EXIT_OK


# ---------------------------------------------------------------- 冒烟自测
def smoke():
    """FakeFetcher 全离线：解析/分页/递归/dlink 组装/403 不重试/缺 token 拒绝/
    分享验证成败双路径。"""
    base = dict(token=None, dir="/", limit=2, fsids=None, dlink=False,
                share=None, pwd=None, out=None, round=1,
                trigger="--smoke 内置自测（不联网）")
    ns = lambda **kw: argparse.Namespace(**{**base, **kw})

    # 1) 分享链接解析
    surl, pwd = parse_share("https://pan.baidu.com/s/1AbCdef?pwd=wxyz")
    assert surl == "1AbCdef" and pwd == "wxyz"
    surl2, pwd2 = parse_share("https://pan.baidu.com/s/xyz123")
    assert surl2 == "xyz123" and pwd2 is None

    with tempfile.TemporaryDirectory(prefix="baidu_smoke_") as tmp:
        # 2) 缺 token 拒绝（退出码 3）
        assert run_xpan_enum(ns(out=tmp), FakeFetcher()) == EXIT_REFUSED
        assert run_dlink(ns(out=tmp, fsids="[1]"), FakeFetcher()) == EXIT_REFUSED
        # 缺提取码拒绝
        assert run_share_enum(ns(out=tmp, share="https://pan.baidu.com/s/xyz123"),
                              FakeFetcher()) == EXIT_REFUSED

        # 3) 官方枚举：limit=2 强制分页（根目录 3 条 → 2 页）+ 递归 /docs
        fx = FakeFetcher()
        rc = run_xpan_enum(ns(token="SMOKE_TOKEN", out=tmp, limit=2), fx)
        assert rc == EXIT_OK, f"xpan 枚举返回 {rc}"
        manifest = os.path.join(tmp, "baidu-xpan", "文件清单_baidu-xpan_第1轮.json")
        with open(manifest, encoding="utf-8") as f:
            m = json.load(f)
        for key in ("source_url", "fetched_at", "summary", "license_note",
                    "round_ts", "objects"):
            assert key in m, f"清单缺键 {key}"
        files = [o for o in m["objects"] if o["type"] == "file"]
        dirs = [o for o in m["objects"] if o["type"] == "directory"]
        assert len(files) == 3 and len(dirs) == 1, f"{len(files)}f/{len(dirs)}d"
        assert m["source_url"] == "baidu-xpan://dir=/"
        names = {o["name"] for o in files}
        assert names == {"readme.txt", "notes.md", "a.pdf"}
        obj = next(o for o in files if o["name"] == "readme.txt")
        assert obj["fsid"] == 12 and obj["category_name"] == "文档"

        # 4) dlink 组装：2 个 fsid → 2 条带 ua/时效注记的直链记录
        rc = run_dlink(ns(token="SMOKE_TOKEN", out=tmp, fsids="[11,12]",
                          dlink=True), FakeFetcher())
        assert rc == EXIT_OK
        with open(os.path.join(tmp, "下载尝试证据.json"), encoding="utf-8") as f:
            ev = json.load(f)
        dls = [r for r in ev["round1"]["dlink_attempts"] if r.get("dlink")]
        assert len(dls) == 2 and all("d.pcs.baidu.com" in r["dlink"] for r in dls)
        assert all("pan.baidu.com" in r["ua_note"] for r in dls)
        assert "600" in dls[0]["expires_note"]
        assert "96-170KB/s" in ev["round1"]["speed_note"]

        # 5) fsids 超上限 / 非法 → 退出码 3
        assert run_dlink(ns(token="T", out=tmp,
                            fsids=json.dumps(list(range(101))),
                            dlink=True), FakeFetcher()) == EXIT_REFUSED
        assert run_dlink(ns(token="T", out=tmp, fsids="not-json",
                            dlink=True), FakeFetcher()) == EXIT_REFUSED

        # 6) 403 确定性拒绝：不重试（该 URL 仅被请求 1 次），诚实退出 4 且留痕
        fx2 = FakeFetcher()
        rc = run_xpan_enum(ns(token="T", out=tmp, dir="/forbidden", round=2), fx2)
        assert rc == EXIT_NET
        hit = [v for k, v in fx2.url_calls.items() if "dir=%2Fforbidden" in k]
        assert hit == [1], f"403 不应重试，实际 {hit}"
        with open(os.path.join(tmp, "下载尝试证据.json"), encoding="utf-8") as f:
            ev = json.load(f)
        assert "round1" in ev and "round2" in ev, "轮次必须追加不覆盖"
        err = ev["round2"]["enumeration"]["baidu-xpan"]["enum_errors"][0]
        assert err["http_status"] == 403 and err["dir"] == "/forbidden"

        # 7) 分享页：正确提取码 → 枚举成功；错误提取码 → errno 非 0 退出 4
        rc = run_share_enum(ns(share="https://pan.baidu.com/s/1AbCdef",
                               pwd="abcd", out=tmp, dir="/", round=3), FakeFetcher())
        assert rc == EXIT_OK
        with open(os.path.join(tmp, "baidu-share-1AbCdef",
                               "文件清单_baidu-share-1AbCdef_第3轮.json"),
                  encoding="utf-8") as f:
            m = json.load(f)
        assert m["channel"] == "share-reverse"
        assert any(o["name"] == "b.docx" for o in m["objects"])
        rc = run_share_enum(ns(share="https://pan.baidu.com/s/1AbCdef",
                               pwd="wrong", out=tmp, round=4), FakeFetcher())
        assert rc == EXIT_NET
        with open(os.path.join(tmp, "下载尝试证据.json"), encoding="utf-8") as f:
            ev = json.load(f)
        assert set(ev) >= {"round1", "round2", "round3", "round4"}
        assert ev["round4"]["enumeration"]["baidu-share-1AbCdef"][
            "enum_errors"][0]["errno"] == -9

    print("[SMOKE OK] baidu_share_browse: 解析/分页/递归/dlink组装/403不重试/"
          "缺token拒绝/分享验证成败/轮次追加 全部通过（未联网）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="百度网盘官方 xpan + 分享页双通道枚举管线")
    ap.add_argument("--token", default=None,
                    help="xpan access_token（用户自行在开放平台 OAuth 获取，脚本不代申请）")
    ap.add_argument("--dir", default="/", help="起始目录（默认 /）")
    ap.add_argument("--fsids", default=None, help='整数 JSON 数组，如 "[123,456]"（≤100）')
    ap.add_argument("--dlink", action="store_true", help="对 --fsids 取 dlink 直链")
    ap.add_argument("--share", default=None, help="分享链接 https://pan.baidu.com/s/{surl}")
    ap.add_argument("--pwd", default=None, help="分享提取码")
    ap.add_argument("--limit", type=int, default=200, help="xpan list 分页大小（≤1000）")
    ap.add_argument("--out", default=".", help="归档根目录（默认当前目录）")
    ap.add_argument("--round", type=int, default=1, help="轮次编号（证据 round{N}）")
    ap.add_argument("--trigger", default="", help="本轮触发说明（写入证据留痕）")
    ap.add_argument("--smoke", action="store_true", help="内置 FakeFetcher 自测，不联网")
    args = ap.parse_args()
    if args.smoke:
        return smoke()
    if not (1 <= args.limit <= 1000):
        ap.error("--limit 须在 1~1000")
    if args.dlink:
        if not args.fsids:
            ap.error("--dlink 需搭配 --fsids")
        return run_dlink(args, UrllibFetcher())
    if args.share:
        return run_share_enum(args, UrllibFetcher())
    if args.token:
        return run_xpan_enum(args, UrllibFetcher())
    ap.error("请指定通道：--token（官方）/ --share（分享页）/ --dlink；或 --smoke 自测")


if __name__ == "__main__":
    sys.exit(main())
