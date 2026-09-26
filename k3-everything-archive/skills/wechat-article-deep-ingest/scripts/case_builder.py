#!/usr/bin/env python3
"""案例库构建器：从 pointers.csv + 各篇 snapshot/md 生成 per-article case JSON、
cases_index.csv 与人可读 cases.py 聚合。v1.2 2026-08-25 修改人: Orchestrator (Kimi K3)
用法:
  python3 case_builder.py --root <wx_archive>            # 全量回填
  python3 case_builder.py --root <wx_archive> --only <slug>
"""
import argparse, csv, glob, json, os, re

def build_case(row, root):
    slug = row["slug"]
    snap_path = os.path.join(root, "articles", slug, f"{slug}.snapshot.json")
    snap = {}
    if os.path.exists(snap_path):
        try: snap = json.load(open(snap_path, encoding="utf-8"))
        except Exception: snap = {"_read_error": True}
    return {
        "slug": slug, "title": row["title"], "account": row["account"],
        "pub_date": row["pub_date"] or None, "url": row["url"],
        "判定": {
            "channel_grade": row["channel_grade"], "proj_grade": row["proj_grade"],
            "promo_flag": row["promo_flag"], "three_state": row["three_state"],
            "p_subtype": None,  # v1.2 字段：待按 slogan-discrimination 七维回填
            "slogan_signals": [], "track_record": {}, "p2l_findings": [],
        },
        "关键事实出列": [],  # 四要素齐全才入（人/代理补充）
        "批判要点": [row["notes"]] if row["notes"] else [],
        "局限": ([f"pub_date 未取得（{snap.get('notes','通道M遇墙')}）"] if not row["pub_date"] else []),
        "待复核问题": [],
        "修改痕迹": [{"by": "case_builder.py", "date": row["fetch_date"], "change": "v1.2 案例库回填（自动）"}],
        "_meta": {"archive_path": row["archive_path"], "conf": row["conf"],
                  "region": row["region"], "industry_tags": row["industry_tags"],
                  "engineering_clue": row["engineering_clue"], "trace": row["trace"]},
    }

PY_HEADER = '''# -*- coding: utf-8 -*-
"""cases.py — wx_archive 案例库人可读聚合（自动生成，人只读不改；改请改 case_<slug>.json 后重跑 case_builder.py）
生成: {gen} ｜ 共 {n} 案 ｜ 每案字段见 references/archive-schema.md §6
"""
CASES = {}
'''

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True); p.add_argument("--only", default="")
    a = p.parse_args()
    rows = list(csv.DictReader(open(os.path.join(a.root, "pointers.csv"), encoding="utf-8-sig")))
    cdir = os.path.join(a.root, "cases"); os.makedirs(cdir, exist_ok=True)
    built, skipped = [], []
    for r in rows:
        if a.only and r["slug"] != a.only: continue
        cj = os.path.join(cdir, f"case_{r['slug']}.json")
        if os.path.exists(cj) and not a.only:
            skipped.append(r["slug"]); continue  # 不覆盖已有（追加走人工/代理+修改痕迹）
        case = build_case(r, a.root)
        json.dump(case, open(cj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        built.append(r["slug"])
    # 索引 CSV（全量重建）
    idx_cols = ["slug","title","pub_date","proj_grade","three_state","p_subtype","conf","region","industry_tags","case_file"]
    all_cases = sorted(glob.glob(os.path.join(cdir, "case_*.json")))
    with open(os.path.join(cdir, "cases_index.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=idx_cols); w.writeheader()
        for cj in all_cases:
            c = json.load(open(cj, encoding="utf-8"))
            w.writerow({"slug": c["slug"], "title": c["title"], "pub_date": c["pub_date"] or "unknown",
                        "proj_grade": c["判定"]["proj_grade"], "three_state": c["判定"]["three_state"],
                        "p_subtype": c["判定"]["p_subtype"] or "", "conf": c["_meta"]["conf"],
                        "region": c["_meta"]["region"], "industry_tags": c["_meta"]["industry_tags"],
                        "case_file": os.path.basename(cj)})
    # cases.py 聚合（人可读）
    import datetime
    hdr = PY_HEADER.replace('{gen}', datetime.date.today().isoformat()).replace('{n}', str(len(all_cases)))
    out = [hdr]
    for cj in all_cases:
        c = json.load(open(cj, encoding="utf-8"))
        out.append(f'\n# === {c["slug"]} ===')
        out.append(f'# {c["title"]} | {c["account"]} | pub={c["pub_date"] or "unknown"}')
        out.append(f'# 判定: {c["判定"]["proj_grade"]}/{c["判定"]["channel_grade"]} promo={c["判定"]["promo_flag"]} 三态={c["判定"]["three_state"]} p_subtype={c["判定"]["p_subtype"]}')
        out.append(f'# 批判: {"；".join(c["批判要点"])[:120]}')
        out.append(f'# 局限: {"；".join(c["局限"]) or "无登记"}')
        out.append(f'CASES[{c["slug"]!r}] = {c!r}')  # repr保证Python字面量合法（null→None）
    open(os.path.join(cdir, "cases.py"), "w", encoding="utf-8").write("\n".join(out))
    print(f"[OK] 新建 {len(built)} 案 / 跳过已有 {len(skipped)} 案 / 索引+聚合 {len(all_cases)} 案")

if __name__ == "__main__": main()
