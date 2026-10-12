# -*- coding: utf-8 -*-
"""glb_facets.py —— 读 GLB 之真实面数（零依赖：只解析 GLB 头与 JSON chunk，不碰二进制体）
用法：python glb_facets.py <文件1> [<文件2> …] [--json out]
输出：各件之 meshes 数、primitives 数、索引数 ⇒ 面数（索引数／3，或顶点数／3 之兜底）
（中文串一律用「」）
"""
import argparse, json, pathlib, struct, sys, time


def read_glb(p):
    b = pathlib.Path(p).read_bytes()
    if b[:4] != b"glTF":
        return None, "非 GLB（magic=%r）" % b[:4]
    ver, length = struct.unpack("<II", b[4:12])
    off = 12
    js = None
    while off + 8 <= len(b):
        clen, ctype = struct.unpack("<II", b[off:off + 8])
        body = b[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:            # 'JSON'
            js = json.loads(body.decode("utf-8", "replace"))
            break
        off += 8 + clen + ((4 - clen % 4) % 4)
    return js, None


def facets(j):
    meshes = j.get("meshes") or []
    accs = j.get("accessors") or []
    tri = 0
    prims = 0
    verts = 0
    for m in meshes:
        for pr in (m.get("primitives") or []):
            prims += 1
            ia = pr.get("indices")
            if isinstance(ia, int) and ia < len(accs):
                c = accs[ia].get("count") or 0
                tri += c // 3
            pa = (pr.get("attributes") or {}).get("POSITION")
            if isinstance(pa, int) and pa < len(accs):
                verts += accs[pa].get("count") or 0
    return {"meshes": len(meshes), "primitives": prims, "triangles": tri, "vertices": verts,
            "materials": len(j.get("materials") or []), "images": len(j.get("images") or []),
            "animations": len(j.get("animations") or []), "nodes": len(j.get("nodes") or [])}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--json", default="")
    a = ap.parse_args()
    out = []
    print("  ═══ GLB 面数核（零依赖解析）═══")
    print("   %-46s %-8s %-9s %-8s %-8s %s" % ("件", "网格", "三角面", "顶点", "动画", "材质/图"))
    for f in a.files:
        p = pathlib.Path(f)
        if not p.exists():
            print("   %-46s ★不在" % p.name[:46]); continue
        j, err = read_glb(p)
        if err or j is None:
            print("   %-46s ★%s" % (p.name[:46], err)); continue
        d = facets(j); d["file"] = p.name; d["size_kb"] = round(p.stat().st_size / 1024, 1)
        out.append(d)
        print("   %-46s %-8d %-9d %-8d %-8d %d/%d" % (p.name[:46], d["meshes"], d["triangles"], d["vertices"],
                                                      d["animations"], d["materials"], d["images"]))
    if out:
        base = out[0]["triangles"] or 1
        print("   ── 相对首件之三角面比 ──")
        for d in out:
            print("     %-46s %6.3f（%d 面）" % (d["file"][:46], d["triangles"] / base, d["triangles"]))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "rows": out},
                                                   ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
