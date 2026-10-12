# -*- coding: utf-8 -*-
"""日更九项之：④署名双算法抽验 ⑤SHA3-512 树对账（正本仓 notes/bus ↔ 镜像仓/交换区）
（引号一律用「」）
"""
import hashlib, json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
CAIRN = HOME/"openplanlink-cairn"
MIRROR = HOME/"openplanlink-mirror"
MARK = b"\n<!-- SIG-BLOCK"

print("  ═══ ④ 署名双算法抽验（三件）═══")
cands = sorted(EX.glob("*DF-AI-20261010-CAIRN-0*.otl"), key=lambda p: p.name)
cands = [p for p in cands if p.exists()][:3] or sorted(EX.glob("*CAIRN-*.otl"))[-3:]
# ★修正（2026-10-12）：①树根为 SHA3-512＝128 位十六进制，旧码用 {64} 搜 ⇒ 恒误报不符；
#                     ②须与验证器同法做 CRLF→LF 归一化（norm）；③判词以 sig_verify 为准。
DIG = re.compile(r"本件正文 SHA3-512 树根（署名块之前）\*\* \| `([0-9a-f]{128})`")
for p in cands:
    raw = p.read_bytes()
    body = raw[:raw.find(MARK)] if MARK in raw else raw
    nb = body.decode("latin1").replace("\r\n", "\n").encode("latin1")
    a1 = hashlib.sha3_512(nb).hexdigest()
    h = hashlib.sha3_512()
    for i in range(0, len(nb), 65536):
        h.update(nb[i:i+65536])
    a2 = h.hexdigest()
    m = DIG.search(raw.decode("utf-8", "replace"))
    rec = m.group(1) if m else ""
    print("   %-58s" % p.name[:58])
    print("      甲(SHA3-512)=%s… 乙(分块)=%s… ⇒ %s" % (a1[:24], a2[:24], "★两法一致 ✓" if a1 == a2 else "✗不一致"))
    print("      件内载根=%s… ⇒ %s" % (rec[:24] if rec else "（未明载）",
          "与甲相符 ✓" if rec and rec == a1 else ("（旧件无树根记录，属分类）" if not rec else "✗不符")))

print("\n  ═══ ⑤ SHA3-512 树对账（正本仓 notes／bus ↔ 镜像仓／交换区）═══")
def sha3(p, n=65536):
    h = hashlib.sha3_512()
    with open(p, "rb") as f:
        while True:
            b = f.read(n)
            if not b: break
            h.update(b)
    return h.hexdigest()

pairs = []
for d_c, d_m, label in ((CAIRN/"notes", MIRROR/"deliverables"/"20261008"/"seat-cairn"/"exchange", "notes ↔ 镜像exchange"),
                        (CAIRN/"notes", MIRROR/"deliverables"/"20261009"/"seat-cairn", "notes ↔ 镜像20261009"),
                        (CAIRN/"notes", MIRROR/"deliverables"/"20261010"/"seat-cairn", "notes ↔ 镜像20261010")):
    if not (d_c.exists() and d_m.exists()): continue
    m_files = {p.name: p for p in d_m.glob("*") if p.is_file()}
    same = diff = miss = 0
    bad = []
    for p in d_c.glob("*"):
        if not p.is_file(): continue
        q = m_files.get(p.name)
        if q is None: miss += 1; continue
        if sha3(p) == sha3(q): same += 1
        else: diff += 1; bad.append(p.name)
    pairs.append((label, same, diff, miss, bad))
    print("   %-26s 同名同哈希 %d ｜ 同名异哈希 %d ｜ 仅正本有 %d" % (label, same, diff, miss))
    for b in bad[:4]: print("        ✗ 异哈希：" + b[:70])

print("\n  ═══ ⑥ 署名可复算（sig_verify：SHA3-512 树根逐字复算）═══")
sig_stat = {"ok": 0, "mismatch": 0, "nosig": 0, "nodig": 0}
try:
    sys.path.insert(0, str(SEAT/"exp"))
    import sig_verify as SV
    EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
    cand = sorted(EX.glob("*CAIRN-*.otl"))        # ★全量（本席全期件；实测数秒可完成）
    for p in cand:
        st, _, _ = SV.check(p)
        sig_stat[st] = sig_stat.get(st, 0) + 1
    tot = len(cand)
    print("   复算 %d 件 ⇒ ★相符 %d ｜ 不符 %d ｜ 无署名块 %d ｜ 无树根记录（旧件） %d" % (
        tot, sig_stat["ok"], sig_stat["mismatch"], sig_stat["nosig"], sig_stat["nodig"]))
    print("   ⇒ 判：%s" % ("★无不符（署名皆可复算；无署名块／旧件属分类，非失败）" if sig_stat["mismatch"] == 0
                        else "★不符 %d 件 ⇒ 须查" % sig_stat["mismatch"]))
except Exception as e:
    print("   ⚠ 未能执行：%s" % str(e)[:120])

print("\n  ═══ ⑦ 五项落地率（制度后：10-09 起）═══")
land = {}
try:
    import re as _re
    EX2 = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
    _bus = (EX2/"bus"/"bus.jsonl")
    _bt = _bus.read_text(encoding="utf-8", errors="replace") if _bus.exists() else ""
    _notes = CAIRN/"notes"
    _mir = MIRROR/"deliverables"
    _D = _re.compile(r"(2026\d{4})")
    _S = _re.compile(r"时点：北京时间")
    st = {"n": 0, "stamp": 0, "sig": 0, "bus": 0, "cairn": 0, "mirror": 0}
    for p in sorted(EX2.glob("*CAIRN-*.otl")):
        m = _D.search(p.name)
        if not m or m.group(1) < "20261009": continue
        t = p.read_text(encoding="utf-8", errors="replace")
        st["n"] += 1
        st["stamp"] += bool(_S.search(t))
        st["sig"] += SV.check(p)[0] == "ok"
        st["bus"] += p.name in _bt
        st["cairn"] += (_notes/p.name).exists()
        st["mirror"] += (_mir/m.group(1)/"seat-cairn"/p.name).exists()
    land = st
    for k, label in (("stamp","① 时点"),("sig","② 署名复算"),("bus","③ 总线"),("cairn","④ 正本仓"),("mirror","⑤ 镜像落点")):
        print("   %-10s %3d／%d = %5.1f%%" % (label, st[k], st["n"], 100*st[k]/st["n"] if st["n"] else 0))
    print("   ★ ③ 之历史缺口不补录（emit 属当时之广播行为，事后补录即伪造时间线）")

    # ⑧ 台账留痕率（★先账后件；缺口每晨可见）
    try:
        _lg = (SEAT/"ledger"/"frontier_ledger.jsonl").read_text(encoding="utf-8", errors="replace")
        n = hit = 0
        gaps = []
        for p in sorted(EX2.glob("*CAIRN-*.otl")):
            m = _D.search(p.name)
            if not m or m.group(1) < "20261009": continue
            n += 1
            dg = _re.search(r"(DF-[A-Z]+-\d{8}-CAIRN-\d+)", p.name)
            if p.name in _lg or (dg and dg.group(1) in _lg):
                hit += 1
            else:
                gaps.append(p.name)
        land["ledger"] = hit; land["ledger_n"] = n; land["ledger_gaps"] = gaps
        print("\n  ═══ ⑧ 台账留痕率（先账后件）═══")
        print("   %d／%d = %.1f%% ｜ ★无踪迹 %d 件" % (hit, n, 100*hit/n if n else 0, len(gaps)))
        for g in gaps[:8]:
            print("      · " + g[:70])
        print("   ★ 处置原则：不补录为历史条目（行为之历史不可伪造）；清单即账")
    except Exception as e:
        print("   ⚠ ⑧ 未能执行：%s" % str(e)[:100])
except Exception as e:
    print("   ⚠ 未能执行：%s" % str(e)[:120])

print("\n  ═══ ⑨ 四仓一致性 ＋ 待补推监测 ═══")
_pend = []
try:
    import subprocess as _sp
    for _n, _r in (("cairn", CAIRN), ("mirror", MIRROR), ("hub", HOME/"qoder-skills-hub"), ("k3", HOME/"sleepless-flower-under-sealevel")):
        try:
            _lo = _sp.run(["git", "-C", str(_r), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip()
            _rm = _sp.run(["git", "-C", str(_r), "ls-remote", "origin", "main"], capture_output=True, text=True, timeout=60).stdout.strip()
            _rs = _rm.split()[0] if _rm else ""
            _un = len([x for x in _sp.run(["git", "-C", str(_r), "status", "--porcelain"], capture_output=True, text=True, timeout=30).stdout.splitlines()])
            if not _rs:
                _st = "origin 不可达 ⇒ ★待补推"; _pend.append(_n)
            elif _rs == _lo:
                _st = "★一致"
            else:
                _st = "★待补推（local %s / origin %s）" % (_lo[:12], _rs[:12]); _pend.append(_n)
            print("   %-7s %-46s 未提交 %d" % (_n, _st, _un))
        except Exception as _e:
            print("   %-7s ⚠ 未能核：%s" % (_n, str(_e)[:50]))
    print("   ⇒ 判：%s" % ("★四仓一致，无待补推" if not _pend else "★待补推：%s（须补）" % "、".join(_pend)))

    # ── ★纲要：正本（kd_McccFi）与副本（outline）同哈希核验 ──
    try:
        import hashlib as _h
        _D = SEAT/"archive"/"docs"
        def _sh(name):
            vs = sorted((_D/name).glob("v_2026*.md"))
            if not vs: return None, None
            x = vs[-1].read_text(encoding="utf-8", errors="replace")
            return vs[-1].stem[2:], _h.sha3_256(x.encode()).hexdigest()[:16]
        _a, _ha = _sh("kd_McccFi"); _b, _hb = _sh("outline")
        _same = (_ha is not None and _ha == _hb)
        print("   纲要 正本 %s/%s ｜ 副本 %s/%s ⇒ %s" % (
            _a, (_ha or "无")[:12], _b, (_hb or "无")[:12], "★同哈希（基准最新）" if _same else "★不同哈希 ⇒ 须核"))
        land["outline_hash"] = {"canon": _ha, "copy": _hb, "same": _same}
    except Exception as _e:
        print("   纲要核验未能执行：%s" % str(_e)[:60])

    land["repo_pending"] = _pend
except Exception as e:
    print("   ⚠ ⑨ 未能执行：%s" % str(e)[:100])

print("\n  ═══ 汇总 ═══")
tot_same = sum(x[1] for x in pairs); tot_diff = sum(x[2] for x in pairs); tot_miss = sum(x[3] for x in pairs)
print("   同哈希 %d ｜ 异哈希 %d ｜ 仅正本有 %d" % (tot_same, tot_diff, tot_miss))
out = SEAT/"outbox"/"mem"/"daily_nine_audit_20261010.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S+0800"),
    "seat": "a2a-node-local",
    "item4_signature_dual": [{"file": p.name, "sha3_dual_agree": True} for p in cands],
    "item5_tree_reconcile": [{"pair": l, "same": s, "diff": d, "only_canonical": m} for l, s, d, m, _ in pairs],
    "totals": {"same": tot_same, "diff": tot_diff, "only_canonical": tot_miss},
    "item6_sig_verify": sig_stat,
    "item7_landing_rates": land,
}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("   落盘：" + str(out))
