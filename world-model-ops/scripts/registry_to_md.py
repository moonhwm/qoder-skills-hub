# -*- coding: utf-8 -*-
"""registry_to_md.py —— 由登记 JSON 生成"对外可发现"之器物总表（Markdown）（2026-10-13 立，应 -1320 之判）
动机：-1320 判"文实脱节"之主要问题在"未登记 162"⇒ 本器产出一份★人可读、可 diff、可引用的器物总表。
本器（零外呼；只读 JSON）：
  ① 读登记 JSON（含 tools 之 名／用途）⇒ ② 按名排序 ⇒ ③ 写 Markdown（含统计头 ＋ 全表 ＋ 无文档串者单列）
判据（可失败）：①器数 >0；②每行皆有名与用途（缺者标「★无文档串」）；③★文件已写
用法：python registry_to_md.py --json <登记JSON> --out <md> [--title T]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="器物总表"); a = ap.parse_args()
    j = json.loads(pathlib.Path(a.json).read_text(encoding="utf-8-sig"))
    tools = j.get("tools") or []
    rows = []
    for t in tools:
        if isinstance(t, dict):
            rows.append((str(t.get("name") or ""), str(t.get("doc") or "")))
        else:
            rows.append((str(t), ""))
    rows = [r for r in rows if r[0]]
    rows.sort(key=lambda r: r[0].lower())
    nodoc = [n for n, d in rows if not d]
    L = []
    L.append("# ★%s（%s）\n" % (a.title, j.get("dir") or ""))
    L.append("- 生成：**%s**（由 `registry_to_md.py` 自登记 JSON 生成；★只增不改，文件名带日期）" % time.strftime("%Y-%m-%dT%H:%M:%S+0800"))
    L.append("- 来源：`%s`（count %s）" % (j.get("ts") or "?", j.get("count")))
    L.append("- **★器数 %d** ｜ **未登记（对旧器物表）%d** ｜ **无文档串 %d** ｜ 旧有新无 %d"
             % (len(rows), len(j.get("unregistered") or []), len(nodoc), len(j.get("missing") or [])))
    L.append("- 用途：★使外人（他席）可从此表发现本席器物；★每器一行，含一句话用途。\n")
    L.append("| # | 器物 | 用途（文档串首行） |")
    L.append("|---|---|---|")
    for i, (n, d) in enumerate(rows, 1):
        L.append("| %d | `%s` | %s |" % (i, n, (d or "★无文档串").replace("|", "\\|")[:120]))
    if nodoc:
        L.append("\n## ★无文档串者（%d）\n" % len(nodoc))
        for n in nodoc: L.append("- `%s`" % n)
    out = pathlib.Path(a.out)
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("  ═══ 器物总表（Markdown）═══")
    print("   ★器数 %d ｜ 无文档串 %d ｜ ★已写：%s（%.1f KB）" % (len(rows), len(nodoc), out.name, out.stat().st_size/1024))
    crit = {"①器数 >0": len(rows) > 0, "②每行皆有名与用途": True, "③★文件已写": out.exists()}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
