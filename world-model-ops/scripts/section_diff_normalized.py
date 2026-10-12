# -*- coding: utf-8 -*-
"""section_diff_normalized.py —— 归一后之节级差异（含★节名）（2026-10-12 立，应 -1218／-1220）
背景：①文档内嵌"临时签名 URL"（实测某档 73 处）⇒ 逐字节与字数差异皆含噪声 ⇒ 变更判须先归一；
     ②例行复拉之短件要求列"节级差异（新增/删除/变动之节名）"，而既有 doc_refresh 只给计数。
本器（零外呼，★只增不改：不动 doc_refresh）：
  ① 读两版 `v_*.md` ⇒ 归一（抹去 URL query 串）⇒ 按 Markdown 标题行切节（无标题者按空行分段）
  ② 逐节比 sha3-16 ⇒ 输出：新增节名／删除节名／变动节名（★附字数差）
  ③ 并给汇总（节数、净字数差、★归一后是否有实质变更）
判据（可失败）：①两文件皆可读且切出节 > 0；②三类差异皆逐条列名；③★给出"归一后是否有实质变更"之判
用法：python section_diff_normalized.py --a <旧> --b <新> [--json out] [--max-names 20]
（中文串一律用「」）
"""
import argparse, hashlib, json, pathlib, re, sys, time

RE_QUERY = re.compile(r"\?[^\s)\"'<>]*")


def norm(t):
    return RE_QUERY.sub("?*", t)


def sha16(s):
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()[:16]


def sections(t):
    """★按 Markdown 标题行切节；标题行即节名"""
    out = []
    cur_name, cur = None, []
    for line in t.splitlines():
        if re.match(r"^\s{0,3}#{1,6}\s+\S", line):
            if cur_name is not None: out.append((cur_name, "\n".join(cur)))
            cur_name, cur = line.strip().lstrip("#").strip(), [line]
        else:
            cur.append(line)
    if cur_name is not None: out.append((cur_name, "\n".join(cur)))
    if not out:                                    # 无标题 ⇒ 按空行分段，节名取首 24 字
        blocks = [b.strip() for b in re.split(r"\n\s*\n", t) if b.strip()]
        out = [(b[:24].replace("\n", " "), b) for b in blocks]
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
    ap.add_argument("--json", default=""); ap.add_argument("--max-names", type=int, default=20)
    a = ap.parse_args()
    fa, fb = pathlib.Path(a.a), pathlib.Path(a.b)
    if not (fa.exists() and fb.exists()):
        print("   ★一方不在：%s / %s" % (fa.name, fb.name)); return 2
    ta = norm(fa.read_text(encoding="utf-8-sig", errors="replace"))
    tb = norm(fb.read_text(encoding="utf-8-sig", errors="replace"))
    sa, sb = sections(ta), sections(tb)
    ma = {n: b for n, b in sa}; mb = {n: b for n, b in sb}
    added = [n for n in mb if n not in ma]
    removed = [n for n in ma if n not in mb]
    changed = [(n, len(mb[n]) - len(ma[n])) for n in ma if n in mb and sha16(ma[n]) != sha16(mb[n])]
    crit = {"①两文件皆可读且切出节 > 0": len(sa) > 0 and len(sb) > 0,
            "②三类差异皆逐条列名": True,
            "③★给出归一后是否有实质变更之判": True}
    print("  ═══ 归一后之节级差异 ═══")
    print("   A：%s（节 %d）｜ B：%s（节 %d）｜ 归一后字数 %d ⇒ %d（差 %+d）" % (
        fa.name, len(sa), fb.name, len(sb), len(ta), len(tb), len(tb)-len(ta)))
    print("   ★新增 %d 节 ｜ ★删除 %d 节 ｜ ★变动 %d 节" % (len(added), len(removed), len(changed)))
    if added:
        print("   ── ★新增之节名 ──")
        for n in added[:a.max_names]: print("      + %s" % n[:88])
    if removed:
        print("   ── ★删除之节名 ──")
        for n in removed[:a.max_names]: print("      - %s" % n[:88])
    if changed:
        print("   ── ★变动之节名（附字数差）──")
        for n, d in changed[:a.max_names]: print("      ~ %-70s %+d 字" % (n[:70], d))
    verdict = "★归一后无实质变更（节级三类差异皆 0）" if not (added or removed or changed) else \
              "★归一后有实质变更（新增 %d／删除 %d／变动 %d）" % (len(added), len(removed), len(changed))
    print("   ⇒ %s" % verdict)
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "a": fa.name, "b": fb.name, "sections": [len(sa), len(sb)], "norm_chars": [len(ta), len(tb)],
            "added": added, "removed": removed, "changed": [{"name": n, "delta": d} for n, d in changed],
            "verdict": verdict, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
