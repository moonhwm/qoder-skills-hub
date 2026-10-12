# -*- coding: utf-8 -*-
"""rig_audit.py —— 骨格与绑定审计（应《席位分身3D资产 Unity 规范》之「2.3 骨骼与 Rig」）
检查：①skin 存在 ②joints 数 ③骨名 ④层级（父子） ⑤根节点是否在原点 ⑥单位（米） ⑦是否含 inverseBindMatrices ⑧与"人形骨名惯例"之覆盖率
用法：python rig_audit.py --in <glb> [--json out.json]
（中文串一律用「」）
"""
import argparse, json, pathlib, struct, sys
import numpy as np

def parse(p):
    b = pathlib.Path(p).read_bytes(); ln = struct.unpack("<I", b[8:12])[0]; off = 12; J = None; B = b""
    while off < ln:
        cl, ct = struct.unpack("<II", b[off:off+8]); d = b[off+8:off+8+cl]
        if ct == 0x4E4F534A: J = json.loads(d.decode("utf-8", "replace"))
        elif ct == 0x004E4942: B = d
        off += 8 + cl
    return J, B

HUMAN = ["pelvis", "spine", "chest", "neck", "head", "shoulder", "arm", "forearm", "hand", "thigh", "shin", "foot"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--json", default="")
    a = ap.parse_args()
    J, B = parse(a.inp)
    nodes, skins = J.get("nodes", []), J.get("skins", [])
    print("  ═══ 骨格与绑定审计 ｜ %s ═══" % pathlib.Path(a.inp).name)
    print("   节点 %d ｜ skin %d ｜ 动画 %d ｜ 网格 %d" % (len(nodes), len(skins), len(J.get("animations", [])), len(J.get("meshes", []))))
    if not skins:
        print("   ★无 skin ⇒ 本件为静态几何（无绑定）⇒ 判据①②③不适用"); sys.exit(2)
    sk = skins[0]; joints = sk.get("joints", [])
    names = [str(nodes[i].get("name", "?")) for i in joints]
    root_i = joints[0] if joints else None
    root_t = nodes[root_i].get("translation") if root_i is not None else None
    has_ibm = "inverseBindMatrices" in sk
    # 层级：统计父节点中有子者
    children = {i: nodes[i].get("children", []) for i in joints if "children" in nodes[i]}
    depth = {}
    def walk(i, d):
        depth[i] = d
        for c in nodes[i].get("children", []):
            if c in joints: walk(c, d+1)
    if joints: walk(joints[0], 0)
    cov = [h for h in HUMAN if any(h in n.lower() for n in names)]
    # ★修正（2026-10-12）：人形骨架之根（pelvis）本就在髋高 ⇒ "根在原点"不成立；
    #   正确判据＝"网格最低点 y ≈ 0（脚底贴地）"＋"根在合理髋高（0.5–1.2 m）"
    min_y = None
    try:
        import struct as _st
        for m in J.get("meshes", []):
            for pr in m.get("primitives", []):
                a2 = J["accessors"][pr["attributes"]["POSITION"]]
                if "min" in a2:
                    min_y = a2["min"][1] if min_y is None else min(min_y, a2["min"][1])
    except Exception:
        pass
    root_h = (root_t[1] if (root_t and len(root_t) > 1) else None)
    crit = {"①有 skin": True, "②joints ≥ 6": len(joints) >= 6, "③骨名可读": all(n != "?" for n in names),
            "④有层级（父>子）": any(v for v in children.values()),
            "⑤网格最低点 y ≈ 0（脚底贴地；实测 %s）" % ("%.3f" % min_y if min_y is not None else "不可评"): (min_y is not None and abs(min_y) <= 0.05),
            "⑥根（骨盆）在合理髋高 0.5–1.2 m（实测 %s）" % ("%.3f" % root_h if root_h is not None else "—"): (root_h is None or 0.5 <= root_h <= 1.2),
            "⑦含 inverseBindMatrices": has_ibm, "⑧人形骨名覆盖 ≥5 项": len(cov) >= 5}
    print("   ★正名：人形骨架之根＝骨盆，位于髋高（非原点）是常态；判据改看「网格最低点 y」与「根之髋高区间」")
    print("   joints %d ｜ 根「%s」translation=%s ｜ 层级深度 max=%d ｜ IBM=%s" % (
        len(joints), names[0] if names else "—", root_t, max(depth.values()) if depth else 0, has_ibm))
    print("   骨名：%s" % "、".join(names[:12]))
    print("   人形骨名覆盖 %d 项：%s" % (len(cov), "、".join(cov)))
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"file": pathlib.Path(a.inp).name, "joints": len(joints),
            "names": names, "root_translation": root_t, "max_depth": (max(depth.values()) if depth else 0),
            "ibm": has_ibm, "human_cov": cov, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    sys.exit(0 if all(crit.values()) else 1)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
