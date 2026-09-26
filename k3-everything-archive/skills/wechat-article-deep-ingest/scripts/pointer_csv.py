#!/usr/bin/env python3
"""结构化指针 CSV 管理。v1.0 2026-08-25 修改人: Orchestrator (Kimi K3)
用法:
  python3 pointer_csv.py --file pointers.csv add --slug S --title T --account A \
      --pub-date 2026-01-01 --url U --channel C2 --proj B --promo yes --state P \
      --region 江苏 --tags 集成电路;人工智能 --trace "巨潮 X 招股说明书" --path articles/S/S.md --conf C
  python3 pointer_csv.py --file pointers.csv list [--region 江苏]
"""
import argparse, csv, os, sys

COLS = ["slug","title","account","pub_date","fetch_date","url","channel_grade","proj_grade",
        "promo_flag","three_state","region","industry_tags","engineering_clue","trace",
        "archive_path","conf","notes"]
VALID_STATE = ["P","L","U","NA"]  # v1.1: 允许分号有序组合如 "L;P"（主态在前）

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add")
    ALIAS = {"three-state": ["--state"], "industry-tags": ["--tags"], "pub-date": ["--pubdate"], "archive-path": ["--path"]}
    for f in COLS:
        flag = f"--{f.replace('_','-')}"
        add.add_argument(flag, *ALIAS.get(flag.strip("-"), []), dest=f, default="")
    add.add_argument("--by", required=True, help="修改人（留痕）")
    ls = sub.add_parser("list"); ls.add_argument("--region", default="")
    a = p.parse_args()
    rows = []
    if os.path.exists(a.file):
        rows = list(csv.DictReader(open(a.file, encoding="utf-8-sig")))
    if a.cmd == "list":
        for r in rows:
            if a.region and r["region"] != a.region: continue
            print(f"{r['slug']} | {r['title'][:30]} | {r['proj_grade']}/{r['channel_grade']} | {r['three_state']} | {r['pub_date']}")
        return
    row = {f: getattr(a, f, "") for f in COLS}
    if not row["fetch_date"]:
        import datetime; row["fetch_date"] = datetime.date.today().isoformat()
    if row["three_state"]:
        parts = row["three_state"].split(";")
        if any(x not in VALID_STATE for x in parts):
            sys.exit(f"three_state 每项须为 {VALID_STATE}，分号组合主态在前")
    if row["promo_flag"] == "yes" and row["conf"] not in ("C","D","E",""):
        print(f"[WARN] 沥乾标记下 conf={row['conf']} 超过 C 上限，已压为 C", file=sys.stderr); row["conf"]="C"
    row["notes"] = (row["notes"] + f" | by {a.by}").strip(" |")
    if any(r["slug"] == row["slug"] for r in rows):
        sys.exit(f"slug 重复: {row['slug']}（改 slug 或先删旧行）")
    rows.append(row)
    with open(a.file, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    print(f"[OK] {row['slug']} -> {a.file}（共{len(rows)}行）")

if __name__ == "__main__": main()
