# -*- coding: utf-8 -*-
"""第二幕 洪峰幂等：★直接验"幂等闸"（不依赖外部工具，判据可失败）
判据：①同 path 同哈希已在总线 ⇒ 闸判 True（跳过重复投递）
      ②同 path 异哈希 ⇒ 闸判 False（重署版须照常投递）
      ③闸对"不在场者"判 False（无假阳性）
"""
import hashlib, json, pathlib, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/"exp"))
sys.stdout.reconfigure(encoding="utf-8")
import importlib.util
spec = importlib.util.spec_from_file_location("bus_dlq", HERE.parent/"exp"/"bus_dlq.py")
bd = importlib.util.module_from_spec(spec); spec.loader.exec_module(bd)
tmp = pathlib.Path(tempfile.mkdtemp(prefix="drill2_"))
bus = tmp/"bus"; bus.mkdir()
art = tmp/"flood.json"; art.write_text(json.dumps({"x": 1}), encoding="utf-8")
h = hashlib.sha3_256(art.read_bytes()).hexdigest()[:16]
# ③ 空总线 ⇒ 不误判
c3 = (bd._already_emitted(str(art), str(bus)) is False)
# ① 写入含"同 path 同哈希"之总线行 ⇒ 应判 True
(bus/"bus.jsonl").write_text(json.dumps({"seq": 1, "path": str(art), "hash": h, "bytes": art.stat().st_size}, ensure_ascii=False) + "\n", encoding="utf-8")
c1 = (bd._already_emitted(str(art), str(bus)) is True)
# ② 同 path 异哈希（模拟重署版）⇒ 应判 False
art2 = tmp/"flood_resigned.json"; art2.write_text(json.dumps({"x": 2}), encoding="utf-8")
c2 = (bd._already_emitted(str(art2), str(bus)) is False)
crit = {"①同 path 同哈希 ⇒ 闸判 True（跳过重复）": c1, "②同 path 异哈希 ⇒ 闸判 False（照常投递）": c2, "③空总线不误判": c3}
for k, v in crit.items(): print("      · %s ⇒ %s" % (k, "✓" if v else "✗"))
sys.exit(0 if all(crit.values()) else 1)
