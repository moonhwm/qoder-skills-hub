#!/usr/bin/env python3
"""iteration_log.py — 维护项目迭代日志 iteration_log.json（纯标准库）。

用途：落实"版本号诚实"——版本号只按实际落盘变更递增，每个版本附变更条目，
check 子命令校验版本递增、无跳号、最近版本有对应落盘文件。

用法（注意：--log 是顶层参数，必须放在子命令之前）：
  iteration_log.py [--log PATH] init [--project NAME]     初始化日志文件
  iteration_log.py [--log PATH] add <版本> <变更摘要>
         [--file F] [--why W] [--impact I]
         [--branch converge|alpha] [--mode full|fast] [--force]
                                                          追加一条版本记录
  iteration_log.py [--log PATH] check [--root DIR]        校验日志（退出码 0=通过，1=失败）
  iteration_log.py [--log PATH] report                    输出 Markdown 版本史

错误退出码：1=校验失败/参数非法；2=日志文件损坏（非合法 JSON 等）。

版本号格式：x.y 或 x.y-alpha（x,y 为非负整数）。
递增规则：同主版本 minor 每次 +1；主版本升级时 major +1 且 minor 归 0；
alpha 与正式版共享同一 x.y 序列（alpha 视为该版本号的探索形态，不单独占号）。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

DEFAULT_LOG = "iteration_log.json"
# 拒绝前导零（如 01.0）：x/y 要么为 0，要么以非零数字开头
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)(-alpha)?$")


def fmt_version(p):
    """(major, minor, is_alpha) -> '1.0' / '1.0-alpha' 形式的可读字符串。"""
    return f"{p[0]}.{p[1]}{'-alpha' if p[2] else ''}"


def parse_version(v):
    m = VERSION_RE.match(v.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), bool(m.group(3)))


def load_log(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[FAIL] 日志文件不是合法 JSON：{path}（{e}）", file=sys.stderr)
        sys.exit(2)


def save_log(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def cmd_init(args):
    if os.path.exists(args.log):
        print(f"[SKIP] {args.log} 已存在，未覆盖。", file=sys.stderr)
        return 0
    data = {
        "project": args.project,
        "created": datetime.now(timezone.utc).isoformat(),
        "iterations": [],
    }
    save_log(args.log, data)
    print(f"[OK] 已初始化 {args.log}（project={args.project}）")
    return 0


def cmd_add(args):
    data = load_log(args.log)
    if data is None:
        print(f"[FAIL] 日志不存在：{args.log}，请先运行 init。", file=sys.stderr)
        return 1
    if not isinstance(data, dict) or not isinstance(data.get("iterations"), list):
        print(f"[FAIL] 日志结构非法：{args.log}（顶层须为对象且含 iterations 数组）", file=sys.stderr)
        return 1
    parsed = parse_version(args.version)
    if parsed is None:
        print(f"[FAIL] 版本号格式非法：{args.version}（应为 x.y 或 x.y-alpha，不允许前导零）", file=sys.stderr)
        return 1
    entry = {
        "version": args.version.strip(),
        "summary": args.summary,
        "why": args.why or "",
        "impact": args.impact or "",
        "file": args.file or "",
        "branch": args.branch,
        "mode": args.mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # fail-fast：对现有末条做递增校验（复用 check_versions 的递增逻辑）
    iterations = data["iterations"]
    if iterations and isinstance(iterations[-1], dict):
        last_v = iterations[-1].get("version", "")
        if isinstance(last_v, str) and parse_version(last_v) is not None:
            errs, warns = check_versions([{"version": last_v}, entry])
        else:
            errs, warns = [], []
        for w in warns:
            print(f"[WARN] {w}", file=sys.stderr)
        if errs:
            for e in errs:
                tag = "[WARN] --force 生效，仍写入" if args.force else "[FAIL] 拒绝写入"
                print(f"{tag}：{e}", file=sys.stderr)
            if not args.force:
                print("[FAIL] 版本递增非法，未落盘；确需强行记录请加 --force。", file=sys.stderr)
                return 1
    data["iterations"].append(entry)
    save_log(args.log, data)
    print(f"[OK] 已记录 {args.version}：{args.summary}")
    return 0


def check_versions(iterations):
    """返回 (errors, warnings)。校验递增、无跳号、无重复。"""
    errors, warnings = [], []
    prev = None
    for e in iterations:
        if not isinstance(e, dict):
            errors.append(f"非法条目（须为对象）：{e!r}")
            continue
        v = e.get("version", "")
        if not isinstance(v, str):
            errors.append(f"版本号须为字符串：{v!r}")
            continue
        p = parse_version(v)
        if p is None:
            errors.append(f"版本号格式非法：{v}")
            continue
        if prev is not None:
            pm, pn, pa = prev
            m, n, a = p
            if (m, n) == (pm, pn):
                if a == pa:
                    errors.append(f"重复版本号：{v}")
                elif pa and not a:
                    pass  # x.y-alpha -> x.y 收敛转正，合法
                else:
                    errors.append(f"版本回退/乱序：{fmt_version(prev)} -> {fmt_version(p)}")
            elif (m, n) > (pm, pn):
                if m == pm and n != pn + 1:
                    errors.append(f"跳号：{fmt_version(prev)} -> {fmt_version(p)}（minor 应递增 1）")
                elif m == pm + 1 and n != 0:
                    errors.append(f"跳号：{fmt_version(prev)} -> {fmt_version(p)}（主版本升级 minor 应归 0）")
                elif m > pm + 1:
                    errors.append(f"跨大版本号夸大：{fmt_version(prev)} -> {fmt_version(p)}（major 每次只能 +1）")
                elif pa and not a:
                    warnings.append(
                        f"alpha 直接跳收敛 minor 版号：{fmt_version(prev)} -> {fmt_version(p)}"
                        f"（version_honesty_git.md 分支语义禁止此跳法；脚本仅警告，最终靠自律）"
                    )
            else:
                errors.append(f"版本回退：{fmt_version(prev)} -> {fmt_version(p)}")
        prev = p
    return errors, warnings


def check_files(iterations, root):
    """校验最近版本是否有对应落盘文件。"""
    errors = []
    if not iterations:
        return errors
    last = iterations[-1]
    f = last.get("file", "")
    if not f:
        errors.append(
            f"最近版本 {last.get('version')} 未声明落盘文件（--file），"
            f"存在'声称完成但未落盘'风险"
        )
    else:
        path = f if os.path.isabs(f) else os.path.join(root, f)
        if not os.path.exists(path):
            errors.append(f"最近版本 {last.get('version')} 声明的落盘文件不存在：{path}")
    return errors


def cmd_check(args):
    data = load_log(args.log)
    if data is None:
        print(f"[FAIL] 日志不存在：{args.log}", file=sys.stderr)
        return 1
    if not isinstance(data, dict) or not isinstance(data.get("iterations"), list):
        print(f"[FAIL] 日志结构非法：{args.log}（顶层须为对象且含 iterations 数组）", file=sys.stderr)
        return 1
    iterations = data["iterations"]
    v_err, v_warn = check_versions(iterations)
    f_err = check_files(iterations, args.root)
    errors = v_err + f_err
    for w in v_warn:
        print(f"[WARN] {w}")
    if errors:
        print("[CHECK FAILED]")
        for e in errors:
            print(f"  - {e}")
        return 1
    if not iterations:
        print("[CHECK OK] 空日志：无版本记录。")
        return 0
    print(f"[CHECK OK] {len(iterations)} 个版本：递增合法、无跳号、最近版本落盘文件存在。")
    return 0


def cmd_report(args):
    data = load_log(args.log)
    if data is None:
        print(f"[FAIL] 日志不存在：{args.log}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print(f"[FAIL] 日志顶层必须是对象：{args.log}", file=sys.stderr)
        return 1
    lines = [
        f"# 版本史：{data.get('project', '(未命名项目)')}",
        "",
        f"创建时间：{data.get('created', '?')}　共 {len(data.get('iterations', []))} 个版本",
        "",
        "| 版本 | 分支 | 模式 | 变更摘要 | 为什么 | 影响 | 落盘文件 | 时间 |",
        "|------|------|------|----------|--------|------|----------|------|",
    ]
    for e in data.get("iterations", []):
        lines.append(
            "| {v} | {b} | {m} | {s} | {w} | {i} | {f} | {t} |".format(
                v=e.get("version", "?"),
                b=e.get("branch", ""),
                m=e.get("mode", ""),
                s=e.get("summary", "").replace("|", "\\|"),
                w=e.get("why", "").replace("|", "\\|"),
                i=e.get("impact", "").replace("|", "\\|"),
                f=e.get("file", "") or "（未声明）",
                t=e.get("timestamp", "")[:19],
            )
        )
    print("\n".join(lines))
    return 0


def main():
    ap = argparse.ArgumentParser(description="迭代日志维护（版本诚实校验）")
    ap.add_argument("--log", default=DEFAULT_LOG, help="日志文件路径")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="初始化日志")
    p.add_argument("--project", default="unnamed-project")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add", help="追加版本记录")
    p.add_argument("version")
    p.add_argument("summary")
    p.add_argument("--file", default="", help="本版本对应落盘文件路径")
    p.add_argument("--why", default="")
    p.add_argument("--impact", default="")
    p.add_argument("--branch", choices=["converge", "alpha"], default="converge")
    p.add_argument("--mode", choices=["full", "fast"], default="full")
    p.add_argument("--force", action="store_true",
                   help="递增校验失败时打印警告仍强制写入（逃生门，慎用）")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("check", help="校验日志")
    p.add_argument("--root", default=".", help="相对落盘文件的解析根目录")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("report", help="输出 Markdown 版本史")
    p.set_defaults(func=cmd_report)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
