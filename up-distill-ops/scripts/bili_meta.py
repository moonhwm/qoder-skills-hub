#!/usr/bin/env python3
"""B站免登录公开元数据探针 v1.0（up-distill-ops 配套）
用法:
  python3 bili_meta.py video <bvid>     # 单视频元数据
  python3 bili_meta.py search <关键词>  # 搜索前10条
纪律：仅公开面；不绕登录；wbi 签名接口（空间视频列表）不可用属已知坑——用 web_open_url 抓 space 页替代。
"""
import json, sys, urllib.request, urllib.parse

UA = {"User-Agent": "Mozilla/5.0 (up-distill-ops; public-metadata-only)"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def video(bvid):
    d = get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}")
    if d.get("code") != 0:
        print(f"FAIL code={d.get('code')} {d.get('message')}"); return 1
    v = d["data"]
    print(json.dumps({"bvid": bvid, "title": v["title"], "up": v["owner"]["name"],
        "uid": v["owner"]["mid"], "duration_min": round(v["duration"]/60, 1),
        "view": v["stat"]["view"], "danmaku": v["stat"]["danmaku"],
        "pubdate": v["pubdate"], "tname": v.get("tname")}, ensure_ascii=False))
    return 0

def search(kw):
    q = urllib.parse.quote(kw)
    d = get(f"https://api.bilibili.com/x/web-interface/nav")  # 连通性预检（免登录）
    d = get(f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={q}&page_size=10")
    if d.get("code") != 0:
        print(f"FAIL code={d.get('code')}（搜索接口偶尔要求登录态；失败时改用 web 搜索）"); return 1
    for it in (d["data"].get("result") or [])[:10]:
        print(json.dumps({"bvid": it.get("bvid"), "title": (it.get("title") or "").replace("<em class=\"keyword\">","").replace("</em>",""),
            "up": it.get("author"), "uid": it.get("mid"), "view": it.get("play"),
            "pubdate": it.get("pubdate")}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    sys.exit(video(sys.argv[2]) if sys.argv[1] == "video" else search(sys.argv[2]))
