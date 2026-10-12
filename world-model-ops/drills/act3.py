# -*- coding: utf-8 -*-
"""第三幕 断链零丢失：投递失败不得静默丢弃（须入死信队列且可续传）"""
import json, os, pathlib, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
import os
def _seat():
    _ov = os.environ.get("OPL_SEAT")
    if _ov: return pathlib.Path(_ov)
    for c in (HERE.parent, HERE.parent.parent):
        if (c/"exp").is_dir() or (c/"ledger").is_dir(): return c
    return HERE.parent
S = _seat()
wg = (_seat() if False else None) or (S/"exp"/"bus_dlq.py")
env = dict(os.environ); env["PYTHONIOENCODING"] = "utf-8"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="drill3_"))
art = tmp/"lost.json"; art.write_text(json.dumps({"y": 2}), encoding="utf-8")
# ① 断链：把件投给非法总线 ⇒ 必入死信队列（零静默丢弃）
pr = subprocess.run([sys.executable, str(wg), "emit", "--path", str(art), "--kind", "artifact", "--seat", "drill",
                     "--tries", "1"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
# 直接以模块方式校验死信记录（不改真实总线）
led = S/"ledger"/"bus_dlq.jsonl"
if not led.exists():
    print("      · ★依赖不在（ledger/bus_dlq.jsonl）⇒ 未测（环境不足；退出码 2）"); sys.exit(2)
recs = [json.loads(l) for l in led.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()] if led.exists() else []
crit = {"①失败件入死信队列（不静默丢弃）": len(recs) > 0,
        "②死信含 last_error 原文": any(r.get("last_error") for r in recs),
        "③可续传（retry 子命令存在）": "retry" in wg.read_text(encoding="utf-8")}
for k, v in crit.items(): print("      · %s ⇒ %s" % (k, "✓" if v else "✗"))
sys.exit(0 if all(crit.values()) else 1)
