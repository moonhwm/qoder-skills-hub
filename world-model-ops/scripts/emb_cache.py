# -*- coding: utf-8 -*-
"""emb_cache.py —— 嵌入缓存之"自述"层（2026-10-12 立，应 -1198 之判）
背景：既有缓存（emb_*/e302_*）★仅存向量 `v`，无文本、无来源、命名法不明 ⇒ 不可审计
     （实测：对合规档 1102 节重算 sha1(正文)[:20] ⇒ 命中 0 ⇒ 无法回答"覆盖了哪段语料"）。
本器：① 定义★新格式（★旧档一律不动）：
       {"v": [...], "text_sha1_20": "...", "text_head": "前 80 字", "n_chars": 123,
        "dim": 1536, "model": "text-embedding-3-small", "src": "section:…", "ts": "…"}
     ② 读时★兼容旧格式（仅 v）；③ 写法：get/put；④ --audit 出审计（各前缀之件数、维度、含自述字段者占比、是否可回溯）。
★ 纪律：不改任何既有缓存档（只增新档）；命名仍为 <prefix><sha1_20>.json（prefix 默认 e302s_）。
用法：
    python emb_cache.py --audit [--json out]
（中文串一律用「」）
"""
import argparse, hashlib, json, pathlib, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
CACHE = SEAT/".cache"


def key(text, model=""):
    """★缓存键：sha1(text.encode)[:20]（与既有命名一致；model 仅入档不作键，除非显式需要）"""
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:20]


def path_for(text, prefix="e302s_"):
    return CACHE/(prefix + key(text) + ".json")


def get(text, prefix="e302s_"):
    p = path_for(text, prefix)
    if not p.exists(): return None
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
        v = j.get("v") or j.get("embedding")
        return v if isinstance(v, list) else None
    except Exception:
        return None


def put(text, vec, model="", src="", prefix="e302s_"):
    """★写新格式（自述）；★不动旧档"""
    CACHE.mkdir(parents=True, exist_ok=True)
    t = str(text)
    rec = {"v": vec, "text_sha1_20": key(t), "text_head": t[:80], "n_chars": len(t),
           "dim": len(vec), "model": model, "src": src,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800")}
    p = path_for(t, prefix)
    p.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8", newline="\n")
    return p


SELF_FIELDS = ("text_sha1_20", "text_head", "n_chars", "dim", "model", "src")


def audit(prefixes=("emb_", "e302_", "e302s_")):
    out = []
    print("  ═══ 嵌入缓存审计（自述字段之有无）═══")
    print("   %-10s %-7s %-16s %-8s %s" % ("前缀", "件数", "维度分布", "含自述", "可回溯性"))
    for pre in prefixes:
        fs = sorted(CACHE.glob(pre + "*.json"))
        dims = {}
        selfc = 0
        for f in fs:
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            v = j.get("v") or j.get("embedding") if isinstance(j, dict) else None
            if isinstance(v, list): dims[len(v)] = dims.get(len(v), 0) + 1
            if isinstance(j, dict) and all(k in j for k in ("text_head", "text_sha1_20")): selfc += 1
        back = "★可回溯（有 text_head）" if selfc else "★不可回溯（仅向量）"
        print("   %-10s %-7d %-16s %-8d %s" % (pre, len(fs), str(dims)[:16], selfc, back))
        out.append({"prefix": pre, "files": len(fs), "dims": dims, "self_described": selfc, "traceable": bool(selfc)})
    tot = sum(r["files"] for r in out)
    tr = sum(r["files"] for r in out if r["traceable"])
    print("   ⇒ 汇总：缓存件 %d ｜ ★可回溯 %d（%.1f%%）" % (tot, tr, 100.0*tr/max(1, tot)))
    print("   ★判：自述层（e302s_）为新增；★旧档一律未动（只增不改）")
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--audit", action="store_true"); ap.add_argument("--json", default="")
    a = ap.parse_args()
    if a.audit:
        out = audit()
        if a.json:
            pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "rows": out},
                                                       ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        return 0
    ap.print_help(); return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
