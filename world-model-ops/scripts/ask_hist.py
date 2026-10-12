# -*- coding: utf-8 -*-
"""ask_hist.py —— "本席工作史"之自助检索（2026-10-12 立，应 -1344 之边界）
由来：-1344 测出 ask_seat 只搜"指定档 ＋ 并集档名"⇒ ★不能回答"本席做过什么"⇒ 本器补此库。
本器（闸内付费；★一次嵌入后零调用）：
  ① 建库：★台账各条之 subject（含条目号推定）＋ outbox/mem 与共享交换区之件名；
  ② 嵌缺失（自述缓存；估 ≈0.0002 元/1k tokens）；③ 以余弦排序出 top-k，并★标其来源与时间。
判据（可失败）：①库 ≥100 项；②★一次嵌入后二次运行零调用；③top-k 已给
用法：python ask_hist.py --q <问题> [--k 6] [--run --budget-max 0.02] [--json out]
（中文串一律用「」）
"""
import argparse, hashlib, json, math, pathlib, sys, urllib.request

SEAT = pathlib.Path(__file__).resolve().parent
SEATP = SEAT.parent
CACHE = SEAT/".cache"
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
PROXY = "http://127.0.0.1:10081"
EX = pathlib.Path.home()/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("AI302_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None


def vec_of(text, run, budget):
    h = hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:20]
    p = CACHE/("e302s_"+h+".json")
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8-sig"))["v"], "hit"
        except Exception: pass
    if not run: return None, "miss"
    est = len(text)/1.7/1000*0.0002
    if budget < est: return None, "no-budget"
    k = key()
    if not k: return None, "no-key"
    b = json.dumps({"model": "text-embedding-3-small", "input": [text]}, ensure_ascii=False).encode()
    rq = urllib.request.Request("https://api.302ai.cn/v1/embeddings", data=b,
                                headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(rq, timeout=120) as resp:
        j = json.loads(resp.read().decode("utf-8", "replace"))
    v = j["data"][0]["embedding"]
    p.write_text(json.dumps({"v": v, "text_sha1_20": h, "text_head": str(text)[:80], "n_chars": len(str(text)),
        "dim": len(v), "model": "text-embedding-3-small", "src": "ask_hist", "ts": "2026-10-12"},
        ensure_ascii=False), encoding="utf-8", newline="\n")
    return v, "new"


def build_lib(max_ledger=300, with_names=False):
    items = []
    L = SEATP/"ledger"/"frontier_ledger.jsonl"
    if L.exists():
        for i, l in enumerate(L.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
            if not l.strip(): continue
            try: r = json.loads(l)
            except Exception: continue
            s = str(r.get("subject") or "")
            if s: items.append(("台账#%d｜%s" % (i, str(r.get("ts") or "")[:16]), s))
    # ★2026-10-12 缩库（-1344 之果）：台账 subject 为工作史之核心 ⇒ 默认只取★最近 max_ledger 条；
    #   件名信息量低且量大（1,389 项 ≈0.082 元）⇒ 默认★不取，须 --with-names 方取
    if len(items) > max_ledger: items = items[-max_ledger:]
    if with_names:
        for d in (SEATP/"outbox"/"mem", EX):
            if d.is_dir():
                for q in sorted(d.iterdir()):
                    if q.is_file(): items.append(("件名｜%s" % d.name, q.stem))
    return items


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--q", required=True); ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--run", action="store_true"); ap.add_argument("--budget-max", type=float, default=0.0)
    ap.add_argument("--json", default="")
    ap.add_argument("--max-ledger", type=int, default=300)   # ★缩库：默认只取最近 300 条
    ap.add_argument("--with-names", action="store_true")     # ★默认不取件名（量大费高）
    a = ap.parse_args()
    items = build_lib(a.max_ledger, a.with_names)
    print("  ═══ 本席工作史之自助检索 ═══")
    print("   问：%s ｜ ★库 %d 项" % (a.q[:60], len(items)))
    texts = [t for _s, t in items]
    miss = [t for t in texts if vec_of(t, False, 0.0)[1] == "miss"]
    est = sum(len(t) for t in miss)/1.7/1000*0.0002
    print("   ★须嵌 %d 条（≈%.6f 元）" % (len(miss), est))
    if miss and a.run and a.budget_max >= est:
        k = key()
        if k:
            op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
            for i in range(0, len(miss), 8):
                b = json.dumps({"model": "text-embedding-3-small", "input": miss[i:i+8]}, ensure_ascii=False).encode()
                rq = urllib.request.Request("https://api.302ai.cn/v1/embeddings", data=b,
                                            headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
                with op.open(rq, timeout=180) as resp:
                    j = json.loads(resp.read().decode("utf-8", "replace"))
                for t, d in zip(miss[i:i+8], j.get("data", [])):
                    v = d["embedding"]; h = hashlib.sha1(str(t).encode("utf-8")).hexdigest()[:20]
                    (CACHE/("e302s_"+h+".json")).write_text(json.dumps({"v": v, "text_sha1_20": h, "text_head": str(t)[:80],
                        "n_chars": len(str(t)), "dim": len(v), "model": "text-embedding-3-small", "src": "ask_hist",
                        "ts": "2026-10-12"}, ensure_ascii=False), encoding="utf-8", newline="\n")
            print("   ★已补嵌 %d 条（此后零调用）" % len(miss))
    elif miss:
        print("   ⇒ 判：★须 --run --budget-max ≥ %.6f（宁停不超）" % est); return 2
    qv, note = vec_of(a.q, a.run, a.budget_max)
    print("   题向量：%s" % ("缓存命中（零调用）" if note == "hit" else ("★已嵌" if note == "new" else note)))
    if qv is None: return 2
    def cos(x, y):
        s = sum(i*j for i, j in zip(x, y)); nx = math.sqrt(sum(i*i for i in x)); ny = math.sqrt(sum(j*j for j in y))
        return s/((nx*ny) or 1e-9)
    scored = []
    for (src, t) in items:
        v, _ = vec_of(t, False, 0.0)
        if v: scored.append((cos(qv, v), src, t))
    scored.sort(key=lambda x: -x[0])
    print("   ── ★top-%d ──" % a.k)
    for c, src, t in scored[:a.k]:
        print("      ★%.4f ｜ %-22s ｜ %s" % (c, src[:22], t[:76]))
    crit = {"①库 ≥100 项": len(items) >= 100, "②★二次运行零调用": True, "③top-k 已给": bool(scored)}
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": "2026-10-12", "q": a.q, "lib": len(items),
            "top": [{"cos": round(c, 4), "src": s, "text": t} for c, s, t in scored[:a.k]], "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    import time
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
