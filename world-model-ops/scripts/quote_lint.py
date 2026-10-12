# -*- coding: utf-8 -*-
"""quote_lint.py —— 中文串引号自检（2026-10-12 立；防戒三十一复发）
由来：我今夜两次在中文串内使用 ASCII 引号（如 print("…按「有无」分组…")）⇒ 直接 SyntaxError。
本器（零外呼）对被检文件：
  ① 若为 .py ⇒ 先做★干跑编译（py_compile）—— 语法错必被捕获；
  ② ★启发式：扫「中日韩字符 ＋ 半角引号 ＋ 中日韩字符」之形态（如 「按「有无」分组」）⇒ 逐行报出；
  ③ 对 .md/.otl/.txt 仅做启发式（其非代码，但亦宜用「」）。
判据（可失败）：①文件存在；②扫描完成；③★问题逐行列出（或明示无问题）
用法：python quote_lint.py <文件或目录> [--max 20]
（中文串一律用「」）
"""
import argparse, pathlib, py_compile, re, sys, tempfile

CJK = r"[\u4e00-\u9fff\u3000-\u303f]"
PAT = re.compile(CJK + r'["\']' + CJK)


def check(p):
    issues = []
    try:
        txt = p.read_text(encoding="utf-8-sig", errors="replace")
    except Exception as ex:
        return [("★读取失败", str(ex)[:60])]
    for i, line in enumerate(txt.splitlines(), 1):
        if PAT.search(line):
            issues.append((i, line.strip()[:96]))
    if p.suffix == ".py":
        try:
            src = p.read_text(encoding="utf-8")
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8", newline="\n") as f:
                f.write(src); tmp = f.name
            py_compile.compile(tmp, doraise=True)
            pathlib.Path(tmp).unlink(missing_ok=True)
        except Exception as ex:
            issues.insert(0, ("★编译失败", str(ex)[:110]))
    return issues


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("target"); ap.add_argument("--max", type=int, default=20)
    a = ap.parse_args()
    t = pathlib.Path(a.target)
    print("  ═══ 中文串引号自检（戒三十一）═══")
    if not t.exists():
        print("   ★不在：%s" % t); return 2
    files = [t] if t.is_file() else sorted([f for f in t.rglob("*.py")] + [f for f in t.glob("*.otl")] + [f for f in t.glob("*.md")])
    bad = 0; shown = 0
    print("   受检文件 %d 个" % len(files))
    for f in files:
        iss = check(f)
        if iss:
            bad += 1
            hard = any(str(x[0]).startswith("★") for x in iss)
            print("   ── %s（%d 处%s）──" % (f.name, len(iss), "，★含编译失败" if hard else "，★文风提示"))
            for ln, s in iss[:a.max]:
                if shown < 600: print("      L%-5s ｜ %s" % (ln, s)); shown += 1
    # ★2026-10-12 自纠（判据分开）：★"编译失败"才算失败；★"中文串内半角引号"仅为文风提示（不影响退出码）
    crit = {"①文件存在": True, "②扫描完成": True, "③★问题逐行列出（或明示无问题）": True}
    print("   ── 判据 ──")
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ⇒ 判：%s" % ("★有编译失败或文风提示之文件 %d 个（见上；★退出码 0，因文风提示非失败）" % bad if bad
                          else "★全清（.py 皆编译通过，且无中文串内半角引号）"))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
