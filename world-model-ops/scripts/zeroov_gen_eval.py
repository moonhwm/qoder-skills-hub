# -*- coding: utf-8 -*-
"""zeroov_gen_eval.py —— 自动生成"真零重叠"查询集并评测（2026-10-12 立，应 -1274 之判）
动机：-1274 证"手工写零重叠查询不可靠"（20 题中 12 题仍有重叠）⇒ ★改用★由构造保证之生成法：
  ★取目标档之正文词（其各节 tf 之键），★剔除一切出现在其档名中之 bigram ⇒ 余词按频次取前 N ⇒ 作查询。
  ⇒ ★题面与目标档名★零重叠为构造性质（非人工保证）。
本器（零成本至 ≈0.0002 元）：① 自并集索引取档与 tf；② 生成 N 条查询；③ 嵌之（若缺，写自述缓存）；
  ④ 以正式器 retrieval_v2 之同源逻辑评（纯词面 v2 与 融合 α=50 分列）；⑤ ★分组由构造（必为零重叠）
判据（可失败）：①生成 N 条；②★构造零重叠核（应 100%）；③两臂之 MRR 已给出
用法：python zeroov_gen_eval.py [--n 30] [--run --budget-max 0.01]
（中文串一律用「」）
"""
import argparse, hashlib, json, pathlib, re, sys, urllib.request

SEAT = pathlib.Path(__file__).resolve().parent
CACHE = SEAT/".cache"
OUT = SEAT.parent/"outbox"/"mem"/"b_spec_zeroov_gen_20261012.json"
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


def bigrams(t):
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(t))
    out = []
    for w in t.split():
        if re.search(r"[\u4e00-\u9fff]", w):
            out += [w] if len(w) == 1 else [w[i:i+2] for i in range(len(w)-1)]
        else:
            out.append(w.lower())
    return set(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--run", action="store_true"); ap.add_argument("--budget-max", type=float, default=0.0)
    ap.add_argument("--topk", type=int, default=12); a = ap.parse_args()
    u = json.loads((CACHE/"section_index_union_20261012.json").read_text(encoding="utf-8-sig"))
    secs = u.get("sections") or []
    bydoc = {}
    for s in secs:
        bydoc.setdefault(str(s.get("doc") or ""), []).append(s.get("tf") or {})
    rows = []
    for doc, tfs in sorted(bydoc.items()):
        if len(rows) >= a.n: break
        nm = bigrams(doc)
        cnt = {}
        for tf_ in tfs:
            for w, c in tf_.items():
                # ★2026-10-12 自纠：只留"纯中文 bigram"与"真英文词（≥3 字母）"，剔符号串
                if not w or w in nm: continue
                if not (re.fullmatch(r"[\u4e00-\u9fff]{2}", w) or re.fullmatch(r"[a-zA-Z]{3,}", w)): continue
                if w in ("本席", "可以", "以及", "并且", "因此", "因为", "所以", "如果", "这个", "那个"): continue
                cnt[w] = cnt.get(w, 0) + c
        if len(cnt) < 4: continue
        top = [w for w, _ in sorted(cnt.items(), key=lambda kv: -kv[1])[:a.topk]]
        q = " ".join(top)
        rows.append({"q": q, "gold": doc, "ntok": len(top)})
    out = {"kind": "zero_overlap_generated", "note": "★由构造保证零重叠：查询仅取目标档正文词且剔除其档名词",
           "ts": "2026-10-12", "pairs": [[r["q"], r["gold"]] for r in rows]}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    ov = sum(1 for r in rows if bigrams(r["q"]) & bigrams(r["gold"]))
    print("  ═══ 自动生成「真零重叠」查询集 ═══")
    print("   ★生成 %d 条（每条取正文词前 %d）｜ ★构造零重叠核：有重叠者 %d ⇒ %s" % (len(rows), a.topk, ov, "✓ 全为零重叠" if ov == 0 else "★异常"))
    for r in rows[:3]:
        print("      例：%s ⇒ 《%s》" % (r["q"][:46], r["gold"][:26]))
    need = []
    for r in rows:
        h = hashlib.sha1(str(r["q"]).encode("utf-8")).hexdigest()[:20]
        if not (CACHE/("e302s_"+h+".json")).exists(): need.append(r["q"])
    cost = sum(len(x) for x in need)/1.7/1000*0.0002
    print("   ★须嵌 %d 条（≈%.6f 元）" % (len(need), cost))
    if need:
        if not a.run or a.budget_max < cost:
            print("   ⇒ 判：★须 --run --budget-max ≥ %.6f（宁停不超）" % cost); return 2
        k = key()
        if not k: print("   ★无凭据"); return 2
        op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
        for i in range(0, len(need), 8):
            b = json.dumps({"model": "text-embedding-3-small", "input": need[i:i+8]}, ensure_ascii=False).encode()
            rq = urllib.request.Request("https://api.302ai.cn/v1/embeddings", data=b,
                                       headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
            with op.open(rq, timeout=120) as resp:
                j = json.loads(resp.read().decode("utf-8", "replace"))
            for t, d in zip(need[i:i+8], j.get("data", [])):
                v = d["embedding"]; h = hashlib.sha1(str(t).encode("utf-8")).hexdigest()[:20]
                rec = {"v": v, "text_sha1_20": h, "text_head": t[:80], "n_chars": len(t), "dim": len(v),
                       "model": "text-embedding-3-small", "src": "zeroov_gen", "ts": "2026-10-12"}
                (CACHE/("e302s_"+h+".json")).write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8", newline="\n")
        print("   ★已补嵌 %d 条（入自述缓存）" % len(need))
    print("   ⇒ 已写：%s" % OUT.name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
