# -*- coding: utf-8 -*-
"""uv_unwrap_v2.py —— 甲案·阶段二之改进版（零依赖、纯本地、零花费）
相对 v1 之两处改进：
  ① 分岛：由"六桶 + 桶内连通"改为 ★按法线夹角做区域生长（阈值 --angle，默认 60°）⇒ 岛更少更大
  ② 打包：由"固定缩放货架"改为 ★二分搜索缩放之货架装箱（按岛高降序）⇒ 提高利用率
双指标（可失败）：①重叠之面占比 ≤0.30（以 glb_uv_check 之 64×64 栅格化为准）②利用率＝各岛包围盒面积和（★不作硬阈值，仅报数）
用法：python uv_unwrap_v2.py --in <glb> --out <glb> [--angle 60] [--gap 0.005] [--json out]
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


def read_acc(j, bin_, idx):
    a = (j.get("accessors") or [])[idx]
    bv = (j.get("bufferViews") or [])[a["bufferView"]]
    fmt, sz = CT[a["componentType"]]; n = NC[a["type"]]
    stride = bv.get("byteStride") or (sz * n)
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from("<" + fmt * n, bin_, base + i * stride) for i in range(a["count"])]


def face_normal(pos, t):
    a, b, c = pos[t[0]], pos[t[1]], pos[t[2]]
    u1 = [b[i] - a[i] for i in range(3)]; u2 = [c[i] - a[i] for i in range(3)]
    n = [u1[1] * u2[2] - u1[2] * u2[1], u1[2] * u2[0] - u1[0] * u2[2], u1[0] * u2[1] - u1[1] * u2[0]]
    L = math.sqrt(sum(x * x for x in n)) or 1e-9
    return [x / L for x in n], L / 2.0


def unwrap(pos, idx, angle_deg=60.0, gap=0.005):
    cos_t = math.cos(math.radians(angle_deg))
    tris = [(idx[i], idx[i + 1], idx[i + 2]) for i in range(0, len(idx) - 2, 3)]
    norms, areas = [], []
    for t in tris:
        n, ar = face_normal(pos, t); norms.append(n); areas.append(ar)
    e2f = {}
    for ti, t in enumerate(tris):
        for k in range(3):
            e2f.setdefault(tuple(sorted((t[k], t[(k + 1) % 3]))), []).append(ti)
    assigned = [False] * len(tris)
    islands = []
    for f0 in range(len(tris)):
        if assigned[f0]: continue
        assigned[f0] = True
        comp = [f0]
        avg = list(norms[f0])
        stack = [f0]
        while stack:
            f = stack.pop()
            t = tris[f]
            for k in range(3):
                key = tuple(sorted((t[k], t[(k + 1) % 3])))
                for g in e2f.get(key, []):
                    if assigned[g]: continue
                    # ★与岛"当前平均法线"之夹角判定
                    L = math.sqrt(sum(x * x for x in avg)) or 1e-9
                    an = [x / L for x in avg]
                    dot = sum(an[i] * norms[g][i] for i in range(3))
                    if dot >= cos_t:
                        assigned[g] = True; comp.append(g); stack.append(g)
                        avg = [avg[i] + norms[g][i] for i in range(3)]
        islands.append(comp)
    # 逐岛：以平均法线定投影平面（取法线主轴为 z，另两轴为平面基）
    parts = []
    for comp in islands:
        L = [0.0, 0.0, 0.0]
        for f in comp:
            for i in range(3): L[i] += norms[f][i]
        LL = math.sqrt(sum(x * x for x in L)) or 1e-9
        n = [x / LL for x in L]
        ax = max(range(3), key=lambda i: abs(n[i]))
        p0, p1 = (ax + 1) % 3, (ax + 2) % 3
        pts = []
        for f in comp:
            for vi in tris[f]: pts.append((pos[vi][p0], pos[vi][p1]))
        minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
        miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)
        w = max(maxx - minx, 1e-9); h = max(maxy - miny, 1e-9)
        parts.append({"comp": comp, "p0": p0, "p1": p1, "minx": minx, "miny": miny, "w": w, "h": h})
    # ★二分搜索缩放：使货架装箱可容
    def fits(scale):
        items = sorted([(p["w"] * scale, p["h"] * scale) for p in parts], key=lambda t: -t[1])
        x = y = row_h = 0.0
        for w, h in items:
            if w > 1.0 - 2 * gap or h > 1.0 - 2 * gap: return False
            if x + w > 1.0 - gap:
                x = 0.0; y += row_h + gap; row_h = 0.0
            if y + h > 1.0 - gap: return False
            x += w + gap; row_h = max(row_h, h)
        return True
    lo, hi = 1e-6, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if fits(mid): lo = mid
        else: hi = mid
    scale = lo * 0.98
    items = sorted(parts, key=lambda p: -(p["h"] * scale))
    x = y = row_h = 0.0
    placed = []
    for p in items:
        w, h = p["w"] * scale, p["h"] * scale
        if x + w > 1.0 - gap:
            x = 0.0; y += row_h + gap; row_h = 0.0
        placed.append((p, x, y, w, h))
        x += w + gap; row_h = max(row_h, h)
    uv = [(0.0, 0.0)] * len(pos)
    util = 0.0
    for p, bx, by, w, h in placed:
        util += w * h
        sx = (w / p["w"]) if p["w"] else 0.0
        sy = (h / p["h"]) if p["h"] else 0.0
        for f in p["comp"]:
            for vi in tris[f]:
                u = bx + (pos[vi][p["p0"]] - p["minx"]) * sx
                v = by + (pos[vi][p["p1"]] - p["miny"]) * sy
                uv[vi] = (min(1.0, max(0.0, u)), min(1.0, max(0.0, v)))
    return uv, {"islands": len(islands), "tris": len(tris), "scale": round(scale, 5),
                "packed_bbox_area": round(util, 4)}


def rebuild(j, bin_, new_uv, out):
    targets = set()
    for m in (j.get("meshes") or []):
        for pr in (m.get("primitives") or []):
            t = (pr.get("attributes") or {}).get("TEXCOORD_0")
            if isinstance(t, int): targets.add(t)
    if not targets: return "无 TEXCOORD_0"
    data = bytearray(bin_)
    for ai in targets:
        a = j["accessors"][ai]; bv = j["bufferViews"][a["bufferView"]]
        base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride") or 8
        cnt = min(a["count"], len(new_uv))
        for i in range(cnt):
            struct.pack_into("<ff", data, base + i * stride, new_uv[i][0], new_uv[i][1])
        us = [new_uv[i][0] for i in range(cnt)]; vs = [new_uv[i][1] for i in range(cnt)]
        if us: a["min"] = [min(us), min(vs)]; a["max"] = [max(us), max(vs)]
    jsb = json.dumps(j, separators=(",", ":")).encode("utf-8"); jsb += b" " * ((4 - len(jsb) % 4) % 4)
    bb = bytes(data); bb += b"\x00" * ((4 - len(bb) % 4) % 4)
    with open(out, "wb") as f:
        f.write(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(jsb) + 8 + len(bb)))
        f.write(struct.pack("<II", len(jsb), 0x4E4F534A) + jsb)
        f.write(struct.pack("<II", len(bb), 0x004E4942) + bb)
    return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True); ap.add_argument("--angle", type=float, default=60.0)
    ap.add_argument("--gap", type=float, default=0.005); ap.add_argument("--json", default="")
    a = ap.parse_args()
    j, bin_ = load(a.src)
    for m in (j.get("meshes") or []):
        for pr in (m.get("primitives") or []):
            at = pr.get("attributes") or {}
            if isinstance(at.get("TEXCOORD_0"), int) and isinstance(at.get("POSITION"), int):
                pos = read_acc(j, bin_, at["POSITION"])
                idx = [x[0] for x in read_acc(j, bin_, pr["indices"])] if isinstance(pr.get("indices"), int) else list(range(len(pos)))
                uv, st = unwrap(pos, idx, a.angle, a.gap)
                err = rebuild(j, bin_, uv, a.dst)
                print("   ★分岛 %d（夹角阈值 %.0f°）｜ 三角 %d ｜ 缩放 %.5f ｜ 岛包围盒面积和 %.4f ⇒ %s" % (
                    st["islands"], a.angle, st["tris"], st["scale"], st["packed_bbox_area"],
                    err or ("已写 " + pathlib.Path(a.dst).name)))
                if a.json: pathlib.Path(a.json).write_text(json.dumps(
                    {"in": pathlib.Path(a.src).name, "angle": a.angle, **st}, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="\n")
                return 0 if not err else 1
    print("   ★未找到含 TEXCOORD_0 与 POSITION 之 primitive"); return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
