# -*- coding: utf-8 -*-
"""分身 GLB v2：★时间轴修为 0…1.000（25 帧）＋ 一次导出三级 LOD
LOD0：12 骨（全）；LOD1：10 骨（去双足）；LOD2：8 骨（去双足、去双小臂）
自检：每级之魔数／声明长度／节点／动画／★时间轴端点须为 [0.000, 1.000]
（引号一律用「」）
"""
import json, math, pathlib, struct, sys, time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
FPS, KEYLAST = 24, 23
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
KEYS = list(NEUTRAL.keys())
def mix(a, b, t): return {k: a[k] + (b[k]-a[k])*t for k in KEYS}
def mir(p):
    q = dict(p)
    for A, B in (("hip_L","hip_R"),("knee_L","knee_R"),("ankle_L","ankle_R"),("shoulder_L","shoulder_R"),("elbow_L","elbow_R")):
        q[A], q[B] = p[B], p[A]
    return q
def table(name):
    n, T = NEUTRAL, POSE[name]
    if name == "dash":   return [(0,n,0,0),(6,T,0.28,0.02),(12,n,0.56,0),(18,mir(T),0.84,0.02),(23,n,1.12,0)]
    if name == "jump":   return [(0,n,0,0),(5,POSE["crouch"],0.02,-0.10),(11,T,0.06,0.38),(17,POSE["crouch"],0.10,-0.10),(23,n,0.12,0)]
    if name == "crouch": return [(0,n,0,0),(10,T,0,0),(15,T,0,0),(23,n,0,0)]
    return [(0,n,0,0),(6,mix(n,T,0.4),0.05,0),(12,T,0.18,0),(18,mix(n,T,0.25),0.24,0),(23,n,0.26,0)]
def frames(name, J):          # ★25 帧：[0, 24] ⇒ 时间轴 0…1.000
    T = table(name); out = []
    for f in range(J):
        ff = f*KEYLAST/(J-1)                      # 映射回关键帧表之坐标
        for i in range(len(T)-1):
            f0,p0,x0,z0 = T[i]; f1,p1,x1,z1 = T[i+1]
            if f0 <= ff <= f1:
                t = 0.0 if f1 == f0 else (ff-f0)/(f1-f0)
                out.append((mix(p0,p1,t), x0+(x1-x0)*t, 0.95+z0+(z1-z0)*t)); break
    return out
def locals_(p):
    return {"pelvis": 0.0, "spine": p["torso_lean"], "upperArmL": p["shoulder_L"], "foreArmL": p["elbow_L"],
            "upperArmR": p["shoulder_R"], "foreArmR": p["elbow_R"], "thighL": p["hip_L"], "shinL": -p["knee_L"],
            "footL": p["ankle_L"], "thighR": p["hip_R"], "shinR": -p["knee_R"], "footR": p["ankle_R"]}
def quat_y(d):
    a = math.radians(d)/2.0
    return [0.0, math.sin(a), 0.0, math.cos(a)]

FULL = [("pelvis",None,(0.0,0.0,0.0),0.0),("spine","pelvis",(0.0,0.0,0.0),0.55),
        ("upperArmL","spine",(0.10,0.0,-0.50),0.30),("foreArmL","upperArmL",(0.0,0.0,-0.30),0.28),
        ("upperArmR","spine",(-0.10,0.0,-0.50),0.30),("foreArmR","upperArmR",(0.0,0.0,-0.30),0.28),
        ("thighL","pelvis",(0.05,0.0,0.0),0.42),("shinL","thighL",(0.0,0.0,-0.42),0.42),("footL","shinL",(0.0,0.0,-0.42),0.11),
        ("thighR","pelvis",(-0.05,0.0,0.0),0.42),("shinR","thighR",(0.0,0.0,-0.42),0.42),("footR","shinR",(0.0,0.0,-0.42),0.11)]
LODS = {"LOD0": {"bones": FULL, "box": 0.055},
        "LOD1": {"bones": [b for b in FULL if not b[0].startswith("foot")], "box": 0.075},
        "LOD2": {"bones": [b for b in FULL if not b[0].startswith("foot") and not b[0].startswith("foreArm")], "box": 0.095}}


def build(lod, J=25):
    bones, box = LODS[lod]["bones"], LODS[lod]["box"]
    nodes, idx = [], {}
    for i, (nm, par, tr, ln) in enumerate(bones):
        idx[nm] = i; nodes.append({"name": nm, "translation": list(tr), "rotation": [0,0,0,1], "children": []})
    for nm, par, tr, ln in bones:
        if par is not None: nodes[idx[par]]["children"].append(idx[nm])
    verts, inds = [], []
    for nm, par, tr, ln in bones:
        if ln <= 0: continue
        w = h = box; base = len(verts)
        for sz in (-ln, 0.0):
            for sx, sy in ((-w,-h),(w,-h),(w,h),(-w,h)): verts += [sx, sy, sz]
        inds += [base+0,base+1,base+2, base+0,base+2,base+3, base+4,base+6,base+5, base+4,base+7,base+6,
                 base+0,base+4,base+5, base+0,base+5,base+1, base+3,base+2,base+6, base+3,base+6,base+7,
                 base+0,base+3,base+7, base+0,base+7,base+4, base+1,base+5,base+6, base+1,base+6,base+2]
        ni = len(nodes); nodes.append({"name": nm+"_mesh", "mesh": 0}); nodes[idx[nm]]["children"].append(ni)
    vb = struct.pack("<%df" % len(verts), *verts); ib = struct.pack("<%dH" % len(inds), *inds)
    vmin = [min(verts[i::3]) for i in range(3)]; vmax = [max(verts[i::3]) for i in range(3)]
    views = [{"buffer":0,"byteOffset":0,"byteLength":len(vb),"target":34962},
             {"buffer":0,"byteOffset":len(vb),"byteLength":len(ib),"target":34963}]
    accs = [{"bufferView":0,"componentType":5126,"count":len(verts)//3,"type":"VEC3","min":vmin,"max":vmax},
            {"bufferView":1,"componentType":5123,"count":len(inds),"type":"SCALAR"}]
    blob = vb + ib; anims = []; times = [round(f/FPS, 6) for f in range(J)]
    tb = struct.pack("<%df" % J, *times)
    views.append({"buffer":0,"byteOffset":len(blob),"byteLength":len(tb)}); blob += tb
    accs.append({"bufferView":len(views)-1,"componentType":5126,"count":J,"type":"SCALAR","min":[times[0]],"max":[times[-1]]})
    tacc = len(accs)-1; names = [b[0] for b in bones]
    for name in ("dash","jump","crouch","attack"):
        fr = frames(name, J); samplers, channels = [], []
        for nm in names:
            qs = []
            for p, rx, rz in fr: qs += quat_y(locals_(p)[nm])
            qb = struct.pack("<%df" % len(qs), *qs)
            views.append({"buffer":0,"byteOffset":len(blob),"byteLength":len(qb)}); blob += qb
            accs.append({"bufferView":len(views)-1,"componentType":5126,"count":J,"type":"VEC4"})
            samplers.append({"input":tacc,"output":len(accs)-1,"interpolation":"LINEAR"})
            channels.append({"sampler":len(samplers)-1,"target":{"node":idx[nm],"path":"rotation"}})
        ts = []
        for p, rx, rz in fr: ts += [rx, rz, 0.0]
        tb2 = struct.pack("<%df" % len(ts), *ts)
        views.append({"buffer":0,"byteOffset":len(blob),"byteLength":len(tb2)}); blob += tb2
        accs.append({"bufferView":len(views)-1,"componentType":5126,"count":J,"type":"VEC3"})
        samplers.append({"input":tacc,"output":len(accs)-1,"interpolation":"LINEAR"})
        channels.append({"sampler":len(samplers)-1,"target":{"node":idx["pelvis"],"path":"translation"}})
        anims.append({"name":name,"samplers":samplers,"channels":channels})
    G = {"asset":{"version":"2.0","generator":"Cairn persona exporter v2 (FK-numeric, %s)" % lod},
         "scene":0,"scenes":[{"nodes":[idx["pelvis"]]}],"nodes":nodes,
         "meshes":[{"name":"CairnPersona_%s"%lod,"primitives":[{"attributes":{"POSITION":0},"indices":1,"material":0}]}],
         "materials":[{"name":"bone","pbrMetallicRoughness":{"baseColorFactor":[0.47,0.78,1.0,1.0],"metallicFactor":0.1,"roughnessFactor":0.7}}],
         "bufferViews":views,"accessors":accs,"animations":anims,"buffers":[{"byteLength":len(blob)}]}
    jb = json.dumps(G, ensure_ascii=False, separators=(",",":")).encode("utf-8")
    jb += b" " * ((4 - len(jb) % 4) % 4)
    bb = blob + b"\x00" * ((4 - len(blob) % 4) % 4)
    glb = b"glTF" + struct.pack("<II", 2, 12+8+len(jb)+8+len(bb)) + struct.pack("<I", len(jb)) + b"JSON" + jb + struct.pack("<I", len(bb)) + b"BIN\x00" + bb
    return glb, len(bones), J


R = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "asset": "CAIRN_avatar_actions_v2", "fps": FPS, "frames": 25,
     "fixed": "时间轴修为 0…1.000（25 帧）", "lods": {}}
print("  ═══ 导出三级 LOD（★时间轴 0…1.000）═══")
for lod in ("LOD0", "LOD1", "LOD2"):
    glb, nb, J = build(lod)
    out = SEAT/"exp"/("CAIRN_avatar_%s_actions_v2_20261011.glb" % lod)
    out.write_bytes(glb)
    raw = out.read_bytes(); assert raw[:4] == b"glTF"
    ver, total = struct.unpack("<II", raw[4:12]); jl = struct.unpack("<I", raw[12:16])[0]
    G2 = json.loads(raw[20:20+jl].decode("utf-8"))
    t = G2["accessors"][G2["animations"][0]["samplers"][0]["input"]]
    ok_len = (total == len(raw)); ok_t = abs(t["min"][0]) < 1e-9 and abs(t["max"][0]-1.0) < 1e-9
    R["lods"][lod] = {"file": out.name, "bytes": len(glb), "bones": nb, "nodes": len(G2["nodes"]),
                      "animations": [a["name"] for a in G2["animations"]],
                      "channels_per_anim": len(G2["animations"][0]["channels"]),
                      "t_min": t["min"][0], "t_max": t["max"][0], "len_ok": ok_len, "timeline_ok": ok_t}
    print("   %s：%6.1f KB ｜ 骨 %2d ｜ 节点 %2d ｜ 动画 %d ｜ 每段通道 %d ｜ 时间轴 [%.3f..%.3f] %s ｜ 长度自洽 %s" % (
        lod, len(glb)/1024, nb, len(G2["nodes"]), len(G2["animations"]), len(G2["animations"][0]["channels"]),
        t["min"][0], t["max"][0], "✓" if ok_t else "⚠", "✓" if ok_len else "⚠"))
(EX/"avatar_glb_v2_export_20261011.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\n  ⇒ 判：三级 LOD 皆导出；★时间轴已修为 [0.000, 1.000] ⇒ 上一版瑕疵闭合")
print("  落盘：avatar_glb_v2_export_20261011.json")
