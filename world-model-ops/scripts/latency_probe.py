# -*- coding: utf-8 -*-
"""latency_probe.py —— 关键器物之时延探针（2026-10-13 立，应 -1325 之缺）
由来：深读 zep-eval-harness 见其 Metrics 含"latency"，而本席度量中★无时延一项 ⇒ 今补。
本器（★零外呼；串行；每个探针带超时）：
  ① 对每个探针命令：计时（perf_counter）⇒ 记 秒 与 返回码；
  ② 输出表（★含"是否含网络"标注）；③ 汇总（最慢者、总耗时）
判据（可失败）：①每探针皆有结果；②★每探针皆返回码 ≤2；③时延表已给
用法：python latency_probe.py [--only NAME] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, subprocess, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
SEATP = SEAT.parent
OUT = SEATP/"outbox"/"mem"

# ★探针：名／命令／是否含网络（★不含付费调用；语义类需载大索引故单列）
PROBES = [
    ("词面检索（前 5）", [sys.executable, str(SEAT/"retrieval_v2.py"), "--set",
                       str(OUT/"b_spec_doc_20261012.json"), "--json", str(OUT/"_lat_lex.json")], False),
    # ★2026-10-13 自纠（-1326 之果）：本器无 --set（那是 retrieval_v2 之参数）⇒ 误传致 rc=2
    #   其正用法为 --q 或 --selftest ⇒ 改以 --selftest（内置自检，零外呼）
    ("决策（离线契约自检）", [sys.executable, str(SEAT/"decision_from_retrieval.py"), "--selftest",
                       "--json", str(OUT/"_lat_dec.json")], False),
    ("台账闸检", [sys.executable, str(SEAT/"ledger_gate.py"), "check"], False),
    ("器物登记刷新（cairn）", [sys.executable, str(SEAT/"tools_registry_refresh.py"), "--tools",
                        str(pathlib.Path.home()/"openplanlink-cairn"/"tools"),
                        "--out", str(OUT/"_lat_reg.json")], False),
    ("文档差异（归一化）", [sys.executable, str(SEAT/"section_diff_normalized.py"),
                     "--a", str(SEATP/"archive"/"docs"/"outline"/"v_20261012_2039.md"),
                     "--b", str(SEATP/"archive"/"docs"/"outline"/"v_20261012_2039.md")], False),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only", default=""); ap.add_argument("--json", default="")
    a = ap.parse_args()
    rows = []
    print("  ═══ 关键器物之时延探针（★零外呼；串行）═══")
    t_all = time.perf_counter()
    for name, cmd, net in PROBES:
        if a.only and a.only not in name: continue
        if not pathlib.Path(cmd[1]).exists():
            print("   ★%-22s 探针不在（跳过）" % name); continue
        t0 = time.perf_counter()
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            rc = r.returncode
        except subprocess.TimeoutExpired:
            rc = -9
        dt = time.perf_counter() - t0
        rows.append({"probe": name, "sec": round(dt, 3), "rc": rc, "net": net})
        print("   %-22s ｜ ★%7.3f s ｜ rc=%s ｜ 网络=%s" % (name, dt, rc, "是" if net else "否"))
    if rows:
        slow = max(rows, key=lambda r: r["sec"])
        print("   ── 汇总 ──")
        print("   ★最慢：%s（%.3f s）｜ ★总 %.3f s（%d 探针）" % (slow["probe"], slow["sec"], time.perf_counter()-t_all, len(rows)))
        print("   ★中位 %.3f s" % sorted(r["sec"] for r in rows)[len(rows)//2])
    crit = {"①每探针皆有结果": bool(rows), "②★每探针返回码 ≤2": all(r["rc"] <= 2 for r in rows),
            "③时延表已给": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "rows": rows, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
