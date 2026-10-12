# -*- coding: utf-8 -*-
"""video_probe.py —— 录像之"定量检视"（2026-10-12 立，为判"指令是否兑现为可见动作"）
本器（零外呼；★低内存：逐帧读、不整段载入）：
  ① 用 cv2 读帧数／尺寸／帧率；② 均匀抽样 N 帧 ⇒ 报"帧间平均绝对差"（判画面是否在动）；
  ③ ★检"标记色"（品红 255,0,200 之近似像素）之像素数与质心 ⇒ 判"本席分身是否在场且移动"
  ④ 抽样帧落盘（小尺寸 JPEG，供人看）
判据（可失败）：①能读到帧；②帧间差已给；③★标记色之有无与轨迹已给（或明示"无"）
用法：python video_probe.py <mp4> [--n 10] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--json", default=""); a = ap.parse_args()
    import cv2, numpy as np
    p = pathlib.Path(a.video)
    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        print("   ★无法打开：%s" % p.name); return 2
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("  ═══ 录像定量检视（★低内存逐帧）═══")
    print("   %s ｜ %.2f MB ｜ ★帧数 %d ｜ %.1f fps ｜ %dx%d ｜ 约 %.1f s" % (
        p.name, p.stat().st_size/1048576, total, fps, w, h, total/max(1, fps)))
    idxs = [int(total*i/(a.n-1)) for i in range(a.n)] if total > a.n else list(range(total))
    prev = None; diffs = []; marks = []; outdir = p.parent/("frames_"+p.stem[-4:]); outdir.mkdir(exist_ok=True)
    for k, i in enumerate(idxs, 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = cap.read()
        if not ok: continue
        g = cv2.cvtColor(cv2.resize(f, (320, 180)), cv2.COLOR_BGR2GRAY).astype("int16")
        if prev is not None: diffs.append(float(np.abs(g - prev).mean()))
        prev = g
        # ★标记色（品红 BGR=(200,0,255)）之近似
        b, gr, r = f[:, :, 0].astype("int16"), f[:, :, 1].astype("int16"), f[:, :, 2].astype("int16")
        mk = (np.abs(r-255) < 60) & (gr < 70) & (np.abs(b-200) < 70)
        cnt = int(mk.sum())
        cen = None
        if cnt > 20:
            ys, xs = np.where(mk)
            cen = [round(float(xs.mean()), 1), round(float(ys.mean()), 1)]
        marks.append({"frame": i, "marker_px": cnt, "centroid": cen})
        cv2.imwrite(str(outdir/("f_%02d.jpg" % k)), cv2.resize(f, (480, 270)), [cv2.IMWRITE_JPEG_QUALITY, 70])
    cap.release()
    print("   ★抽样 %d 帧 ⇒ %s" % (len(marks), outdir.name))
    print("   ★帧间平均绝对差（0–255）：%s" % "、".join("%.2f" % d for d in diffs))
    print("   ★帧间差之均值 %.2f ｜ 最大 %.2f ⇒ %s" % (
        (sum(diffs)/len(diffs)) if diffs else 0, max(diffs) if diffs else 0,
        "★画面在动（差 >1.0）" if (diffs and sum(diffs)/len(diffs) > 1.0) else "★画面近乎静止（差 ≤1.0）"))
    mm = [m for m in marks if m["marker_px"] > 20]
    print("   ★标记色（品红）之帧：%d／%d" % (len(mm), len(marks)))
    for m in marks: print("      帧 %-4d ｜ 像素 %-6d ｜ 质心 %s" % (m["frame"], m["marker_px"], m["centroid"]))
    moved = False
    if len(mm) >= 2 and all(m["centroid"] for m in mm):
        dx = max(abs(m["centroid"][0] - mm[0]["centroid"][0]) for m in mm)
        dy = max(abs(m["centroid"][1] - mm[0]["centroid"][1]) for m in mm)
        moved = (dx + dy) > 2
        print("   ★标记色质心位移：Δx %.1f ｜ Δy %.1f ⇒ %s" % (dx, dy, "★有位移（分身在动）" if moved else "★无显著位移"))
    crit = {"①能读到帧": bool(marks), "②帧间差已给": bool(diffs), "③★标记色之有无与轨迹已给": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "file": p.name, "frames": total, "fps": fps, "size": [w, h], "diffs": [round(d, 2) for d in diffs],
            "marks": marks, "moved": moved, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
