#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ECtHR HUDOC 事实型公开 JSON 端点只读薄封装。
注意：该端点未见官方文档（F1 定性），仅作可行性评估用只读调用；
正式封装前置动作=向欧洲人权法院书面确认合规。
输出统一引证契约 {title, url, snippet, court, date, itemid}。"""
import json, sys, urllib.parse, urllib.request

BASE = "https://hudoc.echr.coe.int/app/query/results"
UA = "intl-case-toolkit/0.1 (read-only feasibility evaluation)"

def search(keyword: str, length: int = 10):
    # HUDOC 查询语法：全文域 contentsitename 限定在 ECHR 库内检索
    q = f'contentsitename:ECHR AND ({keyword})'
    url = BASE + "?" + urllib.parse.urlencode({
        "query": q,
        "select": "itemid,docname,appno,conclusion,judgementdate,importance,respondent,doctype",
        "sort": "", "start": "0", "length": str(length),
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for it in data.get("results", []):
        cols = it.get("columns", {})  # 实测：columns 为 dict（2026-09-01）
        itemid = cols.get("itemid", "")
        raw_date = cols.get("judgementdate", "") or ""
        # HUDOC 日期形 DD/MM/YYYY HH:MM:SS → ISO
        iso = ""
        if len(raw_date) >= 10 and raw_date[2] == "/":
            d_, m_, y_ = raw_date[:10].split("/")
            iso = f"{y_}-{m_}-{d_}"
        out.append({
            "title": cols.get("docname", ""),
            "url": f"https://hudoc.echr.coe.int/eng#{{\"itemid\":[\"{itemid}\"]}}" if itemid else "",
            "snippet": cols.get("conclusion", "")[:300],
            "court": "ECtHR",
            "date": iso,
            "itemid": itemid,
            "appno": cols.get("appno", ""),
            "importance": cols.get("importance", ""),
        })
    return {"resultcount": data.get("resultcount"), "results": out}

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "freedom of expression"
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print(json.dumps(search(kw, lim), ensure_ascii=False, indent=2))
