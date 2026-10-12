# -*- coding: utf-8 -*-
"""uv_unwrap_v4.py —— 岛内参数化（★Tutte 均值嵌入）＋ 拆点 ＋ 装箱（零依赖／纯本地／零花费）
为何选 Tutte 而非 LSCM：★Tutte 定理 —— 若把"盘拓扑"岛之边界映到★凸多边形（此处取圆周），
  内部顶点取邻居之加权平均，则所得嵌入★无翻转（即二维上不重叠）⇒ 此为"无重叠"之硬保证；
  LSCM 只最小化保角能量，无此保证（亦可能翻转）。
做法（逐岛）：
  ① 取岛之顶点与边；② 找边界（在本岛内只被一个三角使用的边）之环；
  ③ 若岛有边界（盘拓扑）⇒ 边界按弧长映到圆周；内部顶点解"均值坐标"线性系统（Jacobi 或 numpy 直接解）；
  ④ 若岛无边界（闭合面片，如孤立多面体）⇒ ★回退为平面投影（Tutte 不适用，如实记）；
  ⑤ 归一化 ⇒ 按岛包围盒二分缩放货架装箱；⑥ 按 (岛, 顶点) 拆点并复制全部属性；⑦ 重建 GLB。
用法：python uv_unwrap_v4.py --in <glb> --out <glb> [--gap 0.01] [--iters 400]
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


def acc(j, bin_, ai):
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


def islands(pos, tris, angle):
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


def tutte(pos, comp, tris, iters=400):
    """★Tutte 均值嵌入：边界→圆周，内部→邻居平均（Jacobi 迭代，零依赖）。
    返回 {原顶点: (u,v)}（岛局部坐标）；若无边界 ⇒ 返回 None（调用方回退）。"""
    vs = sorted({v for f in comp for v in tris[f]})
    vset = set(vs)
    # 岛内边与其面数
    ec = {}
    for f in comp:
        t = tris[f]
        for k in range(3):
            e = tuple(sorted((t[k], t[(k + 1) % 3])))
            ec[e] = ec.get(e, 0) + 1
    bedges = [e for e, c in ec.items() if c == 1]
    if not bedges: return None, "无边界（闭合面片）"
    # 邻接
    adj = {v: set() for v in vs}
    for a_, b_ in ec:
        adj[a_].add(b_); adj[b_].add(a_)
    # 边界环（从任一边界边出发走）
    nxt = {}
    for a_, b_ in bedges:
        nxt.setdefault(a_, []).append(b_); nxt.setdefault(b_, []).append(a_)
    start = bedges[0][0]; loop = [start]; prev = None; cur = start
    for _ in range(len(bedges) + 2):
        cand = [x for x in nxt.get(cur, []) if x != prev]
        if not cand: break
        nx = cand[0]
        if nx == start: break
        loop.append(nx); prev, cur = cur, nx
    if len(loop) < 3: return None, "边界环过短"
    bl = set(loop)
    # 边界 → 单位圆（弧长参数）
    m = len(loop); uv = {}
    cum = [0.0]
    for i in range(1, m + 1):
        a_ = pos[loop[(i - 1) % m]]; b_ = pos[loop[i % m]]
        cum.append(cum[-1] + math.dist(a_, b_))
    total = cum[-1] or 1.0
    for i, v in enumerate(loop):
        th = 2 * math.pi * (cum[i] / total)
        uv[v] = (0.5 + 0.5 * math.cos(th), 0.5 + 0.5 * math.sin(th))
    inner = [v for v in vs if v not in bl]
    if not inner:
        return uv, "边界环（无内部点）"
    for v in inner: uv[v] = (0.5, 0.5)
    for _ in range(iters):
        for v in inner:
            nb = adj[v]
            if not nb: continue
            su = sum(uv[w][0] for w in nb); sv = sum(uv[w][1] for w in nb)
            uv[v] = (su / len(nb), sv / len(nb))
    return uv, "Tutte"


def planar(pos, comp, tris):
    L = [0.0, 0.0, 0.0]
    for f in comp:
        n = fnormal(pos, tris[f])
        for i in range(3): L[i] += n[i]
    LL = math.sqrt(sum(x * x for x in L)) or 1e-9
    n = [x / LL for x in L]
    ax = max(range(3), key=lambda i: abs(n[i]))
    p0, p1 = (ax + 1) % 3, (ax + 2) % 3
    uv = {}
    for f in comp:
        for v in tris[f]: uv[v] = (pos[v][p0], pos[v][p1])
    return uv, (p0, p1)


def norm_and_pack(parts, gap):
    for p in parts:
        us = [uv[0] for uv in p["uv"].values()]; vss = [uv[1] for uv in p["uv"].values()]
        p["minx"], p["miny"] = min(us), min(vss)
        p["w"] = max(max(us) - p["minx"], 1e-9); p["h"] = max(max(vss) - p["miny"], 1e-9)
    def fits(s):
        items = sorted([(p["w"] * s, p["h"] * s) for p in parts], key=lambda t: -t[1])
        x = y = rh = 0.0
        for w, h in items:
            if w > 1 - 2 * gap or h > 1 - 2 * gap: return False
            if x + w > 1 - gap: x = 0.0; y += rh + gap; rh = 0.0
            if y + h > 1 - gap: return False
            x += w + gap; rh = max(rh, h)
        return True
    lo, hi = 1e-9, 10.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if fits(mid): lo = mid
        else: hi = mid
    s = lo * 0.98
    order = sorted(parts, key=lambda p: -(p["h"] * s))
    x = y = rh = 0.0; placed = []
    for p in order:
        w, h = p["w"] * s, p["h"] * s
        if x + w > 1 - gap: x = 0.0; y += rh + gap; rh = 0.0
        placed.append((p, x, y, w, h)); x += w + gap; rh = max(rh, h)
    return placed, s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True); ap.add_argument("--angle", type=float, default=60.0)
    ap.add_argument("--gap", type=float, default=0.01); ap.add_argument("--iters", type=int, default=400)
    a = ap.parse_args()
    j, bin_ = load(a.src)
    mi = pi = None
    for i, m in enumerate(j.get("meshes") or []):
        for k, pr in enumerate(m.get("primitives") or []):
            at = pr.get("attributes") or {}
            if isinstance(at.get("POSITION"), int) and isinstance(pr.get("indices"), int): mi, pi = i, k; break
        if mi is not None: break
    if mi is None: print("   ★未找到可用 primitive"); return 1
    pr = j["meshes"][mi]["primitives"][pi]
    pos = acc(j, bin_, pr["attributes"]["POSITION"])
    idx = [x[0] for x in acc(j, bin_, pr["indices"])]
    tris = [(idx[i], idx[i + 1], idx[i + 2]) for i in range(0, len(idx) - 2, 3)]
    isl = islands(pos, tris, a.angle)
    parts = []; n_tutte = n_planar = 0
    for comp in isl:
        uv, how = tutte(pos, comp, tris, a.iters)
        if uv is None:
            uv, _pv = planar(pos, comp, tris); n_planar += 1
        else:
            n_tutte += 1
        parts.append({"comp": comp, "uv": uv})
    placed, s = norm_and_pack(parts, a.gap)
    vmap = {}; new_pos = []; new_uv = []
    for p, bx, by, w, h in placed:
        sx = (w / p["w"]) if p["w"] else 0.0; sy = (h / p["h"]) if p["h"] else 0.0
        for f in p["comp"]:
            for v in tris[f]:
                key = (id(p), v)
                if key not in vmap:
                    vmap[key] = len(new_pos); new_pos.append(pos[v])
                    u0, v0 = p["uv"][v]
                    new_uv.append((min(1.0, max(0.0, bx + (u0 - p["minx"]) * sx)),
                                   min(1.0, max(0.0, by + (v0 - p["miny"]) * sy))))
    new_idx = []
    for p, *_ in placed:
        for f in p["comp"]:
            new_idx += [vmap[(id(p), v)] for v in tris[f]]
    # 重建 GLB（同 v3：旧 bufferView 原样搬迁 + 重映射）
    blob = bytearray(); bvs = []; accs = []; remap = {}
    for bi, bv in enumerate(j.get("bufferViews") or []):
        off = bv.get("byteOffset", 0); ln = bv.get("byteLength", 0)
        start = len(blob); blob.extend(bin_[off:off + ln])
        while len(blob) % 4: blob.extend(b"\x00")
        remap[bi] = len(bvs); bvs.append({"buffer": 0, "byteOffset": start, "byteLength": ln})
    for ac in (j.get("accessors") or []):
        n2 = dict(ac)
        if "bufferView" in n2: n2["bufferView"] = remap[n2["bufferView"]]
        accs.append(n2)
    def add_acc(data, ctype, typ, mn=None, mx=None):
        fmt, sz = CT[ctype]; n = NC[typ]
        start = len(blob)
        for row in data: blob.extend(struct.pack("<" + fmt * n, *row))
        while len(blob) % 4: blob.extend(b"\x00")
        bvs.append({"buffer": 0, "byteOffset": start, "byteLength": len(data) * sz * n})
        a2 = {"bufferView": len(bvs) - 1, "componentType": ctype, "count": len(data), "type": typ}
        if mn is not None: a2["min"] = mn; a2["max"] = mx
        accs.append(a2); return len(accs) - 1
    a_pos = add_acc(new_pos, 5126, "VEC3", [min(p[i] for p in new_pos) for i in range(3)],
                    [max(p[i] for p in new_pos) for i in range(3)])
    a_uv = add_acc(new_uv, 5126, "VEC2", [min(u[0] for u in new_uv), min(u[1] for u in new_uv)],
                   [max(u[0] for u in new_uv), max(u[1] for u in new_uv)])
    a_idx = add_acc([(i,) for i in new_idx], 5125, "SCALAR")
    nj = dict(j); nj["bufferViews"] = bvs; nj["accessors"] = accs; nj["buffers"] = [{"byteLength": len(blob)}]
    prim = dict(pr); prim["attributes"] = dict(pr["attributes"]); prim["indices"] = a_idx
    prim["attributes"]["POSITION"] = a_pos; prim["attributes"]["TEXCOORD_0"] = a_uv
    meshes = json.loads(json.dumps(j["meshes"])); meshes[mi]["primitives"][pi] = prim; nj["meshes"] = meshes
    jsb = json.dumps(nj, separators=(",", ":")).encode("utf-8"); jsb += b" " * ((4 - len(jsb) % 4) % 4)
    bb = bytes(blob); bb += b"\x00" * ((4 - len(bb) % 4) % 4)
    with open(a.dst, "wb") as f:
        f.write(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(jsb) + 8 + len(bb)))
        f.write(struct.pack("<II", len(jsb), 0x4E4F534A) + jsb)
        f.write(struct.pack("<II", len(bb), 0x004E4942) + bb)
    print("   ★分岛 %d ｜ ★Tutte %d ／ ★回退平面投影 %d ｜ 原顶点 %d ⇒ 新顶点 %d ｜ 三角 %d ｜ 缩放 %.5f ⇒ 已写 %s" % (
        len(isl), n_tutte, n_planar, len(pos), len(new_pos), len(tris), s, pathlib.Path(a.dst).name))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
