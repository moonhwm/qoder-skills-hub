# -*- coding: utf-8 -*-
"""glb_spec_audit.py —— 以 persona-iteration-loop-ops/references/modeling-3d-materials.md 之口径核本席 3D 资产
★零依赖：直接解 GLB（header＋JSON chunk＋BIN chunk）
输出：三角面数／LOD 比例／UV 有无／贴图数／材质 PBR 参数／骨数／动画／包围盒尺度（米）
（中文串一律用「」）
"""
import json, pathlib, struct, sys

def load_glb(p):
    b = pathlib.Path(p).read_bytes()
    if b[:4] != b"glTF": return None, None
    ver, length = struct.unpack("<II", b[4:12])
    off, j, binlen = 12, None, 0
    while off < length:
        clen, ctype = struct.unpack("<II", b[off:off+8])
        data = b[off+8:off+8+clen]
        if ctype == 0x4E4F534A: j = json.loads(data.decode("utf-8", "replace"))
        elif ctype == 0x004E4942: binlen = clen
        off += 8 + clen
    return j, binlen

def tris(j):
    n = 0
    for m in j.get("meshes", []):
        for pr in m.get("primitives", []):
            idx = pr.get("indices")
            if idx is not None:
                n += j["accessors"][idx]["count"] // 3
            else:
                pa = pr.get("attributes", {}).get("POSITION")
                if pa is not None: n += j["accessors"][pa]["count"] // 3
    return n

def bbox(j):
    lo = [1e9]*3; hi = [-1e9]*3
    for m in j.get("meshes", []):
        for pr in m.get("primitives", []):
            a = j["accessors"][pr["attributes"]["POSITION"]]
            if "min" in a and "max" in a:
                for k in range(3):
                    lo[k] = min(lo[k], a["min"][k]); hi[k] = max(hi[k], a["max"][k])
    return [round(hi[k]-lo[k], 4) for k in range(3)] if hi[0] > -1e8 else None

SEAT = pathlib.Path.home()/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
TARGETS = []
for pat in ("*LOD*_v2_20261011.glb", "*avatar*.glb"):
    TARGETS += sorted(SEAT.rglob(pat))
TARGETS = list(dict.fromkeys(TARGETS))
print("  ═══ 本席 GLB 资产（%d 件）═══" % len(TARGETS))
for p in TARGETS:
    j, binlen = load_glb(p)
    if j is None: print("   %-52s ★非 GLB" % p.name[:52]); continue
    t = tris(j)
    imgs = j.get("images", []); mats = j.get("materials", []); sk = j.get("skins", [])
    anims = j.get("animations", [])
    has_uv = any("TEXCOORD_0" in pr.get("attributes", {}) for m in j.get("meshes", []) for pr in m.get("primitives", []))
    joints = len(sk[0].get("joints", [])) if sk else 0
    bb = bbox(j)
    print("   %-50s ｜ tris %6d ｜ 骨 %2d ｜ 动画 %d ｜ UV %s ｜ 贴图 %d ｜ 材质 %d ｜ bbox %s" % (
        p.name[:50], t, joints, len(anims), "✓" if has_uv else "✗", len(imgs), len(mats), bb))
    for mt in mats[:2]:
        pb = (mt.get("pbrMetallicRoughness") or {})
        print("        材质「%s」baseColor %s ｜ metal %s ｜ rough %s" % (
            str(mt.get("name"))[:18], "有" if pb.get("baseColorTexture") else "无",
            pb.get("metallicFactor"), pb.get("roughnessFactor")))
print("\n  ═══ 规范口径对照（modeling-3d-materials.md v1.0.0）═══")
print("   面数分档：手游低模 1.5k–5k tris｜手游主角 10k–20k｜主机 20k–40k（+发饰 5k–15k）｜影视 150k+")
print("   UV/TD：hero 10.24–20.48 px/cm；LOD 逐级减半（10.24→5.12→2.56）")
print("   PBR：Albedo 2K–4K／Normal 切线空间／Roughness 同级／Metalness 0-1／AO 1K–4K")
