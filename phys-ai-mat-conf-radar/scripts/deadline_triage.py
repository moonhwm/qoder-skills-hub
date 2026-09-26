#!/usr/bin/env python3
"""deadline_triage.py — 会议/期刊节点排期分诊。

输入：JSONL 事件清单，每行至少：
  {"event": "APS DPP 2026", "domain": "plasma", "deadline_type": "abstract",
   "date": "2026-07-15", "source_url": "https://...", "conf": "empirical"}
可选字段：cycle_note（周期备注）、tz（时区说明）、tier（会议档位）、verify_stage（T0-T3）。
日期允许 "2026-07-15"（精确）或 "2026-07"（月度窗口，按月末保守估计并标 tentative）。

输出：按日期升序的排期表（markdown）+ 规范化 JSONL，顶层带 data_cutoff。
状态分诊（相对 --today，默认当天）：
  past       已过
  imminent   剩余 <= --window 天（默认 30）
  upcoming   剩余 > window 天
  tentative  月度窗口/未经 T2 核验（conf=assumed）

用法：
  python3 deadline_triage.py events.jsonl --today 2026-08-28 --window 30 --pretty
  python3 deadline_triage.py --smoke
"""
import argparse
import json
import sys
from datetime import date

REQUIRED = ["event", "domain", "deadline_type", "date"]
ALLOWED_CONF = {"empirical", "estimated", "assumed"}


def parse_date(s):
    """返回 (date对象, is_tentative)。"""
    s = s.strip()
    parts = s.split("-")
    if len(parts) == 3:
        return date(int(parts[0]), int(parts[1]), int(parts[2])), False
    if len(parts) == 2:  # 月度窗口：保守按月末
        y, m = int(parts[0]), int(parts[1])
        nxt = date(y + (m == 12), m % 12 + 1, 1)
        from datetime import timedelta
        return nxt - timedelta(days=1), True
    raise ValueError(f"bad date: {s}")


def triage(rec, today, window):
    errs = [f"missing field: {k}" for k in REQUIRED if k not in rec]
    if errs:
        return None, errs
    d, tent = parse_date(str(rec["date"]))
    conf = str(rec.get("conf", "assumed")).lower()
    if conf not in ALLOWED_CONF:
        return None, [f"conf 必须为 {sorted(ALLOWED_CONF)}（数据流层词表），收到 {conf}"]
    tentative = tent or conf == "assumed"
    delta = (d - today).days
    if delta < 0:
        status = "past"
    elif tentative:
        status = "tentative"
    elif delta <= window:
        status = "imminent"
    else:
        status = "upcoming"
    out = dict(rec)
    out.update({"date_norm": d.isoformat(), "days_left": delta, "status": status,
                "tentative": tentative, "conf": conf})
    return out, []


def render_md(rows, data_cutoff):
    lines = [f"| 事件 | 领域 | 节点 | 日期 | 剩余天数 | 状态 | conf | 来源 |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| {event} | {domain} | {deadline_type} | {date_norm} | {days_left} | "
                     "{status} | {conf} | {src} |".format(src=r.get("source_url", "—"), **r))
    return f"数据截止：{data_cutoff}\n\n" + "\n".join(lines)


def smoke():
    sample = [
        {"event": "Conf A", "domain": "plasma", "deadline_type": "abstract",
         "date": "2026-09-10", "conf": "empirical"},
        {"event": "Conf B", "domain": "ai", "deadline_type": "paper",
         "date": "2026-05", "conf": "assumed"},
        {"event": "Conf C", "domain": "materials", "deadline_type": "registration",
         "date": "2026-08-01", "conf": "empirical"},
    ]
    today = date(2026, 8, 28)
    rows = []
    for s in sample:
        r, errs = triage(s, today, 30)
        assert not errs, errs
        rows.append(r)
    assert rows[0]["status"] == "imminent" and rows[0]["days_left"] == 13
    # 设计决策：过期即 past（tentative 只管未来节点）；rows[1] 月度窗口 2026-05 已过 → past
    assert rows[1]["status"] == "past" and rows[1]["days_left"] < 0
    assert rows[2]["status"] == "past"
    # 未来 + 月度窗口/assumed → tentative
    fut = {"event": "Conf D", "domain": "ai", "deadline_type": "paper",
           "date": "2027-03", "conf": "assumed"}
    rf, _ = triage(fut, today, 30)
    assert rf["status"] == "tentative"
    # conf 词表守卫
    bad = {"event": "X", "domain": "ai", "deadline_type": "paper", "date": "2027-01-01", "conf": "high"}
    _, errs = triage(bad, today, 30)
    assert errs and "conf" in errs[0]
    print("SMOKE OK: deadline_triage 全部断言通过")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="会议节点排期分诊（JSONL → 状态表）")
    ap.add_argument("files", nargs="*", help="JSONL 事件文件（缺省 stdin）")
    ap.add_argument("--today", help="基准日 YYYY-MM-DD（默认今天）")
    ap.add_argument("--window", type=int, default=30, help="imminent 窗口天数（默认 30）")
    ap.add_argument("--pretty", action="store_true", help="输出 markdown 表 + JSONL")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)

    if args.smoke:
        return smoke()

    today = date.fromisoformat(args.today) if args.today else date.today()
    text = ""
    if args.files:
        for fp in args.files:
            with open(fp, encoding="utf-8") as f:
                text += f.read() + "\n"
    else:
        text = sys.stdin.read()

    rows, had_err = [], False
    for i, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as ex:
            print(f"line {i}: JSON 解析失败 {ex}", file=sys.stderr)
            had_err = True
            continue
        r, errs = triage(rec, today, args.window)
        if errs:
            print(f"line {i}: {'; '.join(errs)}", file=sys.stderr)
            had_err = True
            continue
        rows.append(r)
    rows.sort(key=lambda r: r["date_norm"])

    cutoff = today.isoformat()
    if args.pretty:
        print(render_md(rows, cutoff))
        print("\n```json")
    print(json.dumps({"data_cutoff": cutoff, "events": rows}, ensure_ascii=False,
                     indent=2 if args.pretty else None))
    if args.pretty:
        print("```")
    return 1 if had_err else 0


if __name__ == "__main__":
    sys.exit(main())
