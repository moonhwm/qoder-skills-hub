#!/usr/bin/env python3
"""livability_doc_scanner.py — 扫描目录，登记「城市宜居度/舒适度」有关文档与字段出现点。

用法:
    python3 livability_doc_scanner.py --root <目录> [--out registry.json]

输出 registry.json:
    {
      "meta": {"root": ..., "scan_date": ..., "doc_count": N},
      "documents": [
        {"path": ..., "category": "city_livability|housing|dorm_bathroom|advisor_comfort|comfort_field|other",
         "hits": [{"keyword":..., "line":..., "excerpt":...}], "hit_count": N,
         "size": bytes, "mtime": "YYYY-MM-DD"}
      ]
    }
纯标准库。类别规则见 CATEGORY_KEYWORDS；命中最多类别归入主类，并列时取优先级靠前者。
"""
import argparse, json, os, re, sys, datetime

CATEGORY_KEYWORDS = {
    "city_livability": ["城市宜居", "宜居度", "livability", "city_livability", "向往度", "LIVABILITY"],
    "housing": ["住房压力", "房价收入比", "房租收入比", "HPI", "hpi", "宜居分"],
    "dorm_bathroom": ["宿舍", "寝室", "卫浴", "澡堂", "独立卫浴", "dorm", "BATHROOM", "bathroom"],
    "advisor_comfort": ["大导", "小导", "导师风评", "LAB_COMFORT", "advisor_pressure", "导师压榨"],
    "comfort_field": ["舒适度", "就读舒适", "comfort"],
}
PRIORITY = ["city_livability", "housing", "dorm_bathroom", "advisor_comfort", "comfort_field", "other"]
TEXT_EXT = {".md", ".py", ".json", ".txt", ".csv", ".yaml", ".yml", ".html"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__"}


def categorize(path, text):
    scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(text.count(k) for k in kws)
    best = max(scores, key=lambda c: (scores[c], -PRIORITY.index(c)))
    return best if scores[best] > 0 else "other"


def scan_file(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except OSError:
        return None
    text = "".join(lines)
    hits = []
    for i, line in enumerate(lines, 1):
        for kws in CATEGORY_KEYWORDS.values():
            for k in kws:
                if k in line:
                    hits.append({"keyword": k, "line": i,
                                 "excerpt": line.strip()[:120]})
                    break
    if not hits:
        return None
    st = os.stat(path)
    return {"path": path, "category": categorize(path, text),
            "hits": hits[:50], "hit_count": len(hits), "size": st.st_size,
            "mtime": datetime.date.fromtimestamp(st.st_mtime).isoformat()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    docs = []
    for dirpath, dirnames, filenames in os.walk(a.root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                r = scan_file(os.path.join(dirpath, fn))
                if r:
                    docs.append(r)
    docs.sort(key=lambda d: (PRIORITY.index(d["category"]), -d["hit_count"]))
    reg = {"meta": {"root": os.path.abspath(a.root),
                    "scan_date": datetime.date.today().isoformat(),
                    "doc_count": len(docs)},
           "documents": docs}
    out = json.dumps(reg, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(out)
    print(out if not a.out else f"registered {len(docs)} docs -> {a.out}")


if __name__ == "__main__":
    main()
