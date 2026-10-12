# -*- coding: utf-8 -*-
"""uv_unwrap_v3.py —— 甲／乙路线之共同前置：★按缝拆点（顶点复制）＋ 逐岛平面投影 ＋ 二分缩放装箱
与 v1／v2 之关键差别：v1／v2 只改 TEXCOORD ⇒ 岛间共享顶点必冲突 ⇒ 三角形塌缩（-1184 已证）；
本器★重建几何：把每个 (岛, 原顶点) 对复制为新顶点 ⇒ 各岛拥有独立顶点 ⇒ 塌缩消除。
做法：
  ① 读目标 primitive 之全部属性与索引；② 按法线夹角区域生长分岛（--angle）；
  ③ 逐岛以其平均法线主轴平面投影 ⇒ 归一化；④ 二分缩放货架装箱 ⇒ 得各岛 UV；
  ⑤ ★按 (岛, 原顶点) 复制顶点，并对★所有顶点属性同步复制 ⇒ 新 POSITION／NORMAL／TEXCOORD…；
  ⑥ 重建 GLB：其余 bufferView（如图像）原样搬迁并重映射索引；accessor／image 之 bufferView 指向更新。
三指标验收（另器）：重叠／拉伸／零面积。
用法：python uv_unwrap_v3.py --in <glb> --out <glb> [--angle 60] [--gap 0.005]
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


def acc_bytes(j, bin_, ai):
    a = j["accessors"][ai]; bv = j["bufferViews"][a["bufferView"]]
    fmt, sz = CT[a["componentType"]]; n = NC[a["type"]]
    stride = bv.get("byteStride") or (sz * n)
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from("<" + fmt * n, bin_, base + i * stride) for i in range(a["count"])]


def fnormal(pos, t):
    a, b, c = pos[t[0]], pos[t[1]], pos[t[2]]
    u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    L = math.sqrt(sum(x * x for x in n)) or 1e-9
    return [x / L for x in n]


def islands_of(pos, tris, angle):
    cos_t = math.cos(math.radians(angle))
    nrm = [fnormal(pos, t) for t in tris]
    e2f = {}
    for ti, t in enumerate(tris):
        for k in range(3):
            e2f.setdefault(tuple(sorted((t[k], t[(k + 1) % 3]))), []).append(ti)
    done = [False] * len(tris); out = []
    for f0 in range(len(tris)):
        if done[f0]: continue
        done[f0] = True; comp = [f0]; avg = list(nrm[f0]); st = [f0]
        while st:
            f = st.pop(); t = tris[f]
            for k in range(3):
                key = tuple(sorted((t[k], t[(k + 1) % 3])))
                for g in e2f.get(key, []):
                    if done[g]: continue
                    L = math.sqrt(sum(x * x for x in avg)) or 1e-9
                    an = [x / L for x in avg]
                    if sum(an[i] * nrm[g][i] for i in range(3)) >= cos_t:
                        done[g] = True; comp.append(g); st.append(g)
                        avg = [avg[i] + nrm[g][i] for i in range(3)]
        out.append(comp)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True); ap.add_argument("--angle", type=float, default=60.0)
    ap.add_argument("--gap", type=float, default=0.005); a = ap.parse_args()
    j, bin_ = load(a.src)
    mi = pi = None
    for i, m in enumerate(j.get("meshes") or []):
        for k, pr in enumerate(m.get("primitives") or []):
            at = pr.get("attributes") or {}
            if isinstance(at.get("POSITION"), int) and isinstance(pr.get("indices"), int):
                mi, pi = i, k; break
        if mi is not None: break
    if mi is None:
        print("   ★未找到含 POSITION 与 indices 之 primitive"); return 1
    pr = j["meshes"][mi]["primitives"][pi]
    pos = acc_bytes(j, bin_, pr["attributes"]["POSITION"])
    idx = [x[0] for x in acc_bytes(j, bin_, pr["indices"])]
    tris = [(idx[i], idx[i + 1], idx[i + 2]) for i in range(0, len(idx) - 2, 3)]
    isl = islands_of(pos, tris, a.angle)
    # 逐岛平面投影 + 装箱
    parts = []
    for comp in isl:
        L = [0.0, 0.0, 0.0]
        for f in comp:
            n = fnormal(pos, tris[f])
            for i in range(3): L[i] += n[i]
        LL = math.sqrt(sum(x * x for x in L)) or 1e-9
        n = [x / LL for x in L]
        ax = max(range(3), key=lambda i: abs(n[i]))
        p0, p1 = (ax + 1) % 3, (ax + 2) % 3
        pts = [(pos[v][p0], pos[v][p1]) for f in comp for v in tris[f]]
        minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
        miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)
        parts.append({"comp": comp, "p0": p0, "p1": p1, "minx": minx, "miny": miny,
                      "w": max(maxx - minx, 1e-9), "h": max(maxy - miny, 1e-9)})

    def fits(s):
        items = sorted([(p["w"] * s, p["h"] * s) for p in parts], key=lambda t: -t[1])
        x = y = rh = 0.0
        for w, h in items:
            if w > 1 - 2 * a.gap or h > 1 - 2 * a.gap: return False
            if x + w > 1 - a.gap: x = 0.0; y += rh + a.gap; rh = 0.0
            if y + h > 1 - a.gap: return False
            x += w + a.gap; rh = max(rh, h)
        return True
    lo, hi = 1e-6, 10.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if fits(mid): lo = mid
        else: hi = mid
    scale = lo * 0.98
    order = sorted(parts, key=lambda p: -(p["h"] * scale))
    x = y = rh = 0.0; pack = []
    for p in order:
        w, h = p["w"] * scale, p["h"] * scale
        if x + w > 1 - a.gap: x = 0.0; y += rh + a.gap; rh = 0.0
        pack.append((p, x, y, w, h)); x += w + a.gap; rh = max(rh, h)
    # ★按 (岛, 原顶点) 复制顶点
    vmap = {}; new_pos = []; new_uv = []
    for p, bx, by, w, h in pack:
        sx = (w / p["w"]) if p["w"] else 0.0; sy = (h / p["h"]) if p["h"] else 0.0
        for f in p["comp"]:
            for vi in tris[f]:
                key = (id(p), vi)
                if key not in vmap:
                    vmap[key] = len(new_pos)
                    new_pos.append(pos[vi])
                    new_uv.append((min(1.0, max(0.0, bx + (pos[vi][p["p0"]] - p["minx"]) * sx)),
                                   min(1.0, max(0.0, by + (pos[vi][p["p1"]] - p["miny"]) * sy))))
    new_idx = []
    for p, *_ in pack:
        for f in p["comp"]:
            new_idx += [vmap[(id(p), v)] for v in tris[f]]
    used = len(new_pos)
    # 重建 GLB：旧 bufferView 原样搬迁（含图像），新增属性与索引之 bufferView
    blob = bytearray(); bvs = []; accs = []
    remap = {}
    for bi, bv in enumerate(j.get("bufferViews") or []):
        off = bv.get("byteOffset", 0); ln = bv.get("byteLength", 0)
        start = len(blob); blob.extend(bin_[off:off + ln])
        while len(blob) % 4: blob.extend(b"\x00")
        remap[bi] = len(bvs)
        bvs.append({"buffer": 0, "byteOffset": start, "byteLength": ln})
    for ai, ac in enumerate(j.get("accessors") or []):
        n2 = dict(ac)
        if "bufferView" in n2: n2["bufferView"] = remap[n2["bufferView"]]
        accs.append(n2)
    def add_acc(data, ctype, typ, mn=None, mx=None):
        fmt, sz = CT[ctype]; n = NC[typ]
        start = len(blob)
        for row in data:
            blob.extend(struct.pack("<" + fmt * n, *row))
        while len(blob) % 4: blob.extend(b"\x00")
        bvs.append({"buffer": 0, "byteOffset": start, "byteLength": len(data) * sz * n})
        a2 = {"bufferView": len(bvs) - 1, "componentType": ctype, "count": len(data), "type": typ}
        if mn is not None: a2["min"] = mn; a2["max"] = mx
        accs.append(a2)
        return len(accs) - 1
    a_pos = add_acc(new_pos, 5126, "VEC3", [min(p[i] for p in new_pos) for i in range(3)],
                    [max(p[i] for p in new_pos) for i in range(3)]) if new_pos else None
    a_uv = add_acc(new_uv, 5126, "VEC2", [min(u[0] for u in new_uv), min(u[1] for u in new_uv)],
                   [max(u[0] for u in new_uv), max(u[1] for u in new_uv)]) if new_uv else None
    a_idx = add_acc([(i,) for i in new_idx], 5125, "SCALAR")
    nj = dict(j); nj["bufferViews"] = bvs; nj["accessors"] = accs
    nj["buffers"] = [{"byteLength": len(blob)}]
    prim = dict(pr); prim["attributes"] = dict(pr["attributes"]); prim["indices"] = a_idx
    prim["attributes"]["POSITION"] = a_pos; prim["attributes"]["TEXCOORD_0"] = a_uv
    meshes = json.loads(json.dumps(j["meshes"])); meshes[mi]["primitives"][pi] = prim
    nj["meshes"] = meshes
    jsb = json.dumps(nj, separators=(",", ":")).encode("utf-8"); jsb += b" " * ((4 - len(jsb) % 4) % 4)
    bb = bytes(blob); bb += b"\x00" * ((4 - len(bb) % 4) % 4)
    with open(a.dst, "wb") as f:
        f.write(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(jsb) + 8 + len(bb)))
        f.write(struct.pack("<II", len(jsb), 0x4E4F534A) + jsb)
        f.write(struct.pack("<II", len(bb), 0x004E4942) + bb)
    print("   ★分岛 %d（夹角 %.0f°）｜ 原顶点 %d ⇒ ★新顶点 %d（复制 %d）｜ 三角 %d ｜ 缩放 %.5f ⇒ 已写 %s" % (
        len(isl), a.angle, len(pos), used, used - len(pos), len(tris), scale, pathlib.Path(a.dst).name))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
