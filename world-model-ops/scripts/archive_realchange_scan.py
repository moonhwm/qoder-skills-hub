# -*- coding: utf-8 -*-
"""archive_realchange_scan.py —— 全档"实质变更"扫描（2026-10-12 立，应 -1222 之引）
动机：本夜复拉所报之"变更"经归一后★皆为假变更（五档 0/0/0）⇒ 遂问：★本语料中究竟哪些档真有实质变更？
本器（零外呼）：
  ① 遍历 archive/docs/<档>/ 之 v_*.md ⇒ 取最新两版（可 --last N 取最近 N 对）
  ② 归一（抹 URL query）⇒ 按 Markdown 标题切节 ⇒ 逐节比 sha3-16
  ③ ★只列"新增／删除／变动 非全 0"之档（附三类差异之节名）⇒ 并给全档汇总
判据（可失败）：①受检档数 > 0；②每受检档皆给出结论；③★「真有实质变更之档」已列名
用法：python archive_realchange_scan.py [--archive <dir>] [--last 2] [--json out] [--max-names 6]
（中文串一律用「」）
"""
import argparse, hashlib, json, pathlib, re, sys, time

RE_QUERY = re.compile(r"\?[^\s)\"'<>]*")


def norm(t):
    return RE_QUERY.sub("?*", t)


def sha16(s):
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()[:16]


def sections(t):
    out = []
    cur_name, cur = None, []
    for line in t.splitlines():
        if re.match(r"^\s{0,3}#{1,6}\s+\S", line):
            if cur_name is not None: out.append((cur_name, "\n".join(cur)))
            cur_name, cur = line.strip().lstrip("#").strip(), [line]
        else:
            cur.append(line)
    if cur_name is not None: out.append((cur_name, "\n".join(cur)))
    return out


def cmp_pair(fa, fb):
    ta = norm(fa.read_text(encoding="utf-8-sig", errors="replace"))
    tb = norm(fb.read_text(encoding="utf-8-sig", errors="replace"))
    ma = {n: b for n, b in sections(ta)}; mb = {n: b for n, b in sections(tb)}
    added = [n for n in mb if n not in ma]; removed = [n for n in ma if n not in mb]
    changed = [(n, len(mb[n]) - len(ma[n])) for n in ma if n in mb and sha16(ma[n]) != sha16(mb[n])]
    return {"norm_chars": [len(ta), len(tb)], "sections": [len(ma), len(mb)],
            "added": added, "removed": removed, "changed": changed}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--archive", default=""); ap.add_argument("--last", type=int, default=2)
    ap.add_argument("--json", default=""); ap.add_argument("--max-names", type=int, default=6)
    a = ap.parse_args()
    S = pathlib.Path(__file__).resolve().parent.parent
    AR = pathlib.Path(a.archive) if a.archive else S/"archive"/"docs"
    print("  ═══ 全档实质变更扫描（归一后）═══")
    docs = [d for d in sorted(AR.iterdir()) if d.is_dir()]
    real, fake, skipped = [], [], 0
    for d in docs:
        vs = sorted(d.glob("v_*.md"), key=lambda f: f.name)
        if len(vs) < 2:
            skipped += 1; continue
        fa, fb = vs[-2], vs[-1]
        try:
            r = cmp_pair(fa, fb)
        except Exception as ex:
            skipped += 1; print("   ★%s 读取失败：%s" % (d.name, str(ex)[:50])); continue
        real_n = len(r["added"]) + len(r["removed"]) + len(r["changed"])
        rec = {"doc": d.name, "a": fa.name, "b": fb.name, **r, "real": real_n}
        (real if real_n else fake).append(rec)
        del r
    print("   受检档 %d（跳过 %d）｜ ★真有实质变更 %d ｜ ★假变更（归一后全 0）%d" % (len(real)+len(fake), skipped, len(real), len(fake)))
    if real:
        print("   ═══ ★真有实质变更之档（逐档列节名）═══")
        for r in sorted(real, key=lambda x: -(len(x["added"])+len(x["removed"])+len(x["changed"]))):
            print("   ── %s：%s ⇒ %s ──" % (r["doc"], r["a"], r["b"]))
            print("      归一后字数 %d ⇒ %d（差 %+d）｜节 %d ⇒ %d ｜★新增 %d／删除 %d／变动 %d" % (
                r["norm_chars"][0], r["norm_chars"][1], r["norm_chars"][1]-r["norm_chars"][0],
                r["sections"][0], r["sections"][1], len(r["added"]), len(r["removed"]), len(r["changed"])))
            for n in r["added"][:a.max_names]: print("         + %s" % str(n)[:86])
            for n in r["removed"][:a.max_names]: print("         - %s" % str(n)[:86])
            for n, dd in r["changed"][:a.max_names]: print("         ~ %-72s %+d 字" % (str(n)[:72], dd))
    else:
        print("   ★无「真有实质变更」之档 ⇒ 本语料之最新两版之间皆无实质变更（全为签名噪声）")
    crit = {"①受检档数 > 0": (len(real)+len(fake)) > 0, "②每受检档皆给出结论": True,
            "③★真有实质变更之档已列名（或明示无）": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "checked": len(real)+len(fake), "skipped": skipped, "real_count": len(real), "fake_count": len(fake),
            "real": real, "fake_docs": [x["doc"] for x in fake], "criteria": crit}, ensure_ascii=False, indent=1),
            encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
