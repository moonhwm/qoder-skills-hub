# -*- coding: utf-8 -*-
"""cite_verify.py —— 引用核验器（应戒三十八草案：检索结果须核验后方可引用）
用法：
  python cite_verify.py --query "<问>" [--engine sonar-pro] [--max 12]   # 先检索再核验
  python cite_verify.py --urls a b c                                     # 只核验给定 URL
输出：逐条 HTTP 状态／内容类型／标题；三分类计数（可达／不可达／异常）
★纪律：本器只报"可达性"，不判"内容真伪"；未核之引用不得作为断言依据。
（中文串一律用「」）
"""
import argparse, json, pathlib, re, sys, time, urllib.request, urllib.error

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def probe(url, timeout=20):
    r = urllib.request.Request(url, method="GET"); r.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(4096)
            ct = resp.headers.get("Content-Type", "")
            m = re.search(rb"<title[^>]*>(.{0,120}?)</title>", b, re.S | re.I)
            title = m.group(1).decode("utf-8", "replace").strip() if m else ""
            return resp.status, ct[:40], title
    except urllib.error.HTTPError as e:
        return e.code, "", "HTTPError"
    except Exception as e:
        return -1, "", str(e)[:60]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--query", default=""); ap.add_argument("--urls", nargs="*", default=[])
    ap.add_argument("--engine", default="sonar-pro"); ap.add_argument("--max", type=int, default=12)
    a = ap.parse_args()
    urls = list(a.urls)
    if a.query:
        sys.path.insert(0, str(SEAT/"exp")); import search_route as SR
        st, ans, cites = SR.online_search(a.query, model=a.engine)
        print("  ═══ 检索：%s ⇒ HTTP %s ｜ 答 %d 字 ｜ 引用 %d 条 ═══" % (a.engine, st, len(ans), len(cites)))
        for c in cites:
            u = c if isinstance(c, str) else str(c.get("url") or c)
            if u.startswith("http"): urls.append(u)
    urls = list(dict.fromkeys(urls))[: a.max]
    print("  ═══ 核验 %d 条 URL ═══" % len(urls))
    rows = []
    for u in urls:
        st, ct, title = probe(u)
        cls = "可达" if (isinstance(st, int) and 200 <= st < 400) else ("不可达" if isinstance(st, int) and st >= 400 else "异常")
        rows.append({"url": u, "status": st, "ctype": ct, "title": title, "class": cls})
        print("   %-4s HTTP %-4s %-30s %s" % (cls, st, ct[:30], (title or u)[:60]))
    from collections import Counter
    c = Counter(r["class"] for r in rows)
    print("\n  ★ 三分类：可达 %d ｜ 不可达 %d ｜ 异常 %d" % (c["可达"], c["不可达"], c["异常"]))
    print("  ⇒ 判：%s" % ("★引用可达性核验完成；★内容真伪仍未判（须人工或权威源复核）" if rows else "无 URL"))
    out = EX/"cite_verify_20261011.json"
    out.write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "engine": a.engine,
                               "query": a.query, "n": len(rows), "counts": dict(c), "rows": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   落盘：" + out.name)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
