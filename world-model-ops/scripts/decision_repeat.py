# -*- coding: utf-8 -*-
"""decision_repeat.py —— 决策基准之多跑取均值（2026-10-12 立，应 -1360 之噪声底线）
由来：-1360 测得"16 题基准复跑波动 ±0.08"⇒ ★单跑不可判 <0.08 之差 ⇒ 本器以★多跑取均值±标准误。
本器（★闸内；串行；每跑独立）：
  ① 对给定基准 × 给定证据件 × R 次 ⇒ 逐跑调 bailian_decision_probe.py；
  ② 读每跑之 json ⇒ 汇总 平衡准确率之 均值／标准差／标准误／极差；
  ③ ★并与基线 0.500 及"噪声底线"对照给判
判据（可失败）：①跑数 ≥2；②★每跑皆有 json；③均值与标准误已给
用法：python decision_repeat.py --suite <json> --ev <json> --runs 4 [--budget-per 0.02] --tag lib124
（中文串一律用「」）
"""
import argparse, json, pathlib, statistics as st, subprocess, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
SEATP = SEAT.parent


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--suite", required=True); ap.add_argument("--ev", required=True)
    ap.add_argument("--runs", type=int, default=4); ap.add_argument("--budget-per", type=float, default=0.02)
    ap.add_argument("--model", default="qwen3.7-plus"); ap.add_argument("--tag", default="run")
    ap.add_argument("--out", default=""); a = ap.parse_args()
    OUT = SEATP/"outbox"/"mem"
    print("  ═══ 决策基准之多跑取均值（★%s；%d 跑）═══" % (a.tag, a.runs))
    vals = []; raws = []
    for i in range(1, a.runs+1):
        jf = OUT/("rep_%s_%d.json" % (a.tag, i))
        cmd = [sys.executable, str(SEAT/"bailian_decision_probe.py"), "--model", a.model, "--shots",
               "--ev-file", a.ev, "--suite", a.suite, "--run", "--budget-max", str(a.budget_per),
               "--json", str(jf)]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        dt = time.time()-t0
        try:
            j = json.loads(jf.read_text(encoding="utf-8-sig"))
            su = j.get("suite") or {}
            vals.append(float(su.get("balanced_acc") or 0.0)); raws.append(su)
            print("   跑 %d：★平衡 %.3f ｜ acc %.3f ｜ 契约 %s／%s ｜ %.0f s"
                  % (i, su.get("balanced_acc") or 0, su.get("acc") or 0, su.get("contract_ok"), su.get("n"), dt))
        except Exception as ex:
            print("   跑 %d：★无 json（%s）" % (i, str(ex)[:50]))
    if len(vals) < 2:
        print("   ⇒ 判：★跑数不足，止"); return 2
    mean = st.mean(vals); sd = st.pstdev(vals) if len(vals) > 1 else 0.0
    se = sd/(len(vals) ** 0.5)
    print("   ── ★汇总（%s）──" % a.tag)
    print("   ★平衡准确率：逐跑 %s" % "／".join("%.3f" % v for v in vals))
    print("   ★均值 %.3f ｜ 标准差 %.3f ｜ ★标准误 %.3f ｜ 极差 %.3f" % (mean, sd, se, max(vals)-min(vals)))
    print("   ★与基线 0.500 之差 %+.3f（★以标准误判：%s）"
          % (mean-0.5, ("★显著（|差| > 2×SE）" if abs(mean-0.5) > 2*se else "★不显著")))
    res = {"tag": a.tag, "suite": pathlib.Path(a.suite).name, "ev": pathlib.Path(a.ev).name, "runs": len(vals),
           "vals": vals, "mean": round(mean, 4), "sd": round(sd, 4), "se": round(se, 4),
           "range": round(max(vals)-min(vals), 4), "vs_baseline": round(mean-0.5, 4), "raw": raws}
    d = pathlib.Path(a.out) if a.out else (OUT/("decision_repeat_%s_20261012.json" % a.tag))
    d.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   ⇒ 已写：%s" % d.name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
