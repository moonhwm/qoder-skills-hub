# -*- coding: utf-8 -*-
"""rmem_grade.py —— 可用物理内存分级（应「元处理口径细则」之 A 级项：R_mem 分级）
分级（承令条口径）：M_floor ≈ 1256 MB ｜ 警戒线 819.2 MB ｜ 深警戒 512.0 MB
做法：ctypes 调 GlobalMemoryStatusEx（零依赖、零外部命令）
用法：python rmem_grade.py [--json out]
（中文串一律用「」）
"""
import argparse, ctypes, json, pathlib, sys, time


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def avail_mb():
    st = MEMORYSTATUSEX(); st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        return None, None
    return st.ullAvailPhys / 1048576.0, st.ullTotalPhys / 1048576.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    av, tot = avail_mb()
    print("  ═══ R_mem 分级 ═══")
    if av is None:
        print("   ★取不到内存读数 ⇒ 未测（退出码 2）"); return 2
    floor, warn, deep = 1256.0, 819.2, 512.0
    if av >= floor: grade = "充裕（≥M_floor）"
    elif av >= warn: grade = "正常（≥警戒线）"
    elif av >= deep: grade = "★警戒（低于 819.2，宜收敛并行）"
    else: grade = "★深警戒（低于 512.0，须暂停新后台任务）"
    ok = av >= warn
    print("   可用 %.1f MB ｜ 总 %.1f MB ｜ 分级：%s" % (av, tot, grade))
    print("   门槛：M_floor %.1f ｜ 警戒 %.1f ｜ 深警戒 %.1f ⇒ %s" % (floor, warn, deep, "✓ 在警戒线以上" if ok else "★低于警戒线"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "avail_mb": round(av, 1), "total_mb": round(tot, 1), "grade": grade, "ok": ok,
            "thresholds": {"M_floor": floor, "warn": warn, "deep": deep}}, ensure_ascii=False, indent=1),
            encoding="utf-8", newline="\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
