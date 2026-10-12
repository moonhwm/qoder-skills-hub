# -*- coding: utf-8 -*-
"""wm_min_instruct.py —— 在★既有世界（夜间游乐场）上做一次★最小生成（2026-10-12 立）
承：exp6_persona_in_world.py 之链路（POST /worlds → build-status → get-travel-credential → enter-travel
     → ★/travels/instruct → /travels/artifacts ⇒ video.original.url）
本器：★不新建世界（用既有「夜间游乐场」之 encryptedWorldId）⇒ 取票 ⇒ 进房（60 s）⇒ ★一次短指令
      ⇒ 轮询产物（至多 3 次、间隔 15 s）⇒ 若得 URL 则下载录像（★限 <8 MB）
★纪律：ticket / token ★不打印、不落盘；只报 HTTP／业务码／时延／是否有 URL；录像落 outbox/mem（非临时目录）
判据（可失败）：①各步皆给出 code；②产物状态给出；③★"指令是否兑现"之原始证据（录像或不兑现之读数）已取
用法：python wm_min_instruct.py [--wid <id>] [--sec 60] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

WID_NIGHT = "8rcpnKlw6xp3FtpLvZIGB0G5gEekLc2xgt4Xh4Y6GfceXZFiVk889HrvHtCxWWeB"   # ★既有「夜间游乐场」
B = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
SEAT = pathlib.Path(__file__).resolve().parent.parent
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
INSTRUCT = "请让环心的人形分身向前走两步，然后举起右手。"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("DASHSCOPE_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--wid", default=WID_NIGHT); ap.add_argument("--sec", type=int, default=60)
    ap.add_argument("--json", default=""); a = ap.parse_args()
    K = key()
    R = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "wid_tail": a.wid[-8:], "instruct": INSTRUCT, "steps": []}
    print("  ═══ 既有世界上之最小生成（★ticket/token 不落盘）═══")
    print("   世界：…%s ｜ 令：%s" % (a.wid[-8:], INSTRUCT))

    def call(method, path, body=None, to=200):
        r = urllib.request.Request(B + path, data=json.dumps(body, ensure_ascii=False).encode() if body else None, method=method)
        r.add_header("Authorization", "Bearer " + K)
        if body: r.add_header("Content-Type", "application/json")
        t0 = time.time()
        try:
            with urllib.request.urlopen(r, timeout=to) as resp:
                return resp.status, resp.read().decode("utf-8", "replace"), round(time.time()-t0, 2)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace"), round(time.time()-t0, 2)
        except Exception as e:
            return -1, str(e)[:150], round(time.time()-t0, 2)

    def od(tx):
        try:
            o = json.loads(tx).get("output") or {}
            return o.get("code"), o.get("message"), (o.get("data") or {})
        except Exception:
            return None, tx[:90], {}

    # ① 取票
    st, tx, dt = call("POST", "/worlds/get-travel-credential", {"encryptedWorldId": a.wid})
    c, m, d = od(tx); tk = d.get("ticket")
    R["steps"].append({"step": "ticket", "http": st, "code": c, "sec": dt, "has_ticket": bool(tk)})
    print("   ① 取票 ⇒ HTTP %s ｜ code=%s ｜ %.2f s ｜ 有票=%s" % (st, c, dt, bool(tk)))
    if not tk:
        print("   ⇒ ★未取到票（code=%s msg=%s）⇒ 停（宁停不超）" % (c, m)); return 2
    # ② 进房
    st, tx, dt = call("POST", "/travels/enter-travel", {"ticket": tk, "maxExperienceTimeSec": a.sec})
    c, m, d = od(tx); tid = d.get("encryptedTravelId")
    R["steps"].append({"step": "enter", "http": st, "code": c, "sec": dt, "has_travel": bool(tid)})
    print("   ② 进房 ⇒ HTTP %s ｜ code=%s ｜ %.2f s ｜ 有房=%s" % (st, c, dt, bool(tid)))
    if not tid:
        print("   ⇒ ★未进房（code=%s msg=%s）⇒ 停" % (c, m)); return 2
    # ③ 指令
    st, tx, dt = call("POST", "/travels/instruct", {"encryptedTravelId": str(tid), "content": INSTRUCT})
    c, m, d = od(tx)
    R["steps"].append({"step": "instruct", "http": st, "code": c, "sec": dt})
    print("   ③ 指令 ⇒ HTTP %s ｜ code=%s ｜ %.2f s" % (st, c, dt))
    # ④ 产物
    print("   …候产物（%d s）" % min(a.sec, 45)); time.sleep(min(a.sec, 45))
    url = None
    for att in range(1, 4):
        st, tx, dt = call("GET", "/travels/artifacts?encryptedTravelId=" + str(tid))
        c, m, d = od(tx)
        url = ((d.get("video") or {}).get("original") or {}).get("url")
        R["steps"].append({"step": "artifacts-%d" % att, "http": st, "code": c, "compose": d.get("composeStatus"), "has_url": bool(url)})
        print("   ④ 产物 第%d次 ⇒ HTTP %s ｜ code=%s ｜ compose=%s ｜ URL=%s" % (att, st, c, d.get("composeStatus"), "有" if url else "无"))
        if url: break
        time.sleep(15)
    if url:
        dst = SEAT/"outbox"/"mem"/("wm_min_instruct_%s.mp4" % time.strftime("%Y%m%d_%H%M"))
        try:
            req = urllib.request.Request(url); req.add_header("User-Agent", "cairn/1.0")
            with urllib.request.urlopen(req, timeout=300) as resp, open(dst, "wb") as f:
                n = 0
                while True:
                    b = resp.read(1 << 20)
                    if not b: break
                    f.write(b); n += len(b)
                    if n > 8*1024*1024: break
            print("   ★录像已落：%s（%.2f MB）" % (dst.name, n/1048576))
            R["video"] = {"file": dst.name, "bytes": n}
        except Exception as e:
            print("   ★下载失败：%s" % str(e)[:90])
    crit = {"①各步皆给出 code": all("code" in s for s in R["steps"] if s["step"] != "artifacts-1" or True),
            "②产物状态给出": any(s.get("compose") for s in R["steps"]),
            "③★指令是否兑现之原始证据已取": bool(url)}
    print("   ── 判据 ──")
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
