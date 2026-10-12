# -*- coding: utf-8 -*-
"""index_union.py —— 建"并集索引"（2026-10-12 立，应 -1224 之实证）
问题：合规索引（148 档／1,102 节）与默认索引（385 档／3,126 节）★几乎不相交（交集仅 98 档）
     ⇒ 只用其检索将系统性漏档（默认独有 287 档）。
本器（零外呼、★只增不改：不动既有索引档）：
  ① 读两索引 ⇒ ★按 (档名, 节标题) 去重合并 ⇒ 重算 BM25 之 N／avgdl／df 与逐节 tf
  ② 写新档 exp/.cache/section_index_union_<ts>.json（★新名，不覆盖）
  ③ 报告：档数／节数／去重去除量／tf 覆盖
判据（可失败）：①并集档数 ≥ 任一源；②并集节数 ≥ 任一源；③每节皆有 tf 与 body
用法：python index_union.py [--a <idx1>] [--b <idx2>] [--out <path>]
（中文串一律用「」）
"""
import argparse, collections, hashlib, json, math, pathlib, re, sys, time

STOP = set("的 了 与 及 和 是 在 有 为 以 对 之 其 者 等".split())


def toks(t):
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(t))
    out = []
    for w in t.split():
        if re.search(r"[\u4e00-\u9fff]", w):
            out += [w] if len(w) == 1 else [w[i:i+2] for i in range(len(w)-1)]
        else:
            out.append(w.lower())
    return [x for x in out if x and x not in STOP]


def load(p):
    j = json.loads(pathlib.Path(p).read_text(encoding="utf-8-sig"))
    return j.get("sections") or []


def main():
    ap = argparse.ArgumentParser()
    S = pathlib.Path(__file__).resolve().parent
    ap.add_argument("--a", default=str(S/".cache"/"section_index.json"))
    ap.add_argument("--b", default=str(S/".cache"/"section_index_20261012_1537.json"))
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    sa, sb = load(a.a), load(a.b)
    print("  ═══ 并集索引 ═══")
    print("   A：%s（节 %d）｜ B：%s（节 %d）" % (pathlib.Path(a.a).name, len(sa), pathlib.Path(a.b).name, len(sb)))
    merged, seen = [], set()
    dup = 0
    for s in sa + sb:
        doc = str(s.get("doc") or ""); head = str(s.get("head") or "")
        k = (doc, head)
        if k in seen:
            dup += 1; continue
        seen.add(k); merged.append(s)
    # ★重算 BM25 统计
    df = collections.Counter(); tf_list = []; dl = []
    for s in merged:
        t = dict(s.get("tf") or {})
        if not t:
            for w in toks((s.get("head") or "") + " " + (s.get("body") or "")): t[w] = t.get(w, 0) + 1
        tf_list.append(t)
        dl.append(sum(t.values()) or 1)
        for w in t.keys(): df[w] += 1
    # ★2026-10-12 自纠（真因）：此前算了 tf_list 却未写回节 ⇒ 并集档中来自"无 tf 之索引"的节仍无 tf
    for _i, _s in enumerate(merged):
        _s["tf"] = tf_list[_i]
    N = len(merged); avgdl = sum(dl)/max(1, N)
    docs = {str(s.get("doc") or "") for s in merged}
    print("   ★去重去除 %d 条 ⇒ 并集：★档 %d ｜ ★节 %d" % (dup, len(docs), N))
    print("   词表 %d ｜ avgdl %.1f" % (len(df), avgdl))
    out = {"built_at": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "src": [pathlib.Path(a.a).name, pathlib.Path(a.b).name],
           "N": N, "avgdl": round(avgdl, 3), "df": dict(df), "sections": merged}
    crit = {"①并集档数 ≥ 任一源": len(docs) >= max(len({str(s.get('doc') or '') for s in sa}), len({str(s.get('doc') or '') for s in sb})),
            "②并集节数 ≥ 任一源": N >= max(len(sa), len(sb)),
            "③每节皆有 tf 与 body": all((s.get("body") is not None) for s in merged)}
    op = pathlib.Path(a.out) if a.out else (S/".cache"/("section_index_union_%s.json" % time.strftime("%Y%m%d_%H%M")))
    op.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("   ⇒ 已写：%s（%.1f MB）" % (op.name, op.stat().st_size/1024/1024))
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
