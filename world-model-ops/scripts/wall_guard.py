# -*- coding: utf-8 -*-
"""wall_guard.py —— 容量墙闸（应《跨生态A2A协作网络体系建设方案》：
「遇到额度墙（墙码 1308/1310/1005）零重试，按预案切换通道或等待窗口，异常事件按『撞墙即停』原则处置并全程留痕」）
三分类（★判据在手，勿凭感觉重试）：
  wall       额度／预算／欠费类 ⇒ ★零重试；按预案切通道或等窗口；★全程留痕
  transient  网络重置／超时／5xx ⇒ 可有限重试（默认 3 次，退避递增）
  permanent  参数／类型／路径类（400/404）⇒ 不重试；★报错并修因
用法：
  python wall_guard.py --classify "<错误原文或码>"
  python wall_guard.py --scan [--dir <目录>]        # 回溯扫记录中之墙码 ⇒ 补留痕
  python wall_guard.py --ledger [--tail 20]
（中文串一律用「」）
"""
import argparse, json, pathlib, re, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
WALL_LEDGER = SEAT/"ledger"/"wall_ledger_v2.jsonl"

# ★严格判据（v2）：结构化或紧邻同现，杜绝散文子串误配
WALL_PAT = re.compile(r'("code"\s*[:=]\s*"?\s*(1308|1310|1005)\b)|(BudgetLimitExceeded|Arrearage)|'
                      r'((budget|额度|预算|欠费|配额)[^。\n]{0,24}(exhaust|exceed|insufficient|不足|耗尽|用尽|超限|停服))', re.I)
TRANS_PAT = re.compile(r'(WinError\s*10054)|(ConnectionReset|connection reset)|(timed?\s*out)|(HTTP[/ ]?\s*5\d\d)|(MemoryError)|(远程主机强迫关闭)', re.I)
PERM_PAT  = re.compile(r'("code"\s*[:=]\s*"?\s*(400|404|400001|403)\b)|(Unsupported file type)|(InvalidAction)', re.I)

def classify(text):
    t = str(text)
    m = WALL_PAT.search(t)
    if m: return ("wall", (m.group(2) or m.group(3) or m.group(5) or "wall")[:24], "额度／预算类（结构化或紧邻同现）")
    m = TRANS_PAT.search(t)
    if m: return ("transient", (m.group(0) or "")[:24].strip(), "瞬态（可有限重试，退避递增）")
    m = PERM_PAT.search(t)
    if m: return ("permanent", (m.group(2) or m.group(3) or "")[:24] or "perm", "参数／类型类（不重试，修因）")
    return ("unknown", "", "未识别 ⇒ 默认按 permanent 处置（不重试）并记待核")

def record(text, source="", channel="", kind="", code="", advice=""):
    if not kind: kind, code, advice = classify(text)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "kind": kind, "code": code, "advice": advice,
           "source": source, "channel": channel, "excerpt": re.sub(r"\s+", " ", str(text))[:160],
           "retry_policy": "★零重试（切通道或等窗口）" if kind == "wall" else ("有限重试 3 次" if kind == "transient" else "不重试")}
    WALL_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(WALL_LEDGER, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

def scan(root=None, maxfiles=4000, hint_only=True):
    root = pathlib.Path(root) if root else SEAT
    pats = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in (".json", ".jsonl", ".md", ".log", ".txt", ".py") and p.stat().st_size < 2_000_000]
    hits = 0; seen = set()
    for p in pats[:maxfiles]:
        try: t = p.read_text(encoding="utf-8", errors="replace")
        except Exception: continue
        for line in t.splitlines():
            if not (WALL_PAT.search(line) or TRANS_PAT.search(line) or PERM_PAT.search(line)): continue
            k, c, a = classify(line)
            if k in ("wall", "transient") and c:
                key = (c, re.sub(r"\W", "", line)[:40])
                if key in seen: continue
                seen.add(key)
                if not hint_only: record(line, source=str(p.relative_to(root))[:70], channel=p.suffix.lstrip("."))
                hits += 1
    return hits, len(pats)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--classify", default=""); ap.add_argument("--scan", action="store_true", help="（已废弃：改为 --hint，只打印不落账）")
    ap.add_argument("--hint", action="store_true")
    ap.add_argument("--dir", default=""); ap.add_argument("--ledger", action="store_true"); ap.add_argument("--tail", type=int, default=20)
    a = ap.parse_args()
    if a.classify:
        k, c, adv = classify(a.classify)
        print("   ★ 判：%s ｜ 码=%s ｜ %s ｜ 处置=%s" % (k, c or "—", adv,
              "★零重试（切通道或等窗口）" if k == "wall" else ("有限重试 3 次" if k == "transient" else "不重试")))
    if a.scan or a.hint:
        h, n = scan(a.dir or None, hint_only=True)
        print("   ★提示扫（不落账）：扫 %d 件 ⇒ 疑似墙／瞬态行 %d 条 ⇒ ★仅作线索，不得当事件证据" % (n, h))
    if a.ledger and WALL_LEDGER.exists():
        rows = WALL_LEDGER.read_text(encoding="utf-8", errors="replace").splitlines()
        print("   墙账共 %d 条 ⇒ 末 %d 条：" % (len(rows), min(a.tail, len(rows))))
        for l in rows[-a.tail:]:
            j = json.loads(l); print("     · [%s] %s ｜ %s ｜ %s" % (j.get("kind","?"), j.get("code") or "—", str(j.get("advice",""))[:34], str(j.get("excerpt",""))[:64]))

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
