# -*- coding: utf-8 -*-
"""exp26_determinism.py —— 同帧双建：世界之"id 与内容"确定性测试
命题：同一首帧、同一 prompt 连续建两次世界，比较 ①encryptedWorldId ②平台命名 ③平台首帧哈希。
纪律：如实分类（同／异）；id 之异同不得单独作为"新世界"之证据（须并列内容）。
（中文串一律用「」）
"""
import base64, hashlib, json, pathlib, sys, time, urllib.request, urllib.error, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
BASE = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
env = {}
for line in (HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env").read_text(encoding="utf-8-sig", errors="replace").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("="); env[k.strip()] = v.strip().strip('"').strip("'")
K = env.get("DASHSCOPE_API_KEY", "")
PNG = SEAT/"exp"/"exp24_persona_firstframe_16x9_20261011.png"
B64 = "data:image/png;base64," + base64.b64encode(PNG.read_bytes()).decode()
PROMPT = "第三人称：夜间游乐场大门前，守门人背影立于阶上，手持刻纹石碑短杖，门内透出暖黄灯光，薄雾，湿石板地面反光。"

def call(url, body=None, method="GET", to=90):
    data = json.dumps(body, ensure_ascii=False).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Bearer " + K)
    if body: r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=to) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:
        return -1, str(e)[:150]

def od(txt):
    try:
        j = json.loads(txt); o = j.get("output") or {}
        return o.get("code"), (o.get("data") or {})
    except Exception:
        return None, {}

res = []
for rnd in (1, 2):
    st, tx = call(BASE + "/worlds", {"async": True, "perspective": "third_person", "prompt": PROMPT, "firstFrameImage": {"base64": B64}}, "POST")
    code, d = od(tx)
    wid = d.get("encryptedWorldId") or ""
    name = ffh = None
    for i in range(5):
        time.sleep(6)
        s2, t2 = call(BASE + "/worlds/build-status?encryptedWorldId=" + urllib.parse.quote(str(wid)))
        _, dd = od(t2)
        if dd.get("status") == "ready":
            name = dd.get("name")
            ff = dd.get("firstFrame")
            if ff:
                try:
                    req = urllib.request.Request(ff, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=90) as resp:
                        raw = resp.read()
                    ffh = hashlib.sha3_256(raw).hexdigest()[:16] + "（%d B）" % len(raw)
                    (SEAT/"exp"/("exp26_platform_frame_%d.png" % rnd)).write_bytes(raw)
                except Exception as e:
                    ffh = "下载失败：" + str(e)[:50]
            break
        if dd.get("status") == "failed":
            break
    res.append({"rnd": rnd, "http": st, "code": code, "worldId": wid, "name": name, "firstFrameHash": ffh})
    print("   第%d次：HTTP %s ｜ code=%s ｜ worldId=%s… ｜ 名=%s ｜ 平台首帧 %s" % (
        rnd, st, code, (wid[:22] + "…") if wid else "无", name, ffh))
    time.sleep(2)
if len(res) == 2:
    same_id = res[0]["worldId"] == res[1]["worldId"]
    same_name = res[0]["name"] == res[1]["name"]
    same_ff = res[0]["firstFrameHash"] == res[1]["firstFrameHash"]
    print("\n   ★ 判：worldId %s ｜ 平台命名 %s ｜ 平台首帧 %s" % (
        "★相同" if same_id else "★不同", "★相同" if same_name else "★不同", "★相同" if same_ff else "★不同"))
    print("   ⇒ %s" % ("★内容确定、id 不同 ⇒ id 为每次唯一之句柄（非内容标识）" if (not same_id and same_ff) else
                       ("★id 与内容皆同 ⇒ 该调用具确定性" if same_id else "★id 与首帧皆异 ⇒ 内容亦不确定")))
    (SEAT/"exp"/"exp26_determinism_20261012.json").write_text(json.dumps(
        {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "runs": res,
         "same": {"worldId": same_id, "name": same_name, "firstFrame": same_ff}}, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    print("   落盘：exp26_determinism_20261012.json")
