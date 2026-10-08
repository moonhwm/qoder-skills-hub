#!/usr/bin/env python3
"""A2A hooks pack · post_scan（观察相位）
链自动化：scan 完成后自动链生 digest 总线 SQL 底稿。
纪律入钩：本钩只生成底稿，绝不执行 SQL——写总线仍须当轮批准。"""
import json, os, subprocess, sys

manifest = os.environ.get("LBF_MANIFEST", "")
runs_dir = os.environ.get("LBF_RUNS_DIR", "")
if not manifest or not runs_dir:
    sys.exit(0)  # 观察相位：上下文缺席不阻断
script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "scripts", "ls_bus_format.py")
if not os.path.isfile(script):
    # 包外直挂场景：从已安装技能位取脚本
    alt = "/app/.user/skills/ls-bus-format-ops/scripts/ls_bus_format.py"
    script = alt if os.path.isfile(alt) else None
if not script:
    print("WARN: post_scan 找不到 ls_bus_format.py，跳过链生", file=sys.stderr)
    sys.exit(0)
r = subprocess.run([sys.executable, script, "bussql", "--manifest", manifest, "--digest"],
                   capture_output=True, text=True)
note = {"phase": "post_scan", "chain": "scan->bussql(digest)",
        "rc": r.returncode, "out": r.stdout.strip()[-400:]}
with open(os.path.join(runs_dir, "chain_note_post_scan.json"), "w", encoding="utf-8") as f:
    json.dump(note, f, ensure_ascii=False, indent=1)
sys.exit(0)
