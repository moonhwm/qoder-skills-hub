# -*- coding: utf-8 -*-
"""add_docstring.py —— 为"无文档串"之器补一行文档串（2026-10-12 立，应 -1319 之判）
做法（★三件套：备份 ＋ 干跑编译 ＋ 失败回退）：
  ① 备份至 _docstr_backup_20261013/；② 在文件首个非 shebang/coding 行之前插入所给文档串；
  ③ 干跑编译（py_compile）⇒ 失败即回退；④ 报每支之结果
判据（可失败）：①每支皆有结果；②失败者已回退；③编译通过数已给
用法：python add_docstring.py --map <json> [--run]
  map 形如 {"tool_name": "一行文档串", …}
（中文串一律用「」）
"""
import argparse, json, pathlib, py_compile, shutil, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
BAK = SEAT/"_docstr_backup_20261013"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--map", required=True)
    ap.add_argument("--dir", default="")
    ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    mp = json.loads(pathlib.Path(a.map).read_text(encoding="utf-8-sig"))
    root = pathlib.Path(a.dir) if a.dir else (pathlib.Path.home()/"openplanlink-cairn"/"tools")
    if a.run: BAK.mkdir(exist_ok=True)
    print("  ═══ 补文档串（★备份＋干跑＋回退）═══")
    ok = fail = skip = 0
    for name, doc in mp.items():
        p = root/(name + ".py")
        if not p.exists():
            print("   ★%-30s 不在" % name); skip += 1; continue
        t = p.read_text(encoding="utf-8-sig", errors="replace")
        lines = t.splitlines(keepends=True)
        ins = 0
        for i, l in enumerate(lines[:6]):
            s = l.strip()
            if s.startswith("#!") or "coding" in s or not s:
                ins = i + 1; continue
            break
        if '"""' in "".join(lines[:ins+2]):
            print("   · %-30s 疑已有文档串（跳过）" % name); skip += 1; continue
        new = "".join(lines[:ins]) + '"""%s"""\n' % doc + "".join(lines[ins:])
        if not a.run:
            print("   · %-30s 将插于 L%d 之后（dry-run）" % (name, ins)); continue
        tmp = root/("_dry_ds_"+name+".py")
        tmp.write_text(new, encoding="utf-8", newline="\n")
        try:
            py_compile.compile(str(tmp), doraise=True); tmp.unlink()
            shutil.copy2(p, BAK/(name + ".py"))
            p.write_text(new, encoding="utf-8", newline="\n")
            py_compile.compile(str(p), doraise=True)
            print("   ✓ %-30s 已补（L%d 之后）" % (name, ins)); ok += 1
        except Exception as ex:
            tmp.unlink(missing_ok=True)
            if (BAK/(name+".py")).exists(): shutil.copy2(BAK/(name+".py"), p)
            print("   ✗ %-30s 失败已回退：%s" % (name, str(ex)[:50])); fail += 1
    print("   ── 判据 ──")
    print("   ①每支皆有结果 ⇒ %s" % ("✓" if (ok+fail+skip) == len(mp) else "✗"))
    print("   ②失败者已回退 ⇒ %s" % ("✓" if fail == 0 else "★有 %d 支失败" % fail))
    print("   ③★已补 %d ｜ 跳过 %d ｜ 失败 %d" % (ok, skip, fail))
    print("   ⇒ 备份在 %s" % BAK.name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
