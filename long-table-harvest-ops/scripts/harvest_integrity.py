#!/usr/bin/env python3
"""harvest_integrity.py — 长表逐字收割完整性三合一机检.

子命令:
  continuity  序号连续性/断号/重号检查
  overlap     两段件重叠带逐字 diff(拼接前闸)
  scan        伪造签名机检(S1 机械序号 / S2 周期重复 / S3 零有机变异代理指标)

退出码: 0 = PASS, 1 = FAIL/发现嫌疑, 2 = 用法或文件错误。
仅机械检查, 不能替代重抓源比对(SKILL.md §3.6)。
"""
import argparse
import os
import re
import sys


def parse_rows(path, col):
    """解析 markdown 表, 返回 [(lineno, serial, cells, raw)]; serial 非整数的行(表头等)跳过."""
    if not os.path.isfile(path):
        print(f"ERROR: 文件不存在: {path}", file=sys.stderr)
        sys.exit(2)
    rows = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            raw = line.rstrip("\n")
            s = raw.strip()
            if not (s.startswith("|") and s.endswith("|")):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if col - 1 >= len(cells):
                continue
            if re.fullmatch(r"\d+", cells[col - 1]):
                rows.append((lineno, int(cells[col - 1]), cells, raw))
    return rows


def cmd_continuity(a):
    rows = parse_rows(a.file, a.col)
    if not rows:
        print("FAIL: 未解析到任何数据行", file=sys.stderr)
        return 1
    serials = [r[1] for r in rows]
    seen, dups = set(), []
    breaks = []
    prev = None
    for lineno, sr, _, _ in rows:
        if sr in seen:
            dups.append((lineno, sr))
        seen.add(sr)
        if prev is not None and sr != prev + 1:
            breaks.append((lineno, prev, sr))
        prev = sr
    print(f"行数={len(rows)} 首={serials[0]} 末={serials[-1]}")
    ok = not dups and not breaks
    if dups:
        print(f"重号×{len(dups)}: {dups[:10]}")
    if breaks:
        print(f"断号×{len(breaks)}: {breaks[:10]}")
    print("PASS: 连续无断无重" if ok else "FAIL: 存在断号/重号")
    return 0 if ok else 1


def cmd_overlap(a):
    lo, hi = a.band
    ra = {sr: raw for _, sr, _, raw in parse_rows(a.file_a, a.col) if lo <= sr <= hi}
    rb = {sr: raw for _, sr, _, raw in parse_rows(a.file_b, a.col) if lo <= sr <= hi}
    missing_a = sorted(set(rb) - set(ra))
    missing_b = sorted(set(ra) - set(rb))
    diffs = [(s, ra[s], rb[s]) for s in sorted(set(ra) & set(rb)) if ra[s] != rb[s]]
    ok = not missing_a and not missing_b and not diffs
    print(f"重叠带 {lo}-{hi}: A {len(ra)} 行, B {len(rb)} 行")
    if missing_a:
        print(f"A 缺: {missing_a[:10]}")
    if missing_b:
        print(f"B 缺: {missing_b[:10]}")
    for s, xa, xb in diffs[:10]:
        print(f"DIFF 序号{s}:\n  A: {xa}\n  B: {xb}")
    print("OVERLAP_IDENTICAL" if ok else "OVERLAP_DIFF — 禁止拼接, 上报处置")
    return 0 if ok else 1


def _code_name(cell):
    m = re.match(r"(\d+)(.*)", cell)
    return (int(m.group(1)), m.group(2)) if m else (None, cell)


def cmd_scan(a):
    rows = parse_rows(a.file, a.col)
    if not rows:
        print("FAIL: 未解析到任何数据行", file=sys.stderr)
        return 1
    findings = []
    ui = a.unit_col - 1
    # S1: 同名单位 +1 连续代码长链(块内同码多行先合并, 跨块看 +1)
    codes = []  # (code, name, first_lineno)
    for lineno, sr, cells, _ in rows:
        if cells is None or ui >= len(cells):
            continue
        code, name = _code_name(cells[ui])
        if code is None:
            continue
        if codes and codes[-1][0] == code and codes[-1][1] == name:
            continue
        codes.append((code, name, lineno))
    run_start = 0
    for k in range(1, len(codes) + 1):
        cont = k < len(codes) and codes[k][1] == codes[k - 1][1] and codes[k][0] == codes[k - 1][0] + 1
        if not cont:
            length = k - run_start
            if length >= a.s1_min:
                nm = codes[run_start][1]
                findings.append(("S1", f"机械序号链: 单位「{nm[:30]}」连续+1代码 ×{length} "
                                       f"({codes[run_start][0]}–{codes[k-1][0]}, 约行 {codes[run_start][2]} 起)"))
            run_start = k
    # S2: 数值元组周期重复
    vcols = [int(x) - 1 for x in a.value_cols.split(",")]
    seen = {}
    for lineno, sr, cells, _ in rows:
        if cells is None or any(v >= len(cells) for v in vcols):
            continue
        t = tuple(cells[v] for v in vcols)
        seen.setdefault(t, []).append(lineno)
    for t, lns in seen.items():
        if len(lns) >= 3:
            d = [lns[i + 1] - lns[i] for i in range(len(lns) - 1)]
            if len(set(d)) == 1:
                findings.append(("S2", f"周期重复: 元组 {t} 恒距 {d[0]} 行 ×{len(lns)} (行 {lns[:5]}…)"))
    # S3 代理指标: 超长无备注/缺考段(仅提示)
    noise = 0
    for _, _, cells, _ in rows:
        joined = " ".join(cells)
        if re.search(r"缺考|弃考|放弃|同分|特设|备注\S|参照", joined):
            noise += 1
    if len(rows) >= a.s3_min and noise == 0:
        findings.append(("S3", f"零有机变异代理指标: {len(rows)} 行无缺考/弃考/同分/备注任一噪声(单独不立案, 需组合)"))
    for tag, msg in findings:
        print(f"[{tag}] {msg}")
    print(f"扫描行数={len(rows)} 嫌疑={len(findings)}")
    print("FAIL: 命中签名, 按 references/fabrication-forensics.md §3 分级" if findings else "PASS: 未命中签名(不替代重抓源比对)")
    return 1 if findings else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("continuity")
    c.add_argument("file"); c.add_argument("--col", type=int, default=1)
    c.set_defaults(fn=cmd_continuity)
    o = sub.add_parser("overlap")
    o.add_argument("file_a"); o.add_argument("file_b")
    o.add_argument("--band", type=int, nargs=2, required=True, metavar=("LO", "HI"))
    o.add_argument("--col", type=int, default=1)
    o.set_defaults(fn=cmd_overlap)
    s = sub.add_parser("scan")
    s.add_argument("file"); s.add_argument("--col", type=int, default=1)
    s.add_argument("--unit-col", type=int, default=4)
    s.add_argument("--value-cols", default="5,6,7")
    s.add_argument("--s1-min", type=int, default=10, help="S1 立案的最短连续代码链(默认10)")
    s.add_argument("--s3-min", type=int, default=100, help="S3 代理指标的最小行数(默认100)")
    s.set_defaults(fn=cmd_scan)
    a = p.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
