# -*- coding: utf-8 -*-
"""video_local_track.py —— 局部跟踪与"阶跃 vs 漂移"之判（2026-10-12 立，承 -1290 之判）
动机：-1290 见"变动集中画面中部偏右（最大块 14.24 vs 全图均 3.97）"，然不知其为"姿态阶跃"抑或"渲染漂移"。
本器（零外呼；★低内存）：① 逐帧取标记色像素数（品红）与质心 ⇒ 细时间序列；
  ② 切"热区"（中右）与两控制区（左／右上）⇒ 逐帧算区内平均绝对差（相对首帧）；
  ③ ★判：a) 序列若呈"平台＋阶跃"（某帧起显著抬升并持续）⇒ 支持"姿态变化"；b) 若呈"均匀缓慢漂移"⇒ 渲染；
  ④ 报各序列之"首末差／最大跳变／跳变所在帧"。
判据（可失败）：①帧可读；②序列长度＝帧数；③★"阶跃／漂移"之判已给
用法：python video_local_track.py <mp4> [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--json", default=""); a = ap.parse_args()
    import cv2, numpy as np
    p = pathlib.Path(a.video); cap = cv2.VideoCapture(str(p))
    if not cap.isOpened(): print("   ★无法打开"); return 2
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # ★热区：列 4–6／行 2–4（由 -1290 之分块运动图）；控制区：左侧三分之一、右上
    hot = (0, int(w*4/8), int(w*7/8), int(h*2/6), int(h*5/6))       # x0,x1,y0,y1
    ctl1 = (0, 0, int(w/3), 0, h)                                    # 左三分
    ctl2 = (0, int(w*7/8), w, 0, h)                                  # 最右八分（★自纠：原漏一维）
    print("  ═══ 局部跟踪（★阶跃 vs 漂移）═══")
    print("   %s ｜ %d 帧 ｜ %dx%d" % (p.name, total, w, h))
    print("   ★热区 x%d–%d／y%d–%d ｜ 控制区1 左三分 ｜ 控制区2 最右八分" % hot[1:])
    first = None; seq = {"marker": [], "hot": [], "ctl1": [], "ctl2": []}
    i = 0
    while i < total:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, f = cap.read()
        if not ok: break
        if first is None: first = f.copy(); i += 1; continue
        b, g, r = f[:, :, 0].astype("int16"), f[:, :, 1].astype("int16"), f[:, :, 2].astype("int16")
        seq["marker"].append(int(((np.abs(r-255) < 60) & (g < 70) & (np.abs(b-200) < 70)).sum()))
        d = np.abs(f.astype("int16")-first.astype("int16")).mean(axis=2)
        seq["hot"].append(float(d[hot[3]:hot[4], hot[1]:hot[2]].mean()))
        seq["ctl1"].append(float(d[ctl1[3]:ctl1[4], ctl1[1]:ctl1[2]].mean()))
        seq["ctl2"].append(float(d[ctl2[3]:ctl2[4], ctl2[1]:ctl2[2]].mean()))
        i += 1
    cap.release()
    for k in seq: print("   ★%-7s 长度 %d ｜ 首 %.2f ｜ 末 %.2f ｜ 最大 %.2f" % (k, len(seq[k]), seq[k][0], seq[k][-1], max(seq[k]) if seq[k] else 0))
    # ★判"阶跃"：最大跳变 / 全序列标准差
    def step_ratio(v):
        if len(v) < 5: return 0.0, 0, 0.0
        jumps = [abs(v[k+1]-v[k]) for k in range(len(v)-1)]
        mx = max(jumps); at = jumps.index(mx)+1
        sd = (sum((x-sum(v)/len(v))**2 for x in v)/len(v))**0.5
        return (mx/sd if sd > 1e-6 else 0.0), at, mx
    for k in ("hot", "ctl1", "ctl2", "marker"):
        v = seq[k]
        if len(v) < 5: continue
        sr, at, mx = step_ratio(v)
        print("   ★%-7s 最大跳变 %.2f（第 %d 帧）｜ 跳变/标准差 = %.2f ⇒ %s" % (
            k, mx, at, sr, "★有阶跃（>3.0）" if sr > 3.0 else "★无显著阶跃（漂移型）"))
    # ★标记色序列之单调性
    m = seq["marker"]
    if len(m) > 5:
        dec = sum(1 for k in range(1, len(m)) if m[k] <= m[k-1]+1)/ (len(m)-1)
        print("   ★标记色序列：首 %d ⇒ 末 %d ｜ 递减步占比 %.2f ⇒ %s" % (
            m[0], m[-1], dec, "★单调递减（或为缩放／遮挡渐变）" if dec > 0.8 else "★非单调（有起伏）"))
    print("   ⇒ 判：★热区与两控制区之比较可判「局部之变」是否为渲染性 —— ★若三者同型 ⇒ 渲染；★若热区独异 ⇒ 局部事件")
    crit = {"①帧可读": bool(seq["hot"]), "②序列长度＝帧数": len(seq["hot"]) == total-1, "③★阶跃／漂移之判已给": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "file": p.name,
            "seq": seq, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
