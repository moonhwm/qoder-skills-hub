#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_regression.py 回归单测（seat-naming-ops 发版前自检）

锚定历届外池判后修复（R8-R10 在卷）：复姓判据重映射、两字名退化守卫、
碰撞拦截守卫、W 注记格式、⑧覆盖口径、文档陈旧 grep。
退出码: 0=全过；1=存在失败。
"""
import sys, os, json, subprocess, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from name_audit import parse_pinyin, audit, detect_surname_len, POLY_WARN  # noqa: E402

CASES = [  # (name, pinyin, surname_len, expect_verdict, must_in, must_not_in)
    ("皇甫景行", "huang2 fu3 jing3 xing2", 2, "FAIL", ["R5a"], []),
    ("令狐厚德", "ling2 hu2 hou4 de2", 2, "FAIL", ["R4"], []),
    ("公孙松茂", "gong1 sun1 song1 mao4", 2, "FAIL", ["R4"], []),
    ("欧阳如琢", "ou1 yang2 ru2 zhuo2", 2, "PASS", [], ["R3", "R4"]),
    ("夏侯云汉", "xia4 hou2 yun2 han4", 2, "PASS", [], ["R5a"]),
    ("李白", "li3 bai2", 1, "PASS", [], ["N4", "R3"]),          # 两字名退化守卫
    ("李理", "li3 li3", 1, "FAIL", ["R1", "R2", "R4", "R5a"], ["R3", "N4"]),
    ("李伟", "li3 wei3", 1, "FAIL", ["R1", "R5a"], []),          # A4 修复锚：两字名 R5a
    ("李想", "li3 xiang3", 1, "FAIL", ["R5a"], []),
    ("梁思成", "liang2 si1 cheng2", 1, "PASS", [], []),          # 音韵无罪，碰撞层拦截（下查）
]


def main():
    bad = []
    for nm, py, sl, ev, mins, mnot in CASES:
        v, fails, notes = audit(nm, parse_pinyin(py), surname_len=sl)
        blob = " ".join(fails + notes)
        if v != ev:
            bad.append((nm, "判级", ev, v))
        for k in mins:
            if not any(x.startswith(k) for x in fails + notes):
                bad.append((nm, "应中未中", k, blob[:80]))
        for k in mnot:
            if any(x.startswith(k) for x in fails + notes):
                bad.append((nm, "不应中而中", k, blob[:80]))

    # 复姓自动识别
    if detect_surname_len("皇甫景行") != 2 or detect_surname_len("谢如琢") != 1:
        bad.append(("detect_surname_len", "自动识别失效", "", ""))
    # POLY_WARN 外置精确断言（防内建回退空转，C11 指摘）：加载集须与文件全等
    pw_file = os.path.join(ROOT, "assets", "polyphone-warn.json")
    if not os.path.exists(pw_file):
        bad.append(("POLY_WARN", "外置文件缺失", "", ""))
    else:
        want = set(json.load(open(pw_file, encoding="utf-8"))["chars"])
        if POLY_WARN != want:
            bad.append(("POLY_WARN", "加载集与外置文件不等", str(sorted(want - POLY_WARN)[:5]), ""))

    # 拦截表守卫（存在且非空）
    bl = json.load(open(os.path.join(ROOT, "assets", "collision-blocklist.json"), encoding="utf-8"))
    if not bl.get("blocked"):
        bad.append(("blocklist", "空表", "", ""))
    if ("梁", "思成") not in {(b["surname"], b["ming"]) for b in bl["blocked"]}:
        bad.append(("blocklist", "梁思成条目缺失", "", ""))

    # verify_bank 八项全绿
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verify_bank.py")],
                       capture_output=True, text=True)
    if r.returncode != 0 or "VERDICT: PASS" not in r.stdout:
        bad.append(("verify_bank", "八项非全绿", r.stdout[-120:], ""))

    # 文档陈旧 grep（B9/F5/C11 锚）
    stale = []
    for fn in ["SKILL.md", "references/phonology-gate.md", "references/canon-pool.md",
               "references/pairing-rules.md", "references/governance.md"]:
        txt = open(os.path.join(ROOT, fn), encoding="utf-8").read()
        for pat in ["六项", "surnames-60", "四条表", "3720", "×60", "60 姓", "int[3]", "三字声调"]:
            if pat in txt:
                stale.append((fn, pat))
    if stale:
        bad.append(("陈旧grep", str(stale[:4]), "", ""))

    # 章次统计守卫（B11 锚：高置信/待核计数钉死，改动须显式更新本锚）
    seed = json.load(open(os.path.join(ROOT, "assets", "canon-seed.json"), encoding="utf-8"))
    done = sum(1 for e in seed if e.get("chapters") not in (None, "待核"))
    pend = sum(1 for e in seed if e.get("chapters") == "待核")
    # 章次内容抽检锚（B14 指摘：计数守卫不拦内容错误）
    want_ch = {"令闻": "六章", "圭璋": "六章", "于飞": "七章", "聿修": "六章", "作孚": "七章", "同袍": "一章／三章", "鸣谦": "六二（名出", "鸿渐": "初六／上九", "他山": "二章", "令仪": "四章", "令德": "三章", "飞翰": "五章", "夙兴": "四章", "柔嘉": "二章", "维翰": "四章", "明哲": "四章", "秉文": "清庙一章"}
    ch_map = {e["ming"]: e.get("chapters") for e in seed}
    bad_ch = {m: ch_map.get(m) for m, w in want_ch.items() if not (ch_map.get(m) or "").startswith(w)}
    if bad_ch:
        bad.append(("章次内容锚", str(bad_ch), "", ""))
    # 章次闸动态复演（B19/B20/C20 锚）：真函数注入测试
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import verify_bank as _vb
    pool_text = open(os.path.join(ROOT, "references", "canon-pool.md"), encoding="utf-8").read()
    tbl_text = _vb.pool_table_text(pool_text)
    corpus = _vb.verse_corpus(tbl_text)
    if _vb.chapters_quote_violations(seed, tbl_text):
        bad.append(("章次闸", "现种子池外引文", "", ""))
    inj = [dict(seed[0], chapters="一章「此句绝不在池中之伪造句」")]
    if not _vb.chapters_quote_violations(inj, tbl_text):
        bad.append(("章次闸", "动态注入未检出（引文闸失效）", "", ""))
    poem_names = {pn.strip() for line in tbl_text.splitlines() if line.strip().startswith("|")
                  for cells in [[c.strip() for c in line.strip().strip("|").split("|")]]
                  if len(cells) >= 5 and cells[0].strip().isdigit() for pn in cells[4].split("／")}
    if _vb.chapters_smuggle_violations(seed, corpus, poem_names):
        bad.append(("夹带闸", "现种子注文夹带", "", ""))
    inj2 = [dict(seed[0], chapters="一章 注文参考如切如磋式样")]
    if not _vb.chapters_smuggle_violations(inj2, corpus, poem_names):
        bad.append(("夹带闸", "动态注入未检出（夹带闸失效）", "", ""))
    inj3 = [dict(seed[0], chapters="一章 昊天有成命")]
    if _vb.chapters_smuggle_violations(inj3, corpus, poem_names):
        bad.append(("夹带闸", "篇目豁免失效（昊天有成命被误判）", "", ""))  # 豁免正锚（C21）
    pos_ok = all(seg in tbl_text for seg in ["莫不令仪", "莫不令德", "鸣谦贞吉"])
    if not pos_ok:
        bad.append(("章次闸", "正样例失衡", "", ""))
    if (done, pend) != (62, 0) or done + pend != len(seed):
        bad.append(("章次守卫", "计数漂移", "expect (62,0)&total==len(seed)", "got (%d,%d)/%d" % (done, pend, len(seed))))

    for nm, kind, a, b in bad:
        print("FAIL %s %s %s %s" % (nm, kind, a, b))
    print("REGRESSION: %s (%d cases + guards)" % ("PASS" if not bad else "FAIL", len(CASES)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
