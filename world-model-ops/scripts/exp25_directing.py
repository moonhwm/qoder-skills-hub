# -*- coding: utf-8 -*-
"""exp25_directing.py —— 试「实时导演」模式（令条第二模式）：能否直出可下载之影像（不经 RTC）
流程：POST /worlds（simple：prompt＋resolution＋可选首帧）→ 轮询 build-status → 若 ready：
      换票 → enter-travel → 轮询状态 → 探测产物（含任何 URL 字段）→ 若有视频即下载
纪律：ticket/token 零打印零落盘；HTTP 200 须读 output.code；失败如实分类
（中文串一律用「」）
"""
import argparse, base64, json, pathlib, sys, time, urllib.request, urllib.error, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
DT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
APPS = {"adventure": "happyoyster-1.0-adventure", "directing": "happyoyster-1.0-directing", "acting": "happyoyster-1.0-acting"}
env = {}
for line in (HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env").read_text(encoding="utf-8-sig", errors="replace").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("="); env[k.strip()] = v.strip().strip('"').strip("'")
K = env.get("DASHSCOPE_API_KEY", "")

def base(mode): return "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/%s/openapi/v1" % APPS[mode]

def call(url, body=None, method="GET", to=90):
    data = json.dumps(body, ensure_ascii=False).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Bearer " + K)
    if body: r.add_header("Content-Type", "application/json")
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=to) as resp:
            return resp.status, round(time.time()-t0, 2), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, round(time.time()-t0, 2), e.read().decode("utf-8", "replace")[:400]
    except Exception as e:
        return -1, round(time.time()-t0, 2), str(e)[:160]

def od(txt):
    try:
        j = json.loads(txt); o = j.get("output") or {}
        return o, (o.get("data") or {}), o.get("code")
    except Exception:
        return {}, {}, None

ap = argparse.ArgumentParser(); ap.add_argument("--mode", default="directing")
ap.add_argument("--png", default=str(SEAT/"exp"/"exp24_persona_firstframe_16x9_20261011.png"))
ap.add_argument("--sec", type=int, default=60); a = ap.parse_args()
png = pathlib.Path(a.png)
B64 = "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()
body = {"async": True, "prompt": "第三人称：夜间游乐场大门前，守门人立于阶上，门内暖光，薄雾，湿地反光。",
        "resolution": "1280x720", "firstFrameImage": {"base64": B64}}
st, dt, tx = call(base(a.mode) + "/worlds", body, "POST")
o, d, code = od(tx)
print("  ① 建（%s/simple）⇒ HTTP %s ｜ code=%s ｜ worldId=%s ｜ status=%s" % (
    a.mode, st, code, (str(d.get("encryptedWorldId"))[:20]+"…") if d.get("encryptedWorldId") else "无", d.get("status")))
if not d.get("encryptedWorldId"):
    print("     原始：%s" % tx[:300]); sys.exit(1)
wid = d["encryptedWorldId"]
for i in range(6):
    time.sleep(8)
    s2, d2, t2 = call(base(a.mode) + "/worlds/build-status?encryptedWorldId=" + urllib.parse.quote(str(wid)))
    o2, dd, c2 = od(t2)
    print("  ② 轮询 %d ⇒ HTTP %s ｜ code=%s ｜ status=%s ｜ 名=%s" % (i+1, s2, c2, dd.get("status"), dd.get("name")))
    if dd.get("status") in ("ready", "failed"): break
s3, d3, t3 = call(base(a.mode) + "/worlds/get-travel-credential", {"encryptedWorldId": wid}, "POST")
o3, dd3, c3 = od(t3)
tk = dd3.get("ticket") or ""
print("  ③ 换票 ⇒ HTTP %s ｜ code=%s ｜ ticket=%s" % (s3, c3, "★有" if tk else "无"))
if tk:
    s4, d4, t4 = call(base(a.mode) + "/travels/enter-travel", {"ticket": tk, "maxExperienceTimeSec": a.sec}, "POST")
    o4, dd4, c4 = od(t4)
    tid = dd4.get("encryptedTravelId") or ""
    print("  ④ 进房 ⇒ HTTP %s ｜ code=%s ｜ travelId=%s ｜ 字段=%s" % (s4, c4, (str(tid)[:18]+"…") if tid else "无", sorted(dd4.keys())[:8]))
    if tid:
        for i in range(4):
            time.sleep(6)
            s5, d5, t5 = call(base(a.mode) + "/travels/status?encryptedTravelId=" + urllib.parse.quote(str(tid)))
            o5, dd5, c5 = od(t5)
            print("     状态%d ⇒ status=%s ｜ rtc=%s ｜ 键=%s" % (i+1, dd5.get("status"), dd5.get("rtcStatus"), sorted(dd5.keys())[:9]))
        for path in ("/travels/artifacts?encryptedTravelId=", "/travels/artifact?encryptedTravelId=", "/travels/video?encryptedTravelId="):
            s6, d6, t6 = call(base(a.mode) + path + urllib.parse.quote(str(tid)))
            o6, dd6, c6 = od(t6)
            urls = [v for v in (dd6.values() if isinstance(dd6, dict) else []) if isinstance(v, str) and v.startswith("http")]
            print("     产物 %-34s ⇒ HTTP %s ｜ code=%s ｜ 键=%s ｜ URL %d" % (path.split("?")[0], s6, c6, sorted(dd6.keys()) if isinstance(dd6, dict) else "—", len(urls)))
            for u in urls[:3]:
                print("        · %s" % u[:110])
            if urls:
                try:
                    req = urllib.request.Request(urls[0], headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=180) as resp:
                        raw = resp.read()
                    ext = ".mp4" if b"ftyp" in raw[:64] else ".bin"
                    out = DT/("exp25_directing_artifact_20261011" + ext)
                    out.write_bytes(raw)
                    print("        ★已下载 %s（%.2f MB）⇒ %s" % (out.name, len(raw)/1048576, "MP4" if ext == ".mp4" else "非MP4"))
                except Exception as e:
                    print("        × 下载失败：%s" % str(e)[:90])
                break
print("  ★ 结论：模式 %s 之'能否直出影像'见上" % a.mode)
