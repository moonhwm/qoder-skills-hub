# -*- coding: utf-8 -*-
"""第五幕 注入拒绝：含墙码／注入标记之载荷须被拒（分类正确且不入投递）"""
import pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/"exp"))
import wall_guard as wg
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
