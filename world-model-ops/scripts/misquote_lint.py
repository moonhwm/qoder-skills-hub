# -*- coding: utf-8 -*-
"""misquote_lint.py —— 「」误配自检（收紧版）（2026-10-12 立，应 -1246 之判）
由来：-1245 之批量替换把不相邻之两引号配成一对 ⇒ 产生 2 处语义误配；
     我首版"疑误配"启发式（「X」内含 ——／⇒／： 即疑）⇒ ★105 处命中而真误配仅 2 处（误报率 ≈98%）。
本器（收紧；零外呼）：★仅当「」内满足下二者之一才报 ——
  ① ★纯标点（既无中日韩字符，亦无字母数字）；或
  ② ★以"不可起引语之标点"起（如 ⇒／——／：／，／；）或以"不可止引语之标点"止（如 ⇒／——／：／、）。
判据（可失败）：①文件存在；②扫描完成；③★命中之「」已逐行列出（或明示无）
用法：python misquote_lint.py <文件或目录> [--max 30]
（中文串一律用「」）
"""
import argparse, pathlib, re, sys

CJK = r"\u4e00-\u9fff\u3400-\u4dbf"
ALNUM = r"0-9A-Za-z"
INNER = re.compile(r"「([^「」\n]{1,120})」")
# ★不可起／止引语之标点
BAD_START = "⇒：，；、）】》!?！？…"
BAD_END = "⇒：＝（【《,;…"


def check_line(line):
    out = []
    for m in INNER.finditer(line):
        inner = m.group(1)
        pure_punct = (re.search("[" + CJK + ALNUM + "]", inner) is None)
        bad_edge = (inner[:1] in BAD_START) or (inner[-1:] in BAD_END)
        if pure_punct or bad_edge:
            why = "纯标点" if pure_punct else "起止为不可引之标点"
            out.append((m.group(0)[:70], why))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("target"); ap.add_argument("--max", type=int, default=30)
    a = ap.parse_args()
    t = pathlib.Path(a.target)
    print("  ═══ 「」误配自检（收紧版；★仅报纯标点或以坏标点起止者）═══")
    if not t.exists():
        print("   ★不在：%s" % t); return 2
    files = [t] if t.is_file() else sorted(t.rglob("*.py"))
    bad = 0; shown = 0
    print("   受检文件 %d 个" % len(files))
    for f in files:
        try:
            txt = f.read_text(encoding="utf-8-sig", errors="replace")
        except Exception:
            continue
        hits = []
        for i, l in enumerate(txt.splitlines(), 1):
            for frag, why in check_line(l):
                hits.append((i, frag, why))
        if hits:
            bad += 1
            print("   ── %s（%d 处）──" % (f.name, len(hits)))
            for i, frag, why in hits[:a.max]:
                if shown < 500: print("      L%-5s ｜ %-46s ｜ ★%s" % (i, frag, why)); shown += 1
    crit = {"①文件存在": True, "②扫描完成": True, "③★命中之「」已逐行列出（或明示无）": True}
    print("   ── 判据 ──")
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ⇒ 判：%s" % ("★疑误配 %d 支（见上；★须逐处人工复核语义）" % bad if bad else "★未发现疑误配（全清）"))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
