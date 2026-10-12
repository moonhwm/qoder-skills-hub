# -*- coding: utf-8 -*-
"""video_motion_map.py —— 录像之细粒度运动分析（2026-10-12 立，深化 -1285 之判）
动机：-1285 仅以 9 帧抽样判"标记色质心不动"；本器加密到"每 4 帧"并做"分块运动图"，以定"是否有行走级位移"。
本器（零外呼；★低内存：逐帧读）：
  ① 密集抽帧（每 step 帧）⇒ ★标记色像素数与质心之完整轨迹
  ② 分块运动图：首末帧按 8x6 网格算"块内平均绝对差" ⇒ ★定"变动集中在何处"
  ③ ★判据：a) 质心位移 < 视野 2% ⇒ 无行走；b) 位移方向性（单调 vs 抖动）；c) 块运动之最大者所在
判据（可失败）：①帧可读；②轨迹点数 ≥10；③★"是否行走"之判已给
用法：python video_motion_map.py <mp4> [--step 4] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--step", type=int, default=4)
    ap.add_argument("--json", default=""); a = ap.parse_args()
    import cv2, numpy as np
    p = pathlib.Path(a.video); cap = cv2.VideoCapture(str(p))
    if not cap.isOpened(): print("   ★无法打开"); return 2
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("  ═══ 细粒度运动分析（每 %d 帧）═══" % a.step)
    print("   %s ｜ %d 帧 ｜ %dx%d" % (p.name, total, w, h))
    traj = []; first = last = None
    i = 0
    while i < total:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, f = cap.read()
        if not ok: break
        if first is None: first = f.copy()
        last = f.copy()
        b, g, r = f[:, :, 0].astype("int16"), f[:, :, 1].astype("int16"), f[:, :, 2].astype("int16")
        mk = (np.abs(r-255) < 60) & (g < 70) & (np.abs(b-200) < 70)
        cnt = int(mk.sum()); cen = None; box = None
        if cnt > 20:
            ys, xs = np.where(mk); cen = [float(xs.mean()), float(ys.mean())]
            box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        traj.append({"f": i, "px": cnt, "c": cen, "box": box})
        i += a.step
    cap.release()
    print("   ★轨迹点 %d" % len(traj))
    cs = [t for t in traj if t["c"]]
    if cs:
        xs_ = [c["c"][0] for c in cs]; ys_ = [c["c"][1] for c in cs]
        dx = max(xs_)-min(xs_); dy = max(ys_)-min(ys_)
        print("   ★标记色：见 %d／%d 点 ｜ 像素 %d→%d ｜ ★轨迹范围 Δx %.1f ｜ Δy %.1f" % (
            len(cs), len(traj), cs[0]["px"], cs[-1]["px"], dx, dy))
        print("   ★位移占视野：Δx %.2f%% ｜ Δy %.2f%%" % (100*dx/w, 100*dy/h))
        # ★方向性：以 x 之累计变化与净变化之比（1 ⇒ 单调定向；0 ⇒ 抖动）
        sx = 0.0; net = xs_[-1]-xs_[0]
        for k in range(1, len(xs_)): sx += abs(xs_[k]-xs_[k-1])
        ratio = abs(net)/sx if sx > 1e-6 else 0.0
        print("   ★方向性：净位移 %.1f ｜ 累计路径 %.1f ｜ ★定向比 %.2f（1＝单调定向；0＝原地抖动）" % (net, sx, ratio))
        walk = (dx/w > 0.02) or (dy/h > 0.02)
        print("   ⇒ 判：★%s" % ("★有行走级位移（>2% 视野）" if walk else "★无行走级位移（<2% 视野）⇒ 与 -1285 一致"))
    else:
        print("   ⇒ 判：★未见标记色")
    if first is not None and last is not None:
        d = np.abs(first.astype("int16")-last.astype("int16")).mean(axis=2)
        gh, gw = 6, 8
        print("   ★分块运动图（6x8 网格；块内平均绝对差，0–255）：")
        grid = []
        for r_ in range(gh):
            row = []
            for c_ in range(gw):
                blk = d[r_*h//gh:(r_+1)*h//gh, c_*w//gw:(c_+1)*w//gw]
                row.append(float(blk.mean()))
            grid.append(row)
            print("      " + " ".join("%5.2f" % v for v in row))
        mx = max(max(r) for r in grid)
        ys2, xs2 = max(((r_, c_) for r_ in range(gh) for c_ in range(gw)), key=lambda rc: grid[rc[0]][rc[1]])
        print("   ★最大变动块：第 %d 行第 %d 列（%.2f）｜ 全图均 %.2f" % (ys2+1, xs2+1, mx, sum(sum(r) for r in grid)/(gh*gw)))
    crit = {"①帧可读": bool(traj), "②轨迹点数 ≥10": len(traj) >= 10, "③★是否行走之判已给": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "file": p.name,
            "traj": traj, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
