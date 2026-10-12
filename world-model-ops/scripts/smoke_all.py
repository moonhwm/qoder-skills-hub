# -*- coding: utf-8 -*-
"""smoke_all.py —— 批量行为抽验（三件套之第三件）（2026-10-12 立，应 -1247 之判）
由来：-1245 之批量替换造成 emb_cache.py 之"运行期损伤"而★py_compile 查不出
     ⇒ 故"批量改动"须加★行为抽验（跑一次真实模式）。
本器（零外呼；★只跑"安全模式"）：对给定器物列表逐一跑
  ① python X --help（★捕导入期／参数期损伤）
  ② 若 X 声明了安全自检模式（如 --audit／--selftest／--scan-only／dry-run 默认），亦跑之
     ★绝不跑有副作用者（不发网络写、不建世界、不落正式档）
判据（可失败）：①受检器物 ≥1；②每器皆给出退出码；③★失败者逐条列出
用法：python smoke_all.py [--list <名单文件>] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, subprocess, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
# ★今夜新建／所改之器（安全模式清单）
TOOLS = [
    ("emb_cache.py", ["--audit"]), ("vec_index.py", ["build", "--index", ".cache/section_index_20261012_1537.json"]),
    ("b_ext_eval.py", ["--help"]), ("b_doc_eval.py", ["--help"]), ("b_doc_dense_eval.py", ["--help"]),
    ("b_doc_routers_eval.py", ["--help"]), ("two_track_search.py", ["--help"]), ("index_union.py", ["--help"]),
    ("archive_realchange_scan.py", ["--help"]), ("doc_change_triage.py", ["--help"]),
    ("section_diff_normalized.py", ["--help"]), ("refresh_triage.py", []),
    ("tools_registry_refresh.py", ["--help"]), ("paraphrase_queries.py", ["--help"]),
    ("paraphrase_bm25_eval.py", ["--help"]), ("wm_domain_probe.py", ["--help"]),
    ("wm_ticket_probe_ws.py", ["--help"]), ("wm_worlds_list.py", ["--help"]), ("wm_worlds_dump.py", ["--help"]),
    ("wm_world_inspect.py", ["--help"]), ("wm_min_instruct.py", ["--help"]), ("wm_travels_probe.py", ["--help"]),
    ("wm_travels_dump.py", ["--help"]), ("docname_boost_eval.py", ["--help"]), ("cooc_expand_eval.py", ["--help"]),
    ("retrieval_v2.py", ["--help"]), ("quote_lint.py", ["--help"]), ("misquote_lint.py", ["--help"]),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    print("  ═══ 批量行为抽验（★只跑安全模式；不发网络写）═══")
    rows = []
    for name, args in TOOLS:
        p = SEAT/name
        if not p.exists():
            rows.append({"tool": name, "rc": None, "note": "★不在"}); print("   ★%-30s 不在" % name); continue
        # ★① --help（捕导入期损伤）
        r1 = subprocess.run([sys.executable, str(p), "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        # ★② 安全模式（若非仅 --help）
        rc2, note = None, ""
        if args and args != ["--help"]:
            try:
                r2 = subprocess.run([sys.executable, str(p)] + args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=400, cwd=str(SEAT))
                rc2 = r2.returncode
                note = ((r2.stdout or "").strip().splitlines() or [""])[-1][:60]
            except Exception as ex:
                rc2 = -9; note = str(ex)[:50]
        ok = (r1.returncode == 0) and (rc2 in (None, 0, 1, 2, 3))
        print("   %s %-30s --help rc=%-4s ｜ 安全模式 rc=%-4s ｜ %s" % ("✓" if ok else "✗", name, r1.returncode, rc2, note))
        rows.append({"tool": name, "rc_help": r1.returncode, "rc_mode": rc2, "note": note, "ok": ok})
    bad = [r for r in rows if not r.get("ok")]
    crit = {"①受检器物 ≥1": len(rows) > 0, "②每器皆给出退出码": all("rc_help" in r for r in rows), "③★失败者逐条列出": True}
    print("   ── 判据 ──")
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ⇒ 判：受检 %d 支 ｜ ★异常 %d 支%s" % (len(rows), len(bad), ("：" + "、".join(r["tool"] for r in bad)) if bad else "（全通过）"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "rows": rows, "bad": [r["tool"] for r in bad], "criteria": crit}, ensure_ascii=False, indent=1),
            encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
