#!/usr/bin/env python3
# --- K3 依赖预检（发行包注入：缺依赖时显式报缺并以 exit 2 降级，不抛裸 ImportError）---
import importlib.util as _ilu, sys as _sys
_k3_missing = [m for m in ['PIL', 'rapidocr_onnxruntime'] if _ilu.find_spec(m) is None]
if _k3_missing:
    _sys.stderr.write("[K3 deps] 缺依赖 %s —— 请 pip install 后使用本脚本；包内其余技能不受影响\n" % _k3_missing)
    _sys.exit(2)
# --- K3 依赖预检完 ---

"""ocr_shot.py v2.1 — 截图"文字主干 + 数字裁图核验"双模式 OCR
v2.0 2026-08-27：主引擎换 RapidOCR(PP-OCRv4 ONNX)——实测全面碾压 tesseract
  （A@20% 19/20 vs 1/20；B@50% 40/40 vs 17/40）；tesseract 保留为 --engine tesseract 兜底。
  272px 压缩长条为双方共同死区（0/18 密码），此类图只能裁小图发视觉模型。
v2.1 2026-08-27 双角审核修订：digits 补 -l chi_sim/--tessdata-dir、白名单加 ",%"（千分位逗号场景）、
  --box 缺失/越界显式报错、tessdata 多路径发现、tmp 文件 finally 清理。
  注意：digits→tesseract 的分工基于单样本个案（RapidOCR 漏检裁片内超大美术字），
  遇误读/空输出应 --engine rapid 双引擎互验。
用法:
  python3 ocr_shot.py IMG --mode full                       # 全文 → IMG.ocr.txt
  python3 ocr_shot.py IMG --mode digits --box 45,905,500,995 [--zoom 3]
  python3 ocr_shot.py IMG --engine tesseract                # 兜底引擎
"""
import argparse, os, re, subprocess, sys
from PIL import Image

def _find_tessdata():
    """按优先级找 chi_sim.traineddata；都找不到返回 None（用 tesseract 系统默认路径）"""
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [os.path.join(here, "tessdata"), here,
             "<上传区>/cross-ai-toolkit/tessdata", "<上传区>/cross-ai-toolkit"]
    for d in cands:
        if os.path.exists(os.path.join(d, "chi_sim.traineddata")):
            return d
    return None

TESSDATA = _find_tessdata()

def tess_cmd(img_path, extra, chi=True):
    """chi=True 时挂 chi_sim（full 兜底用）；digits 白名单走系统默认 eng——
    实测 eng 数字精度更高（¥28.26 精确 vs chi_sim 误读 28.20），且 ¥ 在 eng unicharset 内可输出；
    白名单中的 CJK 字符（万元折）在 eng 下被静默忽略，需要这些字符时请 --engine rapid 互验。"""
    cmd = ["tesseract", img_path, "stdout"]
    if chi and TESSDATA:
        cmd += ["--tessdata-dir", TESSDATA, "-l", "chi_sim"]
    return cmd + extra

_rapid = None
def rapid():
    global _rapid
    if _rapid is None:
        from rapidocr_onnxruntime import RapidOCR
        _rapid = RapidOCR()
    return _rapid

def ocr_image(img_path, engine):
    if engine == "rapid":
        res, _ = rapid()(img_path)
        return "\n".join(r[1] for r in (res or []))
    return subprocess.run(tess_cmd(img_path, ["--psm", "3"]), capture_output=True, text=True).stdout

def p_exit(msg):
    print(f"[错误] {msg}", file=sys.stderr); sys.exit(2)

def parse_box(box_str, w, h):
    if not box_str:
        p_exit("--mode digits 必须提供 --box x0,y0,x1,y1")
    try:
        v = [int(t) for t in box_str.split(",")]
    except ValueError:
        p_exit(f"--box 解析失败：{box_str!r}（需4个整数，逗号分隔）")
    if len(v) != 4:
        p_exit(f"--box 需4个值，实得{len(v)}个：{box_str!r}")
    x0, y0, x1, y1 = v
    if x0 > x1: x0, x1 = x1, x0
    if y0 > y1: y0, y1 = y1, y0
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    if (cx0, cy0, cx1, cy1) != (x0, y0, x1, y1):
        print(f"  ⚠ box 越界已裁剪：({x0},{y0},{x1},{y1}) → ({cx0},{cy0},{cx1},{cy1})")
    if cx1 - cx0 < 2 or cy1 - cy0 < 2:
        p_exit(f"--box 有效区域过小：({cx0},{cy0},{cx1},{cy1})")
    return cx0, cy0, cx1, cy1

def main():
    p = argparse.ArgumentParser()
    p.add_argument("src"); p.add_argument("--mode", choices=["full", "digits"], default="full")
    p.add_argument("--box", default=None); p.add_argument("--zoom", type=float, default=3.0)
    p.add_argument("--out", default=None, help="full 模式输出路径（默认=源文件+.ocr.txt；源目录只读时自动落当前目录）")
    p.add_argument("--engine", choices=["auto", "rapid", "tesseract"], default="auto",
                   help="auto=实测最优分工：full→RapidOCR，digits→tesseract白名单（遇误读请双引擎互验）")
    a = p.parse_args()
    if not 0 < a.zoom <= 10:
        p_exit(f"--zoom 超出安全范围 (0,10]：{a.zoom}")
    engine = {"full": "rapid", "digits": "tesseract"}[a.mode] if a.engine == "auto" else a.engine
    if a.mode == "full":
        txt = ocr_image(a.src, engine)
        out = a.out or (a.src + ".ocr.txt")
        try:
            open(out, "w", encoding="utf-8").write(txt)
        except OSError:
            out = os.path.basename(a.src) + ".ocr.txt"
            open(out, "w", encoding="utf-8").write(txt)
            print(f"  ⚠ 原目录不可写，改写到当前目录（也可用 --out 显式指定）")
        print(f"[full:{engine}] → {out}（{len([l for l in txt.splitlines() if l.strip()])} 非空行）")
    else:
        w0 = Image.open(a.src); W, H = w0.size; w0.close()
        x0, y0, x1, y1 = parse_box(a.box, W, H)
        im = Image.open(a.src).convert("RGB").crop((x0, y0, x1, y1))
        im = im.resize((round(im.width * a.zoom), round(im.height * a.zoom)), Image.LANCZOS)
        tmp = f"/tmp/_ocr_digits_{os.getpid()}.png"
        try:
            im.save(tmp)
            if engine == "rapid":
                txt = ocr_image(tmp, "rapid")
            else:
                txt = subprocess.run(tess_cmd(tmp, ["--psm", "7", "-c",
                                     "tessedit_char_whitelist=0123456789.¥-:,%万元折"], chi=False),
                                     capture_output=True, text=True).stdout
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        txt = txt.strip()
        print(f"[digits:{engine}] ({x0},{y0},{x1},{y1}) zoom×{a.zoom} → {txt}")
        if engine == "tesseract" and not txt:
            print("  ⚠ 白名单模式空输出：可能是美术字/非数字内容，建议 --engine rapid 互验")

if __name__ == "__main__":
    main()
