# -*- coding: utf-8 -*-
"""glb_uv_check.py —— UV 之实质可用性读数（零依赖：自解 GLB 之 JSON 与 BIN chunk）
判据（可失败）：①存在 TEXCOORD_0 ②u／v 值域在 [0,1]（容差 0.02）③非退化（值域跨度 ≥0.1）
              ④覆盖密度：8×8 网格中非空格数 ≥ 8（否则 UV 挤在一角 ⇒ 纹理无用）
用法：python glb_uv_check.py <glb…> [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, struct, sys, time

CT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def load(p):
    b = pathlib.Path(p).read_bytes()
    if b[:4] != b"glTF":
        return None, None, "非 GLB"
    off, js, bin_ = 12, None, None
    while off + 8 <= len(b):
        clen, ctype = struct.unpack("<II", b[off:off + 8])
        body = b[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A: js = json.loads(body.decode("utf-8", "replace"))
        elif ctype == 0x004E4942: bin_ = body
        off += 8 + clen + ((4 - clen % 4) % 4)
    return js, bin_, None


def read_acc(j, bin_, idx):
    a = (j.get("accessors") or [])[idx]
    bv = (j.get("bufferViews") or [])[a["bufferView"]]
    fmt, sz = CT[a["componentType"]]
    n = NC[a["type"]]
    stride = bv.get("byteStride") or (sz * n)
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    out = []
    for i in range(a["count"]):
        o = base + i * stride
        out.append(struct.unpack_from("<" + fmt * n, bin_, o))
    return out


def uv_stats(uv, grid=8):
    us = [t[0] for t in uv]; vs = [t[1] for t in uv]
    if not us: return None
    span_u, span_v = max(us) - min(us), max(vs) - min(vs)
    inside = all(-0.02 <= x <= 1.02 for x in us + vs)
    cells = set()
    for u, v in uv:
        cells.add((min(grid - 1, max(0, int(u * grid))), min(grid - 1, max(0, int(v * grid)))))
    return {"n": len(uv), "umin": round(min(us), 4), "umax": round(max(us), 4),
            "vmin": round(min(vs), 4), "vmax": round(max(vs), 4),
            "span_u": round(span_u, 4), "span_v": round(span_v, 4), "in01": inside,
            "cells": len(cells), "cells_of": grid * grid,
            "fill_ratio": round(len(cells) / (grid * grid), 3)}


def overlap_ratio(j, bin_, grid=64):
    """★逐面重叠之真检测（2026-10-12 加，零依赖）：把各 UV 三角形栅格化到 grid×grid 之占用计数图
    ⇒ 被 ≥2 个面覆盖之像素占比 ＝ 重叠像素率；并给出"至少与他一面相叠"之面数占比。
    ★此为取代"以 UV 面积和 >1 推断重叠率 100%"之正确法（面积和只可推"存在重叠"）。"""
    import math as _m
    occ = [0] * (grid * grid)
    tri_cells = []
    tot = 0.0
    for m in (j.get("meshes") or []):
        for pr in (m.get("primitives") or []):
            tu = (pr.get("attributes") or {}).get("TEXCOORD_0"); ia = pr.get("indices")
            if not isinstance(tu, int): continue
            uv = read_acc(j, bin_, tu)
            idx = [x[0] for x in read_acc(j, bin_, ia)] if isinstance(ia, int) else list(range(len(uv)))
            for i in range(0, len(idx) - 2, 3):
                a, b, c = uv[idx[i]], uv[idx[i + 1]], uv[idx[i + 2]]
                tot += abs((b[0]-a[0])*(c[1]-a[1]) - (c[0]-a[0])*(b[1]-a[1])) / 2.0
                x0 = _m.floor(min(a[0], b[0], c[0]) * grid); x1 = _m.ceil(max(a[0], b[0], c[0]) * grid)
                y0 = _m.floor(min(a[1], b[1], c[1]) * grid); y1 = _m.ceil(max(a[1], b[1], c[1]) * grid)
                cells = []
                for gx in range(max(0, x0), min(grid - 1, x1) + 1):
                    for gy in range(max(0, y0), min(grid - 1, y1) + 1):
                        px, py = (gx + 0.5) / grid, (gy + 0.5) / grid
                        d1 = (px-b[0])*(a[1]-b[1]) - (py-b[1])*(a[0]-b[0])
                        d2 = (px-c[0])*(b[1]-c[1]) - (py-c[1])*(b[0]-c[0])
                        d3 = (px-a[0])*(c[1]-a[1]) - (py-a[1])*(c[0]-a[0])
                        neg = (d1 < 0) or (d2 < 0) or (d3 < 0); pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
                        if not (neg and pos):
                            cells.append(gy * grid + gx)
                for cc in cells: occ[cc] += 1
                if cells: tri_cells.append(set(cells))
    used = sum(1 for o in occ if o >= 1)
    multi = sum(1 for o in occ if o >= 2)
    over_faces = 0
    for s in tri_cells:
        if any(occ[cc] >= 2 for cc in s): over_faces += 1
    nf = len(tri_cells)
    return {"grid": grid, "faces": nf, "uv_area_sum": round(tot, 4),
            "used_cells": used, "multi_cells": multi,
            "overlap_pixel_ratio": round(multi / max(1, used), 4),
            "faces_touching_overlap": over_faces,
            "face_overlap_ratio": round(over_faces / max(1, nf), 4)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--json", default="")
    a = ap.parse_args()
    rows = []
    print("  ═══ UV 实质可用性读数（零依赖）═══")
    for f in a.files:
        p = pathlib.Path(f)
        if not p.exists(): print("   %-46s ★不在" % p.name[:46]); continue
        j, bin_, err = load(p)
        if err or j is None or bin_ is None: print("   %-46s ★%s" % (p.name[:46], err or "无 BIN")); continue
        got = []
        for m in (j.get("meshes") or []):
            for k, pr in enumerate(m.get("primitives") or []):
                t = (pr.get("attributes") or {}).get("TEXCOORD_0")
                if isinstance(t, int):
                    got.append(uv_stats(read_acc(j, bin_, t)))
        has_img = len(j.get("images") or [])
        if not got:
            print("   %-46s ★无 TEXCOORD_0（UV 缺）｜图 %d" % (p.name[:46], has_img))
            rows.append({"file": p.name, "uv": False, "images": has_img}); continue
        s = got[0]
        _ov0 = overlap_ratio(j, bin_)
        crit = {"①存在 TEXCOORD_0": True,
                "②u/v 在 [0,1]（±0.02）": bool(s["in01"]),
                "③非退化（跨度 ≥0.1）": (s["span_u"] >= 0.1 and s["span_v"] >= 0.1),
                "④覆盖密度 ≥8/64 格": (s["cells"] >= 8),
                "★⑤重叠之面占比 ≤0.30（否则不可用于独立贴图）": (_ov0["face_overlap_ratio"] <= 0.30)}
        ok = all(crit.values())
        print("   %-46s UV点 %-5d u[%.3f,%.3f] v[%.3f,%.3f] 覆盖 %d/64 ⇒ %s" % (
            p.name[:46], s["n"], s["umin"], s["umax"], s["vmin"], s["vmax"], s["cells"], "✓ 可用" if ok else "★有不过"))
        for k2, v in crit.items():
            if not v: print("        ★不过：%s" % k2)
        _ov = _ov0
        print("        重叠检测：面 %d ｜ 重叠像素率 %.4f ｜ 涉重叠之面 %.4f（★真检测）" % (_ov["faces"], _ov["overlap_pixel_ratio"], _ov["face_overlap_ratio"]))
        rows.append({"file": p.name, "uv": True, "images": has_img, "stats": s, "criteria": crit, "usable": ok, "overlap": _ov})
    if rows:
        u = sum(1 for r in rows if r.get("usable"))
        print("   ⇒ 汇总：%d／%d 件之 UV 达「可用」判据" % (u, len(rows)))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "rows": rows},
                                                   ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
