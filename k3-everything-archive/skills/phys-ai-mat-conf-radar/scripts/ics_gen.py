#!/usr/bin/env python3
"""ics_gen.py — 排期 JSONL → iCalendar (.ics) 文件。

输入：deadline_triage.py 输出的 JSONL（顶层 {"data_cutoff":..., "events":[...]}）
      或裸事件 JSONL 行（每行一个事件，至少含 event/date_norm 或 date）。
输出：标准 RFC 5545 .ics，全天事件（DATE 型 DTSTART/DTEND），可直接导入日历。

用法：
  python3 ics_gen.py events.jsonl --out schedule.ics
  python3 ics_gen.py --smoke
"""
import argparse
import json
import re
import sys
import uuid

NS = "phys-ai-mat-conf-radar"


def esc(s):
    return re.sub(r"([,;\\])", r"\\\1", str(s)).replace("\n", "\\n")


def to_ics_date(iso):
    return iso.replace("-", "")[:8]


def _next_day(d8):
    """YYYYMMDD → 次日 YYYYMMDD（RFC 5545 全天事件 DTEND 为排他端点，须 +1 天）。"""
    from datetime import date, timedelta
    d = date(int(d8[:4]), int(d8[4:6]), int(d8[6:8]))
    return (d + timedelta(days=1)).strftime("%Y%m%d")


def event_to_vevent(ev):
    d = ev.get("date_norm") or ev.get("date")
    if not d:
        return None
    d8 = to_ics_date(str(d))
    uid = f"{uuid.uuid5(uuid.NAMESPACE_URL, NS + ev.get('event','') + d8)}@{NS}"
    summ = f"[{ev.get('deadline_type','node')}] {ev.get('event','(untitled)')}"
    desc_bits = [f"domain: {ev.get('domain','?')}", f"status: {ev.get('status','?')}",
                 f"conf: {ev.get('conf','assumed')}"]
    if ev.get("source_url"):
        desc_bits.append(f"source: {ev['source_url']}")
    if ev.get("cycle_note"):
        desc_bits.append(f"note: {ev['cycle_note']}")
    return "\r\n".join([
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{to_ics_date(str(ev.get('_generated','20260101')))}T000000Z",
        f"DTSTART;VALUE=DATE:{d8}",
        f"DTEND;VALUE=DATE:{_next_day(d8)}",
        f"SUMMARY:{esc(summ)}",
        f"DESCRIPTION:{esc(' | '.join(desc_bits))}",
        f"CATEGORIES:{esc(str(ev.get('domain','misc')).upper())}",
        "END:VEVENT",
    ])


def build_ics(events, calname="conf-radar"):
    body = [e for e in (event_to_vevent(ev) for ev in events) if e]
    return "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{NS}//CN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{esc(calname)}",
        *body,
        "END:VCALENDAR",
    ]) + "\r\n"


def load_events(text):
    """兼容两种输入：顶层包裹 JSON 或裸 JSONL。"""
    text = text.strip()
    events = []
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "events" in obj:
            return obj["events"]
        if isinstance(obj, list):
            return obj
    except json.JSONDecodeError:
        pass
    for line in text.splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def smoke():
    evs = [
        {"event": "APS DPP 2026", "domain": "plasma", "deadline_type": "abstract",
         "date_norm": "2026-07-15", "status": "upcoming", "conf": "empirical",
         "source_url": "https://engage.aps.org/dpp/meetings"},
        {"event": "NeurIPS 2027", "domain": "ai", "deadline_type": "paper",
         "date": "2027-05-15", "conf": "assumed"},
    ]
    ics = build_ics(evs)
    assert ics.startswith("BEGIN:VCALENDAR") and ics.rstrip().endswith("END:VCALENDAR")
    assert ics.count("BEGIN:VEVENT") == 2
    assert "DTSTART;VALUE=DATE:20260715" in ics
    assert "DTEND;VALUE=DATE:20260716" in ics  # 排他端点 +1 天
    assert _next_day("20261231") == "20270101"  # 跨年边界
    assert "SUMMARY:[abstract] APS DPP 2026" in ics
    assert "conf: assumed" in ics
    # load_events 两种形态
    assert len(load_events(json.dumps({"data_cutoff": "2026-08-28", "events": evs}))) == 2
    assert len(load_events("\n".join(json.dumps(e) for e in evs))) == 2
    print("SMOKE OK: ics_gen 全部断言通过")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="排期 JSONL → .ics 日历")
    ap.add_argument("files", nargs="*", help="输入文件（缺省 stdin）")
    ap.add_argument("--out", required=False, help="输出 .ics 路径（缺省 stdout）")
    ap.add_argument("--calname", default="conf-radar", help="日历名称")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)

    if args.smoke:
        return smoke()

    text = ""
    if args.files:
        for fp in args.files:
            with open(fp, encoding="utf-8") as f:
                text += f.read() + "\n"
    else:
        text = sys.stdin.read()
    events = load_events(text)
    if not events:
        print("无有效事件", file=sys.stderr)
        return 1
    ics = build_ics(events, args.calname)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as f:
            f.write(ics)
        print(f"已写入 {args.out}（{ics.count('BEGIN:VEVENT')} 个事件）", file=sys.stderr)
    else:
        sys.stdout.write(ics)
    return 0


if __name__ == "__main__":
    sys.exit(main())
