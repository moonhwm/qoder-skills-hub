# -*- coding: utf-8 -*-
"""零依赖渲染：从 Tripo GLB 抽顶点 => 16:9 首帧（无纹理，仅点云剪影+深度着色）
自检：顶点数/包围盒/覆盖率/输出尺寸与字节；不装任何库
（中文串一律用「」）
"""
import json, pathlib, struct, sys, time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import numpy as np
from PIL import Image, ImageDraw

HOME = pathlib.Path.home()
SRC = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"_Download_待清理"/"com.huawei.hmos.browser"
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
g = sorted(SRC.glob("tripo_convert_*.glb"))[0]
print("  ═══ ① 读 %s（%.1f MB）═══" % (g.name[:40], g.stat().st_size/1048576))
t0 = time.time()
raw = g.read_bytes()
jl = struct.unpack("<I", raw[12:16])[0]
G = json.loads(raw[20:20+jl].decode("utf-8", "replace"))
binoff = 20 + jl + 8
prim = G["meshes"][0]["primitives"][0]
ai = prim["attributes"]["POSITION"]
acc = G["accessors"][ai]; bv = G["bufferViews"][acc["bufferView"]]
off = binoff + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
cnt = acc["count"]; comp = {5126: "<f4", 5125: "<u4", 5123: "<u2"}[acc["componentType"]]
arr = np.frombuffer(raw, dtype=np.dtype(comp), count=cnt*3, offset=off).reshape(-1, 3).astype(np.float32)
print("  顶点 %s（%s）｜ 读耗时 %.1f s" % (format(cnt, ","), acc["componentType"], time.time()-t0))
print("  包围盒 min=%s max=%s" % (np.round(arr.min(0), 3).tolist(), np.round(arr.max(0), 3).tolist()))

# ② 抽稀（目标 ~45k 点）
step = max(1, cnt // 45000)
V = arr[::step]
print("  ═══ ② 抽稀 1/%d ⇒ %s 点 ═══" % (step, format(len(V), ",")))

# ③ 正交投影：以 Y 为纵、X 为横（Z 作深度），置于 16:9 画布
W, H = 1280, 720
c = (V.max(0) + V.min(0)) / 2.0
Vc = V - c
size = float(np.abs(Vc).max()) * 2.05
sx = W / size; sy = H / size
s = min(sx, sy)
px = (Vc[:, 0] * s + W/2).astype(np.int32)
py = (-Vc[:, 1] * s + H/2).astype(np.int32)
pz = Vc[:, 2]
ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
print("  画布内 %s／%s 点（%.1f%%）｜ 缩放 %.2f px/unit" % (
    format(int(ok.sum()), ","), format(len(V), ","), 100*ok.sum()/len(V), s))

# ④ 深度着色（远暗近亮）＋ 覆盖率统计
img = np.zeros((H, W), dtype=np.float32)
z = pz[ok]; pxn, pyn = px[ok], py[ok]
zn = (z - z.min()) / max(1e-6, (z.max() - z.min()))
np.maximum.at(img, (pyn, pxn), 0.35 + 0.65 * zn)
# 简易膨胀（3×3）使剪影连成面
sh = img.copy()
for dy in (-1, 0, 1):
    for dx in (-1, 0, 1):
        sh = np.maximum(sh, np.roll(np.roll(img, dy, 0), dx, 1))
cover = float((sh > 0.05).mean() * 100)
print("  ═══ ③ 覆盖率 %.2f%%（膨胀前 %.2f%%）═══" % (cover, float((img > 0.05).mean()*100)))
rgb = np.stack([(sh*0.75+0.05), (sh*0.85+0.06), (sh*1.0+0.08)], axis=-1)
rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
im = Image.fromarray(rgb, "RGB")
d = ImageDraw.Draw(im)
d.text((14, 12), "CAIRN / Tripo asset silhouette (zero-dep numpy render) | verts=%s step=1/%d cover=%.1f%%" % (
    format(len(V), ","), step, cover), fill=(220, 226, 238))
d.text((14, 30), "src=%s" % g.name[:52], fill=(170, 178, 192))
out = SEAT/"exp"/"tripo_silhouette_firstframe_20261011.png"
im.save(out)
R = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "op": "tripo-zero-dep-render",
     "src": g.name, "src_mb": round(g.stat().st_size/1048576, 1), "verts_total": int(cnt),
     "verts_used": int(len(V)), "step": int(step), "canvas": [W, H], "cover_pct": round(cover, 2),
     "bbox_min": np.round(arr.min(0), 3).tolist(), "bbox_max": np.round(arr.max(0), 3).tolist(),
     "out": out.name, "out_kb": round(out.stat().st_size/1024, 1), "secs": round(time.time()-t0, 1)}
(EX/"tripo_silhouette_render_20261011.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("  ═══ ④ 出图 %s（%d×%d，%.1f KB，总耗时 %.1f s）═══" % (out.name, W, H, out.stat().st_size/1024, time.time()-t0))
print("  ⇒ 判：%s" % ("★剪影成立（覆盖率 5–70%%）⇒ 可作首帧候选，待入世验证" if 5 < cover < 70 else "★覆盖率异常 ⇒ 须调"))
