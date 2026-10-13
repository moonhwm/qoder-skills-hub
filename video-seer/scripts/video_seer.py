#!/usr/bin/env python3
"""video_seer.py — 让 agent 真能「看」视频：底层抽取帧 + 时序统计。

纯标准库 + ffmpeg/ffprobe 子进程。用法:
    python3 video_seer.py <video.mp4> [--frames N] [--outdir DIR]

输出:
  (a) ffprobe 元数据(时长/分辨率/码率/帧率)
  (b) 场景切换点清单 (select='gt(scene,0.3)': 时刻+分数)
  (c) 等间隔抽帧 jpg (宽<=768) 存 <outdir>/<视频名>/
  (d) 每帧亮度均值/色彩摘要 + 帧间差分运动强度曲线
  (e) report.json + report.md 骨架
"""
import argparse, json, math, os, re, statistics, subprocess, sys

def run(cmd, capture=True):
    r = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.PIPE, text=False)
    return r

def probe_meta(path):
    r = run(["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", path])
    d = json.loads(r.stdout.decode("utf-8", "replace"))
    fmt = d.get("format", {})
    vs = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    fps_raw = vs.get("avg_frame_rate", "0/1")
    try:
        num, den = fps_raw.split("/")
        fps = round(float(num) / float(den), 3) if float(den) else 0.0
    except Exception:
        fps = 0.0
    return {
        "duration_s": round(float(fmt.get("duration", 0)), 3),
        "size_bytes": int(fmt.get("size", 0)),
        "bitrate_kbps": round(int(fmt.get("bit_rate", 0)) / 1000, 1),
        "width": vs.get("width"), "height": vs.get("height"),
        "codec": vs.get("codec_name"), "fps": fps,
        "pix_fmt": vs.get("pix_fmt"), "has_audio": has_audio,
    }

def scene_cuts(path, thresh=0.3):
    """select='gt(scene,T)' + metadata=print 解析时刻与分数。"""
    r = run(["ffmpeg", "-hide_banner", "-i", path,
             "-vf", f"select='gt(scene,{thresh})',metadata=print:file=-",
             "-an", "-f", "null", "-"])
    text = r.stdout.decode("utf-8", "replace")
    cuts, cur_t = [], None
    for line in text.splitlines():
        m = re.search(r"pts_time:([0-9.]+)", line)
        if m:
            cur_t = round(float(m.group(1)), 3)
        m = re.search(r"lavfi\.scene_score=([0-9.]+)", line)
        if m and cur_t is not None:
            cuts.append({"time_s": cur_t, "score": round(float(m.group(1)), 4)})
            cur_t = None
    return cuts

def extract_frames(path, outdir, duration, n):
    """等间隔抽 n 帧，宽<=768，返回 [{file,time_s}]。"""
    os.makedirs(outdir, exist_ok=True)
    n = max(1, min(n, 12))
    frames = []
    for i in range(n):
        t = duration * (i + 0.5) / n
        fn = os.path.join(outdir, f"frame_{i+1:02d}_t{t:06.2f}s.jpg")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error",
             "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
             "-vf", "scale='min(768,iw)':-2", "-q:v", "3", "-y", fn])
        if os.path.exists(fn) and os.path.getsize(fn) > 0:
            frames.append({"file": fn, "time_s": round(t, 3)})
    return frames

def frame_visual_stats(img_path):
    """缩到 16x16 raw RGB，标准库算亮度均值/通道均值/饱和度/色偏。 """
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", img_path,
             "-vf", "scale=16:16", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    buf = r.stdout
    if len(buf) < 16 * 16 * 3:
        return None
    npx = len(buf) // 3
    rs = buf[0::3]; gs = buf[1::3]; bs = buf[2::3]
    rmean = sum(rs) / npx; gmean = sum(gs) / npx; bmean = sum(bs) / npx
    lums = [0.2126 * rs[i] + 0.7152 * gs[i] + 0.0722 * bs[i] for i in range(npx)]
    lum_mean = sum(lums) / npx
    lum_sd = math.sqrt(sum((l - lum_mean) ** 2 for l in lums) / npx)
    # 平均饱和度(HSV 近似): 每像素 (max-min)/max
    sat_sum = 0.0
    for i in range(npx):
        mx = max(rs[i], gs[i], bs[i]); mn = min(rs[i], gs[i], bs[i])
        sat_sum += (mx - mn) / mx if mx else 0.0
    return {
        "brightness": round(lum_mean / 255, 4),       # 0..1 亮度均值
        "contrast_sd": round(lum_sd / 255, 4),
        "saturation": round(sat_sum / npx, 4),        # 0..1 平均饱和度
        "rgb_mean": [round(rmean, 1), round(gmean, 1), round(bmean, 1)],
        "tone_hint": ("冷/蓝" if bmean > rmean + 8 else
                      "暖/红" if rmean > bmean + 8 else "中性"),
    }

def motion_curve(path, duration, sample_fps=2):
    """小尺寸灰度帧差分 → 运动强度曲线(每对相邻帧的平均绝对差)。"""
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path,
             "-vf", f"fps={sample_fps},scale=64:36,format=gray",
             "-f", "rawvideo", "-"])
    buf = r.stdout
    fsize = 64 * 36
    nfr = len(buf) // fsize
    curve = []
    for i in range(1, nfr):
        a = buf[(i - 1) * fsize:i * fsize]
        b = buf[i * fsize:(i + 1) * fsize]
        diff = sum(abs(b[j] - a[j]) for j in range(0, fsize, 4)) / (fsize / 4)
        t = i / sample_fps
        curve.append({"time_s": round(t, 2), "motion": round(diff, 2)})
    vals = [c["motion"] for c in curve]
    summary = {
        "samples": len(curve),
        "mean_motion": round(statistics.mean(vals), 2) if vals else 0,
        "max_motion": round(max(vals), 2) if vals else 0,
        "peak_time_s": (curve[vals.index(max(vals))]["time_s"]
                        if vals else None),
        "still_ratio": round(sum(1 for v in vals if v < 2.0) / len(vals), 3)
                       if vals else 0,
    }
    return curve, summary

def build_markdown(name, meta, cuts, frames, fstats, msum, curve):
    L = [f"# video-seer 报告: {name}", "", "## 元数据",
         f"- 时长: {meta['duration_s']}s | {meta['width']}x{meta['height']} | "
         f"{meta['fps']}fps | {meta['bitrate_kbps']}kbps | {meta['codec']}"
         f" | 音轨: {'有' if meta['has_audio'] else '无'}", "",
         f"## 场景切换 (score>0.3, 共 {len(cuts)} 处)",
         ", ".join(f"{c['time_s']}s({c['score']})" for c in cuts) or "无",
         "", "## 抽帧与画面统计",
         "| 帧 | 时刻 | 亮度 | 对比 | 饱和 | RGB均值 | 色偏 |",
         "|---|---|---|---|---|---|---|"]
    for f, s in zip(frames, fstats):
        if s:
            L.append(f"| {os.path.basename(f['file'])} | {f['time_s']}s "
                     f"| {s['brightness']} | {s['contrast_sd']} "
                     f"| {s['saturation']} | {s['rgb_mean']} | {s['tone_hint']} |")
    L += ["", "## 运动强度",
          f"- 均值 {msum['mean_motion']} / 峰值 {msum['max_motion']}"
          f" @{msum['peak_time_s']}s / 静止占比 {msum['still_ratio']}",
          "- 曲线: " + " ".join(f"{c['time_s']}s:{c['motion']}" for c in curve),
          "", "## 观看笔记(人工/agent 补充)", "", "- (待填)", ""]
    return "\n".join(L)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--frames", type=int, default=10)
    ap.add_argument("--outdir", default="/tmp/video-seer-frames")
    ap.add_argument("--scene-thresh", type=float, default=0.3)
    a = ap.parse_args()

    name = os.path.splitext(os.path.basename(a.video))[0]
    odir = os.path.join(a.outdir, name)
    meta = probe_meta(a.video)
    print(f"[video-seer] {name}: {meta['duration_s']}s "
          f"{meta['width']}x{meta['height']} @{meta['fps']}fps")
    cuts = scene_cuts(a.video, a.scene_thresh)
    print(f"[video-seer] 场景切换: {len(cuts)} 处")
    frames = extract_frames(a.video, odir, meta["duration_s"], a.frames)
    print(f"[video-seer] 抽帧: {len(frames)} 张 -> {odir}")
    fstats = [frame_visual_stats(f["file"]) for f in frames]
    curve, msum = motion_curve(a.video, meta["duration_s"])
    print(f"[video-seer] 运动均值 {msum['mean_motion']} 峰值 "
          f"{msum['max_motion']}@{msum['peak_time_s']}s")

    report = {"video": a.video, "name": name, "meta": meta,
              "scene_cuts": cuts, "frames": frames,
              "frame_stats": fstats, "motion_summary": msum,
              "motion_curve": curve}
    jpath = os.path.join(odir, "report.json")
    with open(jpath, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    mpath = os.path.join(odir, "report.md")
    with open(mpath, "w") as f:
        f.write(build_markdown(name, meta, cuts, frames, fstats, msum, curve))
    print(f"[video-seer] 报告: {jpath}\n             {mpath}")

if __name__ == "__main__":
    main()
