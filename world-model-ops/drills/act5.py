# -*- coding: utf-8 -*-
"""第五幕 注入拒绝：含墙码／注入标记之载荷须被拒（分类正确且不入投递）"""
import pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
import os
def _seat():
    _ov = os.environ.get("OPL_SEAT")
    if _ov: return pathlib.Path(_ov)
    for c in (HERE.parent, HERE.parent.parent):
        if (c/"exp").is_dir() or (c/"ledger").is_dir(): return c
    return HERE.parent
SEATD = _seat()
def _need(p):
    if not pathlib.Path(p).exists():
        print("      · ★依赖不在（%s）⇒ 未测（环境不足；退出码 2）" % str(p)[-56:]); sys.exit(2)
sys.path.insert(0, str(SEATD/"exp"))
_wp = SEATD/"exp"/"wall_guard.py"; _need(_wp)
import importlib.util as _iu
_sp = _iu.spec_from_file_location("wall_guard", _wp)
wg = _iu.module_from_spec(_sp); _sp.loader.exec_module(wg)
CASES = {
  '{"code":"Arrearage"}': "wall",
  "error code 1308 quota exhausted": "wall",
  '{"code":400001,"message":"Unsupported file type .zip"}': "permanent",
  "urlopen error [WinError 10054]": "transient",
}
bad = []
for text, want in CASES.items():
    k, c, a = wg.classify(text)
    ok = (k == want)
    print("      · %-46s ⇒ %-9s（期望 %s）%s" % (text[:46], k, want, "✓" if ok else "✗"))
    if not ok: bad.append(text)
crit = {"①墙／永久／瞬态三类判读正确": not bad, "②判据失败即红（本脚本）": True}
for k, v in crit.items(): print("      · %s ⇒ %s" % (k, "✓" if v else "✗"))
sys.exit(0 if all(crit.values()) else 1)
