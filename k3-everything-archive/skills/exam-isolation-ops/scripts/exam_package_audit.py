#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exam_package_audit.py —— 考场隔离协议配套机检工具（出题人打包核验 / 监管门取证）

三个子命令：
  fingerprint <题面包.md>                      打印 sha256[:16] 指纹（题面包唯一身份锚，
                                               写入所有角色简报与监考报告）
  scan <题面包.md> [--extra-words 词表.txt]    泄漏词扫描：命中即列出 行号:行内容。
                                               exit 0=净 / 2=有命中 / 3=用法错误
  isomorph <答卷.md> <定稿.md> [--n 12]        字符 n-gram 重叠取证：答卷 n-gram 被定稿
                                               覆盖的比例（containment）。定量线索，
                                               不替代监管门裁定（同模型收敛 vs 泄漏
                                               必须结合反向证据人工裁定）。
  --self-test                                  合成夹具离线自测，不读外部文件

纪律：只读机检，不改任何考场文件；扫描/isomorph 结果必须原样入监考报告，
禁止编造"已扫描"结论。仅标准库。
"""
import argparse
import hashlib
import re
import sys
import tempfile
import os

# 默认泄漏词表：题面包中不得出现的角色越界信息。
# 源自 2026-08 大工 806 模拟考场实战（打包物理剥离答案/存疑/provenance/Help 文本的同款纪律）。
DEFAULT_LEAK_WORDS = [
    "参考答案", "参考解答", "标准答案", "答案：", "答案:",
    "评分标准", "评分细则", "分值分配", "满分",
    "解析：", "解析:", "解答：", "解答:",
    "【存疑】", "provenance", "考点频次", "难度系数", "失分率",
]

_CN_PUNCT = "，。；：？！、（）【】《》〈〉「」『』—…· \t\r\n"


def fingerprint(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def scan(path, extra_words=None):
    words = list(DEFAULT_LEAK_WORDS)
    if extra_words:
        with open(extra_words, encoding="utf-8") as f:
            words += [w.strip() for w in f if w.strip()]
    hits = []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            for w in words:
                if w in line:
                    hits.append((ln, w, line.rstrip()))
    return hits


def _normalize(text):
    # 归一化：去空白/常见标点/Markdown 记号并小写化，使重叠反映内容而非格式；
    # 保留字母与数字——公式级同构（如 "ih da/dt = [a, h]"）正是取证对象
    text = re.sub(r"[#>*`\-$|=_~^\\(){}\[\]+/]", "", text.lower())
    for ch in _CN_PUNCT:
        text = text.replace(ch, "")
    return text


def _ngrams(text, n):
    return {text[i:i + n] for i in range(len(text) - n + 1)} if len(text) >= n else ({text} if text else set())


def isomorph(sheet_path, standard_path, n=12):
    with open(sheet_path, encoding="utf-8") as f:
        sheet = _normalize(f.read())
    with open(standard_path, encoding="utf-8") as f:
        std = _normalize(f.read())
    gs, gt = _ngrams(sheet, n), _ngrams(std, n)
    if not gs:
        return 0.0, 0, 0
    inter = len(gs & gt)
    return inter / len(gs), inter, len(gs)


def _self_test():
    with tempfile.TemporaryDirectory() as d:
        pkg = os.path.join(d, "pkg.md")
        sheet = os.path.join(d, "sheet.md")
        std = os.path.join(d, "std.md")
        with open(pkg, "w", encoding="utf-8") as f:
            f.write("一、填空题\n1. 写出海森堡运动方程。\n二、证明题\n1. 证明 TRK 求和规则。\n")
        with open(sheet, "w", encoding="utf-8") as f:
            f.write("一.1 海森堡运动方程为 iħ dA/dt = [A, H]，已作答。\n")
        with open(std, "w", encoding="utf-8") as f:
            f.write("一.1 海森堡运动方程为 iħ dA/dt = [A, H]。得分点：对易子形式。\n")

        # 1. 指纹稳定且为 16 位
        fp1, fp2 = fingerprint(pkg), fingerprint(pkg)
        assert fp1 == fp2 and len(fp1) == 16, "指纹不稳定"

        # 2. 干净题面包扫描为净
        assert scan(pkg) == [], "干净题面包误报"

        # 3. 污染题面包必须命中并给行号
        with open(pkg, "a", encoding="utf-8") as f:
            f.write("\n附：本题参考答案略。\n")
        hits = scan(pkg)
        assert hits and hits[0][0] == 6 and hits[0][1] == "参考答案", f"污染漏检: {hits}"

        # 4. 高重叠答卷 containment 显著高于无关答卷
        with open(os.path.join(d, "unrelated.md"), "w", encoding="utf-8") as f:
            f.write("考生完全跑题，讨论经典力学拉格朗日量与哈密顿原理的哲学史。\n")
        r_hit, _, _ = isomorph(sheet, std, n=6)
        r_miss, _, _ = isomorph(os.path.join(d, "unrelated.md"), std, n=6)
        assert r_hit > 0.3 and r_miss < r_hit, f"isomorph 区分度异常: {r_hit} vs {r_miss}"

    print("SELF-TEST PASS: fingerprint / scan / isomorph 全部符合预期")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="考场隔离协议机检：指纹/泄漏扫描/同构取证")
    ap.add_argument("--self-test", action="store_true", help="合成夹具离线自测")
    sub = ap.add_subparsers(dest="cmd")

    p_fp = sub.add_parser("fingerprint", help="题面包 sha256[:16] 指纹")
    p_fp.add_argument("package")

    p_sc = sub.add_parser("scan", help="泄漏词扫描（exit 0=净, 2=命中）")
    p_sc.add_argument("package")
    p_sc.add_argument("--extra-words", help="自定义追加词表（每行一词）")

    p_is = sub.add_parser("isomorph", help="答卷↔定稿 n-gram 重叠取证")
    p_is.add_argument("sheet")
    p_is.add_argument("standard")
    p_is.add_argument("--n", type=int, default=12, help="n-gram 长度（默认 12，短卷可降 6-8）")

    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()

    if args.cmd == "fingerprint":
        print(fingerprint(args.package))
        return 0
    if args.cmd == "scan":
        hits = scan(args.package, args.extra_words)
        if hits:
            print(f"LEAK-SCAN FAIL: {len(hits)} 处命中")
            for ln, w, line in hits:
                print(f"  L{ln} [{w}] {line[:120]}")
            return 2
        print("LEAK-SCAN CLEAN: 默认词表零命中（如用自定义词表，结果一并如实登记）")
        return 0
    if args.cmd == "isomorph":
        if args.n < 4:
            print("n 过小无判别力，拒绝运行", file=sys.stderr)
            return 3
        ratio, inter, total = isomorph(args.sheet, args.standard, args.n)
        print(f"containment={ratio:.3f}  (答卷 {args.n}-gram 命中定稿 {inter}/{total})")
        print("判读：比值仅为定量线索——高比值可能是同模型收敛（正确解自然同构），")
        print("也可能是泄漏。监管门须结合反向证据（独立记号、第三读法、推导路径差异）裁定，")
        print("禁止仅凭本数值改分或定案。")
        return 0

    ap.print_help()
    return 3


if __name__ == "__main__":
    sys.exit(main())
