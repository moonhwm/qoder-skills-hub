# -*- coding: utf-8 -*-
"""section_search.py —— 章节级检索（BM25 词法 ＋ 自造重排＝字符二元组 TF-IDF 余弦）
★零 API 调用（不依赖嵌入额度）：中文以「字符二元组」为词元，故无需分词器。
用法：
  python section_search.py --build                 # 建索引（纲要 ＋ 交换区各件之章节）
  python section_search.py --query "<问>" --top 8   # 检索并重排
★纪律：结果为"检索线索"；引用前须过 cite_verify；不同源之节不得混为一谈。
（中文串一律用「」）
"""
import argparse, json, math, pathlib, re, sys
from collections import Counter

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
IDX = SEAT/"exp"/".cache"/"section_index.json"


def toks(s, n=2):
    s = re.sub(r"\s+", "", s)
    out = [s[i:i+n] for i in range(len(s)-n+1)]
    out += re.findall(r"[A-Za-z0-9_\-]{2,}", s)      # 兼收西文词
    return out


def split_sections(name, text, maxlen=700):
    lines = text.splitlines()
    idx, cur = [], []
    for l in lines:
        if re.match(r"^\s{0,6}#{1,6}\s", l) and cur:
            idx.append(cur); cur = [l]
        else:
            cur.append(l)
    if cur: idx.append(cur)
    out = []
    for i, blk in enumerate(idx):
        head = next((x.strip() for x in blk if re.match(r"^\s{0,6}#{1,6}\s", x)), "(无标头)")
        body = " ".join(x.strip() for x in blk)[:maxlen]
        if len(body) < 60: continue
        out.append({"doc": name, "i": i, "head": re.sub(r"^[#\s]+", "", head)[:80], "body": body})
    return out


def build():
    secs = []
    o = SEAT/"archive"/"docs"/"outline"/"v_20261011_1925.md"
    if o.exists(): secs += split_sections("纲要 v_20261011_1925", o.read_text(encoding="utf-8", errors="replace"))
    for p in sorted(EX.glob("*CAIRN-*.otl")):
        t = p.read_text(encoding="utf-8", errors="replace")
        t = re.sub(r"<!-- SIG-BLOCK.*", "", t, flags=re.S)
        secs += split_sections(p.name.split("_")[0], t)
    df = Counter()
    for s in secs:
        s["tf"] = Counter(toks(s["body"] + " " + s["head"]))
        for w in s["tf"]: df[w] += 1
    N = len(secs); avg = sum(sum(s["tf"].values()) for s in secs)/max(1, N)
    data = {"N": N, "avgdl": avg, "df": dict(df), "sections": [{"doc": s["doc"], "i": s["i"], "head": s["head"], "body": s["body"][:400]} for s in secs]}
    IDX.parent.mkdir(parents=True, exist_ok=True)
    IDX.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("  ✓ 索引建成：%d 节（源自 纲要 ＋ 交换区 CAIRN 件）｜%.1f MB" % (N, IDX.stat().st_size/1048576))
    return data


def load():
    if not IDX.exists(): return build()
    return json.loads(IDX.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true")
    ap.add_argument("--query", default=""); ap.add_argument("--top", type=int, default=8)
    a = ap.parse_args()
    if a.build or not IDX.exists():
        d = build()
    else:
        d = load()
    if not a.query:
        print("  （无查询）"); return
    N, avg, df = d["N"], d["avgdl"], d["df"]
    k1, b = 1.5, 0.75
    qt = Counter(toks(a.query))
    sc = []
    for s in d["sections"]:
        tf = Counter(toks(s["body"] + " " + s["head"]))
        dl = sum(tf.values()) or 1
        sc_ = 0.0
        for w, qn in qt.items():
            f = tf.get(w, 0)
            if not f: continue
            idf = math.log(1 + (N - df.get(w, 0) + 0.5)/(df.get(w, 0) + 0.5))
            sc_ += qn * idf * (f*(k1+1))/(f + k1*(1-b + b*dl/avg))
        sc.append((sc_, s))
    sc.sort(key=lambda x: -x[0])
    cand = sc[:max(a.top*4, 24)]
    # 自造重排：与查询之字符二元组余弦（TF-IDF 加权）
    qv = Counter(toks(a.query)); qn = math.sqrt(sum((v*math.log(1+N/(1+df.get(w,0))))**2 for w, v in qv.items())) or 1
    rr = []
    for base, s in cand:
        tf = Counter(toks(s["body"] + " " + s["head"]))
        dot = sum(qv[w]*tf[w]*(math.log(1+N/(1+df.get(w,0)))**2) for w in qv if w in tf)
        sn = math.sqrt(sum((v*math.log(1+N/(1+df.get(w,0))))**2 for w, v in tf.items())) or 1
        rr.append((dot/(qn*sn), base, s))
    rr.sort(key=lambda x: -x[0])
    print("  ═══ 章节级检索（索引 %d 节；BM25 → 余弦重排）═══" % N)
    for i, (cos, base, s) in enumerate(rr[:a.top]):
        print("   %2d. 余弦 %.3f ｜ BM25 %6.2f ｜ %s ｜ %s" % (i+1, cos, base, s["doc"][:34], s["head"][:44]))
    print("   ⇒ 判：★节级命中（非件级）；引用前须过 cite_verify；不同源之节不得混为一谈")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
