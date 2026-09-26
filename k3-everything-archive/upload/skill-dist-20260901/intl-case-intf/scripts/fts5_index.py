#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite FTS5 本地索引 + BM25 检索（F2 先例标准模式：外部内容表可省，直接内容表即可）。
用法：python3 fts5_index.py build <db> <json结果文件...>
      python3 fts5_index.py query <db> <关键词> [limit]"""
import json, sqlite3, sys

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases(
  id INTEGER PRIMARY KEY,
  source TEXT,      -- cjeu / hudoc
  title TEXT,
  url TEXT,
  snippet TEXT,
  date TEXT,
  ref TEXT          -- celex 或 itemid
);
CREATE VIRTUAL TABLE IF NOT EXISTS cases_fts USING fts5(
  title, snippet, content='cases', content_rowid='id');
CREATE TRIGGER IF NOT EXISTS cases_ai AFTER INSERT ON cases BEGIN
  INSERT INTO cases_fts(rowid, title, snippet) VALUES (new.id, new.title, new.snippet);
END;
"""

def build(db_path, files):
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    n = 0
    for f in files:
        data = json.load(open(f, encoding="utf-8"))
        rows = data["results"] if isinstance(data, dict) and "results" in data else data
        src = "hudoc" if isinstance(data, dict) and "resultcount" in data else "cjeu"
        for r in rows:
            ref = r.get("celex") or r.get("itemid", "")
            cur = con.execute(
                "INSERT INTO cases(source,title,url,snippet,date,ref) VALUES(?,?,?,?,?,?)",
                (src, r.get("title", ""), r.get("url", ""), r.get("snippet", ""), r.get("date", ""), ref))
            n += 1
    con.commit()
    total = con.execute("SELECT count(*) FROM cases").fetchone()[0]
    con.close()
    print(f"indexed {n} new rows; total {total} in {db_path}")

def query(db_path, kw, limit=10):
    con = sqlite3.connect(db_path)
    rows = con.execute("""
      SELECT c.source, c.title, c.date, c.url, bm25(cases_fts) AS rank
      FROM cases_fts f JOIN cases c ON c.id=f.rowid
      WHERE cases_fts MATCH ? ORDER BY rank LIMIT ?""",
      (kw, limit)).fetchall()
    con.close()
    print(json.dumps([
        {"source": s, "title": t, "date": d, "url": u, "bm25": round(r, 4)}
        for s, t, d, u, r in rows], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] == "query":
        query(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 10)
