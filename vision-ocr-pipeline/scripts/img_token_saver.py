#!/usr/bin/env python3
"""img_token_saver.py — 截图省token预处理（PIL，无需神经网络）
v1.1 2026-08-27 Orchestrator (Kimi K3) — 双角审核修订：死循环校验/横图切片/透明底白合成/crop校验/阈值口径
原理：图像token消耗随像素总量增长；极端长宽比（>1:7）还可能被平台拒收或低效。
     省token的正确方向 = 裁掉无关区域 + 长条切片 + 降到可读最低分辨率，而不是超分放大。
用法:
  python3 img_token_saver.py IN.jpg --mode report [--glyph]   # 诊断（尺寸/长宽比/切片建议；--glyph=OCR估字高）
  python3 img_token_saver.py IN.jpg --mode slice [--screen-h 1080] [--overlap 48]
  python3 img_token_saver.py IN.jpg --mode fit   [--long-side 1568]
  python3 img_token_saver.py IN.jpg --mode crop  --box 0,1800,272,1900 [--zoom 3]
"""
import argparse, os, sys
from PIL import Image

TENCENT_RATIO = 7.0  # 腾讯元器文档口径：图片长宽比不超过1:7（助手甲同系生态的经验警戒线）

def open_rgb_white(path):
    """透明 PNG 合成到白底（直接 convert('RGB') 会把 alpha 变黑底，毁浅色文字）"""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        return Image.alpha_composite(bg, im).convert("RGB")
    return im.convert("RGB")

def report(im, name, glyph=False):
    w, h = im.size
    r = max(w, h) / max(1, min(w, h))
    print(f"[report] {name}: {w}x{h} 像素总量={w*h/1e6:.2f}MP 长宽比=1:{r:.1f}")
    if r > TENCENT_RATIO:
        print(f"  ⚠ 长宽比超过1:{TENCENT_RATIO:.0f}，腾讯系（助手甲/元器）可能拒收或解析低效 → 建议 slice")
    # 切片建议：优先每片长宽比不劣于1:2，单高上限1600px防单片过大
    if h > w:
        per = min(1600, max(2 * w, 768))
        n = (h + per - 1) // per
        if n > 1:
            print(f"  建议切片：--mode slice --screen-h {per}（约{n}片，加48px重叠防断行；"
                  f"w>800 时受1600上限约束长宽比略逊于1:2；slice 默认 screen-h=1080 需显式传此值）")
    # 2026-08-27 实测阈值（references/thresholds_and_pitfalls.md；2图6锚点、自评非盲测，档位有±30%平移误差）：
    print("  阈值参考(±30%误差带)：发Kimi→正文字高≥9px（按字高≈36px@1260w样本外推："
          "手机图宽≥450px/桌面图宽≥900px，像素面积降至~13%，token节省上限~87%，"
          "实际计费以 estimate-token-count 为准）；本地OCR→RapidOCR字高≥6-7px / tesseract≥14px或先回放大")
    if glyph:
        try:
            from rapidocr_onnxruntime import RapidOCR
            res, _ = RapidOCR()(name)
            hs = [max(pt[1] for pt in box) - min(pt[1] for pt in box)
                  for box, txt, _ in (res or []) if any('\u4e00' <= c <= '\u9fff' for c in txt)]
            if hs:
                hs.sort()
                print(f"  [glyph] 汉字行高中位数≈{hs[len(hs)//2]}px（n={len(hs)}，RapidOCR框高粗测±20%）")
        except Exception as e:
            print(f"  [glyph] 字高估测不可用（{e}），请裁一行正文目测像素高度")

def parse_box(a, w, h):
    if not a.box:
        p_exit("--mode crop 必须提供 --box x0,y0,x1,y1")
    try:
        v = [int(t) for t in a.box.split(",")]
    except ValueError:
        p_exit(f"--box 解析失败：{a.box!r}（需4个整数，逗号分隔）")
    if len(v) != 4:
        p_exit(f"--box 需4个值，实得{len(v)}个：{a.box!r}")
    x0, y0, x1, y1 = v
    if x0 > x1: x0, x1 = x1, x0
    if y0 > y1: y0, y1 = y1, y0
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    if (cx0, cy0, cx1, cy1) != (x0, y0, x1, y1):
        print(f"  ⚠ box 越界已裁剪：({x0},{y0},{x1},{y1}) → ({cx0},{cy0},{cx1},{cy1})")
    if cx1 - cx0 < 2 or cy1 - cy0 < 2:
        p_exit(f"--box 有效区域过小：({cx0},{cy0},{cx1},{cy1})")
    return cx0, cy0, cx1, cy1

def p_exit(msg):
    print(f"[错误] {msg}", file=sys.stderr); sys.exit(2)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("src"); p.add_argument("--mode", choices=["report", "slice", "fit", "crop"], default="report")
    p.add_argument("--out-dir", default=None)
    p.add_argument("--screen-h", type=int, default=1080)
    p.add_argument("--overlap", type=int, default=48)
    p.add_argument("--long-side", type=int, default=1568)
    p.add_argument("--box", default=None, help="x0,y0,x1,y1")
    p.add_argument("--zoom", type=float, default=2.0)
    p.add_argument("--glyph", action="store_true", help="report 时附带 OCR 字高估测（需 rapidocr）")
    a = p.parse_args()

    if not 0 <= a.zoom <= 10:
        p_exit(f"--zoom 超出安全范围 [0,10]：{a.zoom}")
    im = open_rgb_white(a.src)
    base = os.path.splitext(os.path.basename(a.src))[0]
    out = a.out_dir or (os.path.dirname(os.path.abspath(a.src)) + "/" + base + "_slices")
    report(im, a.src, glyph=a.glyph)
    if a.mode == "report":
        return
    os.makedirs(out, exist_ok=True)

    if a.mode == "slice":
        w, h = im.size
        if h >= w:  # 竖长条沿 y 切
            if a.screen_h <= 0:
                p_exit(f"--screen-h 必须为正整数：{a.screen_h}")
            if not 0 <= a.overlap < a.screen_h:
                p_exit(f"--overlap 需满足 0 ≤ overlap < screen_h（{a.overlap} ≥ {a.screen_h} 会导致死循环）")
            n = 0; y = 0; step = a.screen_h - a.overlap
            while y < h:
                im.crop((0, y, w, min(h, y + a.screen_h))).save(f"{out}/{base}_part{n:02d}.jpg", quality=88)
                n += 1; y += step
        else:  # 横长条沿 x 切（用同一 screen-h 参数当片宽）
            if a.screen_h <= 0:
                p_exit(f"--screen-h 必须为正整数：{a.screen_h}")
            if not 0 <= a.overlap < a.screen_h:
                p_exit(f"--overlap 需满足 0 ≤ overlap < screen_h（{a.overlap} ≥ {a.screen_h} 会导致死循环）")
            n = 0; x = 0; step = a.screen_h - a.overlap
            while x < w:
                im.crop((x, 0, min(w, x + a.screen_h), h)).save(f"{out}/{base}_part{n:02d}.jpg", quality=88)
                n += 1; x += step
        print(f"[slice] → {n} 片 → {out}/")
    elif a.mode == "fit":
        w, h = im.size; s = a.long_side / max(w, h)
        if s >= 1:
            print(f"[fit] 长边{max(w,h)} ≤ {a.long_side}，无需缩放")
        else:
            nw, nh = round(w * s), round(h * s)
            fp = f"{out}/{base}_fit{a.long_side}.jpg"
            im.resize((nw, nh), Image.LANCZOS).save(fp, quality=88)
            print(f"[fit] {w}x{h} → {nw}x{nh}（像素降为 {s*s:.0%}）→ {fp}")
    elif a.mode == "crop":
        w, h = im.size
        x0, y0, x1, y1 = parse_box(a, w, h)
        c = im.crop((x0, y0, x1, y1))
        if a.zoom != 1:
            c = c.resize((round(c.width * a.zoom), round(c.height * a.zoom)), Image.LANCZOS)
        fp = f"{out}/{base}_crop_{x0}_{y0}_{x1}_{y1}_x{a.zoom}.jpg"
        c.save(fp, quality=92)
        print(f"[crop] ({x0},{y0},{x1},{y1}) zoom×{a.zoom} → {fp}（{c.width}x{c.height}）")

if __name__ == "__main__":
    main()
