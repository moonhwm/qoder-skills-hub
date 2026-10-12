# -*- coding: utf-8 -*-
"""decision_evidence_build.py —— 为决策基准构造"外部事实源"证据（2026-10-12 立，应 -1358 之请）
由来：-1358 证"决策模型对本席事实无判断力"⇒ ★所拟之解为"接入外部事实源（★本席台账）再做 RAG 式判定"。
本器（★闸内；以已缓存向量为主）：
  ① 库：台账各条之 subject（默认最近 N 条）；
  ② 对基准之每条陈述，★嵌其向量（若缓存无则付费，估极微）⇒ 与库余弦比 ⇒ 取 top-K 为证据；
  ③ 输出新基准件：{stmt, truth, ev:[...]} ⇒ 供探针之 --ev-file 使用
判据（可失败）：①库 ≥50；②每条陈述皆有 top-K；③★不回显凭据
用法：python decision_evidence_build.py --suite <stmt基准> [--max-ledger 200] [--topk 3] [--run --budget-max 0.01] --out <json>
（中文串一律用「」）
"""
import argparse, hashlib, json, math, pathlib, sys, urllib.request

SEAT = pathlib.Path(__file__).resolve().parent
SEATP = SEAT.parent
CACHE = SEAT/".cache"
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
PROXY = "http://127.0.0.1:10081"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("AI302_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None


def vec(text, want, budget):
    h = hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:20]
    p = CACHE/("e302s_"+h+".json")
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8-sig"))["v"], "hit"
        except Exception: pass
    if not want: return None, "miss"
    if budget < 0.0005: return None, "no-budget"
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
        "dim": len(v), "model": "text-embedding-3-small", "src": "decision_ev", "ts": "2026-10-12"},
        ensure_ascii=False), encoding="utf-8", newline="\n")
    return v, "new"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--suite", required=True)
    ap.add_argument("--max-ledger", type=int, default=200); ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--run", action="store_true"); ap.add_argument("--budget-max", type=float, default=0.0)
    ap.add_argument("--out", default=""); a = ap.parse_args()
    L = SEATP/"ledger"/"frontier_ledger.jsonl"
    lib = []
    for i, l in enumerate(L.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
        if not l.strip(): continue
        try: r = json.loads(l)
        except Exception: continue
        s = str(r.get("subject") or "")
        if s: lib.append(("台账#%d" % i, s))
    if len(lib) > a.max_ledger: lib = lib[-a.max_ledger:]
    sj = json.loads(pathlib.Path(a.suite).read_text(encoding="utf-8-sig"))
    items = sj if isinstance(sj, list) else (sj.get("items") or sj.get("suite") or [])
    print("  ═══ 外部事实源之证据构造（★台账为源）═══")
    print("   库 %d 条 ｜ 基准 %d 项 ｜ top-%d" % (len(lib), len(items), a.topk))
    # 库向量（缓存多半已有）
    libv = []
    miss_lib = 0
    for name, s in lib:
        v, note = vec(s, False, 0.0)
        if v is None: miss_lib += 1; continue
        libv.append((name, s, v))
    print("   ★库向量命中 %d／%d（★缺 %d ⇒ 若须嵌请先跑 ask_hist 以复用其缓存）" % (len(libv), len(lib), miss_lib))
    if len(libv) < 50:
        print("   ⇒ 判：★库向量不足（<50），止（★宁停不做假）"); return 2
    need = [str(it.get("stmt") or it.get("q") or "") for it in items]
    est = sum(len(t) for t in need)/1.7/1000*0.0002
    print("   ★陈述须嵌 %d 条（≈%.6f 元）" % (len(need), est))
    if est > 0 and (not a.run or a.budget_max < est):
        print("   ⇒ 判：★须 --run --budget-max ≥ %.6f（宁停不超）" % est); return 2

    def cos(x, y):
        s = sum(i*j for i, j in zip(x, y)); nx = math.sqrt(sum(i*i for i in x)); ny = math.sqrt(sum(j*j for j in y))
        return s/((nx*ny) or 1e-9)

    out = []
    for it, t in zip(items, need):
        tv, note = vec(t, a.run, a.budget_max)
        if tv is None:
            out.append({"stmt": t, "truth": bool(it.get("truth")), "ev": [], "note": note}); continue
        sc = sorted(((cos(tv, v), n, s) for n, s, v in libv), key=lambda x: -x[0])[:a.topk]
        out.append({"stmt": t, "truth": bool(it.get("truth")),
                    "ev": [{"src": n, "text": s[:150], "cos": round(c, 4)} for c, n, s in sc]})
    d = pathlib.Path(a.out) if a.out else (SEATP/"outbox"/"mem"/"decision_stmt_ev_20261012.json")
    d.write_text(json.dumps({"ts": "2026-10-12", "source": "台账 subject（最近 %d 条）" % len(lib),
        "topk": a.topk, "n": len(out), "items": out}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   ⇒ 已写：%s（%d 项）" % (d.name, len(out)))
    for r in out[:3]:
        e = r["ev"][0] if r["ev"] else {"cos": 0, "src": "-", "text": ""}
        print("     ★真=%-5s ｜ top1 %.3f ｜ %s ｜ 证据：%s" % (str(r["truth"]), e["cos"], r["stmt"][:24], str(e["text"])[:40]))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
