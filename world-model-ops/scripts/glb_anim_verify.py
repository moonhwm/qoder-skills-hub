import argparse, json, pathlib, struct, sys
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import numpy as np
NCOMP = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
def verify(p, min_change=1e-6):
    raw = p.read_bytes(); jl = struct.unpack("<I", raw[12:16])[0]
    G = json.loads(raw[20:20+jl].decode("utf-8","replace")); bo = 20+jl+8
    def acc(i):
        a = G["accessors"][i]; bv = G["bufferViews"][a["bufferView"]]
        off = bo + bv.get("byteOffset",0) + a.get("byteOffset",0)
        dt = {5126:"<f4",5125:"<u4",5123:"<u2",5121:"<u1"}[a["componentType"]]
        return np.frombuffer(raw, dtype=dt, count=a["count"]*NCOMP[a["type"]], offset=off), NCOMP[a["type"]], a["count"]
    out = {"file": p.name, "kb": round(p.stat().st_size/1024,1), "animations": [], "nodes": len(G.get("nodes",[])),
           "meshes": len(G.get("meshes",[])), "skins": len(G.get("skins",[]))}
    tot=mov=0; mx=0.0
    for ai, an in enumerate(G.get("animations", [])):
        sm = an.get("samplers", []); ch = an.get("channels", [])
        name = an.get("name") or ("anim%d"%ai); paths={}; rmax=0.0; kf=0; tspan=[0.0,0.0]
        for c in ch:
            s = sm[c["sampler"]]; tv,_,kf = acc(s["input"]); tspan=[float(tv.min()), float(tv.max())]
            ov,nc,_ = acc(s["output"]); vv = ov.reshape(-1,nc)
            r = float(np.abs(vv-vv[0]).max()); pa = c["target"]["path"]
            paths[pa] = max(paths.get(pa,0.0), r)
            tot += 1
            if r > min_change: mov += 1
            rmax = max(rmax, r); mx = max(mx, r)
        static_paths = sorted(k for k,v in paths.items() if v <= min_change)
        out["animations"].append({"name": name, "channels": len(ch), "keyframes": kf, "t_span": tspan,
                                  "max_change": round(rmax,4), "static_paths": static_paths})
    out["channels_total"]=tot; out["channels_moving"]=mov; out["max_change"]=round(mx,4)
    out["verdict"] = "animations-are-real-motion" if (mov>0 and mx>1e-3) else "near-static"
    return out
ap = argparse.ArgumentParser(); ap.add_argument("--file", required=True); ap.add_argument("--min-change", type=float, default=1e-6)
a = ap.parse_args()
r = verify(pathlib.Path(a.file), a.min_change)
print("  ═══ %s（%.1f KB）｜ nodes=%d meshes=%d skins=%d ═══" % (r["file"], r["kb"], r["nodes"], r["meshes"], r["skins"]))
for an in r["animations"]:
    print("   · %-14s 通道 %2d ｜ 关键帧 %2d ｜ 时间轴 [%.3f, %.3f] ｜ 最大变化 %.4f ｜ 静态路径 %s" % (
        an["name"][:14], an["channels"], an["keyframes"], an["t_span"][0], an["t_span"][1], an["max_change"], an["static_paths"] or "无"))
print("   ★ 通道 %d ｜ 有效运动 %d ｜ 最大变化 %.4f ⇒ 判：%s" % (r["channels_total"], r["channels_moving"], r["max_change"], r["verdict"]))
