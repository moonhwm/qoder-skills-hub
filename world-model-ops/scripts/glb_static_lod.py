# -*- coding: utf-8 -*-
"""glb_static_lod.py —— 甲案·阶段二（甲二-B）：静态几何 LOD（顶点聚类减面；不绑骨、不动蒙皮资产）
目标：tris 比例按规范"逐级减半"（LOD0 : LOD1 : LOD2 ＝ 1 : 0.5 : 0.25）
保留：UV（簇内平均）＋ 材质与内嵌贴图
用法：python glb_static_lod.py --in <glb> --outdir <dir> --tag staticLOD [--tris 756,378]
（中文串一律用「」）
"""
import argparse, json, pathlib, struct, sys
import numpy as np

def parse(p):
    b = pathlib.Path(p).read_bytes(); ln = struct.unpack("<I", b[8:12])[0]; off=12; J=None; B=b""
    while off < ln:
        cl, ct = struct.unpack("<II", b[off:off+8]); d = b[off+8:off+8+cl]
        if ct == 0x4E4F534A: J = json.loads(d.decode("utf-8","replace"))
        elif ct == 0x004E4942: B = d
        off += 8+cl
    return J, B

def rd(J,B,ai,n):
    a=J["accessors"][ai]; bv=J["bufferViews"][a["bufferView"]]
    dt={5126:"<f4",5123:"<u2",5125:"<u4",5121:"<u1"}[a["componentType"]]
    start=bv.get("byteOffset",0)+a.get("byteOffset",0); stride=bv.get("byteStride") or (np.dtype(dt).itemsize*n)
    out=np.zeros((a["count"],n),dtype=dt)
    for i in range(a["count"]): out[i]=np.frombuffer(B,dtype=dt,count=n,offset=start+i*stride)
    return out.astype(np.float32)

def cluster(P, idx, UV, cell):
    key = np.floor(P/cell).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    nC = int(inv.max())+1
    rep = np.zeros((nC,3), np.float32); uvm = np.zeros((nC,2), np.float32); cnt = np.zeros(nC, np.float32)
    for k in range(3): np.add.at(rep[:,k], inv, P[:,k])
    for k in range(2): np.add.at(uvm[:,k], inv, UV[:,k])
    np.add.at(cnt, inv, 1)
    rep = rep/cnt[:,None]; uvm = uvm/cnt[:,None]
    tri = inv[idx.reshape(-1,3)]
    keep = (tri[:,0]!=tri[:,1]) & (tri[:,1]!=tri[:,2]) & (tri[:,0]!=tri[:,2])
    tri = np.unique(np.sort(tri[keep], axis=1), axis=0)   # 去重并规范顶点序
    return rep, tri.astype(np.uint32), uvm

def build(P, tri, UV, imgpng, out, name):
    # 法线由面法线累加
    fn = np.cross(P[tri[:,1]]-P[tri[:,0]], P[tri[:,2]]-P[tri[:,0]])
    ln = np.linalg.norm(fn,axis=1,keepdims=True); ln[ln==0]=1; fn=fn/ln
    N = np.zeros_like(P)
    for k in range(3): np.add.at(N, tri[:,k], fn)
    nn = np.linalg.norm(N,axis=1,keepdims=True); nn[nn==0]=1; N=(N/nn).astype(np.float32)
    J = {"asset":{"version":"2.0","generator":"cairn glb_static_lod"},
         "scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0,"name":name}],
         "meshes":[{"name":name,"primitives":[{"attributes":{},"indices":0,"material":0}]}],
         "materials":[{"name":"cairn_pbr_static","pbrMetallicRoughness":{"baseColorTexture":{"index":0},"metallicFactor":0.0,"roughnessFactor":0.7}}],
         "textures":[{"sampler":0,"source":0}],"samplers":[{"magFilter":9729,"minFilter":9987,"wrapS":10497,"wrapT":10497}],
         "images":[{"mimeType":"image/png","name":"cairn_albedo"}],
         "accessors":[], "bufferViews":[], "buffers":[{"byteLength":0}]}
    bin_ = bytearray()
    def pad4(b): return b + b"\x00"*((4-len(b)%4)%4)
    def view(data, target=None):
        off=len(bin_); bin_.extend(pad4(data))
        v={"buffer":0,"byteOffset":off,"byteLength":len(data)}
        if target: v["target"]=target
        J["bufferViews"].append(v); return len(J["bufferViews"])-1
    _EL = {5126:4, 5125:4, 5123:2, 5121:1}
    _NC = {"SCALAR":1, "VEC2":2, "VEC3":3, "VEC4":4}
    def acc(data, ctype, typ, target=None, mn=None, mx=None):
        bv=view(data, target)
        # ★元素数 = 字节数 / (每元素字节)，勿把字节数当元素数（曾致 ×4/×12 之错）
        cnt = int(len(data) // (_EL[ctype] * _NC[typ]))
        a={"bufferView":bv,"componentType":ctype,"count":cnt,"type":typ}
        if mn is not None: a["min"]=mn; a["max"]=mx
        J["accessors"].append(a); return len(J["accessors"])-1
    i_pos = acc(P.astype("<f4").tobytes(), 5126, "VEC3", 34962, [float(x) for x in P.min(axis=0)], [float(x) for x in P.max(axis=0)])
    i_nrm = acc(N.astype("<f4").tobytes(), 5126, "VEC3", 34962)
    i_uv  = acc(np.asarray(UV, dtype="<f4").tobytes(), 5126, "VEC2", 34962)
    i_idx = acc(tri.reshape(-1).astype("<u4").tobytes(), 5125, "SCALAR", 34963)
    bv_img = view(imgpng)
    J["images"][0]["bufferView"] = bv_img
    prim = J["meshes"][0]["primitives"][0]
    prim["attributes"] = {"POSITION": i_pos, "NORMAL": i_nrm, "TEXCOORD_0": i_uv}
    prim["indices"] = i_idx
    J["buffers"][0]["byteLength"] = len(bin_)
    js = json.dumps(J, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4-len(js)%4)%4)
    o = bytearray(b"glTF"); o += struct.pack("<II", 2, 12+8+len(js)+8+len(bin_))
    o += struct.pack("<II", len(js), 0x4E4F534A)+js
    o += struct.pack("<II", len(bin_), 0x004E4942)+bytes(bin_)
    pathlib.Path(out).write_bytes(bytes(o))
    return len(tri), len(P), pathlib.Path(out).stat().st_size

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--in",dest="inp",required=True)
    ap.add_argument("--outdir",required=True); ap.add_argument("--tag",default="staticLOD")
    ap.add_argument("--tris",default="756,378"); a=ap.parse_args()
    J,B = parse(a.inp); prim=J["meshes"][0]["primitives"][0]
    P = rd(J,B,prim["attributes"]["POSITION"],3)
    UV = rd(J,B,prim["attributes"]["TEXCOORD_0"],2)
    idx = rd(J,B,prim["indices"],1).reshape(-1).astype(np.int64)
    img = b""
    if J.get("images") and "bufferView" in J["images"][0]:
        bv=J["bufferViews"][J["images"][0]["bufferView"]]; img = B[bv.get("byteOffset",0):bv.get("byteOffset",0)+bv["byteLength"]]
    t0 = len(idx)//3
    print("  基准：顶点 %d ｜ tris %d ｜ UV %s ｜ 内嵌贴图 %d B" % (len(P), t0, "✓" if len(UV)==len(P) else "✗", len(img)))
    outdir = pathlib.Path(a.outdir); outdir.mkdir(parents=True, exist_ok=True)
    # LOD0（原样重建，含 UV/贴图/法线）
    n, v, sz = build(P, idx.reshape(-1,3).astype(np.uint32), UV, img, outdir/("%s0_20261012.glb"%a.tag), a.tag+"0")
    print("  ✓ LOD0 ⇒ tris %d ｜ 顶点 %d ｜ %.1f KB" % (n, v, sz/1024))
    for i, tgt in enumerate([int(x) for x in a.tris.split(",")], start=1):
        lo, hi = 0.001, min(P.max(axis=0)-P.min(axis=0))
        best = None
        for _ in range(22):     # 二分校正 cell 尺寸以命中目标面数
            cell = (lo+hi)/2
            rep, tri, uvm = cluster(P, idx, UV, cell)
            if best is None or abs(len(tri)-tgt) < abs(best[2]-tgt): best = (cell, (rep,tri,uvm), len(tri))
            if len(tri) > tgt: lo = cell
            else: hi = cell
        cell, (rep, tri, uvm), ntr = best
        n, v, sz = build(rep, tri, uvm, img, outdir/("%s%d_20261012.glb"%(a.tag,i)), "%s%d"%(a.tag,i))
        print("  ✓ LOD%d ⇒ tris %d（目标 %d，偏差 %+d）｜ 顶点 %d ｜ cell %.4f ｜ %.1f KB" % (i, n, tgt, n-tgt, v, cell, sz/1024))

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
