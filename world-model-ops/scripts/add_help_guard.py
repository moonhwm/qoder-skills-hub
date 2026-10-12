# -*- coding: utf-8 -*-
"""add_help_guard.py —— 为"无参数解析 × 有副作用"之器补 -h 自护（2026-10-12 立，应 -1282 之判）
做法（★最小侵入、可回退）：对指定器物：
  ① 找"最后一个顶层 import／from 行"⇒ ★在其后插守卫（★确保在任何副作用之前）
  ② 守卫：若 argv 含 -h／--help ⇒ 打印用法与"本器有副作用"之警告后 sys.exit(0)
  ③ ★确保 sys 已导入（否则补 import sys）
  ④ 干跑编译 ⇒ 失败则回退（★三件套）
判据（可失败）：①每支皆有干跑编译结果；②插入点已报；③★失败者已回退
用法：python add_help_guard.py tool1.py tool2.py … [--run]
（中文串一律用「」）
"""
import argparse, pathlib, py_compile, re, shutil, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
BAK = SEAT/"_helped_backup_20261012"

GUARD = '''

# ★2026-10-12 参数卫生（应 -1282 之判）：本器原无参数解析 ⇒ 任何参数（含 -h／--help）皆被忽略而主流程照跑
#   ⇒ ★-h／--help 须只示帮助、不执行主流程（★本器有副作用：见其自身说明）
if any(x in ("-h", "--help") for x in sys.argv):
    print("用法：python %s [参数]  ★-h／--help 只示帮助，不执行主流程（本器有副作用）" % __file__.split("\\\\")[-1])
    sys.exit(0)
'''


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tools", nargs="+"); ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    BAK.mkdir(exist_ok=True)
    print("  ═══ 补 -h 自护（★最小侵入；干跑编译＋失败回退）═══")
    for name in a.tools:
        p = SEAT/name
        if not p.exists():
            print("   ★%-30s 不在" % name); continue
        t = p.read_text(encoding="utf-8")
        if "只示帮助，不执行主流程" in t:
            print("   · %-30s 已有守卫（跳过）" % name); continue
        lines = t.splitlines(keepends=True)
        last_imp = -1
        for i, l in enumerate(lines):
            if re.match(r"^(import |from )\S", l): last_imp = i
        if last_imp < 0:
            print("   ★%-30s 未找到顶层 import（跳过，须人工）" % name); continue
        need_sys = not re.search(r"^import .*\bsys\b|^import sys", t, re.M)
        add = GUARD.replace("sys.argv", "sys.argv")
        new = "".join(lines[:last_imp+1]) + add + "".join(lines[last_imp+1:])
        if need_sys:
            marker = 'if any(x in ("-h", "--help") for x in sys.argv):'
            new = new.replace(marker, "import sys\n\n" + marker, 1)
        if not a.run:
            print("   · %-30s 将插于 L%d 之后（dry-run）｜ 需补 import sys=%s" % (name, last_imp+1, need_sys)); continue
        tmp = SEAT/("_dry_guard_"+name)
        tmp.write_text(new, encoding="utf-8", newline="\n")
        try:
            py_compile.compile(str(tmp), doraise=True); tmp.unlink()
            shutil.copy2(p, BAK/name)
            p.write_text(new, encoding="utf-8", newline="\n")
            py_compile.compile(str(p), doraise=True)
            print("   ✓ %-30s 已插守卫（L%d 之后；补 sys=%s）" % (name, last_imp+1, need_sys))
        except Exception as ex:
            tmp.unlink(missing_ok=True)
            if (BAK/name).exists(): shutil.copy2(BAK/name, p)
            print("   ✗ %-30s 失败已回退：%s" % (name, str(ex)[:60]))
    print("   ⇒ 备份在 %s" % BAK.name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
