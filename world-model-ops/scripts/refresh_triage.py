# -*- coding: utf-8 -*-
"""refresh_triage.py —— 例行复拉之「第 3.5 步」裁决器（2026-10-12 立，应 -1218／-1220／-1221）
问题：含「临时签名 URL」之档（如 polish，实测嵌 73 处）每轮复拉皆报「变更」，然★归一后节级差异为 0
     ⇒ 若照旧出短件，则为「假变更」出件（浪费且污染台账）。
本器（零外呼、★只增不改）一步裁决：
  ① 读 outbox/notify 最新之 doc_update_*.md ⇒ 取其列名之文档（manifest 键，如 polish）
  ② 对该档，从 archive/docs/<键>/ 取最新两版 v_*.md ⇒ 跑「归一后节级差异」（内联实现，复用同法）
  ③ ★给裁决：若归一后新增/删除/变动皆 0 ⇒ "★假变更 ⇒ 只台账一行，不出短件"；否则 ⇒ "★实质变更 ⇒ 出短件"
判据（可失败）：①能读到最新通知；②能取到该档 ≥2 版；③★裁决已给出（出件／不出件）
用法：python refresh_triage.py [--notify-dir <dir>] [--archive <dir>] [--json out]
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


def diff_norm(fa, fb):
    ta = norm(fa.read_text(encoding="utf-8-sig", errors="replace"))
    tb = norm(fb.read_text(encoding="utf-8-sig", errors="replace"))
    ma = {n: b for n, b in sections(ta)}; mb = {n: b for n, b in sections(tb)}
    added = [n for n in mb if n not in ma]; removed = [n for n in ma if n not in mb]
    changed = [n for n in ma if n in mb and sha16(ma[n]) != sha16(mb[n])]
    return {"norm_chars": [len(ta), len(tb)], "sections": [len(ma), len(mb)],
            "added": added, "removed": removed, "changed": changed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notify-dir", default=""); ap.add_argument("--archive", default=""); ap.add_argument("--json", default="")
    a = ap.parse_args()
    S = pathlib.Path(__file__).resolve().parent.parent
    nd = pathlib.Path(a.notify_dir) if a.notify_dir else S/"outbox"/"notify"
    ar = pathlib.Path(a.archive) if a.archive else S/"archive"/"docs"
    print("  ═══ 复拉裁决（第 3.5 步）═══")
    nf = sorted(nd.glob("doc_update_*.md"), key=lambda f: f.stat().st_mtime)
    if not nf:
        print("   ★无通知档 ⇒ 无变更可裁"); return 1
    latest = nf[-1]
    txt = latest.read_text(encoding="utf-8-sig", errors="replace")
    keys = re.findall(r"-\s+\*\*([A-Za-z0-9_\-]+)\*\*（", txt)
    if not keys:
        # ★格式 B（只给计数）⇒ 由 manifest 取「latest.ver 最近之档」（至多 5 个）
        try:
            mf = json.loads((ar/"index.json").read_text(encoding="utf-8-sig"))
            cand = []
            for k2, v2 in mf.items():
                if not isinstance(v2, dict): continue
                lat = v2.get("latest") or {}
                cand.append((str(lat.get("ver") or ""), k2))
            cand.sort(reverse=True)
            keys = [k2 for _, k2 in cand[:5]]
            print("   （格式 B：只给计数 ⇒ 由 manifest 取 latest.ver 最近之 5 档）")
        except Exception as ex:
            print("   ★manifest 不可解析：%s" % str(ex)[:60])
    print("   最新通知：%s（%s）｜ 其列名之档：%s" % (latest.name, time.strftime("%H:%M", time.localtime(latest.stat().st_mtime)), "、".join(keys) or "（无）"))
    if not keys:
        print("   ⇒ 判：★本轮无变更（无需出短件）"); return 0
    rows = []
    for k in keys:
        d = ar/k
        if not d.exists():
            print("   ★%s 之归档目录不在 ⇒ 跳过" % k); continue
        vs = sorted(d.glob("v_*.md"), key=lambda f: f.name)
        if len(vs) < 2:
            print("   ★%s 仅有 %d 版 ⇒ 无法比 ⇒ 跳过" % (k, len(vs))); continue
        fa, fb = vs[-2], vs[-1]
        r = diff_norm(fa, fb)
        real = bool(r["added"] or r["removed"] or r["changed"])
        print("   ── %s：%s ⇒ %s ──" % (k, fa.name, fb.name))
        print("      归一后字数 %d ⇒ %d（差 %+d）｜节 %d ⇒ %d" % (r["norm_chars"][0], r["norm_chars"][1],
              r["norm_chars"][1]-r["norm_chars"][0], r["sections"][0], r["sections"][1]))
        print("      ★新增 %d／删除 %d／变动 %d ⇒ ★%s" % (len(r["added"]), len(r["removed"]), len(r["changed"]),
              "实质变更「 if real else 」假变更（归一后全 0）"))
        for n in r["added"][:6]: print("         + %s" % n[:80])
        for n in r["removed"][:6]: print("         - %s" % n[:80])
        for n in r["changed"][:6]: print("         ~ %s" % n[:80])
        rows.append({"doc": k, "a": fa.name, "b": fb.name, "real_change": real, **r})
    real_n = sum(1 for r in rows if r["real_change"])
    crit = {"①能读到最新通知": bool(nf), "②能取到该档 ≥2 版": len(rows) > 0, "③★裁决已给出（出件／不出件）": True}
    verdict = ("★有实质变更 ⇒ 出短件（DF-OPS-…），走七步 SOP" if real_n else
               "★全部为假变更（归一后节级差异皆 0）⇒ ★只台账一行，不出短件")
    print("   ⇒ 裁决：%s（实质变更 %d／受检 %d）" % (verdict, real_n, len(rows)))
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "notify": latest.name, "docs": rows, "real_change_count": real_n, "verdict": verdict,
            "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
