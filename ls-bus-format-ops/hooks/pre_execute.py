#!/usr/bin/env python3
"""A2A hooks pack · pre_execute（否决相位）
外部独立硬闸：「先留痕后删除」从流程纪律升级为技术闸——
核验 $LBF_RUNS_DIR/bus_receipt.json 存在且其 manifest_sha256 与本次一致、带总线 id；
缺席/不符 → exit 1 否决（零删除）。"""
import json, os, sys

runs_dir = os.environ.get("LBF_RUNS_DIR", "")
mhash = os.environ.get("LBF_MANIFEST_SHA256", "")
rcpt_path = os.path.join(runs_dir, "bus_receipt.json")
try:
    with open(rcpt_path, encoding="utf-8") as f:
        rcpt = json.load(f)
except Exception as e:
    print(f"VETO: 总线回执缺席/不可读（{rcpt_path}: {e}）——先留痕后删除", file=sys.stderr)
    sys.exit(1)
if rcpt.get("manifest_sha256") != mhash or not rcpt.get("bus_id"):
    print(f"VETO: 回执与清单不符（receipt={rcpt.get('manifest_sha256','')[:16]}… "
          f"vs manifest={mhash[:16]}…, bus_id={rcpt.get('bus_id')}）", file=sys.stderr)
    sys.exit(1)
print(f"OK: 总线回执核验通过 bus_id={rcpt['bus_id']}")
sys.exit(0)
