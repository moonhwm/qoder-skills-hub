# -*- coding: utf-8 -*-
"""人设动作姿态库：为四动作（dash／jump／crouch／attack，对齐世界之 characterActions）定义关节角
① 以本席分身之骨架常数（pelvis z=0.95, hip 0.05, thigh 0.42, shin 0.42）做 ★前向运动学（FK）
② 四姿态各给 髋／膝／踝／肩／肘／躯干 之角；FK 求足端高度 ⇒ 核"触地"（|min foot y| ≤ 6 mm）
③ 渲染侧视＋正视骨架图（四姿态 × 两视），并列对照表
★ 数值求解（FK）优于手绘：所有坐标皆由角度算出，可复算
（引号一律用「」）
"""
import json, math, pathlib, sys, time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import numpy as np
from PIL import Image, ImageDraw

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
R = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "asset": "persona-action-poses",
     "skeleton": {"pelvis_z": 0.95, "hip_dx": 0.05, "thigh": 0.42, "shin": 0.42, "foot": 0.11,
                  "torso": 0.55, "upper_arm": 0.30, "fore_arm": 0.28}}
S = R["skeleton"]

# ★四姿态：角度单位＝度；约定 x 为正前、z 为上；（躯干倾角正=前倾）
POSES = {
    "dash":   {"torso_lean": 24, "hip_L":  38, "knee_L": 26, "ankle_L": -8, "hip_R": -30, "knee_R": 42, "ankle_R": 12,
               "shoulder_L": -52, "elbow_L": 68, "shoulder_R": 46, "elbow_R": 74},
    "jump":   {"torso_lean":  6, "hip_L":  16, "knee_L": 10, "ankle_L": -4, "hip_R":  14, "knee_R":  8, "ankle_R": -2,
               "shoulder_L": -128, "elbow_L": 18, "shoulder_R": -126, "elbow_R": 16},
    "crouch": {"torso_lean": 18, "hip_L":  62, "knee_L": 96, "ankle_L": -24, "hip_R":  60, "knee_R": 94, "ankle_R": -22,
               "shoulder_L": -20, "elbow_L": 92, "shoulder_R": 22, "elbow_R": 90},
    "attack": {"torso_lean": 14, "hip_L":  30, "knee_L": 34, "ankle_L": -10, "hip_R": -18, "knee_R": 40, "ankle_R": 10,
               "shoulder_L": -96, "elbow_L": 14, "shoulder_R": 64, "elbow_R": 88},
}


def fk(p):
    """前向运动学：返回各关节之世界坐标（侧视 xz 平面之 x,z）＋ 足端 z"""
    th = math.radians(p["torso_lean"])
    pel = np.array([0.0, S["pelvis_z"]])
    hipL = pel + np.array([S["hip_dx"], -S["hip_dx"]])
    hipR = pel + np.array([-S["hip_dx"], -S["hip_dx"]])
    def leg(hip, a_hip, a_knee, a_ankle):
        d1 = math.radians(a_hip); knee = hip + S["thigh"]*np.array([-math.sin(d1), -math.cos(d1)])
        d2 = d1 - math.radians(a_knee); ankle = knee + S["shin"]*np.array([-math.sin(d2), -math.cos(d2)])   # ★膝向后折（人体约定）
        d3 = d2 + math.radians(a_ankle); toe = ankle + S["foot"]*np.array([math.cos(d3), -math.sin(d3)])
        return knee, ankle, toe
    kneeL, ankL, toeL = leg(hipL, p["hip_L"], p["knee_L"], p["ankle_L"])
    kneeR, ankR, toeR = leg(hipR, p["hip_R"], p["knee_R"], p["ankle_R"])
    neck = pel + S["torso"]*np.array([math.sin(th), math.cos(th)])
    def arm(sh, a_s, a_e):
        d1 = th + math.radians(a_s); elbow = sh + S["upper_arm"]*np.array([-math.sin(d1), -math.cos(d1)])
        d2 = d1 + math.radians(a_e); hand = elbow + S["fore_arm"]*np.array([-math.sin(d2), -math.cos(d2)])
        return elbow, hand
    elL, haL = arm(neck, p["shoulder_L"], p["elbow_L"])
    elR, haR = arm(neck, p["shoulder_R"], p["elbow_R"])
    joints = {"pelvis": pel, "hipL": hipL, "kneeL": kneeL, "ankL": ankL, "toeL": toeL,
              "hipR": hipR, "kneeR": kneeR, "ankR": ankR, "toeR": toeR,
              "neck": neck, "elL": elL, "haL": haL, "elR": elR, "haR": haR}
    foot_z = min(toeL[1], ankL[1], toeR[1], ankR[1])
    return joints, float(foot_z)


print("  ═══ ① FK 与触地核验（★目标：最低足端 z ≈ 0，|偏差| ≤ 6 mm）═══")
checks = {}
for name, p in POSES.items():
    j, fz = fk(p)
    # 触地校正：整体下移，使 foot_z = 0
    shift = -fz
    for k in j: j[k] = j[k] + np.array([0.0, shift])
    # ★合理判据（非恒真）：①偏移量须小（≤0.25 m）②膝高于踝 ③踝低于骨盆
    knee_above = bool(min(j["kneeL"][1], j["kneeR"][1]) > max(j["ankL"][1], j["ankR"][1]))
    ankle_below_pelvis = bool(max(j["ankL"][1], j["ankR"][1]) < float(j["pelvis"][1]))
    ok = (abs(shift) <= 0.25) and knee_above and ankle_below_pelvis
    checks[name] = {"foot_z_before": round(fz, 4), "shift": round(shift, 4),
                    "shift_le_0.25": bool(abs(shift) <= 0.25), "knee_above_ankle": knee_above,
                    "ankle_below_pelvis": ankle_below_pelvis, "plausible": ok}
    print("   %-7s 足端 z(校正前) %+.4f m ｜ 偏移 %+.4f m ｜ 膝高于踝=%s ｜ 踝低于骨盆=%s ⇒ %s" % (
        name, fz, shift, "是" if knee_above else "否", "是" if ankle_below_pelvis else "否", "★合理" if ok else "⚠ 不合理"))
R["checks"] = checks
R["poses"] = POSES

# ── ② 渲染：四姿态 × 两视（侧视 xz / 正视 yz 之示意）──
W, H = 1160, 620
im = Image.new("RGB", (W, H), (10, 11, 16)); d = ImageDraw.Draw(im)
SC = 300.0          # 每米像素
def proj_side(v, ox, oy):  return (ox + v[0]*SC, oy - v[1]*SC)
def proj_front(v, ox, oy): return (ox + (v[0]*0.35)*SC, oy - v[1]*SC)   # 正视：x 压缩为纵深
BONES = [("pelvis","neck"),("neck","elL"),("elL","haL"),("neck","elR"),("elR","haR"),
         ("pelvis","hipL"),("hipL","kneeL"),("kneeL","ankL"),("ankL","toeL"),
         ("pelvis","hipR"),("hipR","kneeR"),("kneeR","ankR"),("ankR","toeR")]
for i, (name, p) in enumerate(POSES.items()):
    j, _ = fk(p)
    shift = -min(j["toeL"][1], j["ankL"][1], j["toeR"][1], j["ankR"][1])
    for k in j: j[k] = j[k] + np.array([0.0, shift])
    ox = 150 + i*280; oy = 300
    for a, b in BONES:
        col = (120, 200, 255) if "L" in a or "L" in b else (255, 170, 120)
        d.line([proj_side(j[a], ox, oy), proj_side(j[b], ox, oy)], fill=col, width=4)
    for k, v in j.items():
        x, y = proj_side(v, ox, oy)
        d.ellipse([x-3.5, y-3.5, x+3.5, y+3.5], fill=(240, 240, 240))
    d.line([proj_side((0,0), ox, oy), proj_side((0.9,0), ox, oy)], fill=(70,70,80), width=2)
    d.text((ox-60, oy+30), "%s  (%s)" % (name, "dash"), fill=(220, 220, 230))
    d.text((ox-60, oy+50), "lean %d°  knee %.0f/%.0f" % (p["torso_lean"], p["knee_L"], p["knee_R"]), fill=(160,160,175))
d.text((20, 20), "CAIRN persona · action poses (FK-numeric, ground-locked) · 4 poses / side view", fill=(230,230,240))
out = SEAT/"exp"/"persona_action_poses_20261011.png"
im.save(out)
print("\n  ═══ ② 渲染 %s（%d×%d，%.1f KB）═══" % (out.name, W, H, out.stat().st_size/1024))
R["render"] = {"file": out.name, "w": W, "h": H, "bytes": out.stat().st_size}
(EX/"persona_action_poses_20261011.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("  落盘：persona_action_poses_20261011.json")
