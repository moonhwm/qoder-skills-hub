# -*- coding: utf-8 -*-
"""实验⑭：人设姿态入世 —— 把 dash 姿态渲染进首帧，测"世界是否采纳我摆的姿势"
基线：exp13 之录像（同底图，仅含 32×32 微扰块，无人物）
本件：同底图 ＋ ★按 FK 渲染之 dash 姿态人形（含品红标记）
判：以"人形 ROI 内均差／区外均差＝定位比"为据（ROI 统计法；弃峰值质心法）
（引号一律用「」）
"""
import base64, json, math, pathlib, sys, time, urllib.request, urllib.error

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import numpy as np
from PIL import Image, ImageDraw
HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
TMP = HOME/"AppData"/"Local"/"Temp"/"exp14"; TMP.mkdir(parents=True, exist_ok=True)
env = {}
for line in (HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env").read_text(encoding="utf-8-sig", errors="replace").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("="); env[k.strip()] = v.strip().strip('"').strip("'")
K = env.get("DASHSCOPE_API_KEY", "")
B = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
BASE = SEAT/"exp"/"opening_firstframe_16x9_20261011.jpg"
S = {"pelvis_z":0.95,"hip_dx":0.05,"thigh":0.42,"shin":0.42,"foot":0.11,"torso":0.55,"upper_arm":0.30,"fore_arm":0.28}
DASH = {"torso_lean":24,"hip_L":38,"knee_L":26,"ankle_L":-8,"hip_R":-30,"knee_R":42,"ankle_R":12,
        "shoulder_L":-52,"elbow_L":68,"shoulder_R":46,"elbow_R":74}

# ── ① 以 FK 求 dash 姿态关节（侧视 xz），再投到画面 ──
def fk(p):
    th = math.radians(p["torso_lean"]); pel = np.array([0.0, S["pelvis_z"]])
    hipL = pel + np.array([S["hip_dx"], -S["hip_dx"]]); hipR = pel + np.array([-S["hip_dx"], -S["hip_dx"]])
    def leg(hip, ah, ak, aa):
        d1 = math.radians(ah); knee = hip + S["thigh"]*np.array([-math.sin(d1), -math.cos(d1)])
        d2 = d1 - math.radians(ak); ank = knee + S["shin"]*np.array([-math.sin(d2), -math.cos(d2)])
        d3 = d2 + math.radians(aa); toe = ank + S["foot"]*np.array([math.cos(d3), -math.sin(d3)])
        return knee, ank, toe
    kL,aL,tL = leg(hipL, p["hip_L"], p["knee_L"], p["ankle_L"]); kR,aR,tR = leg(hipR, p["hip_R"], p["knee_R"], p["ankle_R"])
    neck = pel + S["torso"]*np.array([math.sin(th), math.cos(th)])
    def arm(a_s, a_e):
        d1 = th + math.radians(a_s); el = neck + S["upper_arm"]*np.array([-math.sin(d1), -math.cos(d1)])
        d2 = d1 + math.radians(a_e); ha = el + S["fore_arm"]*np.array([-math.sin(d2), -math.cos(d2)])
        return el, ha
    eL,hL = arm(p["shoulder_L"], p["elbow_L"]); eR,hR = arm(p["shoulder_R"], p["elbow_R"])
    j = {"pelvis":pel,"hipL":hipL,"kneeL":kL,"ankL":aL,"toeL":tL,"hipR":hipR,"kneeR":kR,"ankR":aR,"toeR":tR,
         "neck":neck,"elL":eL,"haL":hL,"elR":eR,"haR":hR}
    shift = -min(j["toeL"][1], j["ankL"][1], j["toeR"][1], j["ankR"][1])
    for k in j: j[k] = j[k] + np.array([0.0, shift])
    return j
J = fk(DASH)
im = Image.open(BASE).convert("RGB"); W, H = im.size
d = ImageDraw.Draw(im)
# 人形落点与比例：脚底 y=560，身高 1.32 m ⇒ 每米 210 px；水平置于 x=800
SC, FX, FY = 210.0, 800, 560
def P(v): return (FX + v[0]*SC, FY - v[1]*SC)
BONES = [("pelvis","neck"),("neck","elL"),("elL","haL"),("neck","elR"),("elR","haR"),
         ("pelvis","hipL"),("hipL","kneeL"),("kneeL","ankL"),("ankL","toeL"),
         ("pelvis","hipR"),("hipR","kneeR"),("kneeR","ankR"),("ankR","toeR")]
for a, b in BONES:
    d.line([P(J[a]), P(J[b])], fill=(236, 240, 250), width=13)
for k, v in J.items():
    x, y = P(v); d.ellipse([x-9, y-9, x+9, y+9], fill=(230, 234, 244))
# 品红标记（躯干中部）——与既有方法一致
tp = (J["pelvis"] + J["neck"]) / 2.0
mx, my = P(tp)
for dx in range(-8, 9):
    for dy in range(-8, 9):
        if dx*dx + dy*dy <= 64:
            im.putpixel((int(mx)+dx, int(my)+dy), (255, 0, 200))
frame = SEAT/"exp"/"exp14_dash_persona_firstframe_20261011.jpg"
im.save(frame, "JPEG", quality=72, optimize=True)
panel = (int(FX-140), int(FY-330), int(FX+160), int(FY+30))
R = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "exp": "14-persona-pose-in-world",
     "frame": frame.name, "persona_box": list(panel), "scale_px_per_m": SC, "mark_px": (mx, my)}
print("  ═══ ① 渲染 dash 姿态人形 ⇒ %s（%d×%d；人形框 %s；标记 (%.0f,%.0f)）═══" % (
    frame.name, W, H, panel, mx, my))


def call(method, path, body=None, to=150):
    r = urllib.request.Request((path if path.startswith("http") else B + path),
                               data=json.dumps(body, ensure_ascii=False).encode() if body else None, method=method)
    r.add_header("Authorization", "Bearer " + K)
    if body: r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=to) as resp: return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8", "replace")
    except Exception as e: return -1, str(e)[:140]
def od(tx):
    try:
        o = json.loads(tx).get("output") or {}; return o.get("code"), o.get("message"), (o.get("data") or {})
    except Exception: return None, tx[:90], {}

b64 = "data:image/jpeg;base64," + base64.b64encode(frame.read_bytes()).decode()
st, tx = call("POST", "/worlds", {"async": True, "perspective": "third_person",
    "prompt": "第三人称：夜间游乐场的门前，七枚发光节点连成一环，人形分身正作冲刺之姿。",
    "firstFrameImage": {"base64": b64}})
c, m, dd = od(tx); wid = dd.get("encryptedWorldId")
print("  ② 建世界 ⇒ code=%s ｜ 尾=%s" % (c, str(wid)[-8:]))
for i in range(12):
    st, tx = call("GET", "/worlds/build-status?encryptedWorldId=" + str(wid))
    c2, m2, d2 = od(tx); s = d2.get("status")
    if s in ("ready", "failed"): break
    time.sleep(7)
st, tx = call("POST", "/worlds/get-travel-credential", {"encryptedWorldId": str(wid)})
c3, m3, d3 = od(tx); tk = d3.get("ticket")
st, tx = call("POST", "/travels/enter-travel", {"ticket": tk, "maxExperienceTimeSec": 120})
c4, m4, d4 = od(tx); tid = d4.get("encryptedTravelId")
print("  ③ 进房 ⇒ code=%s ｜ 尾=%s" % (c4, str(tid)[-8:]))
t1 = time.time(); rtcs = set()
while time.time() - t1 < 65:
    st, tx = call("GET", "/travels/status?encryptedTravelId=" + str(tid))
    c5, m5, d5 = od(tx); rtcs.add(str(d5.get("rtcStatus")))
    if d5.get("status") == "completed" and time.time()-t1 > 20: break
    time.sleep(3)
print("  ④ 保活 %.1f s ｜ rtcStatus=%s" % (time.time()-t1, sorted(rtcs)))
time.sleep(20); url = None
for att in range(1, 4):
    st, tx = call("GET", "/travels/artifacts?encryptedTravelId=" + str(tid))
    c6, m6, d6 = od(tx); url = ((d6.get("video") or {}).get("original") or {}).get("url")
    if url: break
    time.sleep(18)
if url:
    dst = TMP/"exp14_dash.mp4"
    req = urllib.request.Request(url); req.add_header("User-Agent", "cairn/1.0")
    with urllib.request.urlopen(req, timeout=300) as resp, open(dst, "wb") as f:
        n = 0
        while True:
            bb = resp.read(1 << 20)
            if not bb: break
            f.write(bb); n += len(bb)
    print("  ⑤ 录像 %.2f MB ⇒ %s" % (n/1048576, dst.name))
    R["video"] = {"file": str(dst), "bytes": n, "rtc": sorted(rtcs)}
(EX/"exp14_persona_pose_world_20261011.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("  落盘：exp14_persona_pose_world_20261011.json")
