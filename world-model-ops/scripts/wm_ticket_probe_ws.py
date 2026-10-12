# -*- coding: utf-8 -*-
"""wm_ticket_probe_ws.py —— 两域各取一次 ticket 以核"既有世界是否仍 ready"（2026-10-12 立）
承：wm_get_ticket.py（官档：POST …/happyoyster-1.0-adventure/openapi/v1/worlds/get-travel-credential；
    体 {"encryptedWorldId": "<ready World>"}；仅主 API Key）；其 URL 写死 trial 域。
本器：① 以 trial 域与 WS（业务空间）域各发一次同请求；② ★只报"是否取到 ticket／前缀／长度／expiresIn／code"
      ⇒ ★ticket 值★不打印、不落盘（未用之票 1800 s 自然过期）；③ 给"世界是否仍 ready"之判。
判据（可失败）：①两域皆得可解析响应；②各域之 code 已给出；③★"既有世界是否仍 ready"已判
用法：python wm_ticket_probe_ws.py [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

WID = "8rcpnKlw6xp3FtpLvZIGB9mlTipFohD7syfWSOD-bt5fNs2BU7TeGEDpaTrloI7x"
PATH = "/api/v2/apps/happyoyster-1.0-adventure/openapi/v1/worlds/get-travel-credential"
DOMS = {"trial": "https://trial.cn-beijing.maas.aliyuncs.com",
        "WS": "https://ws-ay6o8osb22o9dc3t.cn-beijing.maas.aliyuncs.com"}
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("DASHSCOPE_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    K = key()
    print("  ═══ 两域取票探针（★ticket 不打印、不落盘；未用即自然过期）═══")
    print("   World：%s…（%d 字）｜ 凭据：%s" % (WID[:12], len(WID), "已读到（值不回显）" if K else "★未读到"))
    rows = []
    for dn, dom in DOMS.items():
        r = urllib.request.Request(dom + PATH, data=json.dumps({"encryptedWorldId": WID}).encode(), method="POST")
        r.add_header("Authorization", "Bearer " + K); r.add_header("Content-Type", "application/json")
        t0 = time.time()
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                st, txt = resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            st, txt = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            st, txt = -1, str(e)[:160]
        dt = round(time.time()-t0, 2)
        code = None; tk = ""; exp = None; msg = ""
        try:
            j = json.loads(txt); out = j.get("output") or j
            if isinstance(out, dict):
                code = out.get("code"); msg = str(out.get("message") or "")[:80]
                data = out.get("data") or {}
                if isinstance(data, dict): tk = str(data.get("ticket") or ""); exp = data.get("expiresIn")
        except Exception:
            msg = txt[:100]
        got = bool(code == 0 and tk)
        verdict = ("★世界仍有效（成功换取一次性 ticket：前缀 %s／长度 %d／expiresIn %s）" % (tk[:3], len(tk), exp)) if got \
                  else ("未取到（code=%s msg=%s）" % (code, msg))
        rows.append({"domain": dn, "status": st, "code": code, "message": msg, "got_ticket": got,
                     "ticket_prefix": (tk[:3] if tk else ""), "ticket_len": len(tk), "expires_in": exp, "sec": dt})
        print("   %-6s ⇒ HTTP %-5s ｜ code=%-6s ｜ %.2fs ｜ ★%s" % (dn, st, code, dt, verdict))
    crit = {"①两域皆得可解析响应": all(r["code"] is not None or r["message"] for r in rows),
            "②各域之 code 已给出": all("code" in r for r in rows),
            "③★既有世界是否仍 ready 已判": any(r["got_ticket"] for r in rows) or all(r["code"] is not None for r in rows)}
    print("   ── 判据 ──")
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    ok = [r["domain"] for r in rows if r["got_ticket"]]
    print("   ⇒ 判：%s" % ("★既有世界仍有效；可用域＝%s" % "、".join(ok) if ok else "★两域皆未取到 ⇒ 须看 code 定因（403007 未购规格／403008 容量／其它）"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "world_id_prefix": WID[:12], "rows": rows, "criteria": crit}, ensure_ascii=False, indent=1),
            encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s（★ticket 值未落盘）" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
