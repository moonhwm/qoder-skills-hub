# -*- coding: utf-8 -*-
"""wm_worlds_dump.py —— 逐页列举本账户之世界并摘要（只读 GET；2026-10-12 立）
承：wm_worlds_list.py（/worlds 可用，pageSize=20 生效；★20/20 条共享账户级前缀 8rcpnKlw6xp3）
本器：① 以 pageSize 逐页取全清单（至多 --max-pages 页）；② ★打印各世界之"非敏感字段"（id 全长／后段、status、name/描述前 24 字、创建时间）；
      ③ ★核"取票用之 WID"是否在其中；④ 给"世界总数"与"是否含目标"之判。
★安全：只 GET；不建世界、不改配置、不删；★不回显凭据。
判据（可失败）：①至少取到 1 页；②能给出世界总数；③★"取票之 WID 是否在清单中"已判
用法：python wm_worlds_dump.py [--page-size 100] [--max-pages 10] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.parse, urllib.request

WID = "8rcpnKlw6xp3FtpLvZIGB9mlTipFohD7syfWSOD-bt5fNs2BU7TeGEDpaTrloI7x"
BASE = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("DASHSCOPE_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def get(path, K):
    r = urllib.request.Request(BASE + path, method="GET")
    if K: r.add_header("Authorization", "Bearer " + K)
    try:
        with urllib.request.urlopen(r, timeout=40) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, str(e)[:160]


def items_of(txt):
    try:
        j = json.loads(txt); out = j.get("output") if isinstance(j.get("output"), dict) else j
        d = out.get("data") if isinstance(out, dict) else None
        its = d.get("items") if isinstance(d, dict) else (d if isinstance(d, list) else None)
        return its if isinstance(its, list) else []
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page-size", type=int, default=100); ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    K = key()
    print("  ═══ 世界逐页列举（只读；★不回显凭据）═══")
    allit, page = [], 1
    while page <= a.max_pages:
        st, txt = get("/worlds?pageSize=%d&pageNumber=%d" % (a.page_size, page), K)
        its = items_of(txt)
        print("   第 %d 页（pageSize=%d）⇒ HTTP %s ｜ 条目 %d" % (page, a.page_size, st, len(its)))
        if not its: break
        allit += its
        if len(its) < a.page_size: break
        page += 1
    seen = set(); uniq = []
    for it in allit:
        k = str(it.get("encryptedWorldId") or it.get("worldId") or it.get("id") or "")
        if k and k not in seen: seen.add(k); uniq.append(it)
    print("   ★世界总数（去重后）：%d" % len(uniq))
    rows = []
    for it in uniq:
        i = str(it.get("encryptedWorldId") or it.get("worldId") or it.get("id") or "")
        rows.append({"id": i, "tail": i.split("-")[-1][:12], "status": str(it.get("status") or it.get("state") or ""),
                     "name": str(it.get("name") or it.get("title") or it.get("description") or "")[:24],
                     "created": str(it.get("createdAt") or it.get("createTime") or it.get("gmtCreate") or "")[:19]})
    print("   ── 各世界（id 后段 ｜ status ｜ name ｜ 创建）──")
    for r in rows[:25]:
        print("      %-14s ｜ %-10s ｜ %-24s ｜ %s" % (r["tail"], r["status"][:10], r["name"], r["created"]))
    if len(rows) > 25: print("      …（余 %d 条）" % (len(rows)-25))
    has = any(r["id"] == WID for r in rows)
    wait = [r for r in rows if r["status"].lower() in ("ready", "running", "active")]
    crit = {"①至少取到 1 页": len(allit) > 0, "②能给出世界总数": len(uniq) > 0,
            "③★取票之 WID 是否在清单中已判": True}
    print("   ── 判据 ──")
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    print("   ⇒ 判：★取票用之 WID 在清单中＝★%s ｜ 状态为 ready/running 者 %d 条" % (has, len(wait)))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "pages": page, "total": len(uniq), "has_wid": has, "ready_count": len(wait), "rows": rows,
            "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
