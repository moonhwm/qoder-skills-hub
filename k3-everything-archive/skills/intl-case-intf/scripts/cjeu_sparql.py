#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CJEU CELLAR SPARQL 只读薄封装（官方公共端点，无需认证）。
输出统一引证契约 {title, url, snippet, court, date, celex}。"""
import json, sys, urllib.parse, urllib.request

ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
UA = "intl-case-toolkit/0.1 (read-only research; sandbox legal-research facility)"

QUERY_TMPL = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?work ?title ?date ?celex WHERE {
  ?work cdm:work_has_resource-type <http://publications.europa.eu/resource/authority/resource-type/JUDG> .
  ?work cdm:work_date_document ?date .
  ?work cdm:work_id_document ?celex .
  ?exp cdm:expression_belongs_to_work ?work .
  ?exp cdm:expression_title ?title .
  ?exp cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> .
  FILTER(CONTAINS(LCASE(STR(?title)), LCASE("%s")))
} ORDER BY DESC(?date) LIMIT %d
"""

def search(keyword: str, limit: int = 10):
    q = QUERY_TMPL % (keyword.replace('"', ''), limit)
    url = ENDPOINT + "?" + urllib.parse.urlencode({
        "query": q, "format": "application/sparql-results+json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for b in data["results"]["bindings"]:
        celex = b.get("celex", {}).get("value", "")
        out.append({
            "title": b.get("title", {}).get("value", ""),
            "url": b.get("work", {}).get("value", ""),
            "snippet": "",
            "court": "CJEU",
            "date": b.get("date", {}).get("value", "")[:10],
            "celex": celex,
            "eurlex": f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}" if celex else "",
        })
    return out

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "state aid"
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print(json.dumps(search(kw, lim), ensure_ascii=False, indent=2))
