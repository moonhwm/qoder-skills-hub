#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_bank.py 样本库八项回核（seat-naming-ops）

判据来源：references/canon-pool.md §1 第 6 条（分解核对，逐字 grep 整串属错误判据）。
八项：①可复现（重跑逐字节一致）②全量过闸（0 FAIL）③唯一性（三元组+全名）
     ④引文分解核对（篇目/引文段/注文逐字见于 canon-pool.md）
     ⑤典池一致性（种子 62 条全过分解核对+表格行数=62）⑥声调一致性（拼音尾码=tones=tone_pattern）
     ⑦碰撞拦截（姓+名组合全量过 collision-blocklist.json，命中即 FAIL；表缺失或空表即 FAIL 守卫）
     ⑧定读对账（reading-registry.json 机读定读表 ↔ canon-seed/bank 拼音逐条一致）

用法: python3 scripts/verify_bank.py [--bank ../assets/sample-bank-1000.jsonl]
退出码: 0=八项全 PASS；1=存在 FAIL；2=参数/文件错误。
"""
import sys, os, json, re, subprocess, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from name_audit import parse_pinyin, audit  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pool_table_text(pool_text):
    """§2 典池表切片（章次闸/引文闸比对面；B19 收窄在卷）。fail-closed：失配即抛错（C21——回退全文档属静默放宽，禁）"""
    m = re.search(r"## §2 典池.*?(?=\n## )", pool_text, re.S)
    if not m:
        raise RuntimeError("canon-pool.md §2 典池表切片失败：闸面不可用，禁止回退全文档")
    return m.group(0)


def verse_corpus(tbl_text):
    """§2 表原文列语料（注文夹带启发式闸比对用）：取每行「原文」列之后的诗句段"""
    corpus = []
    for line in tbl_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and cells[0].strip().isdigit():
            corpus.append(cells[5])  # 原文列
    return "\n".join(corpus)


def chapters_quote_violations(seed, tbl_text):
    """章次引文闸：chapters 中「」段须逐字见于 §2 表（铁律8 机检化）"""
    return [(e["ming"], seg[:18]) for e in seed
            for seg in re.findall(r"「([^「」]*)」", e.get("chapters", "")) if seg not in tbl_text]


def chapters_smuggle_violations(seed, corpus, poem_names):
    """注文夹带启发式闸：chapters 去「」注文中 ≥4 字连续成句见于原文列即违（B20/C20 盲区机检化）；
    篇目名豁免（篇目与原文同文者非夹带，如 昊天有成命——成命条在卷）"""
    viol = []
    for e in seed:
        note = re.sub(r"「[^「」]*」", "", e.get("chapters", ""))
        for run in re.findall(r"[\u4e00-\u9fff]{4,}", note):
            if any(run in pn or pn in run for pn in poem_names):
                continue  # 篇目名豁免
            hit = next((run[i:i + 4] for i in range(len(run) - 3) if run[i:i + 4] in corpus), None)
            if hit:
                viol.append((e["ming"], hit))
    return viol


def decompose(source_verse):
    """'篇目A「q1」「q2」／篇目B「q3」（注）' -> (poems[], quotes[], note_or_None)
    支持单篇目多引文段；跨篇用 ／ 分段。"""
    note = None
    m = re.search(r"（([^（）]*)）$", source_verse)
    body = source_verse[: m.start()] if m else source_verse
    if m:
        note = m.group(1)
    poems, quotes = [], []
    for seg in body.split("／"):
        seg = seg.strip()
        if "「" not in seg:
            return None
        poem = seg.split("「", 1)[0].strip()
        qs = re.findall(r"「([^「」]*)」", seg)
        if not poem or not qs:
            return None
        poems.append(poem)
        quotes.extend(qs)
    return poems, quotes, note


def check_citation(source_verse, pool_text):
    d = decompose(source_verse)
    if d is None:
        return False, "格式不可分解"
    poems, quotes, note = d
    for p in poems:
        if p not in pool_text:
            return False, "篇目 MISS: %s" % p
    for q in quotes:
        if q not in pool_text:
            return False, "引文 MISS: %s" % q
    if note and note not in pool_text:
        return False, "注文 MISS: %s" % note
    return True, ""


def main():
    bank = sys.argv[sys.argv.index("--bank") + 1] if "--bank" in sys.argv else os.path.join(ROOT, "assets", "sample-bank-1000.jsonl")
    canon = os.path.join(ROOT, "assets", "canon-seed.json")
    surnames = os.path.join(ROOT, "assets", "surnames-65.json")
    pool_text = open(os.path.join(ROOT, "references", "canon-pool.md"), encoding="utf-8").read()
    rows = [json.loads(l) for l in open(bank, encoding="utf-8")]
    seed = json.load(open(canon, encoding="utf-8"))
    results = []

    # ①可复现
    tmp = os.path.join(tempfile.mkdtemp(), "rerun.jsonl")
    want = open(bank, "rb").read()
    same, mode = False, "?"
    for extra, mname in ([], "stride"), (["--orthogonal"], "orthogonal"):
        rc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "name_forge.py"),
                             "--canon", canon, "--surnames", surnames, "--n", str(len(rows)),
                             "--out", tmp] + extra, capture_output=True).returncode
        if rc == 0 and open(tmp, "rb").read() == want:
            same, mode = True, mname
            break
    results.append(("①可复现", same, "逐字节一致=%s（复现模式=%s；stride/orthogonal 双模式自证）" % (same, mode)))

    # ②全量过闸 + NOTE 编号合法性（幽灵规则闸：notes 只允许 N1-N5 已定义编号）
    fails = [r for r in rows if audit(r["full_name"], parse_pinyin(r["pinyin"]),
                                      surname_len=len(r["surname"]))[0] == "FAIL"]
    ghost = [(r["id"], n) for r in rows for n in r.get("notes", []) if not re.match(r"^(?:N[1-5]|W[1-3]) ", n)]
    results.append(("②全量过闸", len(fails) == 0 and len(ghost) == 0,
                    "FAIL 行数=%d / %d；幽灵 NOTE=%d %s" % (len(fails), len(rows), len(ghost), ghost[:3])))

    # ③唯一性
    t = len({(r["surname"], r["ming"], r["zi"]) for r in rows})
    f = len({r["full_name"] for r in rows})
    results.append(("③唯一性", t == len(rows) and f == len(rows), "三元组唯一=%d 全名唯一=%d / %d" % (t, f, len(rows))))

    # ④引文分解核对（全量）
    tbl_text4 = pool_table_text(pool_text)  # Y3：比对面=§2 表（§1.6 判据本即「原文列」，收窄更忠实）
    bad = [(r["id"], why) for r in rows for ok, why in [check_citation(r["source_verse"], tbl_text4)] if not ok]
    results.append(("④引文分解核对", len(bad) == 0, "MISS=%d / %d %s" % (len(bad), len(rows), bad[:3])))

    # ⑤典池一致性
    bad5 = [(e["ming"], why) for e in seed for ok, why in [check_citation(e["source_verse"], tbl_text4)] if not ok]
    tbl_rows = len(re.findall(r"^\| \d+ \|", tbl_text4, re.M))  # 切片内计数（C21）
    no_ch = [e["ming"] for e in seed if "chapters" not in e]
    tbl_text = pool_table_text(pool_text)
    ch_quote = chapters_quote_violations(seed, tbl_text)
    poem_names = set()
    for line in tbl_text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 5 and cells[0].strip().isdigit():
                for pn in cells[4].split("／"):
                    if pn.strip():
                        poem_names.add(pn.strip())
    ch_smug = chapters_smuggle_violations(seed, verse_corpus(tbl_text), poem_names)
    results.append(("⑤典池一致性", len(bad5) == 0 and tbl_rows == len(seed) and len(no_ch) == 0 and len(ch_quote) == 0 and len(ch_smug) == 0,
                    "种子 MISS=%s 表格行=%d / 种子=%d 章次字段缺失=%s 池外引文=%s 注文夹带=%s" % (bad5[:3], tbl_rows, len(seed), no_ch[:3], ch_quote[:3], ch_smug[:3])))

    # ⑥声调一致性
    bad6 = [r["id"] for r in rows
            if [int(s[-1]) for s in r["pinyin"].split()] != r["tones"]
            or "-".join(map(str, r["tones"])) != r["tone_pattern"]]
    results.append(("⑥声调一致性", len(bad6) == 0, "不一致=%d %s" % (len(bad6), bad6[:5])))

    # ⑦碰撞拦截（守卫：表缺失或空表即 FAIL——防拦截层被删仍全绿）
    bl_path = os.path.join(ROOT, "assets", "collision-blocklist.json")
    blocked = set()
    bl_ok = os.path.exists(bl_path)
    if bl_ok:
        blocked = {(b["surname"], b["ming"]) for b in json.load(open(bl_path, encoding="utf-8"))["blocked"]}
    bl_ok = bl_ok and len(blocked) > 0
    hits7 = [(r["id"], r["full_name"]) for r in rows if (r["surname"], r["ming"]) in blocked]
    results.append(("⑦碰撞拦截", bl_ok and len(hits7) == 0,
                    "拦截表=%d 条(守卫=%s) 命中=%d %s" % (len(blocked), "OK" if bl_ok else "表缺失/空表", len(hits7), hits7[:5])))

    # ⑧定读对账（机读定读表 ↔ canon-seed/bank/姓氏池/注文 逐条一致；A8/B8 指摘补全姓氏层）
    rr_path = os.path.join(ROOT, "assets", "reading-registry.json")
    bad8 = []
    reg_n = 0
    if os.path.exists(rr_path):
        reg = json.load(open(rr_path, encoding="utf-8"))["readings"]
        reg_n = len(reg)
        mings = {e["ming"]: e["ming_pinyin"] for e in seed}
        zis = {e["zi"]: e["zi_pinyin"] for e in seed}
        sur = {s["surname"]: s["pinyin"] for s in json.load(open(surnames, encoding="utf-8"))}
        cpf = os.path.join(ROOT, "assets", "surnames-compound.json")
        if os.path.exists(cpf):
            sur.update({s["surname"]: s["pinyin"] for s in json.load(open(cpf, encoding="utf-8"))})
        seed_verses = {e["ming"]: e["source_verse"] for e in seed}
        covered8 = 0
        pre8 = []
        for it in reg:
            ctxs = [c.strip() for c in it["context"].split("/")]
            for c in ctxs:
                if c == "姓":  # 姓氏层：与姓氏池 pinyin 对账；池未收录之姓=扩池预备条目（不计失，单列）
                    pin = sur.get(it["char"])
                    if pin is None:
                        pre8.append(it["char"])
                    elif it["reading"] not in pin.split():
                        bad8.append(("姓", it["char"], it["reading"], pin))
                    else:
                        covered8 += 1
                    continue
                if c in sur:  # 复姓层：整条与复姓池 pinyin 对账
                    if it["reading"] not in sur[c].split():
                        bad8.append(("复姓", c, it["reading"], sur[c]))
                    else:
                        covered8 += 1
                    continue
                if c.endswith("条字注"):  # 注文层：与 canon-seed source_verse 注文对账（带调号拼音归一化后比对）
                    ming_key = c.replace("条字注", "")
                    verse = seed_verses.get(ming_key, "")
                    dia = str.maketrans("āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ", "aaaaeeeeiiiioooouuuuvvvv")
                    vnorm = verse.translate(dia)
                    base = it["reading"].rstrip("01234")
                    anchored = re.search(r"(?:读|音) ?%s(?![a-z])" % re.escape(base), vnorm) is not None
                    if it["reading"] in verse or anchored:
                        covered8 += 1
                    else:
                        bad8.append(("注文", c, it["reading"], verse[:40]))
                    continue
                pin = mings.get(c) or (zis.get(c) if c in zis else None)
                if pin is None:
                    bad8.append(("语境缺失", c, it["reading"], ""))
                elif it["char"] in c and it["reading"] not in pin.split():
                    bad8.append((c, it["char"], it["reading"], pin))
                else:
                    covered8 += 1
        # bank 行对账：registry 语境词出现于行的名/字时，其定读须见于该行拼音
        for it in reg:
            ctxs = [c.strip() for c in it["context"].split("/")]
            for c in ctxs:
                if c in zis and c not in mings:
                    continue  # 字层语境：bank 行拼音不含字，已在 canon-seed 段核对
                for r in rows:
                    if r["ming"] == c and it["reading"] not in r["pinyin"].split():
                        bad8.append(("bank#%d" % r["id"], c, it["reading"], r["pinyin"]))
    else:
        bad8.append(("registry", "缺失", "", ""))
    results.append(("⑧定读对账", len(bad8) == 0, "登记=%d 条 覆盖语境=%d 预备姓=%s 不一致=%d %s" % (
        reg_n, covered8 if os.path.exists(rr_path) else 0, pre8 if os.path.exists(rr_path) else [], len(bad8), bad8[:3])))

    # ⑨正交性度量（信息项，不卡闸——A23/B23/C23 合指「充分正交」量化佐证）
    try:
        from collections import Counter
        import math as _m, statistics as _st
        cm9 = Counter(r["ming"] for r in rows); cs9 = Counter(r["surname"] for r in rows)
        obs9 = Counter((r["surname"], r["ming"]) for r in rows)
        tot9 = len(rows)
        chi2, df9 = 0.0, (len(cs9) - 1) * (len(cm9) - 1)
        for s in cs9:
            for m in cm9:
                exp = cs9[s] * cm9[m] / tot9
                if exp > 0:
                    chi2 += (obs9.get((s, m), 0) - exp) ** 2 / exp
        k9 = min(len(cs9), len(cm9))
        cramers_v = _m.sqrt(chi2 / (tot9 * (k9 - 1))) if tot9 > 0 and k9 > 1 else 0.0
        results.append(("⑨正交性(信息)", True,
                        "名边际σ=%.2f 姓边际σ=%.2f χ²=%.0f(df=%d) Cramér's V=%.3f（二元网格 V→0 趋独立）" % (
                            _st.pstdev(cm9.values()), _st.pstdev(cs9.values()), chi2, df9, cramers_v)))
    except Exception as e:
        results.append(("⑨正交性(信息)", True, "度量跳过(%s)" % e))

    allpass = all(ok for _, ok, _ in results)
    for name, ok, detail in results:
        print("%s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    print("VERDICT: %s" % ("PASS" if allpass else "FAIL"))
    return 0 if allpass else 1


if __name__ == "__main__":
    sys.exit(main())
