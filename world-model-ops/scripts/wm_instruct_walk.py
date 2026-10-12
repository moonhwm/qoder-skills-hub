# -*- coding: utf-8 -*-
"""wm_instruct_walk.py —— 以"具名动作"之明确指令再进房一次（2026-10-12 立）
法源：令条「世界模型…均须强制调用」「个人基于人设的动态完善3D建模，放到世界模型中，理应尝试涌现」。
缘由：-1372 定"指令端点＝/travels/instruct（encryptedTravelId ＋ content）"，而 19:14 之"向前走两步"
      得"在场而未演"⇒ ★本器以★更明确之措辞（点名动画／步数／时长）重发，并★前后对照状态字段。
本器（★最小化：一次会话 60 s；★不回显凭据）：
  ① GET /worlds?status=ready ⇒ 取 ready 世界；② POST /worlds/get-travel-credential（取票）；
  ③ POST /travels/enter-travel（60 s）；④ ★读 status（★基线：characterActions 等）；
  ⑤ ★POST /travels/instruct 两条明确指令；⑥ 再读 status（★对照）；⑦ GET /travels/artifacts（若有）
判据（可失败）：①进房 code=0；②★指令后状态字段有变化（否则如实报"未兑现"）；③产物端点有响应
用法：python wm_instruct_walk.py [--sec 60] [--dry]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.parse, urllib.request, urllib.error

BASE = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
PROXY = "http://127.0.0.1:10081"
KEY_NAME = "DASHSCOPE_API_KEY"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith(KEY_NAME):
                return l.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def call(path, body=None, to=90, tries=3):
    k = key()
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    for i in range(tries):
        try:
            data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
            r = urllib.request.Request(BASE + path, data=data,
                                       headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"},
                                       method="POST" if body is not None else "GET")
            t0 = time.time()
            with op.open(r, timeout=to) as resp:
                return resp.status, time.time()-t0, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, 0.0, e.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries-1: return -1, 0.0, str(e)[:120]
            time.sleep(2)
    return -1, 0.0, "?"


def d_of(txt):
    try:
        o = json.loads(txt).get("output") or {}
        return o.get("code"), (o.get("data") or {})
    except Exception:
        return None, {}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sec", type=int, default=60); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    print("  ═══ 以具名动作之明确指令再进房（★最小化：一次会话 %d s）═══" % a.sec)
    st, dt, tx = call("/worlds?page=1&pageSize=50&status=ready")   # ★pageSize 50（-1373 之训：勿截断）
    code, d = d_of(tx)
    items = d.get("items") or []
    print("   ① 列世界：HTTP %s ｜ code=%s ｜ ready %d 个" % (st, code, len(items)))
    if not items:
        print("   ⇒ 判：★无 ready 世界，止"); return 2
    # ★优先选令条所指之"夜间游乐场"（★否则会误进他世界）
    _np = [x for x in items if "夜间游乐场" in str(x.get("name") or "")]
    pick = (_np[0] if _np else items[0])
    print("      ★候选：%s" % "、".join(str(x.get("name"))[:14] for x in items[:5]))
    wid = pick.get("encryptedWorldId"); wname = pick.get("name")
    print("      ★世界：%s（ID 尾 %s）" % (str(wname)[:24], str(wid)[-8:]))
    if a.dry:
        print("   ⇒ DRY：止（不取票、不进房）"); return 0
    st, dt, tx = call("/worlds/get-travel-credential", {"encryptedWorldId": wid})
    code, d = d_of(tx); tk = d.get("ticket")
    print("   ② 取票：HTTP %s ｜ code=%s ｜ %.2fs ｜ 票=%s" % (st, code, dt, "★有" if tk else "无"))
    if not tk:
        print("      ★原始：%s" % tx[:180]); return 2
    st, dt, tx = call("/travels/enter-travel", {"ticket": tk, "maxExperienceTimeSec": a.sec})
    code, d = d_of(tx); tid = d.get("encryptedTravelId")
    print("   ③ 进房：HTTP %s ｜ ★code=%s ｜ %.2fs ｜ TravelId 尾 %s" % (st, code, dt, str(tid)[-8:]))
    if code != 0 or not tid:
        print("      ★原始：%s" % tx[:200]); return 2
    st, dt, tx = call("/travels/status?encryptedTravelId=" + urllib.parse.quote(str(tid)))
    _, s0 = d_of(tx)
    base_acts = s0.get("characterActions") or s0.get("actions")
    print("   ④ 基线状态：status=%s ｜ rtcStatus=%s ｜ ★characterActions=%s"
          % (s0.get("status"), s0.get("rtcStatus"), json.dumps(base_acts, ensure_ascii=False)[:80]
             if base_acts is not None else "null"))
    INSTR = [
        "播放行走动画，向前移动三步",
        "请让角色执行 WALK 动作并前进，动画名 WALK",
    ]
    for i, c in enumerate(INSTR, 1):
        st, dt, tx = call("/travels/instruct", {"encryptedTravelId": str(tid), "content": c})
        code, d = d_of(tx)
        print("   ⑤-%d 指令：%s" % (i, c))
        print("        ⇒ HTTP %s ｜ code=%s ｜ %.2fs ｜ 占比对：%s" % (st, code, dt, json.dumps(d, ensure_ascii=False)[:90]))
        time.sleep(3)
    st, dt, tx = call("/travels/status?encryptedTravelId=" + urllib.parse.quote(str(tid)))
    _, s1 = d_of(tx)
    aft = s1.get("characterActions") or s1.get("actions")
    print("   ⑥ 指令后状态：status=%s ｜ rtcStatus=%s ｜ ★characterActions=%s"
          % (s1.get("status"), s1.get("rtcStatus"), json.dumps(aft, ensure_ascii=False)[:80]
             if aft is not None else "null"))
    changed = (json.dumps(base_acts, ensure_ascii=False, sort_keys=True) != json.dumps(aft, ensure_ascii=False, sort_keys=True))
    print("   ★前后对照：%s" % ("★有变化！" if changed else "★无变化（未兑现）"))
    print("   ★等待会话结束（%d s）…" % a.sec)
    time.sleep(max(0, a.sec))
    st, dt, tx = call("/travels/status?encryptedTravelId=" + urllib.parse.quote(str(tid)))
    _, s2 = d_of(tx)
    print("   ⑦ 末态：status=%s ｜ rtcStatus=%s ｜ 键：%s"
          % (s2.get("status"), s2.get("rtcStatus"), "、".join(list(s2.keys())[:12])))
    arts = s2.get("artifacts") or s2.get("videos") or s2.get("records")
    print("   ★产物线索：%s" % (json.dumps(arts, ensure_ascii=False)[:200] if arts else "（末态无 artifacts/videos/records 键）"))
    crit = {"①进房 code=0": code == 0, "②★指令后字段有变化": changed, "③末态已读": bool(s2)}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    out = pathlib.Path(__file__).resolve().parent.parent/"outbox"/"mem"/"wm_instruct_walk_20261012.json"
    out.write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "world": str(wname), "sec": a.sec,
        "instructions": INSTR, "baseline_acts": base_acts, "after_acts": aft, "end_status": s2,
        "changed": changed, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   ⇒ 已写：%s" % out.name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
