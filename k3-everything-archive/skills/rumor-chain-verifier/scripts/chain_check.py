#!/usr/bin/env python3
"""chain_check.py — 传言逻辑链登记校验与链节判定表生成（纯标准库）。

stdin 读 JSON 对象：
{
  "topic": "传言主题",
  "check_date": "YYYY-MM-DD",
  "links": [
    {"id": "L1", "type": "事实|因果|价值", "claim": "链节断言",
     "verdict": "成立|部分成立|断裂|存疑", "conf": "High|Medium|Low|Conflict",
     "evidence": "证据摘要或 no_evidence 说明"}
  ]
}
stdout 输出 JSON：{"errors": [...], "overall_verdict": str, "markdown": 链节判定表, "stats": {...}}
整体判定规则：任一因果节=断裂 → "链条断裂（整体不成立）"；无因果节 → "非复合断言，按单断言核查"；
存在存疑节 → "部分链节存疑"；全部成立 → "链条成立"。
"""
import json, sys

TYPES = {"事实", "因果", "价值"}
VERDICTS = {"成立", "部分成立", "断裂", "存疑"}
CONFS = {"High", "Medium", "Low", "Conflict"}

def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        print(json.dumps({"errors": [f"JSON 解析失败: {e}"]}, ensure_ascii=False)); return
    errors = []
    topic = data.get("topic", "").strip()
    if not topic:
        errors.append("缺少 topic")
    links = data.get("links")
    if not isinstance(links, list) or len(links) < 2:
        errors.append("links 须为 >=2 链节的数组（复合传言至少两节）")
        links = links if isinstance(links, list) else []
    for i, l in enumerate(links):
        for f in ("id", "type", "claim", "verdict", "conf"):
            if f not in l:
                errors.append(f"links[{i}]: 缺字段 {f}")
        if l.get("type") not in TYPES:
            errors.append(f"links[{i}]: type 非法，须为 {sorted(TYPES)}")
        if l.get("verdict") not in VERDICTS:
            errors.append(f"links[{i}]: verdict 非法，须为 {sorted(VERDICTS)}")
        if l.get("conf") not in CONFS:
            errors.append(f"links[{i}]: conf 非法，须为 {sorted(CONFS)}")
        if not (l.get("evidence") or l.get("no_evidence_reason")):
            errors.append(f"links[{i}]: 缺 evidence 或 no_evidence_reason")
    causal = [l for l in links if l.get("type") == "因果"]
    broken = [l for l in links if l.get("verdict") == "断裂"]
    doubtful = [l for l in links if l.get("verdict") in ("存疑",) or l.get("conf") in ("Low", "Conflict")]
    if not causal:
        overall = "非复合断言，按单断言核查"
    elif any(l.get("verdict") == "断裂" for l in causal):
        overall = "链条断裂（整体不成立）：断裂节=" + "、".join(l["id"] for l in causal if l.get("verdict") == "断裂")
    elif doubtful:
        overall = "链条主体成立，部分链节存疑：" + "、".join(l["id"] for l in doubtful)
    else:
        overall = "链条成立"
    md = [f"# 链节判定表：{topic}", "",
          "| 链节 | 类型 | 断言 | 判定 | conf | 依据 |", "|---|---|---|---|---|---|"]
    for l in links:
        md.append("| {id} | {type} | {claim} | **{verdict}** | {conf} | {ev} |".format(
            id=l.get("id", "?"), type=l.get("type", "?"), claim=str(l.get("claim", "")).replace("|", "｜"),
            verdict=l.get("verdict", "?"), conf=l.get("conf", "?"),
            ev=str(l.get("evidence") or l.get("no_evidence_reason", "—")).replace("|", "｜")[:80]))
    md += ["", f"**整体判定：{overall}**"]
    stats = {"links": len(links), "因果节": len(causal), "断裂节": len(broken), "存疑节": len(doubtful)}
    print(json.dumps({"errors": errors, "overall_verdict": overall,
                      "markdown": "\n".join(md), "stats": stats}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
