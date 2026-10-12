# -*- coding: utf-8 -*-
"""wm_worlds_list.py —— 只读列举本账户之世界（核"取票成功之世界"与"今日方块虚空世界"是否同一）（2026-10-12 立）
承：led_1099 之 evidence（ready「方块虚空」｜id 8rcpnKlw…-8TOusEBzG0Rm｜回显 0.22/255｜标记 197px｜列举 5 条共享前缀）
    与 wm_get_ticket.py 之 WID（8rcpnKlw6xp3FtpLvZIGB9mlTipFohD7syfWSOD-bt5fNs2BU7TeGEDpaTrloI7x）
本器：只发 GET（/worlds 之若干候选路径），★不建世界、不改配置、零花费；★不回显凭据；给出"世界清单"与"是否含 WID"之判。
判据（可失败）：①至少一条候选路径得 2xx；②能取到世界条目数；③★"取票之 WID 是否在清单中"已判
用法：python wm_worlds_list.py [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

WID = "8rcpnKlw6xp3FtpLvZIGB9mlTipFohD7syfWSOD-bt5fNs2BU7TeGEDpaTrloI7x"
BASE = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
CANDS = ["/worlds", "/worlds?pageSize=20", "/world/list", "/worlds/list"]
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("DASHSCOPE_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def mask(s, k):
    s = str(s)
    if k and len(k) > 8: s = s.replace(k, "★KEY★")
    return s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    K = key()
    print("  ═══ 世界列举（只读 GET）═══")
    print("   WID（取票用）：%s…（%d 字）｜ 凭据：%s" % (WID[:12], len(WID), "已读到（值不回显）" if K else "★未读到"))
    best = None
    for path in CANDS:
        r = urllib.request.Request(BASE + path, method="GET")
        if K: r.add_header("Authorization", "Bearer " + K)
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                st, txt = resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            st, txt = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            st, txt = -1, str(e)[:140]
        print("   %-22s ⇒ HTTP %-5s ｜ %s" % (path, st, mask(txt[:150], K).replace("\n", " ")))
        if 200 <= st < 300 and best is None:
            best = (path, txt)
    rows = {}
    n = None
    if best:
        try:
            j = json.loads(best[1])
            out = j.get("output") if isinstance(j.get("output"), dict) else j
            data = out.get("data") if isinstance(out, dict) else None
            items = data if isinstance(data, list) else (data.get("items") if isinstance(data, dict) else None) \
                    or (out.get("items") if isinstance(out, dict) else None)
            if isinstance(items, list):
                n = len(items)
                ids = []
                for it in items:
                    if isinstance(it, dict):
                        ids.append(str(it.get("encryptedWorldId") or it.get("worldId") or it.get("id") or "")[:64])
                rows = {"items": n, "ids_head": [x[:12] for x in ids], "has_wid": any(x == WID for x in ids)}
        except Exception as e:
            print("   ★解析失败：%s" % str(e)[:80])
    crit = {"①至少一条候选路径得 2xx": best is not None, "②能取到世界条目数": n is not None,
            "③★取票之 WID 是否在清单中已判": bool(rows)}
    print("   ── 判据 ──")
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    if rows:
        print("   ⇒ 清单：★%d 条 ｜ 前缀：%s ｜ ★取票之 WID 在清单中＝%s" % (rows["items"], "、".join(rows["ids_head"]), rows["has_wid"]))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "wid_prefix": WID[:12], "path": (best[0] if best else ""), "rows": rows, "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
