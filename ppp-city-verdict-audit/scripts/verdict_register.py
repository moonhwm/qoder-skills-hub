#!/usr/bin/env python3
"""Verdict Register 生成/追加工具（留痕硬要求）。
v1.3 2026-08-27 修改人: K3：补 --threshold-assumption 对齐 reference schema 双字段；list 改 .get 防御缺键老记录（依 v1.2.2 批判#7）
v1.1 2026-08-25 修改人: Orchestrator (Kimi K3)：增「维持·理由重构」+ --threshold（依 swarm 评估 issue 2/5）
用法:
  python3 verdict_register.py --file vr.json add --city 沈阳 --original 淘汰 --reason "普速24h" \
      --new 候选 --change 翻案 --by "Orchestrator" --evidence stages/raw/st21_shenyang.md [--note ...]
  python3 verdict_register.py --file vr.json list
"""
import argparse, json, os, sys

CHANGE_TYPES = ["维持", "维持·理由重构", "翻案", "上调", "下调", "存疑待复核"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add")
    add.add_argument("--city", required=True)
    add.add_argument("--original", required=True, help="原结论")
    add.add_argument("--reason", required=True, help="原理由原文")
    add.add_argument("--new", required=True, help="新判定")
    add.add_argument("--change", required=True, choices=CHANGE_TYPES)
    add.add_argument("--by", required=True, help="修改人（留痕）")
    add.add_argument("--date", required=True)
    add.add_argument("--evidence", nargs="*", default=[], help="证据文件路径")
    add.add_argument("--chain", nargs="*", default=[], help="证据链（翻案须≥2条）")
    add.add_argument("--flags", nargs="*", default=[], help="红旗")
    add.add_argument("--review-after", default="")
    add.add_argument("--threshold", default="", help="原理由阈值原文")
    add.add_argument("--threshold-assumption", default="", help="原阈值不可得时的假设声明（须配±敏感性）")
    sub.add_parser("list")
    a = p.parse_args()

    reg = []
    if os.path.exists(a.file):
        reg = json.load(open(a.file, encoding="utf-8"))
    if a.cmd == "list":
        for v in reg:
            print(f"{v.get('city','?')}: {v.get('original_verdict','?')} → {v.get('new_verdict','?')} [{v.get('change_type','?')}] by {v.get('modified_by','?')} {v.get('date','?')}")
        return
    if a.change == "翻案" and len(a.chain) < 2:
        sys.exit("翻案须 evidence chain ≥2 条独立证据（--chain）")
    if not a.by:
        sys.exit("缺少修改人 --by（留痕硬要求）")
    reg.append({
        "city": a.city, "original_verdict": a.original, "original_reason": a.reason,
        "new_verdict": a.new, "change_type": a.change,
        "evidence_chain": a.chain, "red_flags": a.flags,
        "modified_by": a.by, "date": a.date,
        "evidence_files": a.evidence, "review_after": a.review_after,
        "original_threshold": a.threshold, "threshold_assumption": a.threshold_assumption,
    })
    json.dump(reg, open(a.file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[OK] {a.city}: {a.original} → {a.new} [{a.change}] by {a.by}")

if __name__ == "__main__":
    main()
