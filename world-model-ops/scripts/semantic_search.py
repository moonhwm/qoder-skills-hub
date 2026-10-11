# -*- coding: utf-8 -*-
"""semantic_search.py —— 本席档案之语义检索（向量编码 ＋ 余弦重排）
索引：exp/.cache/embf_*.json（全文嵌入，键名＝文本 sha1 前 20）
用法：python semantic_search.py --query "……" [--top 8] [--build]
（中文串一律用「」）
"""
import argparse, hashlib, json, math, pathlib, re, sys, urllib.request

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
CACHE = SEAT/"exp"/".cache"
INDEX = SEAT/"exp"/".cache"/"search_index.json"


def body(p, lim=1200):
    t = p.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<!-- SIG-BLOCK.*", "", t, flags=re.S)
    t = re.sub(r"[#|>*`\-]{1,}", " ", t)
    return re.sub(r"\s+", " ", t)[:lim]


def embed_one(text, key):
    env = {}
    for line in (HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env").read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("="); env[k.strip()] = v.strip().strip('"').strip("'")
    K = env.get("DASHSCOPE_API_KEY", "")
    r = urllib.request.Request("https://ws-ay6o8osb22o9dc3t.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/embeddings",
                               data=json.dumps({"model": "text-embedding-v4", "input": [text]}, ensure_ascii=False).encode(), method="POST")
    r.add_header("Authorization", "Bearer " + K); r.add_header("Content-Type", "application/json")
    for att in range(1, 4):                      # ★戒三十四：网络带重试
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))["data"][0]["embedding"]
        except urllib.error.HTTPError as e:       # ★戒三十六：4xx 不重试
            msg = e.read().decode("utf-8", "replace")[:200].replace("\n", " ")
            if 400 <= e.code < 500:
                if "Free quota exhausted" in msg:
                    print("   ⚠ 嵌入不可用：★免费额度已用尽。")
                    print("     服务端原话：" + msg)
                    print("     解除：①充值；②或在百炼控制台关闭「仅用免费额度(use free tier only)」模式。")
                else:
                    print("   ⚠ 嵌入请求被拒（HTTP %d）：%s" % (e.code, msg))
                print("   ⇒ 索引与逐件比对仍可本地完成（零调用）；仅「新查询之向量」需额度。")
                return None
            if att == 3:
                print("   ⚠ 服务端错误（已重试 3 次）：HTTP %d" % e.code); return None
        except Exception as e:
            if att == 3:
                print("   ⚠ 网络异常（已重试 3 次）：%s" % str(e)[:80]); return None
    return None


def build():
    idx = []
    for p in sorted(EX.glob("*CAIRN-*.otl")):
        b = body(p)
        if len(b) < 80: continue
        h = hashlib.sha1(b.encode()).hexdigest()[:20]
        f = CACHE/("embf_" + h + ".json")
        if not f.exists(): continue              # 只收已有向量者（★零新调用）
        idx.append({"name": p.name, "title": p.name.split("_")[0], "key": h,
                    "v": json.loads(f.read_text(encoding="utf-8"))["v"]})
    INDEX.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8", newline="\n")
    return idx


def cos(a, b):
    s = sum(x*y for x, y in zip(a, b))
    return s/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(x*x for x in b)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--query", required=True)
    ap.add_argument("--top", type=int, default=8); ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    idx = json.loads(INDEX.read_text(encoding="utf-8")) if (INDEX.exists() and not a.build) else build()
    print("  ═══ 语义检索（索引 %d 件）═══" % len(idx))
    qv = embed_one(a.query, "q")
    if qv is None:
        print("   ⇒ 已中止：无查询向量（额度不足）。索引仍完好（%d 件），待额度恢复即可用。" % len(idx))
        return
    sc = sorted(((cos(qv, it["v"]), it) for it in idx), key=lambda x: -x[0])
    for i, (s, it) in enumerate(sc[:a.top]):
        print("   %2d. %.4f ｜ %s" % (i+1, s, it["name"][:64]))
    print("   ⇒ 判：首名 %.4f（余弦；★绝对分受嵌入几何影响，仅序可采 —— 戒三十五）" % sc[0][0])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
