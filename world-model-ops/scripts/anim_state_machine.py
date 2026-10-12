# -*- coding: utf-8 -*-
"""anim_state_machine.py —— 动画状态机（应《席位分身3D资产 Unity 规范》之「2.6 动画状态机」）
做法：①读 GLB 之动画名（clips）②按声明之状态表建状态机（状态／入口／转移／默认参数）③校验"每个 clip 皆被状态机覆盖"④输出 Unity 可消费之 JSON
用法：python anim_state_machine.py --in <glb> [--out state_machine.json]
（中文串一律用「」）
"""
import argparse, json, pathlib, struct, sys

def clips(p):
    b = pathlib.Path(p).read_bytes(); ln = struct.unpack("<I", b[8:12])[0]; off = 12; J = None
    while off < ln:
        cl, ct = struct.unpack("<II", b[off:off+8])
        if ct == 0x4E4F534A: J = json.loads(b[off+8:off+8+cl].decode("utf-8", "replace"))
        off += 8 + cl
    return [str(a.get("name", "clip%d" % i)) for i, a in enumerate(J.get("animations", []))]

# ★状态表（依本席人设语义；参数：speed／verify／refuse）
SPEC = {
 "states": {
   "IDLE":   {"clip": "IDLE_VERIFY", "loop": True,  "note": "在场待命，周期性自检"},
   "VERIFY": {"clip": "IDLE_VERIFY", "loop": False, "note": "核验动作"},
   "WEIGH":  {"clip": "WEIGH",  "loop": False, "note": "权衡／打分"},
   "INSPECT":{"clip": "INSPECT","loop": False, "note": "查验"},
   "RELAY":  {"clip": "RELAY",  "loop": False, "note": "转达／推送"},
   "REFUSE": {"clip": "REFUSE", "loop": False, "note": "拒绝（墙／红线）"},
   "WALK":   {"clip": "WALK",   "loop": True,  "note": "移动"}
 },
 "params": {"speed": {"type": "float", "default": 0.0}, "busy": {"type": "bool", "default": False}},
 "transitions": [
   {"from": "IDLE", "to": "WALK",   "when": "speed > 0.1"},
   {"from": "WALK", "to": "IDLE",   "when": "speed <= 0.1"},
   {"from": "IDLE", "to": "VERIFY", "when": "trigger:verify"},
   {"from": "IDLE", "to": "WEIGH",  "when": "trigger:judge"},
   {"from": "IDLE", "to": "INSPECT","when": "trigger:inspect"},
   {"from": "IDLE", "to": "RELAY",  "when": "trigger:relay"},
   {"from": "*",    "to": "REFUSE", "when": "trigger:refuse（墙／红线，优先级最高）"},
   {"from": "REFUSE","to": "IDLE",  "when": "trigger:clear"}
 ]
}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--out", default="")
    a = ap.parse_args()
    cs = clips(a.inp)
    print("  ═══ 动画状态机 ｜ %s ═══" % pathlib.Path(a.inp).name)
    print("   GLB 内 clips（%d）：%s" % (len(cs), "、".join(cs)))
    used = {v["clip"] for v in SPEC["states"].values()}
    uncovered = [c for c in cs if c not in used]
    missing = [u for u in used if u not in cs]
    crit = {"①clips 全部被状态覆盖": not uncovered, "②状态机所引 clip 皆存在": not missing,
            "③有默认状态与复位转移": ("IDLE" in SPEC["states"]) and any(t["to"] == "IDLE" for t in SPEC["transitions"]),
            "④有高优先级中断（REFUSE from *）": any(t["from"] == "*" for t in SPEC["transitions"])}
    if uncovered: print("   ★未被覆盖之 clip：%s" % "、".join(uncovered))
    if missing: print("   ★状态机引用而 GLB 缺失之 clip：%s" % "、".join(missing))
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    out = {"schema": "cairn-anim-sm/1", "source": pathlib.Path(a.inp).name, "clips": cs, **SPEC, "criteria": crit}
    p = pathlib.Path(a.out) if a.out else (pathlib.Path(a.inp).parent/"anim_state_machine.json")
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   ✓ 已写 %s" % p.name)
    sys.exit(0 if all(crit.values()) else 1)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
