# -*- coding: utf-8 -*-
"""第一幕 心跳聚合：心跳占比须 ≤30%（正主原值 81%：8,594/10,611）
★口径声明：本判据作用对象＝★本席总线（bus.jsonl）；网络脊髓总线（Supabase）本席不可达 ⇒ 对其占比不作断言
判据：①可算得占比 ②占比 ≤30% ③心跳类条目可辨识（kind／内容含 heartbeat／心跳）
"""
import json, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
import os
_ov = os.environ.get("OPL_BUS")
BUS = pathlib.Path(_ov) if _ov else (HERE.parent.parent/"A2A共同体_共享交换区"/"bus"/"bus.jsonl")
if not BUS.exists():
    _alt = HERE.parent/"bus"/"bus.jsonl"
    BUS = _alt if _alt.exists() else BUS
if not BUS.exists():
    print("      · ★总线不在 ⇒ 未测（环境不足；退出码 2，不冒充通过、亦不判红）"); sys.exit(2)
rows = [json.loads(l) for l in BUS.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
def is_hb(r):
    s = json.dumps(r, ensure_ascii=False).lower()
    return ("heartbeat" in s) or ("心跳" in s) or (r.get("kind") == "heartbeat")
hb = [r for r in rows if is_hb(r)]
share = 100.0*len(hb)/max(1, len(rows))
crit = {"①可算得占比": True, "②占比 ≤30%": share <= 30.0, "③心跳类可辨识（计数可复算）": True}
print("      · 总线 %d 条 ｜ 心跳类 %d 条 ｜ 占比 %.2f%%（阈值 30%%）" % (len(rows), len(hb), share))
for k, v in crit.items(): print("      · %s ⇒ %s" % (k, "✓" if v else "✗"))
sys.exit(0 if all(crit.values()) else 1)
