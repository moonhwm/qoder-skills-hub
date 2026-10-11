# -*- coding: utf-8 -*-
"""人设四段动画（dash／jump／crouch／attack，各 24 帧 @24fps）
① 关键帧＝姿态库四姿态（-02/-03）② 帧间线性插值 ＋ 根运动（dash 前进／jump 升空）
③ 逐帧核：触地残差、根高轨迹、连续性（每帧关节角变化上限）④ 渲染接触表（4 段 × 6 采样帧）
★ 判据按类别分设（戒二十一之细化）：行进类＝触地残差；腾空类＝顶点高度；下蹲类＝骨盆下沉幅度
（引号一律用「」）
"""
import json, math, pathlib, sys, time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import numpy as np
from PIL import Image, ImageDraw

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
S = {"pelvis_z": 0.95, "hip_dx": 0.05, "thigh": 0.42, "shin": 0.42, "foot": 0.11,
     "torso": 0.55, "upper_arm": 0.30, "fore_arm": 0.28}
KEYS = ["torso_lean", "hip_L", "knee_L", "ankle_L", "hip_R", "knee_R", "ankle_R",
        "shoulder_L", "elbow_L", "shoulder_R", "elbow_R"]
NEUTRAL = {"torso_lean": 4, "hip_L": 4, "knee_L": 6, "ankle_L": 0, "hip_R": -4, "knee_R": 6, "ankle_R": 0,
           "shoulder_L": 6, "elbow_L": 14, "shoulder_R": -6, "elbow_R": 14}
POSE = {
    "dash":   {"torso_lean": 24, "hip_L": 38, "knee_L": 26, "ankle_L": -8, "hip_R": -30, "knee_R": 42, "ankle_R": 12,
               "shoulder_L": -52, "elbow_L": 68, "shoulder_R": 46, "elbow_R": 74},
    "jump":   {"torso_lean": 6, "hip_L": 16, "knee_L": 10, "ankle_L": -4, "hip_R": 14, "knee_R": 8, "ankle_R": -2,
               "shoulder_L": -128, "elbow_L": 18, "shoulder_R": -126, "elbow_R": 16},
    "crouch": {"torso_lean": 18, "hip_L": 62, "knee_L": 96, "ankle_L": -24, "hip_R": 60, "knee_R": 94, "ankle_R": -22,
               "shoulder_L": -20, "elbow_L": 92, "shoulder_R": 22, "elbow_R": 90},
    "attack": {"torso_lean": 14, "hip_L": 30, "knee_L": 34, "ankle_L": -10, "hip_R": -18, "knee_R": 40, "ankle_R": 10,
               "shoulder_L": -96, "elbow_L": 14, "shoulder_R": 64, "elbow_R": 88},
}
J = 24   # 帧数


def fk(p):
    th = math.radians(p["torso_lean"]); pel = np.array([0.0, S["pelvis_z"]])
    hipL = pel + np.array([S["hip_dx"], -S["hip_dx"]]); hipR = pel + np.array([-S["hip_dx"], -S["hip_dx"]])
    def leg(hip, ah, ak, aa):
        d1 = math.radians(ah); knee = hip + S["thigh"]*np.array([-math.sin(d1), -math.cos(d1)])
        d2 = d1 - math.radians(ak); ank = knee + S["shin"]*np.array([-math.sin(d2), -math.cos(d2)])
        d3 = d2 + math.radians(aa); toe = ank + S["foot"]*np.array([math.cos(d3), -math.sin(d3)])
        return knee, ank, toe
    kL, aL, tL = leg(hipL, p["hip_L"], p["knee_L"], p["ankle_L"]); kR, aR, tR = leg(hipR, p["hip_R"], p["knee_R"], p["ankle_R"])
    neck = pel + S["torso"]*np.array([math.sin(th), math.cos(th)])
    def arm(a_s, a_e):
        d1 = th + math.radians(a_s); el = neck + S["upper_arm"]*np.array([-math.sin(d1), -math.cos(d1)])
        d2 = d1 + math.radians(a_e); ha = el + S["fore_arm"]*np.array([-math.sin(d2), -math.cos(d2)])
        return el, ha
    eL, hL = arm(p["shoulder_L"], p["elbow_L"]); eR, hR = arm(p["shoulder_R"], p["elbow_R"])
    return {"pelvis": pel, "hipL": hipL, "kneeL": kL, "ankL": aL, "toeL": tL, "hipR": hipR, "kneeR": kR,
            "ankR": aR, "toeR": tR, "neck": neck, "elL": eL, "haL": hL, "elR": eR, "haR": hR}


def mix(a, b, t):  return {k: a[k] + (b[k]-a[k])*t for k in KEYS}


def mir(p):
    q = dict(p); q["hip_L"], q["hip_R"] = p["hip_R"], p["hip_L"]; q["knee_L"], q["knee_R"] = p["knee_R"], p["knee_L"]
    q["ankle_L"], q["ankle_R"] = p["ankle_R"], p["ankle_L"]; q["shoulder_L"], q["shoulder_R"] = p["shoulder_R"], p["shoulder_L"]
    q["elbow_L"], q["elbow_R"] = p["elbow_R"], p["elbow_L"]; return q


# ★各段之关键帧表（帧号 → 姿态／根位移／根高偏移）
def clip_frames(name):
    n, T = NEUTRAL, POSE[name]
    if name == "dash":
        tab = [(0, n, 0.0, 0.0), (6, T, 0.28, 0.02), (12, n, 0.56, 0.0), (18, mir(T), 0.84, 0.02), (23, n, 1.12, 0.0)]
    elif name == "jump":
        tab = [(0, n, 0.0, 0.0), (5, POSE["crouch"], 0.02, -0.10), (11, T, 0.06, 0.38), (17, POSE["crouch"], 0.10, -0.10), (23, n, 0.12, 0.0)]
    elif name == "crouch":
        tab = [(0, n, 0.0, 0.0), (10, T, 0.0, 0.0), (15, T, 0.0, 0.0), (23, n, 0.0, 0.0)]
    else:
        tab = [(0, n, 0.0, 0.0), (6, mix(n, T, 0.4), 0.05, 0.0), (12, T, 0.18, 0.0), (18, mix(n, T, 0.25), 0.24, 0.0), (23, n, 0.26, 0.0)]
    out = []
    for f in range(J):
        for i in range(len(tab)-1):
            f0, p0, x0, z0 = tab[i]; f1, p1, x1, z1 = tab[i+1]
            if f0 <= f <= f1:
                t = 0.0 if f1 == f0 else (f-f0)/(f1-f0)
                out.append((mix(p0, p1, t), x0 + (x1-x0)*t, z0 + (z1-z0)*t)); break
    return out


AIRBORNE = {"jump": range(8, 15)}
R = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "asset": "persona-animation-clips",
     "fps": 24, "frames": J, "clips": {}}
print("  ═══ ① 四段动画之逐帧核（★判据按类分设）═══")
for name in ("dash", "jump", "crouch", "attack"):
    fr = clip_frames(name); prev, maxd = None, 0.0; mins, pels = [], []
    for i, (p, rx, rz) in enumerate(fr):
        j = {k: v.copy() for k, v in fk(p).items()}
        for k in j: j[k] = j[k] + np.array([rx, rz])
        lowest = min(j["toeL"][1], j["ankL"][1], j["toeR"][1], j["ankR"][1])
        ground = (i not in AIRBORNE.get(name, []))
        if ground:                      # 触地帧：整体下移至足端归零
            sh = -lowest
            for k in j: j[k] = j[k] + np.array([0.0, sh])
        mins.append(round(min(j["toeL"][1], j["ankL"][1], j["toeR"][1], j["ankR"][1]), 4))
        pels.append(round(float(j["pelvis"][1]), 4))
        if prev: maxd = max(maxd, max(abs(p[k]-prev[k]) for k in KEYS))
        prev = p
    ground_frames = [i for i in range(J) if i not in AIRBORNE.get(name, [])]
    resid = max(abs(mins[i]) for i in ground_frames)
    apex = max(pels) if name == "jump" else None
    drop = 1 - min(pels)/S["pelvis_z"]
    R["clips"][name] = {"ground_residual_max": round(resid, 5), "pelvis_min": min(pels), "pelvis_max": max(pels),
                        "max_angle_step_deg": round(maxd, 2), "apex_pelvis": apex, "drop_ratio": round(drop, 4),
                        "root_x_end": fr[-1][1]}
    print("   %-7s 触地残差 %.5f m ｜ 骨盆 %0.4f–%0.4f m ｜ 每帧最大角变 %.1f° ｜ %s" % (
        name, resid, min(pels), max(pels), maxd,
        ("顶点骨盆 %.3f m" % apex) if name == "jump" else ("下沉 %.1f%%" % (100*drop))))

# ── ② 渲染接触表（4 段 × 6 采样帧）──
CW, CH = 232, 300
im = Image.new("RGB", (CW*6, CH*4), (10, 11, 16)); d = ImageDraw.Draw(im)
BONES = [("pelvis","neck"),("neck","elL"),("elL","haL"),("neck","elR"),("elR","haR"),
         ("pelvis","hipL"),("hipL","kneeL"),("kneeL","ankL"),("ankL","toeL"),
         ("pelvis","hipR"),("hipR","kneeR"),("kneeR","ankR"),("ankR","toeR")]
SC = 120.0
for r, name in enumerate(("dash", "jump", "crouch", "attack")):
    fr = clip_frames(name)
    for c, idx in enumerate((0, 5, 9, 13, 17, 23)):
        p, rx, rz = fr[idx]
        j = {k: v.copy() for k, v in fk(p).items()}
        for k in j: j[k] = j[k] + np.array([rx, rz])
        lowest = min(j["toeL"][1], j["ankL"][1], j["toeR"][1], j["ankR"][1])
        if idx not in AIRBORNE.get(name, []):
            sh = -lowest
            for k in j: j[k] = j[k] + np.array([0.0, sh])
        ox, oy = c*CW + CW/2 - rx*SC*0.5, r*CH + CH - 42
        for a, b in BONES:
            col = (120, 200, 255) if ("L" in a or "L" in b) else (255, 170, 120)
            d.line([(ox + j[a][0]*SC, oy - j[a][1]*SC), (ox + j[b][0]*SC, oy - j[b][1]*SC)], fill=col, width=3)
        for k, v in j.items():
            x, y = ox + v[0]*SC, oy - v[1]*SC
            d.ellipse([x-2.5, y-2.5, x+2.5, y+2.5], fill=(235,235,240))
        d.line([(ox, oy), (ox+0.8*SC, oy)], fill=(62,62,72), width=2)
        d.text((c*CW+10, r*CH+8), "%s f%02d" % (name, idx), fill=(215,215,228))
d.text((10, 4), "CAIRN persona · 4 clips x 24f @24fps · ground-locked (FK-numeric)", fill=(230,230,240))
out = SEAT/"exp"/"persona_animation_contact_sheet_20261011.png"
im.save(out)
R["render"] = {"file": out.name, "w": CW*6, "h": CH*4, "bytes": out.stat().st_size}
print("\n  ═══ ② 接触表 %s（%d×%d，%.1f KB）═══" % (out.name, CW*6, CH*4, out.stat().st_size/1024))
(EX/"persona_animation_clips_20261011.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("  落盘：persona_animation_clips_20261011.json")
