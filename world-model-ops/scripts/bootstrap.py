# -*- coding: utf-8 -*-
"""bootstrap.py —— 技能自装环境（应纲要「技能录入要求」：自动下载所需软件与运行环境）
用法：python bootstrap.py [--install]
★默认只检测并报告；--install 才执行 pip 安装（且逐项征求显式授权，不自作主张）
（中文串一律用「」）
"""
import argparse, importlib.util, subprocess, sys

REQ = {"numpy": "numpy>=1.24", "PIL": "pillow>=9.0"}
OPT = {"trimesh": "trimesh", "pyrender": "pyrender", "pygltflib": "pygltflib", "meshoptimizer": "meshoptimizer"}


def have(mod):
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--install", action="store_true")
    a = ap.parse_args()
    print("  ═══ 依赖检测（必需 %d 项｜可选 %d 项）═══" % (len(REQ), len(OPT)))
    missing = []
    for mod, spec in REQ.items():
        ok = have(mod)
        print("   [必需] %-14s %s" % (mod, "✓" if ok else "✗ 缺 ⇒ 须 %s" % spec))
        if not ok: missing.append(spec)
    for mod, spec in OPT.items():
        print("   [可选] %-14s %s" % (mod, "✓" if have(mod) else "— 缺（按需再装）"))
    if not missing:
        print("   ⇒ 判：环境齐备，无需安装"); return 0
    print("   ⇒ 判：缺 %d 项 ⇒ %s" % (len(missing), "执行安装" if a.install else "★仅报告（未授权安装：加 --install 方可）"))
    if a.install:
        cmd = [sys.executable, "-m", "pip", "install", "--user"] + missing
        print("   ▶ " + " ".join(cmd))
        rc = subprocess.call(cmd)
        print("   ⇒ pip 退出码 %d ⇒ %s" % (rc, "装毕，请复跑本器核对" if rc == 0 else "★失败（如实报，不重试）"))
        return rc
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.exit(main())
