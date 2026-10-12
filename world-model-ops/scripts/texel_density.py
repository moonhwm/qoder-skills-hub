# -*- coding: utf-8 -*-
"""texel_density.py —— Texel Density 实测与对齐预研（应《席位分身3D资产 Unity 规范》之 2.4／规范口径"hero 10.24–20.48 px/cm"）
口径（★本器所采，可复算）：
  ① 世界表面积 A_world(m²) = Σ 三角面积（由 POSITION 与索引计）
  ② UV 面积 A_uv(∈[0,1]²) = Σ UV 三角面积（绝对面积，非归一化 ⇒ 反映利用与缩放）
  ③ 贴图分辨率 R（取内嵌图最大边长）
  ④ 可用纹素 = R² × A_uv ；世界面积(cm²) = A_world × 10000
  ⑤ ★线性密度 TD(px/cm) = sqrt(可用纹素 / 世界面积cm²)
用法：python texel_density.py --in <glb> [--target 10.24] [--json out]
（中文串一律用「」）
"""
import argparse, io, json, pathlib, struct, sys
import numpy as np
from PIL import Image

def parse(p):
    b = pathlib.Path(p).read_bytes(); ln = struct.unpack("<I", b[8:12])[0]; off = 12; J = None; B = b""
    while off < ln:
        cl, ct = struct.unpack("<II", b[off:off+8]); d = b[off+8:off+8+cl]
        if ct == 0x4E4F534A: J = json.loads(d.decode("utf-8", "replace"))
        elif ct == 0x004E4942: B = d
        off += 8 + cl
    return J, B

def rd(J, B, ai, n):
    a = J["accessors"][ai]; bv = J["bufferViews"][a["bufferView"]]
    dt = {5126: "<f4", 5123: "<u2", 5125: "<u4", 5121: "<u1"}[a["componentType"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride") or (np.dtype(dt).itemsize*n)
    out = np.zeros((a["count"], n), dtype=dt)
    for i in range(a["count"]): out[i] = np.frombuffer(B, dtype=dt, count=n, offset=start+i*stride)
    return out.astype(np.float32)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--target", type=float, default=10.24)
    ap.add_argument("--json", default=""); a = ap.parse_args()
    J, B = parse(a.inp)
    prim = J["meshes"][0]["primitives"][0]
    P = rd(J, B, prim["attributes"]["POSITION"], 3)
    tri = rd(J, B, prim["indices"], 1).reshape(-1, 3).astype(int) if prim.get("indices") is not None else np.arange(len(P)).reshape(-1,3)
    # 世界面积
    v0, v1, v2 = P[tri[:,0]], P[tri[:,1]], P[tri[:,2]]
    A_world = float(np.linalg.norm(np.cross(v1-v0, v2-v0), axis=1).sum()/2.0)
    # UV 面积
    A_uv, has_uv = None, "TEXCOORD_0" in prim["attributes"]
    if has_uv:
        UV = rd(J, B, prim["attributes"]["TEXCOORD_0"], 2)
        u0, u1, u2 = UV[tri[:,0]], UV[tri[:,1]], UV[tri[:,2]]
        A_uv = float(np.abs((u1[:,0]-u0[:,0])*(u2[:,1]-u0[:,1]) - (u2[:,0]-u0[:,0])*(u1[:,1]-u0[:,1])).sum()/2.0)
    # 贴图分辨率
    R = None
    if J.get("images"):
        for im in J["images"]:
            bv = J["bufferViews"][im["bufferView"]] if "bufferView" in im else None
            if bv:
                png = B[bv.get("byteOffset",0):bv.get("byteOffset",0)+bv["byteLength"]]
                w, h = Image.open(io.BytesIO(png)).size
                R = max(R or 0, max(w, h))
    print("  ═══ Texel Density 实测 ｜ %s ═══" % pathlib.Path(a.inp).name)
    print("   三角面 %d ｜ 世界表面积 %.4f m²（%.1f cm²）｜ UV %s" % (len(tri), A_world, A_world*10000, ("有（UV 面积 %.4f）" % A_uv) if has_uv else "无"))
    print("   贴图分辨率 %s" % (("%d px" % R) if R else "无贴图"))
    if not has_uv or not R or not A_world:
        print("   ⇒ ★不可评（缺 UV／贴图／面积）⇒ 退出码 2"); sys.exit(2)
    # ★UV 重叠检测（承 2026-10-12 自纠：A_uv>1 即重叠 ⇒ 会使 TD 虚高）
    G = 256
    grid = np.zeros((G, G), np.int16)
    if has_uv:
        for a_, b_, c_ in UV[tri].astype(np.float32):
            xs = np.clip((np.array([a_[0], b_[0], c_[0]])*G).astype(int), 0, G-1)
            ys = np.clip((np.array([a_[1], b_[1], c_[1]])*G).astype(int), 0, G-1)
            minx, maxx, miny, maxy = xs.min(), xs.max(), ys.min(), ys.max()
            if maxx < minx or maxy < miny: continue
            for yy in range(miny, maxy+1):
                for xx in range(minx, maxx+1):
                    grid[yy, xx] = min(32767, grid[yy, xx] + 1)
    used = int((grid > 0).sum()); over = int((grid > 1).sum())
    overlap_pct = 100.0*over/max(1, used)
    print("   ★UV 重叠检测：占用格 %d／%d ｜ 重复占用格 %d ⇒ 重叠率 %.1f%%" % (used, G*G, over, overlap_pct))
    if overlap_pct > 5.0 or A_uv > 1.0:
        print("   ⇒ ★UV 重叠显著（或 A_uv>1）⇒ TD 不可评（免以虚高之密度充达标）⇒ 退出码 2")
        if a.json:
            pathlib.Path(a.json).write_text(json.dumps({"file": pathlib.Path(a.inp).name, "tris": len(tri),
                "world_area_m2": A_world, "uv_area": A_uv, "uv_overlap_pct": round(overlap_pct, 2),
                "verdict": "★不可评：UV 重叠显著 ⇒ 须先做 UV 岛打包与去重叠"}, ensure_ascii=False, indent=1),
                encoding="utf-8", newline="\n")
        sys.exit(2)
    texels = (R*R)*A_uv
    td = (texels/(A_world*10000))**0.5
    need = a.target
    # 达标所需：R' = R × (need/td)（同 UV 布局下）
    need_R = R*(need/td) if td > 0 else None
    verdict = "✓ 达标" if td >= need else "✗ 未达（差 %.2f 倍）" % (need/td if td else -1)
    print("   可用纹素 %.3e ｜ ★线性密度 %.2f px/cm（门槛 %.2f）⇒ %s" % (texels, td, need, verdict))
    if need_R: print("   ⇒ 同 UV 布局下达标所需贴图边长 ≈ %d px（现 %d）" % (round(need_R), R))
    out = {"file": pathlib.Path(a.inp).name, "tris": len(tri), "world_area_m2": A_world, "uv_area": A_uv,
           "tex_res": R, "texel_density_px_cm": round(td, 3), "target": need, "pass": td >= need,
           "uv_overlap_pct": round(overlap_pct, 2),
           "res_needed_for_target": (round(need_R) if need_R else None)}
    if a.json: pathlib.Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    sys.exit(0 if td >= need else 1)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
