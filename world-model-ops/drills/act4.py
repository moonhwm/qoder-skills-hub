# -*- coding: utf-8 -*-
"""第四幕 升级面 60 秒：★升级后 ≤60 s 恢复且零丢失
做法（本地可复算）：①记前态（台账条目数、总线条目数）②施加一次"良性升级标记"（写版本戳）
③跑验收套件（台账 verify ＋ 第二/三/五幕）④度量耗时 ⑤核零丢失（两计数不减）
判据：①耗时 ≤60 s ②台账条目不减 ③总线条目不减 ④验收套件全绿
"""
import json, pathlib, subprocess, sys, time
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
import os
_ovl = os.environ.get("OPL_LEDGER")
LED = pathlib.Path(_ovl) if _ovl else (S/"ledger"/"frontier_ledger.jsonl")
BUS = pathlib.Path(os.environ["OPL_BUS"]) if os.environ.get("OPL_BUS") else (S.parent/"A2A共同体_共享交换区"/"bus"/"bus.jsonl")
def n(p): return len(p.read_text(encoding="utf-8", errors="replace").splitlines()) if p.exists() else -1
n_led0, n_bus0 = n(LED), n(BUS)
if n_led0 < 0 or n_bus0 < 0:
    print("      · ★台账或总线不在 ⇒ 未测（环境不足；退出码 2）")
    sys.exit(2)
t0 = time.time()
# ② 良性升级标记（只增不改；不删任何既有）
stamp = S/"ledger"/"upgrade_stamp.jsonl"
with open(stamp, "a", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "event": "upgrade_drill", "note": "第四幕：升级面演练（良性标记）"}, ensure_ascii=False) + "\n")
# ③ 验收套件：台账 verify ＋ 三幕
r1 = subprocess.run([sys.executable, str(S/"ledger"/"cairn_ledger.py"), "verify"], capture_output=True, text=True, encoding="utf-8", errors="replace")
r2 = subprocess.run([sys.executable, str(HERE/"run_drills.py"), "--act", "2"], capture_output=True, text=True, encoding="utf-8", errors="replace")
r3 = subprocess.run([sys.executable, str(HERE/"run_drills.py"), "--act", "3"], capture_output=True, text=True, encoding="utf-8", errors="replace")
r4 = subprocess.run([sys.executable, str(HERE/"run_drills.py"), "--act", "5"], capture_output=True, text=True, encoding="utf-8", errors="replace")
el = time.time()-t0
n_led1, n_bus1 = n(LED), n(BUS)
crit = {"①耗时 ≤60 s": el <= 60.0, "②台账条目不减": n_led1 >= n_led0, "③总线条目不减": n_bus1 >= n_bus0,
        "④验收套件全绿（台账链＋三幕）": ("PASS" in (r1.stdout or "")) and all(r.returncode == 0 for r in (r2, r3, r4))}
print("      · 耗时 %.2f s ｜ 台账 %d→%d ｜ 总线 %d→%d" % (el, n_led0, n_led1, n_bus0, n_bus1))
for k, v in crit.items(): print("      · %s ⇒ %s" % (k, "✓" if v else "✗"))
sys.exit(0 if all(crit.values()) else 1)
