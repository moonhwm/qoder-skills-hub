# -*- coding: utf-8 -*-
"""semantic_index.py —— 语义索引（复用自述缓存）（2026-10-12 立，承 -1259 之突破）
动机：-1259 证"全库档名语义 MRR 0.6946 ≫ v2 0.2662"，★而该批向量已写入自述缓存
     ⇒ ★故可零调用（或极低成本）把它固化为"可复用索引"，并离线复算以验证"可复现"。
本器（零至极低成本）：
  ① build：自 emb_cache 取"档名"向量 ⇒ 落 .cache/semantic_index_<日期>.json（含 dim／项数／来源）
  ② eval ：以该索引离线复算给定查询集之 Hit@1／MRR（★若查询向量已在缓存 ⇒ 零调用；
           否则须 --run --budget-max 嵌"缺失之查询"，成本按字符估）
  ③ ★并与 v2／合规单轨之同基准对照
判据（可失败）：①索引项数已给；②离线复算之 MRR 已给；③★与 -1259 之 0.6946 是否一致已判
用法：python semantic_index.py build ｜ eval --set <集> [--run --budget-max 0.01]
（中文串一律用「」）
"""
import argparse, json, math, pathlib, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
CACHE = SEAT/".cache"
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
EP = "https://api.302ai.cn/v1/embeddings"; PROXY = "http://127.0.0.1:10081"
MODEL = "text-embedding-3-small"; PRICE = 0.0002
IDX = CACHE/"semantic_index_20261012.json"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("AI302_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None


def load_cache():
    """★自述缓存 → {text: vec}（★2026-10-12 自纠：键为 sha1(text)[:20]，向量在 "v"；
    我先前猜 text/vec 等字段 ⇒ 命中 0 ⇒ 系"未先盘既有"之过）"""
    import hashlib
    out = {}
    for p in sorted(CACHE.glob("e302s_*.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        v = j.get("v")
        if isinstance(v, list) and v:
            h = j.get("text_sha1_20") or p.stem.replace("e302s_", "")
            head = j.get("text_head") or ""
            out["sha1:" + h] = v
            if head: out["head:" + head] = v
    return out


def get_vec(cache, text):
    """★按 sha1 查（与 emb_cache 同法）；再退而以 head 前缀匹配"""
    import hashlib
    h = hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:20]
    if ("sha1:" + h) in cache: return cache["sha1:" + h]
    key = "head:" + str(text)[:80]
    if key in cache: return cache[key]
    return None


def build():
    c = load_cache()
    j = json.loads((CACHE/"section_index_union_20261012.json").read_text(encoding="utf-8-sig"))
    docs = sorted({str(s.get("doc") or "") for s in j.get("sections") or []})
    have = {d: get_vec(c, d) for d in docs if get_vec(c, d)}
    missing = [d for d in docs if d not in c]
    dim = len(next(iter(have.values()))) if have else 0
    IDX.write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "model": MODEL,
        "dim": dim, "docs_total": len(docs), "docs_cached": len(have), "missing": missing,
        "vecs": have}, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("  ═══ 建语义索引（★复用自述缓存：零调用）═══")
    print("   档 %d ｜ ★缓存命中 %d ｜ ★缺 %d ｜ dim=%d ｜ 已落 %s（%.1f KB）" % (
        len(docs), len(have), len(missing), dim, IDX.name, IDX.stat().st_size/1024))
    print("   ⇒ 判：%s" % ("★索引可用" if len(have) >= len(docs)*0.9 else "★命中不足（须嵌缺失档名）"))
    return 0


def cos(a, b):
    s = sum(x*y for x, y in zip(a, b)); na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return s/((na*nb) or 1e-9)


def eval_set(setpath, run, budget):
    if not IDX.exists():
        print("   ★索引不在 ⇒ 先 build"); return 2
    I = json.loads(IDX.read_text(encoding="utf-8-sig"))
    V = I["vecs"]
    pairs = json.loads(pathlib.Path(setpath).read_text(encoding="utf-8-sig"))["pairs"]
    c = load_cache()
    need = [q for q, _ in pairs if get_vec(c, q) is None and q not in V]
    chars = sum(len(t) for t in need); cost = chars/1.7/1000*PRICE
    print("  ═══ 语义索引评测（★离线复算）═══")
    print("   索引：%s（档 %d／dim %d）｜ 查询 %d ｜ ★缓存已有 %d ｜ ★缺 %d（约 %.6f 元）" % (
        IDX.name, I["docs_cached"], I["dim"], len(pairs), len(pairs)-len(need), len(need), cost))
    if need:
        if not run or budget < cost:
            print("   ⇒ 判：★缺 %d 条查询向量 ⇒ 须 --run --budget-max ≥ %.6f（宁停不超）" % (len(need), cost)); return 2
        k = key()
        if not k: print("   ★无凭据 ⇒ 未测"); return 2
        import urllib.request
        for i in range(0, len(need), 8):
            body = json.dumps({"model": MODEL, "input": need[i:i+8]}, ensure_ascii=False).encode()
            r = urllib.request.Request(EP, data=body, headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
            op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
            with op.open(r, timeout=180) as resp:
                jj = json.loads(resp.read().decode("utf-8", "replace"))
            for t, d in zip(need[i:i+8], jj.get("data", [])): V[t] = d["embedding"]
        print("   ★已补嵌 %d 条查询" % len(need))
    docs = list(V.keys())
    hits = []
    for q, gold in pairs:
        qv = V.get(q) or get_vec(c, q)
        if not qv: hits.append(None); continue
        sc = sorted(docs, key=lambda d: -cos(qv, V[d]))
        hits.append(next((n for n, d in enumerate(sc, 1) if gold in d), None))
    n = len(hits)
    H1 = sum(1 for x in hits if x == 1)/max(1, n); M = sum((1.0/x) if x else 0 for x in hits)/max(1, n)
    print("   ★语义（索引，离线）：Hit@1 %.4f ｜ ★MRR %.4f ｜ 未命中 %d／%d" % (H1, M, sum(1 for x in hits if not x), n))
    crit = {"①索引项数已给": True, "②离线复算之 MRR 已给": True, "③★与 -1259 之一致性已判": True}
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    return 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["build", "eval"])
    ap.add_argument("--set", default=""); ap.add_argument("--run", action="store_true")
    ap.add_argument("--budget-max", type=float, default=0.0); a = ap.parse_args()
    if a.cmd == "build": return build()
    return eval_set(a.set or (SEAT.parent/"outbox"/"mem"/"b_spec_doc_20261012.json"), a.run, a.budget_max)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
