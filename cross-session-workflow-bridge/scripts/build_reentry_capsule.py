#!/usr/bin/env python3
"""build_reentry_capsule.py — 装配递归回灌胶囊（纯标准库）。

从项目目录读取 status_board.json（若存在）、iteration_log.json（若存在）与指定的
关键文件清单，生成回灌胶囊 markdown。协议见 references/reentry_capsule.md。

分层上限：L0 一句话状态 ≤50 字；L1 项目卡 ≤200 字；L2 回灌胶囊 ≤800 字。
字数超限自动截断并向 stderr 打印警告（截断有损，L3 全量归档是唯一完整事实源）。

用法：
  build_reentry_capsule.py [--project-dir DIR] [--level L0|L1|L2]
                           [--project NAME] [--files F1 F2 ...] [--out PATH]
退出码：0=成功；1=参数/输入错误；2=输入文件损坏（JSON 非法等）。
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

LEVEL_LIMIT = {"L0": 50, "L1": 200, "L2": 800}


def load_json(path, label):
    """读取 JSON；不存在返回 None；损坏则报错退出 2。"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[FAIL] {label} 不是合法 JSON：{path}（{e}）", file=sys.stderr)
        sys.exit(2)


def collect_state(project_dir):
    """汇集项目状态：返回 dict（project/version/level/pending/next_action/key_files/gaps）。"""
    state = {
        "project": None,
        "version": "",
        "grad_level": "",
        "pending": [],
        "next_action": "",
        "key_files": [],
        "gaps": [],
        "changes": [],
    }
    sb = load_json(os.path.join(project_dir, "status_board.json"), "status_board.json")
    if isinstance(sb, dict):
        state["project"] = sb.get("project")
        threads = sb.get("threads") if isinstance(sb.get("threads"), list) else []
        for t in threads:
            if not isinstance(t, dict):
                continue
            if t.get("status") in ("pending", "in_progress", "blocked"):
                state["pending"].append(
                    f"{t.get('id', '?')} {t.get('name', '')}（{t.get('status')}）".strip())
            if not state["version"] and t.get("latest_version"):
                state["version"] = str(t["latest_version"]).lstrip("v")
            for f in t.get("key_files") or []:
                if f and f not in state["key_files"]:
                    state["key_files"].append(f)
            for w in t.get("top3_likely_wrong") or []:
                if w:
                    state["gaps"].append(w)
            if not state["next_action"] and t.get("next_action"):
                state["next_action"] = t["next_action"]
        if not state["next_action"] and sb.get("first_task_next_session"):
            state["next_action"] = sb["first_task_next_session"]

    log = load_json(os.path.join(project_dir, "iteration_log.json"), "iteration_log.json")
    if isinstance(log, dict):
        if not state["project"]:
            state["project"] = log.get("project")
        iters = [e for e in (log.get("iterations") or []) if isinstance(e, dict)]
        if iters:
            last = iters[-1]
            if not state["version"] and last.get("version"):
                state["version"] = last["version"]
            state["grad_level"] = str(last.get("grad_level", ""))
            # 差异回灌原料：最近 3 条版本记录作为"自上次以来的变更"
            for e in iters[-3:]:
                state["changes"].append(
                    f"{e.get('version', '?')}:{e.get('summary', '')}".rstrip(":"))
    return state


def render_l0(s):
    ver = f"v{s['version']}" if s["version"] else "v?"
    lv = s["grad_level"] or "L?"
    nxt = s["next_action"] or "见胶囊"
    return f"{s['project']} {ver} {lv}：下一动作 {nxt}"


def render_l1(s):
    files = "、".join(s["key_files"][:3]) or "（未登记）"
    pend = "；".join(s["pending"][:3]) or "无"
    return (f"项目卡｜{s['project']}：状态 v{s['version'] or '?'}/{s['grad_level'] or 'L?'}；"
            f"未决 {pend}；下一动作 {s['next_action'] or '（未定）'}；关键文件 {files}")


def render_l2(s):
    files = "\n".join(f"- {f}" for f in s["key_files"][:7]) or "- （未登记关键文件）"
    pend = "；".join(s["pending"]) or "无"
    gaps = "；".join(s["gaps"]) or "无显式登记缺口（不代表无缺口）"
    changes = "；".join(s["changes"]) or "无"
    return (
        f"# 回灌胶囊：{s['project']}\n"
        f"【项目卡：目标】{s['project']}——按 L3 归档目标推进，本胶囊仅给入口。\n"
        f"【当前状态：版本号+毕业等级】v{s['version'] or '?'} / {s['grad_level'] or 'L?'}"
        f"（等级以 iteration-convergence-ops 严肃化阶梯为准）。\n"
        f"【未决项】{pend}\n"
        f"【下一动作】{s['next_action'] or '（未定：先读状态看板补登）'}\n"
        f"【核验锚点：关键文件路径+开场先 ls 核验的指令】\n{files}\n"
        f"开场先执行：ls 逐个核验以上文件存在。\n"
        f"【信源备忘：证据缺口】{gaps}\n"
        f"【自上次以来变更】{changes}\n"
        f"给下一个 agent：先 ls 核验上方【核验锚点】列出的每个文件存在；任一不存在则如实报告"
        f"并据 L3 归档重建，禁止凭胶囊记忆引用统计口径（数字/排名/结论一律以盘上文件与公开链接"
        f"为准）。核验通过后再执行【下一动作】。"
    )


def truncate(text, limit, level):
    if len(text) <= limit:
        return text, False
    print(f"[WARN] {level} 胶囊 {len(text)} 字超上限 {limit}，已截断（压缩有损，"
          f"完整事实源是 L3 归档）。", file=sys.stderr)
    return text[: max(0, limit - 1)] + "…", True


def main():
    ap = argparse.ArgumentParser(description="装配递归回灌胶囊（L0/L1/L2）")
    ap.add_argument("--project-dir", default=".",
                    help="项目目录（从中读 status_board.json / iteration_log.json）")
    ap.add_argument("--level", choices=["L0", "L1", "L2"], default="L2", help="胶囊层级")
    ap.add_argument("--project", default=None, help="项目名（覆盖状态文件中的名字）")
    ap.add_argument("--files", nargs="*", default=[],
                    help="关键文件清单（并入核验锚点槽位）")
    ap.add_argument("--out", default=None, help="输出路径（默认 stdout）")
    args = ap.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"[FAIL] 项目目录不存在：{args.project_dir}", file=sys.stderr)
        return 1

    state = collect_state(args.project_dir)
    state["project"] = args.project or state["project"] or os.path.basename(
        os.path.abspath(args.project_dir))
    for f in args.files:
        if f not in state["key_files"]:
            state["key_files"].append(f)

    body = {"L0": render_l0, "L1": render_l1, "L2": render_l2}[args.level](state)
    body, _ = truncate(body, LEVEL_LIMIT[args.level], args.level)

    header = ""
    if args.level != "L0":
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        header = f"<!-- 胶囊生成于 {ts}，层级 {args.level}；L3 全量归档是唯一完整事实源 -->\n"
    text = header + body

    if args.out:
        parent = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(parent, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"[OK] 胶囊已写入 {args.out}（{len(body)} 字 / 上限 {LEVEL_LIMIT[args.level]}）")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
