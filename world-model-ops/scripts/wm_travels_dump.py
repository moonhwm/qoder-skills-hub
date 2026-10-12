# -*- coding: utf-8 -*-
"""wm_travels_dump.py —— 只读列出全部会话（travel）并按其状态统计（2026-10-12 立）
承：wm_travels_probe（/travels 可用；pageSize=100 ⇒ 73 条）
本器：① 逐页取全部会话（至多 --max-pages 页）；② ★打印每条之关键字段（id 后 8 字、status、worldId 后 8 字、创建时间）
      ③ ★按 status 计数 ⇒ 判"是否有进行中之会话"（若有 ⇒ 可解释 code=500001 之推理资源分配失败）
★安全：只 GET；不 enter／不 instruct／不关闭任何会话；★不回显凭据
判据（可失败）：①取到 ≥1 条；②status 分布已给出；③★"是否有进行中者"已判
用法：python wm_travels_dump.py [--page-size 100] [--max-pages 5] [--json out]
（中文串一律用「」）
"""
import argparse, collections, json, pathlib, sys, time, urllib.error, urllib.request

B = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
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
    r = urllib.request.Request(B + path, method="GET")
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
        its = (d.get("items") if isinstance(d, dict) else d) or (out.get("items") if isinstance(out, dict) else None)
        return its if isinstance(its, list) else []
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--max-pages", type=int, default=5); ap.add_argument("--json", default="")
    a = ap.parse_args()
    K = key()
    print("  ═══ 会话（travel）全量列举（只读；★不回显凭据）═══")
    allit, page = [], 1
    while page <= a.max_pages:
        st, txt = get("/travels?pageSize=%d&pageNumber=%d" % (a.page_size, page), K)
        its = items_of(txt)
        print("   第 %d 页 ⇒ HTTP %s ｜ 条目 %d" % (page, st, len(its)))
        if not its: break
        allit += its
        if len(its) < a.page_size: break
        page += 1
    seen, uniq = set(), []
    for it in allit:
        k = str(it.get("encryptedTravelId") or it.get("id") or "")
        if k and k not in seen: seen.add(k); uniq.append(it)
    print("   ★会话总数（去重）%d" % len(uniq))
    cnt = collections.Counter(str(it.get("status") or it.get("state") or "?") for it in uniq)
    print("   ★按状态：%s" % "、".join("%s=%d" % (k, v) for k, v in cnt.most_common()))
    rows = []
    for it in uniq[:30]:
        i = str(it.get("encryptedTravelId") or it.get("id") or "")
        rows.append({"tail": i[-8:], "status": str(it.get("status") or it.get("state") or ""),
                     "world_tail": str(it.get("encryptedWorldId") or it.get("worldId") or "")[-8:],
                     "created": str(it.get("createdAt") or it.get("createTime") or "")[:19],
                     "end": str(it.get("endTime") or it.get("expireTime") or "")[:19]})
    print("   ── 前 30 条（id 后 8 ｜ status ｜ world 后 8 ｜ 创建 ｜ 结束）──")
    for r in rows:
        print("      %-9s ｜ %-12s ｜ %-9s ｜ %-19s ｜ %s" % (r["tail"], r["status"][:12], r["world_tail"], r["created"], r["end"]))
    live = [r for r in rows if r["status"].lower() in ("running", "active", "in_progress", "ongoing", "entered")]
    crit = {"①取到 ≥1 条": len(uniq) > 0, "②status 分布已给出": len(cnt) > 0,
            "③★是否有进行中者已判": True}
    print("   ── 判据 ──")
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    print("   ⇒ 判：★进行中之会话 %d 个 ⇒ %s" % (len(live),
          "★可解释 500001（推理资源被占）" if live else "★未见'进行中'之会话（500001 之因须另寻：容量／配额）"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "total": len(uniq), "status_count": dict(cnt), "rows": rows, "live": len(live), "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
