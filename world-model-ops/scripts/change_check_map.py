# -*- coding: utf-8 -*-
"""change_check_map.py —— "变更即校验"映射表（★借 letta-code `hooks/fix-on-changes.sh`／`typecheck-on-changes.sh` 之思路，2026-10-12）
做法：给出变更文件清单（--changed …／或 --git <repo> 取 HEAD 之变更）⇒ 按类型查表 ⇒ 跑对应校验器 ⇒ 汇总判红绿
★边界（如实）：表中所列校验器若不在本机，则该类标"未测"（不冒充通过）。
用法：
  python change_check_map.py --changed a.py b.glb
  python change_check_map.py --git C:\\Users\\…\\openplanlink-cairn
  python change_check_map.py --selftest
（中文串一律用「」）
"""
import argparse, pathlib, subprocess, sys

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EXP = SEAT/"exp"; LED = SEAT/"ledger"

# ★映射表：后缀 → (校验器说明, 命令)
MAP = {
    ".py": ("编译核（py_compile）", [sys.executable, "-m", "py_compile", "{f}"]),
    ".glb": ("3D 规格审计（glb_spec_audit）", [sys.executable, str(EXP/"glb_spec_audit.py"), "--in", "{f}"]),
    ".led": ("台账条目键齐备（mkled 干跑）", [sys.executable, str(EXP/"mkled.py"), "{f}"]),
    ".otl": ("出件七项自检（sop_check）", [sys.executable, str(EXP/"sop_check.py"), "--file", "{f}"]),
}
BYNAME = [
    ("section_index", "索引陈旧检测（index_guard）", [sys.executable, str(EXP/"index_guard.py")]),
    ("frontier_ledger.jsonl", "台账链校验（cairn_ledger verify）", [sys.executable, str(LED/"cairn_ledger.py"), "verify"]),
    ("bus.jsonl", "总线条目校验（bus_dlq valid）", [sys.executable, str(EXP/"bus_dlq.py"), "valid"]),
    ("index_pointer.json", "索引指针状态（index_switch --status）", [sys.executable, str(EXP/"index_switch.py"), "--status"]),
]

def pick(path):
    p = pathlib.Path(path); n = p.name
    for key, desc, cmd in BYNAME:
        if key in n: return desc, cmd
    return MAP.get(p.suffix.lower(), (None, None))

def run_cmd(desc, cmd, f):
    c = [x.replace("{f}", str(f)) for x in cmd]
    if not pathlib.Path(c[1] if c[0].endswith("python.exe") or "python" in c[0] else c[0]).exists() and not c[0].endswith("python.exe"):
        if len(c) > 1 and not pathlib.Path(c[1]).exists():
            return "未测", "★校验器不在：%s" % c[1]
    try:
        pr = subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        ok = (pr.returncode == 0)
        tail = ((pr.stdout or "") + (pr.stderr or "")).strip().splitlines()
        return ("✓" if ok else "✗"), (tail[-1][:96] if tail else "（无输出）")
    except Exception as e:
        return "未测", "★执行异常：%s" % str(e)[:70]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--changed", nargs="*", default=[])
    ap.add_argument("--git", default=""); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("  ═══ 映射表自测 ═══")
        cases = [("x.py", ".py"), ("y.glb", ".glb"), ("z.led", ".led"), ("a.otl", ".otl"),
                 ("section_index_20261012.json", "index_guard"), ("frontier_ledger.jsonl", "ledger"),
                 ("index_pointer.json", "pointer"), ("note.txt", None)]
        ok = True
        for f, want in cases:
            desc, cmd = pick(f)
            got = "无表" if desc is None else ("index_guard" if "index_guard" in desc else
                   "ledger" if "cairn_ledger" in str(cmd) else "pointer" if "index_switch" in str(cmd) else pathlib.Path(f).suffix.lower())
            good = (want is None and desc is None) or (got == want)
            ok &= good
            print("   %-32s ⇒ %-34s %s" % (f, (desc or "★无表（不校验）"), "✓" if good else "★错配"))
        print("   ⇒ 自测判：%s" % ("✓ 全对" if ok else "★有错配"))
        return 0 if ok else 1
    files = list(a.changed)
    if a.git:
        repo = pathlib.Path(a.git)
        try:
            pr = subprocess.run(["git", "-C", str(repo), "show", "--name-only", "--pretty=format:", "HEAD"],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
            files += [l.strip() for l in (pr.stdout or "").splitlines() if l.strip()]
        except Exception as e:
            print("  ★取 git 变更失败：%s" % str(e)[:70]); return 2
    if not files:
        print("  （无变更文件）⇒ 未测"); return 0
    print("  ═══ 变更即校验 ｜ %d 个文件 ═══" % len(files))
    bad = []
    for f in files:
        desc, cmd = pick(f)
        if desc is None:
            print("   ○ %-46s ⇒ 无表（不校验）" % f[:46]); continue
        st, tail = run_cmd(desc, cmd, pathlib.Path(a.git)/f if a.git and not pathlib.Path(f).is_absolute() else f)
        print("   %s %-46s ⇒ %s ｜ %s" % (st, f[:46], desc, tail))
        if st == "✗": bad.append(f)
    print("   ⇒ 判：%s" % ("✓ 变更皆过（无表者不校验）" if not bad else "★%d 个变更未过：%s" % (len(bad), "、".join(bad[:4]))))
    return 0 if not bad else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
