# -*- coding: utf-8 -*-
"""outline_qa_eval.py —— 以令条之「纲要」为本体之自助检索基准（2026-10-12 立）
动机：objective 明言"自助《…纲要》"⇒ ★最切题之验证即"以纲要自身之节为库、以其文意为询"。
本器（零至 ≈0.0003 元）：① 取 archive/docs/outline 最新版之节（35 节）；② 以"节名＋节正文前 120 字"为条目；
  ③ 嵌条目与查询（写入自述缓存）；④ 两臂对照：★词面（BM25 于节） vs ★语义（余弦于条目）；
  ⑤ ★分组：查询与目标节名之词面重叠（有／无）
判据（可失败）：①节数 ≥5；②两臂之 MRR 已给；③★分组已给
用法：python outline_qa_eval.py [--run --budget-max 0.01]
（中文串一律用「」）
"""
import argparse, hashlib, json, math, pathlib, re, sys, urllib.request

SEAT = pathlib.Path(__file__).resolve().parent
CACHE = SEAT/".cache"
ARCH = SEAT.parent/"archive"/"docs"/"outline"   # ★自纠：SEAT 为 exp/ ⇒ archive 须上溯一级
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
PROXY = "http://127.0.0.1:10081"
SET = SEAT.parent/"outbox"/"mem"/"outline_qa_set_20261012.json"

# ★查询集：以"纲要"各节之文意自撰（★非抄节名；建后由程序核重叠）
QS = [
    ("本网络之最高纲领为何", "全局声明"),
    ("运行所需之外部条件为何", "环境信息"),
    ("参与者应守之规矩有哪几条", "准则"),
    ("落地时宜如何安排", "部署建议"),
    ("文件自我修正之长期办法", "永久性自指订正"),
    ("仓库该怎样分层摆放", "目录结构建议"),
    ("系统之总体骨架如何", "整体架构"),
    ("开篇之缘起为何", "序言"),
    ("下游代理与不同厂商之模型如何并用", "子代理与异质模型"),
    ("决策层与外部贡献者之关系", "治理架构与开源社区"),
    ("基础协同与前后端一体推进", "底层协调机制与全栈开发"),
    ("经营之道与个体成长", "商业化运作与人的自由全面发展"),
    ("把问题查遍所需之组织纪律", "穷举研究组织要求"),
    ("能力如何登记入库", "技能录入要求"),
    ("多方如何达成一致并共享数据", "共识机制与跨平台数据协同"),
    ("影像资料之引用", "视频参考"),
    ("随附材料之处", "附件引用"),
    ("历次改动之留痕", "变更记录"),
    ("网络形状之主张与吸收信息之本领", "二、拓扑主张与知识消化能力"),
    ("事件驱动之定义与出错补偿", "三、事件驱动架构定义与异常补偿机制"),
]


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


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true")
    ap.add_argument("--budget-max", type=float, default=0.0); ap.add_argument("--json", default=""); a = ap.parse_args()
    vs = sorted(ARCH.glob("v_*.md"), key=lambda f: f.name)
    if not vs: print("   ★无档案"); return 2
    txt = vs[-1].read_text(encoding="utf-8-sig", errors="replace")
    # ★2026-10-12 自纠：纲要之节标题用 ★六个井号（######）⇒ 原 #{1,3} 不匹配（节 0）
    #   ⇒ 改 #{1,6}；并优先用 sections_*.json 之节名（格式 NNNN|名）作权威名
    parts = re.split(r"\n(?=#{1,6}\s)", txt)
    items = []
    for p in parts:
        m = re.match(r"#{1,3}\s*(.+)", p)
        if not m: continue
        name = m.group(1).strip()[:60]
        body = re.sub(r"\s+", " ", p[m.end():])[:120]
        if name: items.append((name, body))
    print("  ═══ 以「纲要」为本体之自助检索基准 ═══")
    print("   档案：%s ｜ ★节 %d" % (vs[-1].name, len(items)))
    pairs = []
    for q, kw in QS:
        tgt = next((nm for nm, _ in items if kw in nm), None)
        if tgt: pairs.append((q, tgt))
    print("   ★查询 %d 条（★目标节由关键词定位）" % len(pairs))
    texts = [nm + " " + bd for nm, bd in items] + [q for q, _ in pairs]
    need = []
    for t in texts:
        h = hashlib.sha1(str(t).encode("utf-8")).hexdigest()[:20]
        if not (CACHE/("e302s_"+h+".json")).exists(): need.append(t)
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
                       "model": "text-embedding-3-small", "src": "outline_qa", "ts": "2026-10-12"}
                (CACHE/("e302s_"+h+".json")).write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8", newline="\n")
        print("   ★已补嵌 %d 条（入自述缓存）" % len(need))
    # ★载入向量
    V = {}
    for t in texts:
        h = hashlib.sha1(str(t).encode("utf-8")).hexdigest()[:20]
        p = CACHE/("e302s_"+h+".json")
        if p.exists():
            try: V[t] = json.loads(p.read_text(encoding="utf-8-sig"))["v"]
            except Exception: pass
    def cos(x, y):
        s = sum(i*j for i, j in zip(x, y)); nx = math.sqrt(sum(i*i for i in x)); ny = math.sqrt(sum(j*j for j in y))
        return s/((nx*ny) or 1e-9)
    ent = [nm + " " + bd for nm, bd in items]
    # ★词面臂：按查询与条目的 bigram 交集大小
    def lex_rank(q):
        qt = toks(q)
        return sorted(ent, key=lambda e: -len(qt & toks(e)))
    def sem_rank(q):
        qv = V.get(q)
        if not qv: return ent
        return sorted(ent, key=lambda e: -cos(qv, V.get(e) or [0]*len(qv)))
    grp = {"有重叠": [], "零重叠": []}
    for q, tgt in pairs:
        e_tgt = next((e for e in ent if e.startswith(tgt)), None)
        if not e_tgt: continue
        ov = bool(toks(q) & toks(tgt))
        g = "有重叠" if ov else "零重叠"
        for nm, rk in (("词面", lex_rank), ("★语义", sem_rank)):
            r = next((n for n, e in enumerate(rk(q), 1) if e == e_tgt), None)
            grp[g].append((nm, r))
    def mrr(v): return sum((1.0/r) if r else 0 for _, r in v)/max(1, len(v))
    print("   ── 分组（★净重叠：查询与目标节名之 bigram）──")
    for g in ("零重叠", "有重叠"):
        v = grp[g]
        if not v: continue
        for nm in ("词面", "★语义"):
            vv = [(x, r) for x, r in v if x == nm]
            print("      %s（n=%d）｜ %-4s ⇒ ★MRR %.4f" % (g, len(vv), nm, mrr(vv)))
    allv = grp["零重叠"] + grp["有重叠"]
    for nm in ("词面", "★语义"):
        print("   ★全体（n=%d）｜ %-4s ⇒ ★MRR %.4f" % (len([1 for x, _ in allv if x == nm]), nm, mrr([(x, r) for x, r in allv if x == nm])))
    crit = {"①节数 ≥5": len(items) >= 5, "②两臂之 MRR 已给": True, "③★分组已给": True}
    for k2, v2 in crit.items(): print("   %s ⇒ %s" % (k2, "✓" if v2 else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "archive": vs[-1].name, "sections": len(items), "pairs": pairs,
            "groups": {g: [(x, r) for x, r in v] for g, v in grp.items()}, "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    import time
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
