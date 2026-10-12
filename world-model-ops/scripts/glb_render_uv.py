# -*- coding: utf-8 -*-
"""glb_render_uv.py —— 极简 GLB 渲染器（含 UV 贴图采样与 Lambert 明暗）
用途：★验证"贴图是否真生效"——同一几何分别以"采样贴图"与"仅基础色"渲染，比像素差
用法：python glb_render_uv.py --in <glb> --out <png> [--size 512] [--notexture]
（中文串一律用「」）
"""
import argparse, io, json, pathlib, struct, sys
import numpy as np
from PIL import Image

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

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--in",dest="inp",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--size",type=int,default=512); ap.add_argument("--notexture",action="store_true"); a=ap.parse_args()
    J,B = parse(a.inp); prim=J["meshes"][0]["primitives"][0]
    P = rd(J,B,prim["attributes"]["POSITION"],3)
    UV = rd(J,B,prim["attributes"]["TEXCOORD_0"],2) if "TEXCOORD_0" in prim["attributes"] else None
    N = rd(J,B,prim["attributes"]["NORMAL"],3) if "NORMAL" in prim["attributes"] else np.tile([0,0,1.0],(len(P),1))
    idx = rd(J,B,prim["indices"],1).reshape(-1,3).astype(int)
    tex = None; sampled = 0
    if not a.notexture and J.get("textures"):
        src = J["textures"][0].get("source")
        if src is not None and "bufferView" in J.get("images",[{}])[src]:
            bv = J["bufferViews"][J["images"][src]["bufferView"]]
            png = B[bv.get("byteOffset",0):bv.get("byteOffset",0)+bv["byteLength"]]
            tex = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.float32)
    base = (1.0,1.0,1.0)
    if J.get("materials"):
        bc = (J["materials"][0].get("pbrMetallicRoughness") or {}).get("baseColorFactor")
        if bc: base = tuple(bc[:3])
    S = a.size
    # 正交前视：以 XY 平面投影（-Z 朝内），按 bbox 归一化
    lo, hi = P.min(axis=0), P.max(axis=0); ctr = (lo+hi)/2; ext = float(max(hi[0]-lo[0], hi[1]-lo[1])) or 1.0
    sc = (S*0.86)/ext
    X = (P[:,0]-ctr[0])*sc + S/2
    Y = -(P[:,1]-ctr[1])*sc + S/2
    Z = P[:,2]
    img = np.zeros((S,S,3), np.float32); zbuf = np.full((S,S), -1e9, np.float32)
    L = np.array([0.4, 0.6, 0.7]); L = L/np.linalg.norm(L)
    for f in idx:
        x0,y0,z0 = X[f[0]],Y[f[0]],Z[f[0]]; x1,y1,z1 = X[f[1]],Y[f[1]],Z[f[1]]; x2,y2,z2 = X[f[2]],Y[f[2]],Z[f[2]]
        minx,maxx = int(max(0,min(x0,x1,x2))), int(min(S-1,max(x0,x1,x2)))
        miny,maxy = int(max(0,min(y0,y1,y2))), int(min(S-1,max(y0,y1,y2)))
        if maxx<minx or maxy<miny: continue
        det = (y1-y2)*(x0-x2) + (x2-x1)*(y0-y2)
        if abs(det) < 1e-9: continue
        xs = np.arange(minx,maxx+1); ys = np.arange(miny,maxy+1)
        gx,gy = np.meshgrid(xs,ys)
        w0 = ((y1-y2)*(gx-x2) + (x2-x1)*(gy-y2))/det
        w1 = ((y2-y0)*(gx-x2) + (x0-x2)*(gy-y2))/det
        w2 = 1-w0-w1
        m = (w0>=0)&(w1>=0)&(w2>=0)
        if not m.any(): continue
        z = w0*z0 + w1*z1 + w2*z2
        sub = zbuf[miny:maxy+1, minx:maxx+1]
        upd = m & (z > sub)
        if not upd.any(): continue
        col = np.zeros((upd.shape[0], upd.shape[1], 3), np.float32)
        nrm = w0[...,None]*N[f[0]] + w1[...,None]*N[f[1]] + w2[...,None]*N[f[2]]
        nn = np.linalg.norm(nrm, axis=2, keepdims=True); nn[nn==0]=1
        lit = np.clip((nrm/nn) @ L, 0.15, 1.0)[...,None]
        if tex is not None and UV is not None:
            u = w0*UV[f[0]][0] + w1*UV[f[1]][0] + w2*UV[f[2]][0]
            v = w0*UV[f[0]][1] + w1*UV[f[1]][1] + w2*UV[f[2]][1]
            tx = np.clip((u % 1.0)*(tex.shape[1]-1), 0, tex.shape[1]-1).astype(int)
            ty = np.clip((v % 1.0)*(tex.shape[0]-1), 0, tex.shape[0]-1).astype(int)
            col = tex[ty, tx]; sampled += int(upd.sum())
        else:
            col[:] = np.array(base)*255.0
        sel = upd
        img[miny:maxy+1, minx:maxx+1][sel] = (col*lit)[sel]
        sub[sel] = z[sel]
    outpng = np.clip(img,0,255).astype(np.uint8)
    Image.fromarray(outpng).save(a.out)
    cov = 100.0*float((zbuf > -1e8).mean())
    print("  渲染 %s ⇒ %s ｜ 三角面 %d ｜ 覆盖 %.1f%% ｜ 贴图采样 %s ｜ 取景 %.3f" % (
        pathlib.Path(a.inp).name[:44], pathlib.Path(a.out).name, len(idx), cov,
        "✓ %d 像素" % sampled if sampled else ("✗（无贴图模式）" if a.notexture else "✗（无贴图或 UV）"), sc))

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
