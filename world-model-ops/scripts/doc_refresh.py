# -*- coding: utf-8 -*-
"""文档档案维护器：①扫 WPS 网盘本地找新 link_id（本地可达）②全量复拉已档文档并检出变更
用法：python doc_refresh.py [--scan-only] [--budget 300]
（引号一律用「」）
"""
import argparse, hashlib, json, pathlib, re, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HOME = pathlib.Path.home()
WPS = HOME/"WPSDrive"/"29969771"/"WPS云盘"
SEAT = WPS/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
ARCH = SEAT/"archive"/"docs"
CLI = HOME/".kimi-work"/"bin"/"kdocs-cli.exe"
IDX = ARCH/"index.json"; QUEUE = ARCH/"docs_list.json"
TEXTISH = {".md", ".otl", ".txt", ".json", ".jsonl", ".py", ".cs", ".mjs", ".html", ".csv", ".wpsonline", ".yml", ".yaml"}
SKIPDIR = {".git", "node_modules", "__pycache__", ".venv", "venv"}

def sha(t, n=24): return hashlib.sha3_512(t.encode("utf-8")).hexdigest()[:n]
def sections(md):
    out, cur, buf = [], "(前言)", []
    for line in md.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if m:
            out.append((cur, "\n".join(buf).strip())); cur = m.group(2).strip(); buf = [line]
        else: buf.append(line)
    out.append((cur, "\n".join(buf).strip()))
    return [(t, b) for t, b in out if b.strip()]

ap = argparse.ArgumentParser()
ap.add_argument("--scan-only", action="store_true")
ap.add_argument("--budget", type=float, default=300.0)
a = ap.parse_args()

# ── ① 扫 WPS 网盘本地（找新 link_id ＋ 清点本地文档）──
t0 = time.time()
manifest = json.loads(IDX.read_text(encoding="utf-8-sig")) if IDX.exists() else {}
known = {v.get("link_id") for k, v in manifest.items() if not k.startswith("_")}
known |= set(json.loads(QUEUE.read_text(encoding="utf-8-sig"))["ids"]) if QUEUE.exists() else set()
found, files, skipped = {}, 0, 0
pat = re.compile(r"kdocs\.cn/l/([A-Za-z0-9]{8,24})")
for p in WPS.rglob("*"):
    try:
        if any(d in SKIPDIR for d in p.parts): continue
        if not p.is_file(): continue
        if p.suffix.lower() not in TEXTISH: continue
        if p.stat().st_size > 3_000_000: skipped += 1; continue
        files += 1
        t = p.read_text(encoding="utf-8", errors="ignore")
        for m in pat.finditer(t):
            i = m.group(1)
            if i not in found: found[i] = p.name
    except Exception:
        continue
newids = {k: v for k, v in found.items() if k not in known}
print("  ═══ ① 扫 WPS 网盘本地（%s）═══" % WPS.name)
print("   扫描 %.1f s ｜ 文本文件 %d（跳过大文件 %d）｜ 命中 link_id %d ｜ ★新发现 %d" % (
    time.time()-t0, files, skipped, len(found), len(newids)))
for k, v in list(newids.items())[:20]:
    print("     ＋ %-14s ← %s" % (k, v[:52]))

if newids:
    q = json.loads(QUEUE.read_text(encoding="utf-8-sig")) if QUEUE.exists() else {"ids": []}
    q["ids"] = list(newids.keys()) + [x for x in q["ids"] if x not in newids]
    q["note"] = "按频次排序之待拉队列；本轮由扫网盘新增 %d 个" % len(newids)
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   ★ 已把 %d 个新 id 入队" % len(newids))

if a.scan_only:
    sys.exit(0)

# ── ② 全量复拉已档文档 ──
def pull(link_id, to=150):
    try:
        pr = subprocess.run([str(CLI), "drive", "read-file", "--args", json.dumps({"link_id": link_id})],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=to)
    except subprocess.TimeoutExpired:
        return None, {"err": "超时"}
    out = (pr.stdout or "") + (pr.stderr or "")
    i = out.find("{")
    if i < 0: return None, {"err": "无 JSON"}
    try:
        j, _ = json.JSONDecoder().raw_decode(out[i:])
    except Exception as e:
        return None, {"err": str(e)[:60]}
    d = j.get("data") or {}
    code = j.get("code")
    # ★按类型分流（2026-10-12 立）：read-file 失败时回退 otl block-query；并分类失败
    if code not in (0, None) or (not d and j.get("message")):
        msg = str(j.get("message"))[:70]
        if code == 400001 or "Unsupported file type" in msg:
            return None, {"err": "★类型不支持（上游 %s）：%s" % (code, msg)}
        alt = _otl_read(link_id)
        if alt is not None:
            return alt, {"code": 0, "name": None, "via": "otl.block-query"}
        return None, {"err": "★上游 %s：%s" % (code, msg)}
    return d.get("content", ""), {"code": code, "name": d.get("name")}


def _otl_read(link_id, to=150):
    """回退通道：kdocs-cli otl block-query（params.blockIds=[doc]）⇒ 尽力抽正文"""
    try:
        pr = subprocess.run([str(CLI), "otl", "block-query", "--args",
                             json.dumps({"link_id": link_id, "params": {"blockIds": ["doc"]}})],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=to)
    except Exception:
        return None
    out = (pr.stdout or "") + (pr.stderr or "")
    i = out.find("{")
    if i < 0: return None
    try:
        j, _ = json.JSONDecoder().raw_decode(out[i:])
    except Exception:
        return None
    if j.get("code") not in (0, None): return None
    d = j.get("data") or {}
    # 尽力抽取：优先 blocks 之文本，其次 content，再次整段 JSON（保底不丢信息）
    txt = d.get("content")
    if not txt and isinstance(d.get("blocks"), list):
        parts = []
        for b in d["blocks"]:
            for k in ("text", "content", "markdown"):
                v = (b or {}).get(k)
                if isinstance(v, str): parts.append(v); break
        txt = "\n".join(parts) if parts else None
    if not txt:
        txt = json.dumps(d, ensure_ascii=False)[:200000]
    return txt
    # ★上游错误码闸（2026-10-12 立）：非 0／无 data ⇒ 报"失败（上游）"，★绝不当"内容为空"
    if code not in (0, None) or (not d and j.get("message")):
        return None, {"err": "★上游 %s：%s" % (code, str(j.get("message"))[:60])}
    return d.get("content", ""), {"code": code, "name": d.get("name")}

print("\n  ═══ ② 全量复拉（%d 件）═══" % len([k for k in manifest if not k.startswith("_")]))
t1 = time.time(); chg = same = fail = 0; skip_type = 0
for key, v in list(manifest.items()):
    if key.startswith("_"): continue
    if time.time()-t1 > a.budget:
        print("   · 预算到，余件留待下轮"); break
    c, meta = pull(v["link_id"])
    if c is None:
        # ★2026-10-12 自纠：把"类型不支持"（上游 400001；.zip／.json 等不可直读）★单列一类
        #   ⇒ 它们是"永久不可读"，非"失败"；单列后可免每轮重复无意义尝试，且报告更如实（-1286 之判）
        _e = str(meta.get("err") or "")
        if "类型不支持" in _e or "Unsupported" in _e or "400001" in _e:
            skip_type += 1; print("   · %-10s ★跳过（类型不支持，永久不可读）⇒ 不计失败" % key); continue
        fail += 1; print("   ✗ %-10s %s" % (key, meta.get("err"))); continue
    # ★空内容闸（2026-10-12 立；因 1319/1321 批曾写入 0 字空档而工器报"变更"）
    if not c or not c.strip():
        fail += 1; print("   ✗ %-10s ★空内容（拉取返回 0 字）⇒ 不计变更、不写版本" % key); continue
    h = sha(c); secs = {t: sha(b) for t, b in sections(c)}
    prev = v["history"][-1]
    if h == prev["hash"]:
        same += 1; continue
    old = {}
    try: old = json.loads((ARCH/key/("sections_%s.json" % prev["ver"])).read_text(encoding="utf-8-sig"))
    except Exception: pass
    d = {"added": [t for t in secs if t not in old], "removed": [t for t in old if t not in secs],
         "changed": [t for t in secs if t in old and old[t] != secs[t]]}
    ver = time.strftime("%Y%m%d_%H%M")
    (ARCH/key/("v_%s.md" % ver)).write_text(c, encoding="utf-8", newline="\n")
    (ARCH/key/("sections_%s.json" % ver)).write_text(json.dumps(secs, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    v["history"].append({"ver": ver, "ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "hash": h,
                         "chars": len(c), "lines": len(c.splitlines()), "sections": len(secs),
                         "file_id": meta.get("file_id"), "drive_id": meta.get("drive_id"),
                         "changed": True, "diff": d})
    v["latest"] = {"hash": h, "chars": len(c), "sections": len(secs), "ver": ver}
    chg += 1
    print("   ★ %-10s %-40s %+d 字 ｜ 节级 新增%d/删除%d/变动%d" % (
        key, (v.get("title") or "")[:40], len(c)-prev["chars"], len(d["added"]), len(d["removed"]), len(d["changed"])))
    # ★虚警自动标注（口径见 DF-OPS-…-12／-13：本工具存「节计数」而非「节键」）
    _a, _r, _ch = len(d["added"]), len(d["removed"]), len(d["changed"])
    if _a and _r and _a >= 5 and abs(_a - _r) <= max(2, int(0.05*max(_a, _r))) and _ch == 0:
        print("        ★ 判：新增≈删除（%d vs %d）且变动 0 ⇒ 疑为「节键重排」之虚警，实质变动约 0（勿直读为换了 %d 节）" % (_a, _r, _a))
    for t in (d["changed"] + d["added"] + d["removed"])[:3]:
        print("        ～ " + t[:66])
manifest["_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S+0800")
IDX.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\n  ═══ 汇总：复拉 %.1f s ｜ 变更 %d ｜ 未变 %d ｜ ★跳过(类型不支持) %d ｜ 失败 %d ｜ 档案 %d 件 ═══" % (
    time.time()-t1, chg, same, skip_type, fail, len([k for k in manifest if not k.startswith("_")])))
if chg:
    nd = SEAT/"outbox"/"notify"; nd.mkdir(parents=True, exist_ok=True)
    nf = nd/("doc_update_%s.md" % time.strftime("%Y%m%d_%H%M"))
    nf.write_text("# 文档更新通知（%s）\n\n本轮检出 **%d** 件变更（详见 archive/docs/index.json）\n" % (
        time.strftime("%Y-%m-%d %H:%M"), chg), encoding="utf-8", newline="\n")
    print("  ★ 已写通知：" + nf.name)
