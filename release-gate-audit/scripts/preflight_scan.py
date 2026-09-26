#!/usr/bin/env python3
"""
preflight_scan.py — 外发前脱敏扫描器（release-gate-audit / 外发审查官）
推送任何内容到公开/半公开渠道（GitHub、网盘分享、网页发布）前的确定性 PII/凭证扫描。
纯标准库，零依赖。铁律：扫描结果必须来自真实运行，禁止编造（conf=empirical 级别）。

用法:
  python3 preflight_scan.py <目录或文件> [--blocklist private_terms.txt] [--json out.json]
  python3 preflight_scan.py --self-test

判定: HIGH 命中 → verdict=BLOCK（禁推送）；仅 MED → REVIEW（人工过目）；零命中 → PASS。
v1.0.1：新增 SCAN_EXEMPT 行内豁免机制（豁免行登记进报告，透明可审）；
夹具合成化（自扫描实战胜仗：自用例的假手机号/假地址命中自身，且假地址撞上用户真实城区——夹具与真实 PII 零重叠从此入纪律）。
豁免: 二进制/图片/音视频/压缩包自动跳过；.git 目录跳过（历史由"新库无历史"纪律另行保证）。
"""
import os, re, sys, json, argparse, tempfile, pathlib

PATTERNS = [
    # (id, severity, regex, 说明)
    ("PHONE", "HIGH", re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)'), "手机号"),
    ("IDCARD", "HIGH", re.compile(r'(?<!\d)\d{17}[\dXx](?!\d)'), "身份证号"),
    ("BANKCARD", "HIGH", re.compile(r'(?<!\d)\d{16,19}(?!\d)'), "银行卡号"),
    ("APIKEY", "HIGH", re.compile(
        r'(?i)(api[_-]?key|secret|token|password|passwd|授权码|access[_-]?key)\s*[:=：]\s*["\']?[A-Za-z0-9_\-]{8,}'),
        "密钥/口令赋值"),
    ("CRED_FILE", "HIGH", None, "凭证文件名（credentials.env/*.pem/*.key/id_rsa/*.pfx/*.p12）"),
    ("ADDR", "MED", re.compile(r'[一-鿿]{2,}(省|市|区|县)[一-鿿]{0,}(路|街|道|栋|单元|号|室)'), "详细地址疑似"),
    ("EMAIL", "MED", re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'), "邮箱地址"),
    ("AMOUNT", "MED", re.compile(r'(?<!\d)\d{4,}(\.\d+)?\s*(万|元|块)'), "金额表述疑似"),
]
CRED_NAMES = {"credentials.env", ".env", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
CRED_SUFFIX = (".pem", ".key", ".pfx", ".p12", ".keystore")
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp3", ".mp4", ".wav", ".zip",
               ".skill", ".gz", ".tar", ".pdf", ".docx", ".xlsx", ".pptx", ".pyc", ".db", ".sqlite")
MAX_BYTES = 2_000_000  # 单文件超 2MB 跳过并登记（防大卡死）


def mask(s, keep=2):
    s = s.strip()
    return s[:keep] + "***" + str(len(s)) + "chars" if len(s) > keep else "***"


def scan_file(path, rel, blocklist):
    hits = []
    base = os.path.basename(path)
    if base in CRED_NAMES or base.lower().endswith(CRED_SUFFIX):
        hits.append({"file": rel, "line": 0, "pattern": "CRED_FILE", "severity": "HIGH",
                     "excerpt": base, "note": "凭证类文件名"})
        return hits  # 凭证文件不读内容，直接 HIGH
    if base.lower().endswith(SKIP_SUFFIX):
        return hits
    try:
        if os.path.getsize(path) > MAX_BYTES:
            hits.append({"file": rel, "line": 0, "pattern": "TOO_BIG", "severity": "MED",
                         "excerpt": f"{os.path.getsize(path)}B", "note": "超 2MB 未扫，需人工"})
            return hits
        with open(path, encoding="utf-8", errors="strict") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, OSError):
        return hits  # 二进制或非文本，跳过
    for n, line in enumerate(lines, 1):
        if 'SCAN_EXEMPT' in line:
            hits.append({"file": rel, "line": n, "pattern": "EXEMPT", "severity": "INFO",
                         "excerpt": "标记豁免", "note": "人工登记的豁免行（如测试夹具）"})
            continue
        for pid, sev, rx, _ in PATTERNS:
            if rx is None:
                continue
            for m in rx.finditer(line):
                hits.append({"file": rel, "line": n, "pattern": pid, "severity": sev,
                             "excerpt": mask(m.group(0))})
        for term in blocklist:
            if term and term in line:
                hits.append({"file": rel, "line": n, "pattern": "BLOCKLIST", "severity": "HIGH",
                             "excerpt": mask(term), "note": "私有词表命中"})
    return hits


def scan(target, blocklist):
    target = os.path.abspath(target)
    files = []
    if os.path.isfile(target):
        files = [target]; root = os.path.dirname(target)
    else:
        for dirpath, dirnames, filenames in os.walk(target):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            files += [os.path.join(dirpath, fn) for fn in filenames]
        root = target
    hits = []
    for p in sorted(files):
        hits.extend(scan_file(p, os.path.relpath(p, root), blocklist))
    high = sum(1 for h in hits if h["severity"] == "HIGH")
    med = sum(1 for h in hits if h["severity"] == "MED")
    verdict = "BLOCK" if high else ("REVIEW" if med else "PASS")
    return {"target": target, "scanned_files": len(files), "high": high, "med": med,
            "verdict": verdict, "hits": hits}


def load_blocklist(path):
    if not path:
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def self_test():
    ok = True
    with tempfile.TemporaryDirectory() as d:
        pathlib.Path(d, "clean.py").write_text("print('hello')\n# 无敏感内容\n", encoding="utf-8")
        pathlib.Path(d, "bad_phone.md").write_text("联系我 13800000000 详谈\n", encoding="utf-8")  # SCAN_EXEMPT 合成夹具，非真实号码
        pathlib.Path(d, "bad_key.txt").write_text("api_key = \"abcdefgh12345678\"\n", encoding="utf-8")
        pathlib.Path(d, "credentials.env").write_text("AMAP_KEY=whatever\n", encoding="utf-8")
        pathlib.Path(d, "med.txt").write_text("地址：虚构省示例市样例区测试路 0 号\n", encoding="utf-8")  # SCAN_EXEMPT 合成地名夹具
        pathlib.Path(d, "private.txt").write_text("私有词表条目命中测试\n", encoding="utf-8")
        bl = load_blocklist(pathlib.Path(d, "private.txt"))
        cases = [
            ("干净文件 PASS", scan(os.path.join(d, "clean.py"), bl), "PASS", 0),
            ("手机号 BLOCK", scan(os.path.join(d, "bad_phone.md"), bl), "BLOCK", 1),
            ("密钥赋值 BLOCK", scan(os.path.join(d, "bad_key.txt"), bl), "BLOCK", 1),
            ("凭证文件名 BLOCK（不读内容）", scan(os.path.join(d, "credentials.env"), bl), "BLOCK", 1),
            ("地址疑似 REVIEW", scan(os.path.join(d, "med.txt"), bl), "REVIEW", 0),
            ("词表命中 BLOCK", scan(os.path.join(d, "clean.py"), ["hello"]), "BLOCK", 1),
            ("整目录混合 BLOCK", scan(d, bl), "BLOCK", None),
        ]
        for name, rep, expect_v, expect_high in cases:
            good = rep["verdict"] == expect_v and (expect_high is None or rep["high"] >= expect_high)
            ok &= good
            print(f"[{'PASS' if good else 'FAIL'}] {name} → 期望 {expect_v} 实得 {rep['verdict']}(HIGH={rep['high']})",
                  file=sys.stderr)
    print(f"[SELF-TEST {'OK' if ok else 'FAIL'}] 7 用例", file=sys.stderr)
    return ok


def main():
    ap = argparse.ArgumentParser(description="外发前脱敏扫描器")
    ap.add_argument("target", nargs="?", help="扫描目录或文件")
    ap.add_argument("--blocklist", help="私有词表（每行一个词，# 开头为注释）")
    ap.add_argument("--json", help="扫描报告输出路径")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(0 if self_test() else 1)
    if not args.target:
        ap.error("缺 target（或 --self-test）")
    rep = scan(args.target, load_blocklist(args.blocklist))
    out = json.dumps(rep, ensure_ascii=False, indent=2)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(out)
    print(json.dumps({k: rep[k] for k in ("target", "scanned_files", "high", "med", "verdict")},
                     ensure_ascii=False))
    for h in rep["hits"][:20]:
        print(f"[{h['severity']}] {h['file']}:{h['line']} {h['pattern']} {h['excerpt']}", file=sys.stderr)
    if len(rep["hits"]) > 20:
        print(f"... 其余 {len(rep['hits'])-20} 条见 --json 报告", file=sys.stderr)
    sys.exit(0 if rep["verdict"] == "PASS" else (2 if rep["verdict"] == "BLOCK" else 1))


if __name__ == "__main__":
    main()
