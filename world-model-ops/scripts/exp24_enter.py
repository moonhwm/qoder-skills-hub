# -*- coding: utf-8 -*-
"""exp24_enter.py —— 本世界（自生成人设首帧）进房与产物获取
用法：python exp24_enter.py --wid <encryptedWorldId> [--sec 60] [--tag exp24]
纪律：①ticket 不落盘不打印 ②RTC token 不打印（只报字段存在）③失败如实分类
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.request, urllib.error, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HOME = pathlib.Path.home()
BASE = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
OUT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"/"exp"
env = {}
for line in (HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env").read_text(encoding="utf-8-sig", errors="replace").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("="); env[k.strip()] = v.strip().strip('"').strip("'")
K = env.get("DASHSCOPE_API_KEY", "")


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
        return e.code, round(time.time()-t0, 2), e.read().decode("utf-8", "replace")[:300]
    except Exception as e:
        return -1, round(time.time()-t0, 2), str(e)[:160]


def data_of(txt):
    try:
        j = json.loads(txt); return (j.get("output") or {}), (j.get("output") or {}).get("data") or {}
    except Exception:
        return {}, {}


ap = argparse.ArgumentParser(); ap.add_argument("--wid", required=True)
ap.add_argument("--sec", type=int, default=60); ap.add_argument("--tag", default="exp24")
a = ap.parse_args()
st, dt, txt = call(BASE + "/worlds/get-travel-credential", {"encryptedWorldId": a.wid}, "POST")
o, d = data_of(txt)
ticket = d.get("ticket") or ""
print("① 换票 ⇒ HTTP %s ｜ code=%s ｜ ticket=%s ｜ expiresIn=%s" % (st, o.get("code"), "★有" if ticket else "无", d.get("expiresIn")))
if not ticket: print("   原始：%s" % txt[:200]); sys.exit(1)
st, dt, txt = call(BASE + "/travels/enter-travel", {"ticket": ticket, "maxExperienceTimeSec": a.sec}, "POST")
o, d = data_of(txt)
tid = d.get("encryptedTravelId") or ""; rtc = d.get("rtcConfig") or {}
print("② 进房 ⇒ HTTP %s ｜ code=%s ｜ TravelId=%s ｜ rtcConfig=%s（字段 %s）" % (
    st, o.get("code"), (str(tid)[:20]+"…") if tid else "无", "★有" if rtc else "null",
    sorted(rtc.keys()) if isinstance(rtc, dict) and rtc else "—"))
if not tid: print("   原始：%s" % txt[:200]); sys.exit(1)
ses = []
for i in range(4):
    time.sleep(6)
    s, dd, t = call(BASE + "/travels/status?encryptedTravelId=" + urllib.parse.quote(str(tid)), None, "GET")
    o2, j = data_of(t)
    ses.append({"t": i, "status": j.get("status"), "rtc": j.get("rtcStatus"),
                "char": j.get("characterActions"), "env": j.get("environmentActions")})
    print("③ 状态%d ⇒ status=%s ｜ rtcStatus=%s ｜ 角色动作=%s ｜ 环境动作=%s" % (
        i+1, j.get("status"), j.get("rtcStatus"), j.get("characterActions"), j.get("environmentActions")))
print("④ 待 %ds（无客户端推流 ⇒ 预期自终）…" % (a.sec//2))
time.sleep(a.sec//2)
s, dd, t = call(BASE + "/travels/status?encryptedTravelId=" + urllib.parse.quote(str(tid)), None, "GET")
o3, j = data_of(t)
print("   终态 ⇒ status=%s ｜ rtcStatus=%s" % (j.get("status"), j.get("rtcStatus")))
arts = None
for path in ("/travels/artifacts?encryptedTravelId=", "/travels/artifact?encryptedTravelId="):
    s, dd, t = call(BASE + path + urllib.parse.quote(str(tid)), None, "GET")
    o4, jj = data_of(t)
    keys = sorted(jj.keys()) if isinstance(jj, dict) else "—"
    print("⑤ 产物 %-34s ⇒ HTTP %s ｜ keys=%s ｜ %s" % (path.split("?")[0], s, keys, t[:150].replace("\n"," ")))
    if s == 200 and isinstance(jj, dict) and jj: arts = jj; break
rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "tag": a.tag, "world": a.wid, "travel": tid,
       "maxExperienceTimeSec": a.sec, "status_seq": ses,
       "final": {"status": j.get("status"), "rtc": j.get("rtcStatus")},
       "artifacts_keys": (sorted(arts.keys()) if isinstance(arts, dict) else None),
       "artifacts": arts}
p = OUT/(a.tag + "_enter_record_20261011.json")
p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("   落盘：%s" % p.name)
