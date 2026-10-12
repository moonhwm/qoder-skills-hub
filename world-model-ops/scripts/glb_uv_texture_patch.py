# -*- coding: utf-8 -*-
"""glb_uv_texture_patch.py —— 为既有 GLB 补 UV 与 PBR 贴图（甲案·阶段一）
做法（零依赖，仅 numpy/PIL）：
  ① 逐顶点三平面 UV（按法线主轴投影，归一化到 [0,1]）⇒ 新增 TEXCOORD_0
  ② 程序化生成 Albedo／Roughness／AO 三张 PNG（1K）
  ③ 以 bufferView 内嵌 Albedo（PNG）⇒ 新增 image/texture/sampler 并挂到材质
  ④ 重写 GLB（JSON 与 BIN 分块，4 字节对齐）
★诚实标注：此为"自动 UV"，非手工展 UV；接缝与密度不均属预期。
用法：python glb_uv_texture_patch.py --in <glb> --out <glb> [--texdir <dir>] [--size 1024]
（中文串一律用「」）
"""
import argparse, json, pathlib, struct, sys
import numpy as np
from PIL import Image, ImageDraw

def parse_glb(p):
    b = pathlib.Path(p).read_bytes()
    assert b[:4] == b"glTF", "非 GLB"
    ln = struct.unpack("<I", b[8:12])[0]
    off, J, B = 12, None, b""
    while off < ln:
        cl, ct = struct.unpack("<II", b[off:off+8])
        data = b[off+8:off+8+cl]
        if ct == 0x4E4F534A: J = json.loads(data.decode("utf-8", "replace"))
        elif ct == 0x004E4942: B = data
        off += 8 + cl
    return J, B

def acc_read(J, B, ai, comps):
    a = J["accessors"][ai]; bv = J["bufferViews"][a["bufferView"]]
    dt = {5126: "<f4", 5123: "<u2", 5125: "<u4", 5121: "<u1"}[a["componentType"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride") or (np.dtype(dt).itemsize * n)
    out = np.zeros((a["count"], n), dtype=dt)
    for i in range(a["count"]):
        o = start + i * stride
        out[i] = np.frombuffer(B, dtype=dt, count=n, offset=o)
    return out.astype(np.float32) if dt == "<f4" else out

def make_tex(size, kind):
    rng = np.random.default_rng(20261012)
    if kind == "albedo":
        base = np.zeros((size, size, 3), np.float32); base[:] = (214, 205, 190)
        n = rng.normal(0, 4.0, (size, size, 1)); base = np.clip(base + n, 0, 255)
        im = Image.fromarray(base.astype(np.uint8))
        d = ImageDraw.Draw(im)
        for i in range(1, 8):
            y = int(size*i/8); d.line([(0, y), (size, y)], fill=(150, 140, 128), width=max(1, size//512))
        for i in range(1, 12):
            x = int(size*i/12); d.line([(x, 0), (x, size)], fill=(158, 148, 136), width=1)
        return im
    if kind == "rough":
        v = np.clip(0.70*255 + rng.normal(0, 10, (size, size, 1)), 0, 255)
        return Image.fromarray(np.repeat(v.astype(np.uint8), 3, axis=2))
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.sqrt(((xx-size/2)/(size/2))**2 + ((yy-size/2)/(size/2))**2)
    ao = np.clip(1.0 - 0.35*np.clip(r, 0, 1)[..., None], 0, 1)
    return Image.fromarray((np.repeat(ao, 3, axis=2)*255).astype(np.uint8))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--texdir", default=""); ap.add_argument("--size", type=int, default=1024)
    a = ap.parse_args()
    J, B = parse_glb(a.inp)
    prim = J["meshes"][0]["primitives"][0]
    P = acc_read(J, B, prim["attributes"]["POSITION"], 3)
    if "NORMAL" in prim["attributes"]:
        N = acc_read(J, B, prim["attributes"]["NORMAL"], 3); gen_norm = False
    else:
        # ★由索引生成逐顶点法线（原件常缺 NORMAL ⇒ 否则 UV 退化为平面投影）
        idx = acc_read(J, B, prim["indices"], 1).reshape(-1).astype(int) if prim.get("indices") is not None else np.arange(len(P))
        tri = idx.reshape(-1, 3)
        fn = np.cross(P[tri[:,1]] - P[tri[:,0]], P[tri[:,2]] - P[tri[:,0]])
        ln = np.linalg.norm(fn, axis=1, keepdims=True); ln[ln == 0] = 1
        fn = fn/ln
        N = np.zeros_like(P)
        for k in range(3): np.add.at(N, tri[:,k], fn)
        nn = np.linalg.norm(N, axis=1, keepdims=True); nn[nn == 0] = 1
        N = (N/nn).astype(np.float32); gen_norm = True
        print("  ★ 原件无 NORMAL ⇒ 已由索引生成逐顶点法线（%d 面）" % len(tri))
    # ① 三平面 UV：按法线主轴
    ax = np.argmax(np.abs(N), axis=1)
    uv = np.zeros((len(P), 2), np.float32)
    for k in range(len(P)):
        if ax[k] == 0: uv[k] = (P[k][1], P[k][2])
        elif ax[k] == 1: uv[k] = (P[k][0], P[k][2])
        else: uv[k] = (P[k][0], P[k][1])
    lo, hi = uv.min(axis=0), uv.max(axis=0)
    span = np.where((hi-lo) == 0, 1, hi-lo)
    uv = (uv - lo)/span
    print("  ★ UV：顶点 %d ｜ 主轴分布 X/Y/Z = %s ｜ 范围归一化 [%.3f, %.3f]" % (
        len(P), np.bincount(ax, minlength=3).tolist(), float(uv.min()), float(uv.max())))
    # ② 贴图
    texdir = pathlib.Path(a.texdir) if a.texdir else pathlib.Path(a.out).parent
    texdir.mkdir(parents=True, exist_ok=True)
    imgs = {}
    for kind in ("albedo", "rough", "ao"):
        im = make_tex(a.size, kind); p = texdir/("cairn_%s_%d.png" % (kind, a.size)); im.save(p, optimize=True)
        imgs[kind] = p; print("  ★ 贴图：%s（%d×%d，%.1f KB）" % (p.name, a.size, a.size, p.stat().st_size/1024))
    # ③ 写回：BIN 追加（对齐 4）
    def pad4(b): return b + b"\x00" * ((4 - len(b) % 4) % 4)
    bin_new = bytearray(B)
    def add_view(data, target=None):
        off = len(bin_new); bin_new.extend(pad4(data))
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target: v["target"] = target
        J["bufferViews"].append(v); return len(J["bufferViews"]) - 1
    # ★法线回写（若为生成）
    if gen_norm:
        bv_n = add_view(N.astype("<f4").tobytes(), 34962)
        J["accessors"].append({"bufferView": bv_n, "componentType": 5126, "count": int(len(N)), "type": "VEC3"})
        prim["attributes"]["NORMAL"] = len(J["accessors"]) - 1
    bv_uv = add_view(uv.astype("<f4").tobytes(), 34962)
    J["accessors"].append({"bufferView": bv_uv, "componentType": 5126, "count": int(len(uv)),
                           "type": "VEC2", "min": [float(uv[:,0].min()), float(uv[:,1].min())],
                           "max": [float(uv[:,0].max()), float(uv[:,1].max())]})
    prim["attributes"]["TEXCOORD_0"] = len(J["accessors"]) - 1
    png = imgs["albedo"].read_bytes()
    bv_img = add_view(png)
    J.setdefault("images", []).append({"bufferView": bv_img, "mimeType": "image/png", "name": "cairn_albedo"})
    J.setdefault("samplers", []).append({"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497})
    J.setdefault("textures", []).append({"sampler": len(J["samplers"])-1, "source": len(J["images"])-1})
    if not J.get("materials"):
        J["materials"] = [{"name": "cairn_pbr"}]
    J["materials"][0].setdefault("pbrMetallicRoughness", {})
    J["materials"][0]["pbrMetallicRoughness"]["baseColorTexture"] = {"index": len(J["textures"])-1}
    J["materials"][0]["pbrMetallicRoughness"]["metallicFactor"] = 0.0
    J["materials"][0]["pbrMetallicRoughness"]["roughnessFactor"] = 0.7
    if "material" not in prim: prim["material"] = 0
    # ④ 重写 GLB
    J["buffers"] = [{"byteLength": len(bin_new)}]
    js = json.dumps(J, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    out = bytearray(b"glTF"); out += struct.pack("<II", 2, 12 + 8 + len(js) + 8 + len(bin_new))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js
    out += struct.pack("<II", len(bin_new), 0x004E4942) + bytes(bin_new)
    pathlib.Path(a.out).write_bytes(bytes(out))
    print("  ✓ 已写出 %s（%.1f KB）｜ 含 UV accessor=%d ｜ 贴图 %d ｜ 材质 %d" % (
        pathlib.Path(a.out).name, pathlib.Path(a.out).stat().st_size/1024,
        prim["attributes"]["TEXCOORD_0"], len(J["textures"]), len(J["materials"])))

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
