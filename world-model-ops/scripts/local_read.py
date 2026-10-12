# -*- coding: utf-8 -*-
"""local_read.py —— 本地直读通道（根治"复拉上游 404"之事故）
缘起：2026-10-12 上游 kdocs-cli 对多数 link_id 返回 400100（带 file_id 时明示 404 page not found）
     ⇒ 而本机 WPS 同步目录内即有正本（37 件 .otl 为纯文本 ＋ 60 件 .md）
做法：①扫「Plan提示词工程/openplanlink-docx」之 .otl/.md ②建档（字/行/节/哈希）入 archive/docs_local/
     ③与既有 archive/docs 比对（能对上名者，按节比增删改）
用法：python local_read.py [--scan] [--compare]
（中文串一律用「」）
"""
import argparse, hashlib, json, pathlib, re, sys, time

HOME = pathlib.Path.home()
LOC = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"Plan提示词工程"/"openplanlink-docx"
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
OUT = SEAT/"archive"/"docs_local"
ARCH = SEAT/"archive"/"docs"

def secs(t):
    out, cur = {}, "(前言)"
    for l in t.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)$", l.strip())
        if m: cur = m.group(1).strip()
        out[cur] = out.get(cur, 0) + len(l)
    return out

def row(p):
    t = p.read_text(encoding="utf-8", errors="replace")
    s = secs(t)
    return {"name": p.name, "ext": p.suffix, "chars": len(t), "lines": len(t.splitlines()),
            "sections": len(s), "sha3_16": hashlib.sha3_256(t.encode()).hexdigest()[:16],
            "size": p.stat().st_size, "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime)),
            "sec_map": s}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--scan", action="store_true"); ap.add_argument("--compare", action="store_true")
    a = ap.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(list(LOC.glob("*.otl")) + list(LOC.glob("*.md")))
    print("  ═══ 本地直读：扫得 %d 件（.otl %d ｜ .md %d）═══" % (
        len(files), sum(1 for f in files if f.suffix == ".otl"), sum(1 for f in files if f.suffix == ".md")))
    rows = [row(p) for p in files]
    tot = sum(r["chars"] for r in rows)
    print("   合计 %d 字 ｜ 最大 5 件：" % tot)
    for r in sorted(rows, key=lambda x: -x["chars"])[:5]:
        print("     %-56s ｜ 字 %6d ｜ 节 %3d ｜ %s" % (r["name"][:56], r["chars"], r["sections"], r["sha3_16"]))
    idx = OUT/"index.json"
    if idx.exists():
        old = json.loads(idx.read_text(encoding="utf-8"))
        om = {r["name"]: r for r in old.get("files", [])}
        new = [r for r in rows if r["name"] not in om or om[r["name"]]["sha3_16"] != r["sha3_16"]]
        print("   ★ 与上次本地索引比对：新增或变更 %d 件" % len(new))
        for r in new[:6]: print("     · %s（%d 字）" % (r["name"][:60], r["chars"]))
    idx.write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
        "source": str(LOC), "n": len(rows), "total_chars": tot,
        "files": [{k: v for k, v in r.items() if k != "sec_map"} for r in rows]}, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    print("   ✓ 已建档：%s（%d 件）" % (idx.relative_to(SEAT), len(rows)))
    if a.compare:
        print("\n  ═══ 与 archive/docs 比对（按文件名归一化匹配）═══")
        def norm(s): return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", s)[:40]
        hit = 0
        for r in rows:
            if r["sections"] < 3: continue
            cands = [d for d in ARCH.iterdir() if d.is_dir() and norm(d.name) and norm(d.name) in norm(r["name"])]
            if not cands: continue
            d = cands[0]
            vs = sorted(d.glob("v_2026*.md"))
            vs = [v for v in vs if len(v.read_text(encoding="utf-8", errors="replace")) > 0]
            if not vs: continue
            b = row(vs[-1]); hit += 1
            sa, sb = r["sec_map"], b["sec_map"]
            oa = [t for t in sa if t not in sb]; ob = [t for t in sb if t not in sa]
            com = [t for t in sa if t in sb]
            dif = [t for t in com if sa[t] != sb[t]]
            print("   · %-40s 本地 %6d 字 ／ 档案 %6d 字 ｜ 节 %d／%d ｜ 仅本地 %d ｜ 仅档案 %d ｜ 同节异长 %d" % (
                r["name"][:40], r["chars"], b["chars"], len(sa), len(sb), len(oa), len(ob), len(dif)))
        print("   ⇒ 可比对 %d 件" % hit)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
