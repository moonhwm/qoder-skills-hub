#!/usr/bin/env python3
"""ai_deadlines_ingest.py — 把 vendored ai-deadlines YAML 快照转成本技能契约 JSONL。

内置纪律（不可关）：所有转出记录强制 conf=assumed、verify_stage=T1_pending，
并在 cycle_note 标注快照日期——聚合站数据是 C3 线索，不是官宣。
用法：
  python3 ai_deadlines_ingest.py                 # 读默认 vendor 路径 → stdout JSONL
  python3 ai_deadlines_ingest.py --sub ML CV     # 只转指定子领域
  python3 ai_deadlines_ingest.py --smoke
"""
import argparse
import json
import os
import re
import sys

DEFAULT_YML = os.path.join(os.path.dirname(__file__), "..", "references",
                           "data", "ai_deadlines_conferences.yml")
SNAPSHOT = "ai-deadlines@b230d24(2024-09-15)"

# 仅支持该文件的扁平 YAML 子集：`- key: value` 起始记录，后续 `key: value` 行。
REC_START = re.compile(r"^-\s+(\w+):\s*(.*)$")
KV = re.compile(r"^\s{2}(\w+):\s*(.*)$")


def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
        return v[1:-1]
    return v


def parse_subset_yaml(text):
    """扁平 YAML 子集解析器（仅限本 vendor 文件形制；非通用 YAML 解析器）。"""
    recs, cur = [], None
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = REC_START.match(line)
        if m:
            cur = {}
            recs.append(cur)
            cur[m.group(1)] = _unquote(m.group(2))
            continue
        m = KV.match(line)
        if m and cur is not None:
            cur[m.group(1)] = _unquote(m.group(2))
    return recs


def to_contract(rec):
    """ai-deadlines 记录 → 本技能排期契约 JSONL 记录（强制 assumed/T1_pending）。"""
    out = {
        "event": f"{rec.get('title', '?')} {rec.get('year', '?')}",
        "domain": "ai",  # ai-deadlines 以 AI 子领域为主；sub 字段透传
        "sub": rec.get("sub"),
        "tier": "线索",
        "deadline_type": "paper",
        "date": (rec.get("deadline") or "").split(" ")[0] or None,
        "tz": rec.get("timezone"),
        "source_url": rec.get("link"),
        "verify_stage": "T1_pending",
        "conf": "assumed",
        "cycle_note": f"聚合站快照 {SNAPSHOT}，须官网 T2 核验后方可作官宣",
    }
    if rec.get("abstract_deadline"):
        out["abstract_deadline"] = rec["abstract_deadline"].split(" ")[0]
    return {k: v for k, v in out.items() if v is not None}


def smoke():
    sample = """- title: TESTCONF
  year: 2025
  id: test25
  link: https://example.org
  deadline: '2024-10-10 23:59:59'
  timezone: UTC-12
  sub: ML
- title: CONF2
  year: 2026
  link: https://example2.org
  deadline: "2025-05-01 23:59:59"
  sub: CV
"""
    recs = parse_subset_yaml(sample)
    assert len(recs) == 2 and recs[0]["title"] == "TESTCONF"
    assert recs[0]["deadline"] == "2024-10-10 23:59:59"  # 引号剥除
    c = to_contract(recs[0])
    assert c["conf"] == "assumed" and c["verify_stage"] == "T1_pending"
    assert c["date"] == "2024-10-10" and c["tz"] == "UTC-12"
    assert "须官网 T2 核验" in c["cycle_note"]
    # 真实 vendor 文件完整性抽查
    real = parse_subset_yaml(open(DEFAULT_YML, encoding="utf-8").read())
    assert len(real) >= 100, f"vendor 文件解析条数异常: {len(real)}"
    assert any(r.get("title") == "NeurIPS" for r in real)
    print(f"SMOKE OK: ai_deadlines_ingest 断言通过（vendor 文件解析 {len(real)} 条）")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="vendored ai-deadlines 快照 → 契约 JSONL（强制 C3/assumed）")
    ap.add_argument("--yml", default=DEFAULT_YML, help="YAML 快照路径")
    ap.add_argument("--sub", nargs="*", help="只转指定子领域（如 ML CV NLP）")
    ap.add_argument("--out", help="输出文件（默认 stdout）")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)

    if args.smoke:
        return smoke()

    with open(args.yml, encoding="utf-8") as f:
        recs = parse_subset_yaml(f.read())
    if args.sub:
        keep = set(args.sub)
        recs = [r for r in recs if r.get("sub") in keep]
    lines = [json.dumps(to_contract(r), ensure_ascii=False) for r in recs]
    payload = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
    else:
        sys.stdout.write(payload)
    print(f"转出 {len(lines)} 条（全部 conf=assumed，须 T2 核验）", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
