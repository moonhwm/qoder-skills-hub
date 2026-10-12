# -*- coding: utf-8 -*-
"""ask_seat.py —— 本席"自助"检索入口（2026-10-12 立；应 objective 之"自助《纲要》"）
承：-1293（以纲要 35 节为本体：语义 0.6504 vs 词面 0.2889，+125%）⇒ 今做成可用入口。
本器（零至 ≈0.00002 元／问；★闸内）：
  ① 取问题之向量（★若已在自述缓存 ⇒ 零调用；否则嵌之，入自述缓存）
  ② 于两库检索：★纲要 35 节（节名＋正文前 120 字）｜★并集 435 档之档名
  ③ 输出 top-k（分列两库），并标余弦；★并给"词面参照"（bigram 交集）以便对照
判据（可失败）：①两库皆非空；②top-k 已给；③★是否落缓存已标
用法：python ask_seat.py --q "问题" [--k 5] [--run --budget-max 0.001]
（中文串一律用「」）
"""
import argparse, hashlib, json, math, pathlib, re, sys, urllib.request

SEAT = pathlib.Path(__file__).resolve().parent
CACHE = SEAT/".cache"
ARCH_DEF = SEAT.parent/"archive"/"docs"/"outline"
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


def toks(t):
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(t)); out = []
    for w in t.split():
        if re.search(r"[\u4e00-\u9fff]", w): out += [w] if len(w) == 1 else [w[i:i+2] for i in range(len(w)-1)]
        else: out.append(w.lower())
    return set(out)


def vec_of(text, run, budget):
    h = hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:20]
    p = CACHE/("e302s_"+h+".json")
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8-sig"))["v"], "缓存命中（零调用）"
        except Exception: pass
    if not run:
        return None, "★缺向量（须 --run）"
    est = len(text)/1.7/1000*0.0002
    if budget < est: return None, "★预算不足（须 ≥%.6f）" % est
    k = key()
    if not k: return None, "★无凭据"
    b = json.dumps({"model": "text-embedding-3-small", "input": [text]}, ensure_ascii=False).encode()
    rq = urllib.request.Request("https://api.302ai.cn/v1/embeddings", data=b,
                                headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(rq, timeout=120) as resp:
        j = json.loads(resp.read().decode("utf-8", "replace"))
    v = j["data"][0]["embedding"]
    rec = {"v": v, "text_sha1_20": h, "text_head": str(text)[:80], "n_chars": len(str(text)), "dim": len(v),
           "model": "text-embedding-3-small", "src": "ask_seat", "ts": "2026-10-12"}
    p.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8", newline="\n")
    return v, "★已嵌并落缓存"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--q", required=True); ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--run", action="store_true"); ap.add_argument("--budget-max", type=float, default=0.0)
    ap.add_argument("--json", default=""); ap.add_argument("--full", action="store_true")   # ★扩检索面：整节正文
    ap.add_argument("--segment", action="store_true")  # ★分段检索（段级命中回溯到节）
    ap.add_argument("--seg-len", type=int, default=250)
    ap.add_argument("--seg-stride", type=int, default=200)
    ap.add_argument("--doc", default="")   # ★2026-10-12 加：指定档（默认 outline）
    a = ap.parse_args()
    def cos(x, y):
        s = sum(i*j for i, j in zip(x, y)); nx = math.sqrt(sum(i*i for i in x)); ny = math.sqrt(sum(j*j for j in y))
        return s/((nx*ny) or 1e-9)
    # ★库一：纲要 35 节
    ARCH = (SEAT.parent/"archive"/"docs"/a.doc) if a.doc else ARCH_DEF
    if not ARCH.exists():
        print("   ★档不在：%s" % ARCH.name); return 2
    vs = sorted(ARCH.glob("v_*.md"), key=lambda f: f.name)
    secs = []; secs_raw = []
    if vs:
        txt = vs[-1].read_text(encoding="utf-8-sig", errors="replace")
        for p in re.split(r"\n(?=#{1,6}\s)", txt):
            m = re.match(r"#{1,6}\s*(.+)", p)
            if m:
                nm = m.group(1).strip()[:60]
                _lim = 800 if a.full else 120
                bd = re.sub(r"\s+", " ", p[m.end():])[:_lim]
                if nm:
                    secs.append((nm, nm + " " + bd))
                    secs_raw.append((nm, re.sub(r"\s+", " ", p[m.end():])))
    # ★库二：并集 435 档之档名
    docs = []
    IX = CACHE/"semantic_index_20261012.json"
    if IX.exists():
        docs = list(json.loads(IX.read_text(encoding="utf-8-sig"))["vecs"].items())
    qv, note = vec_of(a.q, a.run, a.budget_max)
    print("  ═══ 本席自助检索 ═══")
    print("   问题：%s" % a.q[:70])
    print("   库：纲要节 ★%d ｜ 并集档 ★%d ｜ 题向量：%s" % (len(secs), len(docs), note))
    if qv is None:
        print("   ⇒ 判：★未检索（%s）" % note); return 2
    qt = toks(a.q)
    # ★2026-10-12 自纠：节向量须"按需批量嵌"（此前只逐条查缓存 ⇒ 35 节全缺 ⇒ 该列为空）
    miss = [tx for _nm, tx in secs if vec_of(tx, False, 0.0)[0] is None]
    if miss and a.run:
        _est = sum(len(x) for x in miss)/1.7/1000*0.0002
        if a.budget_max >= _est:
            import urllib.request as _ur
            _k = key()
            if _k:
                _op = _ur.build_opener(_ur.ProxyHandler({"http": PROXY, "https": PROXY}))
                for _i in range(0, len(miss), 8):
                    _b = json.dumps({"model": "text-embedding-3-small", "input": miss[_i:_i+8]}, ensure_ascii=False).encode()
                    _rq = _ur.Request("https://api.302ai.cn/v1/embeddings", data=_b,
                                      headers={"Authorization": "Bearer " + _k, "Content-Type": "application/json"})
                    with _op.open(_rq, timeout=120) as _resp:
                        _j = json.loads(_resp.read().decode("utf-8", "replace"))
                    for _t2, _d2 in zip(miss[_i:_i+8], _j.get("data", [])):
                        _v2 = _d2["embedding"]; _h2 = hashlib.sha1(str(_t2).encode("utf-8")).hexdigest()[:20]
                        (CACHE/("e302s_"+_h2+".json")).write_text(json.dumps(
                            {"v": _v2, "text_sha1_20": _h2, "text_head": str(_t2)[:80], "n_chars": len(str(_t2)),
                             "dim": len(_v2), "model": "text-embedding-3-small", "src": "ask_seat_sec", "ts": "2026-10-12"},
                            ensure_ascii=False), encoding="utf-8", newline="\n")
                print("   ★节向量已批量嵌 %d 条（≈%.6f 元；此后零调用）" % (len(miss), _est))
            else:
                print("   ★无凭据 ⇒ 节向量未嵌")
        else:
            print("   ★节向量缺 %d 条 ⇒ 须 --budget-max ≥ %.6f" % (len(miss), _est))
    if a.segment:
        # ★2026-10-12 加：分段检索 —— 节内切段（默认 250 字、步长 200）⇒ 段级余弦 ⇒ 每节取其最佳段
        segs = []
        for nm, body in secs_raw:
            b = re.sub(r"\s+", " ", body)
            if not b: continue
            k2 = 0
            while k2 < len(b):
                chunk = (nm + " " + b[k2:k2+a.seg_len]).strip()
                if len(chunk) > 12: segs.append((nm, chunk))
                if k2 + a.seg_len >= len(b): break
                k2 += a.seg_stride
        miss = [tx for _nm, tx in segs if vec_of(tx, False, 0.0)[0] is None]
        if miss and a.run:
            _est = sum(len(x) for x in miss)/1.7/1000*0.0002
            if a.budget_max >= _est:
                import urllib.request as _ur
                _k = key()
                if _k:
                    _op = _ur.build_opener(_ur.ProxyHandler({"http": PROXY, "https": PROXY}))
                    for _i in range(0, len(miss), 8):
                        _b = json.dumps({"model": "text-embedding-3-small", "input": miss[_i:_i+8]}, ensure_ascii=False).encode()
                        _rq = _ur.Request("https://api.302ai.cn/v1/embeddings", data=_b,
                                          headers={"Authorization": "Bearer " + _k, "Content-Type": "application/json"})
                        with _op.open(_rq, timeout=180) as _resp:
                            _j = json.loads(_resp.read().decode("utf-8", "replace"))
                        for _t2, _d2 in zip(miss[_i:_i+8], _j.get("data", [])):
                            _v2 = _d2["embedding"]; _h2 = hashlib.sha1(str(_t2).encode("utf-8")).hexdigest()[:20]
                            (CACHE/("e302s_"+_h2+".json")).write_text(json.dumps(
                                {"v": _v2, "text_sha1_20": _h2, "text_head": str(_t2)[:80], "n_chars": len(str(_t2)),
                                 "dim": len(_v2), "model": "text-embedding-3-small", "src": "ask_seat_seg", "ts": "2026-10-12"},
                                ensure_ascii=False), encoding="utf-8", newline="\n")
                    print("   ★段向量已批量嵌 %d 条（≈%.6f 元；此后零调用）" % (len(miss), _est))
        best = {}
        for nm, tx in segs:
            v = vec_of(tx, False, 0.0)[0]
            if v is None: continue
            c = cos(qv, v)
            if nm not in best or c > best[nm][0]: best[nm] = (c, tx[:60])
        srows = sorted(best.items(), key=lambda kv: -kv[1][0])
        print("   ── ★分段检索 top-%d（该节之最佳段余弦）──" % a.k)
        for nm, (c, seg) in srows[:a.k]:
            print("      %-36s ｜ ★%.4f ｜ 段首：%s" % (nm[:36], c, seg[:34]))
        print("   ★段总数 %d ｜ 覆盖节 %d" % (len(segs), len(best)))

    rows = []
    for nm, txt in secs:
        v = vec_of(txt, False, 0.0)[0]
        rows.append((nm, cos(qv, v) if v else None, len(qt & toks(nm))))
    rows = [r for r in rows if r[1] is not None]
    rows.sort(key=lambda r: -r[1])
    print("   ── ★纲要节 top-%d（语义余弦 ｜ 词面 bigram 交集）──" % a.k)
    for nm, c, ov in rows[:a.k]:
        print("      %-42s ｜ ★%.4f ｜ 词面 %d" % (nm[:42], c, ov))
    d2 = [(d, cos(qv, v) if v else None) for d, v in docs]
    d2 = [x for x in d2 if x[1] is not None]
    d2.sort(key=lambda x: -x[1])
    print("   ── ★并集档 top-%d（语义余弦）──" % a.k)
    for d, c in d2[:a.k]: print("      %-42s ｜ ★%.4f" % (d[:42], c))
    crit = {"①两库皆非空": bool(secs) and bool(docs), "②top-k 已给": True, "③★是否落缓存已标": True}
    for k2, v2 in crit.items(): print("   %s ⇒ %s" % (k2, "✓" if v2 else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": "2026-10-12", "q": a.q, "vec_note": note,
            "sections": [{"name": n, "cos": round(c, 4), "lex": o} for n, c, o in rows[:a.k]],
            "docs": [{"doc": d, "cos": round(c, 4)} for d, c in d2[:a.k]], "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    import time
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
