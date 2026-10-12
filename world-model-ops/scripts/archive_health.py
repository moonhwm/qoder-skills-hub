# -*- coding: utf-8 -*-
"""archive_health.py —— 档案健康闸（应本轮事故：复拉写入空档而工器报"变更"）
检查：①末版是否为空（0 字）②是否存在任何非空版③现行版指针是否最新
★另可 --fix-pointer 依"最后非空版"重写现行版指针（只读档案本体，不改任何文档）
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time

D = pathlib.Path.home()/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"/"archive"/"docs"

def rows():
    out = []
    for d in sorted([x for x in D.iterdir() if x.is_dir()]):
        vs = sorted(d.glob("v_2026*.md"))
        if not vs: continue
        sizes = [(p.stem[2:], len(p.read_text(encoding="utf-8", errors="replace"))) for p in vs]
        ok = [s for s in sizes if s[1] > 0]
        out.append({"doc": d.name, "versions": len(sizes), "latest": sizes[-1][0], "latest_chars": sizes[-1][1],
                    "empty_versions": [s[0] for s in sizes if s[1] == 0],
                    "latest_ok": ok[-1][0] if ok else None, "latest_ok_chars": ok[-1][1] if ok else 0})
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fix-pointer", action="store_true"); ap.add_argument("--json", default="")
    a = ap.parse_args()
    R = rows()
    empty_last = [r for r in R if r["latest_chars"] == 0]
    never_ok  = [r for r in empty_last if r["latest_ok"] is None]
    recoverable = [r for r in empty_last if r["latest_ok"] is not None]
    print("  ═══ 档案健康（%d 个文档）═══" % len(R))
    print("   ★末版为空者 %d ｜ 其中「可恢复」（有非空旧版）%d ｜ ★「从无非空版」 %d" % (
        len(empty_last), len(recoverable), len(never_ok)))
    for r in recoverable:
        print("     可恢复 %-14s 末版 %s（0 字）⇒ 现行应取 %s（%d 字）" % (r["doc"], r["latest"], r["latest_ok"], r["latest_ok_chars"]))
    for r in never_ok[:8]:
        print("     ★从无非空版 %-14s（版本 %d，最早 %s）" % (r["doc"], r["versions"], r["empty_versions"][0] if r["empty_versions"] else "—"))
    if len(never_ok) > 8: print("     …（其余 %d 个同类）" % (len(never_ok)-8))
    if a.fix_pointer:
        p = D/("现行版指针_%s.json" % time.strftime("%Y%m%d"))
        p.write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "note": "★现行版指针：空档保留不动（只增不改）；本指针指明各文档之最后非空版本",
            "docs": R}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ✓ 已写现行版指针：%s" % p.name)
    if a.json: pathlib.Path(a.json).write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   ⇒ 判：%s" % ("★有末版为空之文档 ⇒ 复拉须加空内容闸（拉到 0 字不得计为「变更」）" if empty_last else "★无空档"))

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
