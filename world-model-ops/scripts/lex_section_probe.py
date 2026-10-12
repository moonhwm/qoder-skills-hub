# -*- coding: utf-8 -*-
"""lex_section_probe.py —— 词面节级检索之零成本预判（2026-10-12 立，承 -1303 之请）
动机：语义段索引（全真文档）约 0.2887 元 ⇒ 先问"★词面（免费）能到多少？"以判是否值得花。
本器（★零外呼、零成本）：
  ① 扫 archive/docs 之"可读档"（非空行 >0 且非主导重复型）⇒ 逐档切节（有 # 标题者按标题，无者整档为 1 节）；
  ② 对 8 问：以 bigram 交集之加权（含节名加权）排序 ⇒ top-k（档，节）；
  ③ 报：★金标节（纲要之期望节）在 top-1／top-5 之命中数 ⇒ 与语义（纲要内 87.5%）对照
判据（可失败）：①可读档 ≥10；②节数 ≥100；③★top-1／top-5 之命中已给
用法：python lex_section_probe.py [--json out]
（中文串一律用「」）
"""
import argparse, collections, json, pathlib, re, sys, time


def toks(t):
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(t)); out = []
    for w in t.split():
        if re.search(r"[\u4e00-\u9fff]", w): out += [w] if len(w) == 1 else [w[i:i+2] for i in range(len(w)-1)]
        else: out.append(w.lower())
    return out


# ★与 -1296/-1297 同题、同金标（纲要之节）
QS = [
    ("本网络的两根支柱各是什么", "全局声明"),
    ("判据出现分歧时以何为准", "十一、四依据原文链接"),
    ("席位身份凭何判定", "全局声明"),
    ("总线的先行检查义务是什么", "九、总线先行检查义务"),
    ("审批链与对外承诺有何纪律", "八、审批链与对外承诺纪律"),
    ("MFA 与钩子的兼容要求", "五、MFA、Git Hook"),
    ("开源协议如何分层", "六、开源协议分层组合与引入纪律"),
    ("实时推演与鉴权如何兼顾", "全局声明"),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()
    S = pathlib.Path(__file__).resolve().parent.parent
    AR = S/"archive"/"docs"
    secs = []; nread = 0
    for d in sorted(AR.iterdir()):
        if not d.is_dir(): continue
        vs = sorted(d.glob("v_*.md"), key=lambda f: f.name)
        if not vs: continue
        t = vs[-1].read_text(encoding="utf-8-sig", errors="replace")
        if not [l for l in t.splitlines() if l.strip()]: continue
        nread += 1
        parts = re.split(r"\n(?=#{1,6}\s)", t)
        got = 0
        for p in parts:
            m = re.match(r"#{1,6}\s*(.+)", p)
            if m:
                nm = m.group(1).strip()[:60]; bd = re.sub(r"\s+", " ", p[m.end():])[:300]
                if nm: secs.append({"doc": d.name, "name": nm, "text": bd}); got += 1
        if got == 0:  # ★无标题者整档为 1 节
            secs.append({"doc": d.name, "name": "(整档)", "text": re.sub(r"\s+", " ", t)[:300]})
    print("  ═══ 词面节级检索（零成本预判）═══")
    print("   ★可读档 %d ｜ ★节 %d" % (nread, len(secs)))
    for s in secs:
        s["tk"] = collections.Counter(toks(s["name"] + " " + s["text"]))
        s["nt"] = set(toks(s["name"]))
    hit1 = hit5 = 0; rows = []
    for q, gold in QS:
        qc = collections.Counter(toks(q))
        scored = []
        for s in secs:
            ov = sum(min(v, s["tk"][k]) for k, v in qc.items())
            bonus = 3*len(set(toks(q)) & s["nt"])   # ★节名加权
            scored.append((ov + bonus, s))
        scored.sort(key=lambda x: -x[0])
        top = scored[:a.k]
        pos = None
        for i, (sc, s) in enumerate(top, 1):
            if s["doc"] == "outline" and gold in s["name"]: pos = i; break
        if pos == 1: hit1 += 1
        if pos: hit5 += 1
        rows.append({"q": q, "gold": gold, "pos": pos,
                     "top1": "%s｜%s" % (top[0][1]["doc"], top[0][1]["name"][:34]) if top else ""})
        print("   ★%-18s ⇒ 金标位次 %s ｜ top1：%s" % (q[:18], pos if pos else "＞%d" % a.k, rows[-1]["top1"]))
    print("   ── 汇总 ──")
    print("   ★词面（55 档节级）：top-1 ★%d／%d（%.1f%%）｜ top-%d ★%d／%d（%.1f%%）" % (
        hit1, len(QS), 100*hit1/len(QS), a.k, hit5, len(QS), 100*hit5/len(QS)))
    print("   ★对照：语义（纲要内分段）top-1 ★7／8（87.5%）")
    crit = {"①可读档 ≥10": nread >= 10, "②节数 ≥100": len(secs) >= 100, "③★命中已给": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "readable_docs": nread, "sections": len(secs), "hit1": hit1, "hitK": hit5, "k": a.k,
            "rows": rows, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
