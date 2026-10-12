# -*- coding: utf-8 -*-
"""uv_stretch_check.py —— UV 拉伸读数（零依赖）：核"逐岛打包"之代价
原理：把每个三角形之"UV 面积／世界面积"之比 r 视作局部纹理密度之倒数 ⇒
     中位数＝典型密度，max／p95＝异常拉伸 ⇒ ★拉伸比 = max(r)/median(r) 越大，贴图越被扭曲。
★并注：GLB 之 UV 逐顶点存储 ⇒ 若岛与岛共享顶点，"逐岛打包"必然在该顶点处冲突
     ⇒ 正确解须"按缝拆点（duplicate vertices）"；本器以拉伸比间接暴露此问题。
用法：python uv_stretch_check.py <glb…> [--json out]
（中文串一律用「」）
"""
import argparse, json, math, pathlib, struct, sys

CT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def load(p):
    b = pathlib.Path(p).read_bytes()
    off, js, bin_ = 12, None, None
    while off + 8 <= len(b):
        clen, ctype = struct.unpack("<II", b[off:off + 8])
        body = b[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A: js = json.loads(body.decode("utf-8", "replace"))
        elif ctype == 0x004E4942: bin_ = body
        off += 8 + clen + ((4 - clen % 4) % 4)
    return js, bin_


def rd(j, bin_, idx):
    a = (j.get("accessors") or [])[idx]
    bv = (j.get("bufferViews") or [])[a["bufferView"]]
    fmt, sz = CT[a["componentType"]]; n = NC[a["type"]]
    stride = bv.get("byteStride") or (sz * n)
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from("<" + fmt * n, bin_, base + i * stride) for i in range(a["count"])]


def tri_area_3d(a, b, c):
    u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
    cr = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    return 0.5 * math.sqrt(sum(x * x for x in cr))


def tri_area_uv(a, b, c):
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--json", default="")
    a = ap.parse_args()
    rows = []
    print("  ═══ UV 拉伸读数（零依赖）═══")
    print("   %-44s %-7s %-10s %-10s %-9s %s" % ("件", "三角", "密度中位", "p95", "★拉伸比", "判"))
    for f in a.files:
        p = pathlib.Path(f)
        if not p.exists(): print("   %-44s ★不在" % p.name[:44]); continue
        j, bin_ = load(p)
        rs = []
        for m in (j.get("meshes") or []):
            for pr in (m.get("primitives") or []):
                at = pr.get("attributes") or {}
                if not (isinstance(at.get("TEXCOORD_0"), int) and isinstance(at.get("POSITION"), int)): continue
                pos = rd(j, bin_, at["POSITION"]); uv = rd(j, bin_, at["TEXCOORD_0"])
                idx = [x[0] for x in rd(j, bin_, pr["indices"])] if isinstance(pr.get("indices"), int) else list(range(len(pos)))
                for i in range(0, len(idx) - 2, 3):
                    i0, i1, i2 = idx[i], idx[i + 1], idx[i + 2]
                    a3 = tri_area_3d(pos[i0], pos[i1], pos[i2]); a2 = tri_area_uv(uv[i0], uv[i1], uv[i2])
                    if a3 > 1e-9 and a2 > 1e-12: rs.append(a2 / a3)
        if not rs: print("   %-44s ★无可算之三角" % p.name[:44]); continue
        rs.sort()
        med = rs[len(rs) // 2]; p95 = rs[int(len(rs) * 0.95)]
        ratio = (rs[-1] / med) if med > 0 else float("inf")
        ok = ratio <= 4.0
        print("   %-44s %-7d %-10.2f %-10.2f ★%-8.2f %s" % (p.name[:44], len(rs), med, p95, ratio,
                                                          "✓ 可接受" if ok else "★严重拉伸"))
        rows.append({"file": p.name, "tris": len(rs), "median": round(med, 4), "p95": round(p95, 4),
                     "max": round(rs[-1], 4), "stretch_ratio": round(ratio, 3), "ok": ok})
    if rows:
        bad = sum(1 for r in rows if not r["ok"])
        print("   ⇒ 汇总：%d／%d 件达标（拉伸比 ≤4）；★严重拉伸 %d 件" % (len(rows) - bad, len(rows), bad))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
