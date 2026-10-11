# -*- coding: utf-8 -*-
"""批量为 12 件 Tripo 资产出缩览（零依赖）=> 4x3 总览接触表 + 逐件统计
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
TW, TH = 320, 180          # 每格
COLS, ROWS = 4, 3
sheet = Image.new("RGB", (TW*COLS, TH*ROWS), (10, 11, 16))
d = ImageDraw.Draw(sheet)
R = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "op": "tripo-batch-thumbnails", "assets": []}
t0 = time.time()
files = sorted(SRC.glob("tripo_convert_*.glb"))
for i, g in enumerate(files[:COLS*ROWS]):
    try:
        raw = g.read_bytes()
        jl = struct.unpack("<I", raw[12:16])[0]
        G = json.loads(raw[20:20+jl].decode("utf-8", "replace"))
        prim = G["meshes"][0]["primitives"][0]
        acc = G["accessors"][prim["attributes"]["POSITION"]]
        bv = G["bufferViews"][acc["bufferView"]]
        off = 20 + jl + 8 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        V = np.frombuffer(raw, dtype="<f4", count=acc["count"]*3, offset=off).reshape(-1, 3).astype(np.float32)
        step = max(1, len(V)//4000)
        V = V[::step]
        c = (V.max(0)+V.min(0))/2.0; Vc = V-c
        size = float(np.abs(Vc).max())*2.05
        s = min(TW/size, TH/size)
        px = (Vc[:,0]*s + TW/2).astype(np.int32); py = (-Vc[:,1]*s + TH/2).astype(np.int32)
        ok = (px>=0)&(px<TW)&(py>=0)&(py<TH)
        img = np.zeros((TH, TW), dtype=np.float32)
        zn = (Vc[ok,2]-Vc[:,2].min())/max(1e-6,(Vc[:,2].max()-Vc[:,2].min()))
        np.maximum.at(img, (py[ok], px[ok]), 0.35+0.65*zn)
        sh = img.copy()
        for dy in (-1,0,1):
            for dx in (-1,0,1): sh = np.maximum(sh, np.roll(np.roll(img,dy,0),dx,1))
        rgb = np.stack([sh*0.75+0.05, sh*0.85+0.06, sh*1.0+0.08], -1)
        tile = Image.fromarray((np.clip(rgb,0,1)*255).astype(np.uint8), "RGB")
        r, cidx = divmod(i, COLS)
        sheet.paste(tile, (cidx*TW, r*TH))
        cover = float((sh>0.05).mean()*100)
        R["assets"].append({"file": g.name[:30], "mb": round(g.stat().st_size/1048576,1),
                            "verts": int(acc["count"]), "tris": 0, "cover": round(cover,2),
                            "bbox": [round(float(x),3) for x in (V.max(0)-V.min(0))]})
        d.text((cidx*TW+8, r*TH+6), "#%d %s" % (i+1, g.name.replace("tripo_convert_","")[:18]), fill=(225,228,240))
        d.text((cidx*TW+8, r*TH+TH-16), "%.1fMB %s v | cover %.1f%%" % (R["assets"][-1]["mb"], format(acc["count"],","), cover), fill=(170,178,192))
    except Exception as e:
        print("   ⚠ %s 失败：%s" % (g.name[:24], str(e)[:60]))
        R["assets"].append({"file": g.name[:30], "error": str(e)[:80]})
sheet = sheet.resize((TW*COLS//2, TH*ROWS//2), Image.LANCZOS)
out = SEAT/"exp"/"tripo_assets_contact_sheet_20261011.png"
sheet.save(out)
print("  ═══ 出总览接触表 %s（%dx%d，%.1f KB，耗时 %.1f s）═══" % (out.name, sheet.width, sheet.height, out.stat().st_size/1024, time.time()-t0))
for a in R["assets"][:12]:
    if "error" in a: print("   · %-32s ⚠ %s" % (a["file"], a["error"][:40])); continue
    print("   · %-32s %5.1fMB %10s v ｜ 覆盖 %5.2f%% ｜ 尺寸比 %.2f/%.2f/%.2f" % (
        a["file"], a["mb"], format(a["verts"],","), a["cover"], a["bbox"][0], a["bbox"][1], a["bbox"][2]))
R["out"] = out.name; R["secs"] = round(time.time()-t0, 1)
(EX/"tripo_assets_contact_20261011.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("  落盘：tripo_assets_contact_20261011.json")
