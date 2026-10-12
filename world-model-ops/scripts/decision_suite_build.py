# -*- coding: utf-8 -*-
"""decision_suite_build.py —— 由器物总表自动生成"决策基准"（2026-10-12 立，应 -1361 之请）
由来：-1361 见"16 题之分辨率不足（噪声 ±0.08）⇒ 库大小之效应不可判"⇒ ★须扩基准，且★标签须由器自动判定
     （合本席纪律："分组须由器自动判定"）。
本器（★零外呼）：
  ① 读器物总表（tools_fingerprint_manifest_*.json）之 items[].path ⇒ 取名（去 .py）；
  ② 正例：随机抽 N 件真实器物 ⇒ 陈述「本席有名为 X 的器物」⇒ truth=True；
  ③ 负例：以真实名变形（后缀 _v99／前缀 ghost_／后缀 _probe_x）并★核其不在总表 ⇒ truth=False；
  ④ 输出 2N 题之均衡基准（含每项之来源与判据）
判据（可失败）：①正例皆在总表；②★负例皆不在总表；③均衡（正＝负）
用法：python decision_suite_build.py [--n 24] [--seed 20261012] --out <json>
（中文串一律用「」）
"""
import argparse, json, pathlib, random, sys


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--seed", type=int, default=20261012); ap.add_argument("--out", default="")
    a = ap.parse_args()
    SEAT = pathlib.Path(__file__).resolve().parent; SEATP = SEAT.parent
    cand = sorted((pathlib.Path.home()/"openplanlink-cairn"/"mem").glob("tools_fingerprint_manifest_*.json"))
    if not cand:
        print("   ★未见器物总表"); return 2
    mf = cand[-1]
    j = json.loads(mf.read_text(encoding="utf-8-sig"))
    names = []
    for it in (j.get("items") or []):
        p = str(it.get("path") or "")
        nm = pathlib.Path(p).stem
        if nm: names.append(nm)
    names = sorted(set(names))
    print("  ═══ 由器物总表自动生成决策基准 ═══")
    print("   总表：%s（%d 件）" % (mf.name, len(names)))
    rnd = random.Random(a.seed)
    pos = rnd.sample(names, min(a.n, len(names)))
    neg = []
    guard = 0
    while len(neg) < a.n and guard < a.n * 60:
        guard += 1
        base = rnd.choice(names)
        for pat in ("%s_v99" % base, "ghost_%s" % base, "%s_probe_x" % base, "%s_alpha" % base):
            if pat not in names and pat not in neg and pat not in pos:
                neg.append(pat); break
    items = []
    for x in pos: items.append({"stmt": "本席有名为 %s 的器物" % x, "truth": True, "src": "总表正例"})
    for x in neg: items.append({"stmt": "本席有名为 %s 的器物" % x, "truth": False, "src": "总表负例（变形）"})
    rnd.shuffle(items)
    p = pathlib.Path(a.out) if a.out else (SEATP/"outbox"/"mem"/"decision_suite48_20261012.json")
    p.write_text(json.dumps({"ts": "2026-10-12", "kind": "器物有无之判（★标签由器自动判定）",
        "source": mf.name, "n": len(items), "items": items}, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    npos = sum(1 for r in items if r["truth"]); nneg = len(items)-npos
    print("   ★已写：%s（%d 题：正 %d／负 %d）" % (p.name, len(items), npos, nneg))
    # ★判据（可失败）
    c1 = all(x in names for x in pos)
    c2 = all(x not in names for x in neg)
    c3 = npos == nneg
    for k, v in {"①正例皆在总表": c1, "②★负例皆不在总表": c2, "③均衡": c3}.items():
        print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    for r in items[:4]: print("     ★%-5s ｜ %s" % (str(r["truth"]), r["stmt"]))
    return 0 if (c1 and c2 and c3) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
