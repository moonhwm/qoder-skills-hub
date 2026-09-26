#!/usr/bin/env python3
"""arxiv_fetch.py — 通过 arXiv 官方 API 核验论文元数据（反幻觉第一道工序）。

功能：
- 按 ID 批量核验：论文是否真实存在、标题/作者/年月是否与声称一致、最新版本号、
  是否有 journal-ref / DOI（同行评审线索）、是否 withdrawn。
- 按关键词检索（search_query 语法见 references/arxiv_api.md）。
- 输出规范化 JSONL，供 arxiv_cite.py 与人工核对使用。

用法：
  python3 arxiv_fetch.py --ids 2301.07041 1706.03762v3
  python3 arxiv_fetch.py --ids-file ids.txt --out meta.jsonl
  python3 arxiv_fetch.py --search 'all:"attention is all you need"' --max 5
  python3 arxiv_fetch.py --smoke        # 离线解析自检，不访问网络

API 纪律（详见 references/arxiv_api.md）：
- 端点 https://export.arxiv.org/api/query ；连续请求间隔 >=3 秒（本脚本单次调用，不循环轰炸）。
- 网络失败/限流时脚本退出码 2 并打印 stderr 诊断——绝不把"查不到"当"不存在"。
- 批量元数据需求请走 Kaggle/S3 镜像，不要用本脚本爬全库。

纯标准库（urllib + xml.etree）。
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

UA = "arxiv-source-sentinel/1.0 (metadata verification; contact: local-user)"


def _text(el, path):
    node = el.find(path)
    return (node.text or "").strip() if node is not None else None


def parse_atom(xml_bytes):
    """解析 arXiv Atom XML → 记录列表。公开此函数供 --smoke 与复用。"""
    root = ET.fromstring(xml_bytes)
    recs = []
    for e in root.findall(f"{ATOM}entry"):
        entry_id = _text(e, f"{ATOM}id") or ""
        # id 形如 https://arxiv.org/abs/2301.07041v2
        m = re.search(r"/abs/([^/]+)$", entry_id)
        full_id = m.group(1) if m else entry_id
        vm = re.search(r"^(.*?)(v(\d+))?$", full_id)
        id_base, version = vm.group(1), (f"v{vm.group(3)}" if vm.group(3) else None)

        title = " ".join((_text(e, f"{ATOM}title") or "").split())
        summary = " ".join((_text(e, f"{ATOM}summary") or "").split())
        authors = [a.findtext(f"{ATOM}name", "").strip()
                   for a in e.findall(f"{ATOM}author")]
        cats = [c.get("term") for c in e.findall(f"{ATOM}category") if c.get("term")]
        primary = e.find(f"{ARXIV_NS}primary_category")
        links = {l.get("title") or l.get("rel"): l.get("href")
                 for l in e.findall(f"{ATOM}link")}

        comment = _text(e, f"{ARXIV_NS}comment")
        withdrawn = bool(comment and "withdrawn" in comment.lower())

        recs.append({
            "id_base": id_base,
            "version_latest_seen": version,      # API 默认返回最新版本
            "abs_url": entry_id,
            "pdf_url": links.get("pdf") or (links.get("alternate") or "").replace("/abs/", "/pdf/") or None,
            "title": title,
            "authors": authors,
            "published": _text(e, f"{ATOM}published"),
            "updated": _text(e, f"{ATOM}updated"),
            "primary_category": primary.get("term") if primary is not None else None,
            "categories": cats,
            "abstract": summary,
            "doi": _text(e, f"{ARXIV_NS}doi"),
            "journal_ref": _text(e, f"{ARXIV_NS}journal_ref"),
            "comment": comment,
            "withdrawn": withdrawn,
            "peer_review_hint": "has_journal_ref_or_doi" if (_text(e, f"{ARXIV_NS}doi") or _text(e, f"{ARXIV_NS}journal_ref")) else "preprint_only",
        })
    return recs


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_by_ids(ids, batch=50):
    """按 id_list 查询；>batch 个分批，批间隔由调用方保证（本脚本每批一次请求）。"""
    out = []
    for i in range(0, len(ids), batch):
        chunk = ids[i:i + batch]
        qs = urllib.parse.urlencode({"id_list": ",".join(chunk), "max_results": len(chunk)})
        out.extend(parse_atom(http_get(f"{API}?{qs}")))
        if i + batch < len(ids):
            import time
            time.sleep(3)  # arXiv API 礼貌间隔
    return out


def search(query, max_results=10):
    qs = urllib.parse.urlencode({
        "search_query": query, "start": 0, "max_results": max_results,
        "sortBy": "relevance", "sortOrder": "descending"})
    return parse_atom(http_get(f"{API}?{qs}"))


SMOKE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/1706.03762v7</id>
    <updated>2023-08-02T00:41:18Z</updated>
    <published>2017-06-12T17:57:34Z</published>
    <title>Attention Is All You Need</title>
    <summary>  The dominant sequence transduction models are based on complex recurrent or
convolutional neural networks... </summary>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <arxiv:comment>15 pages, 5 figures</arxiv:comment>
    <link href="https://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html"/>
    <link title="pdf" href="https://arxiv.org/pdf/1706.03762v7" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
    <category term="cs.LG"/>
  </entry>
  <entry>
    <id>https://arxiv.org/abs/2301.00001v1</id>
    <updated>2023-01-01T00:00:00Z</updated>
    <published>2023-01-01T00:00:00Z</published>
    <title>Withdrawn Toy Paper</title>
    <summary>toy</summary>
    <author><name>Jane Doe</name></author>
    <arxiv:comment>This paper has been withdrawn by the authors</arxiv:comment>
    <arxiv:journal_ref>J. Test 1 (2024)</arxiv:journal_ref>
    <arxiv:doi>10.0000/test.1</arxiv:doi>
    <arxiv:primary_category term="cs.CV"/>
    <category term="cs.CV"/>
  </entry>
</feed>"""


def smoke():
    recs = parse_atom(SMOKE_XML)
    assert len(recs) == 2
    r = recs[0]
    assert r["id_base"] == "1706.03762" and r["version_latest_seen"] == "v7"
    assert r["title"] == "Attention Is All You Need"
    assert r["authors"] == ["Ashish Vaswani", "Noam Shazeer"]
    assert r["primary_category"] == "cs.CL" and "cs.LG" in r["categories"]
    assert r["peer_review_hint"] == "preprint_only"
    r2 = recs[1]
    assert r2["withdrawn"] is True
    assert r2["journal_ref"] and r2["doi"] and r2["peer_review_hint"] == "has_journal_ref_or_doi"
    print("SMOKE OK: arxiv_fetch 解析器全部断言通过（离线，未访问网络）")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="arXiv 官方 API 元数据核验（反幻觉）")
    ap.add_argument("--ids", nargs="*", help="arXiv ID 列表（可带版本）")
    ap.add_argument("--ids-file", help="每行一个 ID 的文件")
    ap.add_argument("--search", help="search_query 检索式，如 'au:vaswani AND ti:attention'")
    ap.add_argument("--max", type=int, default=10, help="检索最大返回数（默认 10）")
    ap.add_argument("--out", help="写入文件（默认 stdout）")
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="离线自检")
    args = ap.parse_args(argv)

    if args.smoke:
        return smoke()

    ids = list(args.ids or [])
    if args.ids_file:
        with open(args.ids_file, encoding="utf-8") as f:
            ids.extend(x.strip() for x in f if x.strip())

    try:
        if ids:
            recs = fetch_by_ids(ids)
        elif args.search:
            recs = search(args.search, args.max)
        else:
            ap.error("给 --ids / --ids-file / --search 之一")
    except Exception as ex:  # 网络/限流/解析失败：退出码 2，绝不伪装成"不存在"
        print(f"FETCH_FAILED: {type(ex).__name__}: {ex}", file=sys.stderr)
        print("诊断：网络不可达、API 限流或返回异常。查不到 ≠ 不存在，请重试或人工核对 https://arxiv.org", file=sys.stderr)
        return 2

    lines = [(json.dumps(r, ensure_ascii=False, indent=2) if args.pretty
              else json.dumps(r, ensure_ascii=False)) for r in recs]
    payload = "\n".join(lines) + ("\n" if lines else "")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
    else:
        sys.stdout.write(payload)

    # 核验提示：请求了但没回来的 ID（可能不存在或版本不存在）
    if ids:
        got = {r["id_base"] for r in recs}
        missing = [i for i in ids if re.sub(r"v\d+$", "", i) not in got]
        for m_ in missing:
            print(f"NOT_RETURNED: {m_} 未在 API 响应中——疑似不存在/幻觉 ID 或已被撤并，人工到 arxiv.org 核对", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
