# -*- coding: utf-8 -*-
"""glb_anim_add.py —— 为静态 GLB 追加一个最小关键帧动画（2026-10-12 立，应 -1366 之缺）
由来：-1366 核验席位 assets/ 之 6 件 GLB ⇒ ★结构完整但 animations 0 ⇒ 与令条「动态完善」有距。
本器（★零外呼；纯本地）：
  ① 读入 GLB（JSON 块 ＋ BIN 块）；② 生成"张望"关键帧（绕 Y 轴 ±10°，3 帧：0／1.5／3.0 s）；
  ③ 追加 bufferView／accessor（input 带 min/max，合规范）＋ animations 段；④ 重打包（4 字节对齐）；
  ⑤ 写新件并以结构解析复核
判据（可失败）：①头与长度自洽；②★animations ≥1；③通道之 node/path 有效
用法：python glb_anim_add.py --src <glb> --out <glb> [--deg 10] [--dur 3.0]
（中文串一律用「」）
"""
import argparse, json, math, pathlib, struct, sys


def read_glb(p):
    b = pathlib.Path(p).read_bytes()
    if b[:4] != b"glTF":
        raise ValueError("非 GLB")
    ln = struct.unpack("<I", b[8:12])[0]
    off, chunks = 12, []
    while off + 8 <= len(b):
        cl = struct.unpack("<I", b[off:off+4])[0]; ct = b[off+4:off+8]
        chunks.append((ct, b[off+8:off+8+cl])); off += 8 + cl
    j = json.loads(chunks[0][1].decode("utf-8"))
    bin_ = chunks[1][1] if len(chunks) > 1 else b""
    return b, j, bin_, ln


def write_glb(p, j, bin_):
    js = json.dumps(j, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)                 # ★JSON 块以空格补齐
    bn = bin_ + b"\x00" * ((4 - len(bin_) % 4) % 4)   # ★BIN 块以零补齐
    total = 12 + 8 + len(js) + (8 + len(bn) if bn else 0)
    out = b"glTF" + struct.pack("<II", 2, total) + struct.pack("<I", len(js)) + b"JSON" + js
    if bn:
        out += struct.pack("<I", len(bn)) + b"BIN\x00" + bn
    pathlib.Path(p).write_bytes(out)
    return total


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--deg", type=float, default=10.0); ap.add_argument("--dur", type=float, default=3.0)
    a = ap.parse_args()
    print("  ═══ 为静态 GLB 追加最小关键帧动画（★零外呼）═══")
    raw, j, bin_, ln = read_glb(a.src)
    print("   源：%s（%d B ｜ 声明长 %d ⇒ %s）" % (pathlib.Path(a.src).name, len(raw), ln,
                                                  "一致" if ln == len(raw) else "★不一致"))
    print("   ★源动画数 %d ｜ 节点 %d ｜ 网格 %d" % (len(j.get("animations") or []), len(j.get("nodes") or []),
                                                   len(j.get("meshes") or [])))
    if not j.get("nodes"):
        print("   ⇒ 判：★无节点，无法动，止"); return 2
    # ★追加数据：times（float32）＋ rotations（float32 ×4）
    times = [0.0, a.dur/2, a.dur]
    th = math.radians(a.deg)/2.0
    quats = [[0.0, 0.0, 0.0, 1.0],
             [0.0, math.sin(th), 0.0, math.cos(th)],
             [0.0, 0.0, 0.0, 1.0]]
    buf = j.setdefault("buffers", [{}])
    base = len(bin_)
    bv = j.setdefault("bufferViews", []); ac = j.setdefault("accessors", [])
    t_off = base
    t_bytes = b"".join(struct.pack("<f", t) for t in times)
    r_off = base + len(t_bytes)
    r_bytes = b"".join(struct.pack("<f", x) for q in quats for x in q)
    bin_ = bin_ + t_bytes + r_bytes
    i_bv = len(bv); bv.append({"buffer": 0, "byteOffset": t_off, "byteLength": len(t_bytes)})
    o_bv = len(bv); bv.append({"buffer": 0, "byteOffset": r_off, "byteLength": len(r_bytes)})
    i_ac = len(ac); ac.append({"bufferView": i_bv, "componentType": 5126, "count": len(times), "type": "SCALAR",
                              "min": [min(times)], "max": [max(times)]})   # ★动画输入须带 min/max
    o_ac = len(ac); ac.append({"bufferView": o_bv, "componentType": 5126, "count": len(quats), "type": "VEC4"})
    anims = j.setdefault("animations", [])
    anims.append({"name": "张望（绕 Y ±%g°）" % a.deg,
                  "samplers": [{"input": i_ac, "output": o_ac, "interpolation": "LINEAR"}],
                  "channels": [{"sampler": 0, "target": {"node": 0, "path": "rotation"}}]})
    buf[0]["byteLength"] = len(bin_)
    total = write_glb(a.out, j, bin_)
    # ★复核
    raw2, j2, bin2, ln2 = read_glb(a.out)
    ok_hdr = (ln2 == len(raw2) == total)
    na = len(j2.get("animations") or [])
    ch = (j2["animations"][0]["channels"][0]) if na else {}
    ok_ch = bool(ch) and ch.get("target", {}).get("node") == 0 and ch.get("target", {}).get("path") == "rotation"
    print("   ★已写：%s（%d B）" % (pathlib.Path(a.out).name, total))
    print("   ★复核：头/长自洽 %s ｜ animations %d ｜ 通道 node=%s path=%s"
          % (ok_hdr, na, ch.get("target", {}).get("node"), ch.get("target", {}).get("path")))
    crit = {"①头与长度自洽": ok_hdr, "②★animations ≥1": na >= 1, "③通道之 node/path 有效": ok_ch}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
