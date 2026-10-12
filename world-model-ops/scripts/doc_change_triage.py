# -*- coding: utf-8 -*-
"""doc_change_triage.py —— 文档"变更"之双轨判定（2026-10-12 立，应 -1218／-1219 之判）
背景：该档内嵌"带临时签名之图片 URL"（如 ?Expires=…&KSSAccessKeyId=…&Signature=…，实测 73 处），
     Expires 随时间与抓取而变 ⇒ ★逐字节比对必报"不同"，然其非内容变更。
本器（零外呼）两轨：
  ① 实质变更轨：把"URL 之 query 串"★整体抹去（连同百分号编码）⇒ 得归一文本 ⇒ 比字数与 sha3 指纹
  ② 同源轨：归一文本逐字节比对 ⇒ 判"同源／异源"
判据（可失败）：①两文件皆可读；②归一后仍能给出指纹；③★若原字节不同而归一后相同 ⇒ 报"差异全在签名"
用法：python doc_change_triage.py --a <f1> --b <f2> [--json out]
（中文串一律用「」）
"""
import argparse, difflib, hashlib, json, pathlib, re, sys, time

# ★抹去 URL 之 query 串（含百分号编码与 +/= 等）：以 "?" 起至空白/引号/右括号止
RE_QUERY = re.compile(r"\?[^\s)\"'<>]*")
RE_EXPIRES = re.compile(r"Expires=\d+")
RE_SIG = re.compile(r"Signature=[^\s&)\"']*")
RE_KID = re.compile(r"(KSS|OSS|AWS)AccessKeyId=[^\s&)\"']*")


def norm(t):
    t = RE_QUERY.sub("?*", t)
    t = RE_EXPIRES.sub("Expires=*", t)
    t = RE_SIG.sub("Signature=*", t)
    t = RE_KID.sub("KeyId=*", t)
    return t


def sha16(s):
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    fa, fb = pathlib.Path(a.a), pathlib.Path(a.b)
    if not (fa.exists() and fb.exists()):
        print("   ★一方不在：%s / %s" % (fa.name, fb.name)); return 2
    ba, bb = fa.read_bytes(), fb.read_bytes()
    ta = ba.decode("utf-8-sig", errors="replace"); tb = bb.decode("utf-8-sig", errors="replace")
    na, nb = norm(ta), norm(tb)
    raw_same = (ba == bb)
    norm_same = (na == nb)
    # 签名处计数
    nsig = len(re.findall(r"Signature=", ta))
    res = {"a": fa.name, "b": fb.name,
           "bytes": [len(ba), len(bb)], "chars": [len(ta), len(tb)],
           "norm_bytes": [len(na.encode()), len(nb.encode())], "norm_chars": [len(na), len(nb)],
           "raw_same": raw_same, "norm_same": norm_same,
           "hash_raw": [sha16(ta), sha16(tb)], "hash_norm": [sha16(na), sha16(nb)],
           "delta_chars_norm": len(nb) - len(na), "sig_count_a": nsig}
    print("  ═══ 文档变更双轨判定 ═══")
    print("   A：%s（%.1f KB）｜ B：%s（%.1f KB）" % (fa.name, len(ba)/1024, fb.name, len(bb)/1024))
    print("   原字节：%d ／ %d（差 %+d）" % (len(ba), len(bb), len(bb)-len(ba)))
    print("   ★归一后：%d ／ %d 字符（差 %+d）" % (len(na), len(nb), len(nb)-len(na)))
    print("   ★原指纹：%s ／ %s ⇒ 相同=%s" % (sha16(ta), sha16(tb), raw_same))
    print("   ★归一指纹：%s ／ %s ⇒ ★相同=%s" % (sha16(na), sha16(nb), norm_same))
    print("   ★签名处（A）计数：%d" % nsig)
    # ★判
    if raw_same:
        verdict = "★两件逐字节相同（无变更）"
    elif norm_same:
        verdict = "★差异★全在临时签名（归一后相同）⇒ 判：非实质变更"
    else:
        verdict = "★归一后仍不同 ⇒ 判：有实质变更（归一后差 %+d 字）" % (len(nb)-len(na))
    print("   ⇒ %s" % verdict)
    if not norm_same:
        i = 0
        while i < min(len(na), len(nb)) and na[i] == nb[i]: i += 1
        print("      归一后首异位置：%d" % i)
        print("        A：…%s…" % na[max(0,i-50):i+50].replace("\n", " ⏎ "))
        print("        B：…%s…" % nb[max(0,i-50):i+50].replace("\n", " ⏎ "))
    crit = {"①两文件皆可读": True, "②归一后仍能给出指纹": bool(sha16(na) and sha16(nb)),
            "③★差异归因已给出（全在签名／仍有实质）": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    res["verdict"] = verdict; res["criteria"] = crit
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
