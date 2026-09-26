#!/usr/bin/env python3
"""semantics_audit.py

文本语义精度初筛工具（source-semantics-sentinel 功能三的自动化部分）。

对输入文本做四类启发式检查，全部输出为"候选"（candidate）性质——宁多报
不漏报，最终裁决必须人工对照 references/semantic_precision.md 的清单执行：

  1. undefined_term       未定义术语候选：首现未定义的专业词/缩写
                          （罗素 R1/维特根斯坦 W3/W4 入口信号）
  2. ambiguous_term       歧义候选：常见多义词出现；同一多义词在多个
                          不同语境出现时报 context_conflict 子类
  3. quantifier_mixing    量化词域歧义：同一对象被"所有/任何"等全称词与
                          "有些/可能"等存在/模态词混用（罗素 R3 入口信号）
  4. hedging_density      模糊对冲密度："大概/也许/某种程度上"等对冲词
                          密度（每千字），超阈值时给出一条汇总候选
  5. dangling_reference   指称悬空候选："该公司/该政策/上述规定"等无
                          先行词（罗素 R1 入口信号）

输入：文本文件路径（位置参数，可省略）或 stdin。
输出：向 stdout 写入 JSON：
  - stats:    char_count / sentence_count / hedging_density_per_1000 /
              hedging_threshold / finding_counts
  - findings: 数组，每条含 type / subtype / text / offset（字符位置）/
              sentence_index / detail
  - notes:    候选性质与人工裁决要求声明

仅使用 Python 标准库。退出码：0 正常；1 --smoke 断言失败；2 输入错误。
"""

import argparse
import bisect
import json
import re
import sys

# ---------------- 词表（启发式，可按需扩充） ----------------

HEDGING_WORDS = [
    "某种程度上", "一定程度上", "某种意义上", "一般来说", "大体上",
    "大概", "大约", "也许", "或许", "可能", "基本上", "差不多",
    "估计", "似乎", "好像", "仿佛", "或将", "有望", "多半", "兴许",
]

UNIVERSAL_Q = ["所有", "全部", "一切", "任何", "每个", "凡是", "各", "毫无例外"]
PARTIAL_Q = ["有些", "部分", "有的", "某些", "少数", "多数", "一些"]
MODAL_Q = ["可能", "也许", "或许", "大概"]

# 多字多义词（避免单字词在复合词中大量误报）
POLYSEMY_WORDS = [
    "意思", "方便", "自然", "精神", "组织", "运动", "表现", "料理",
    "包袱", "头脑", "天真", "成熟", "灵魂", "窗口", "平台", "落地",
]

JARGON_SUFFIXES = [
    "机制", "体系", "模型", "效应", "范式", "定律", "理论",
    "指数", "工程", "战略", "架构", "曲线", "陷阱", "壁垒",
]

DEFINITION_MARKERS = [
    "即", "是指", "指的是", "定义为", "所谓", "也就是", "简称", "又称",
    "意为", "意思是", "：", ":", "（", "(",
]

DEMONSTRATIVES = ["上述", "该等", "此等", "这一", "这类", "该项", "该", "此"]

# 指示词+副词性固定搭配，不作指称检查
ADV_STOP = {
    "此外", "此处", "此时", "此后", "此前", "此举", "此事", "该当",
}

# 名词尾部裁剪：捕获过界时剥掉常见谓词/虚词首字（保长 2 字）
TRIM_TAIL = ("已将正在是被有对未并完宣表开提进出发经获实指按当与及或"
             "且但就都很还再更不曾刚即才只仅先会可能需应把向从由因")

_ABBR_RE = re.compile(r"[A-Z][A-Za-z0-9&\-]{1,9}")
_CJK = r"一-鿿"
_JARGON_RE = re.compile(
    r"[%s]{2,5}(?:%s)" % (_CJK, "|".join(JARGON_SUFFIXES))
)
# 术语截取：命中串在最后一个虚词处截断（虚词几乎不出现在术语内部）；
# 再剥掉开头的常见动词/虚词字（无分词环境下的近似词边界定位，
# 可能过剥，offset 随之修正，仅供人工定位候选）
_JARGON_SEPARATORS = "的了在是"
_LEAD_TRIM = ("认分关普注遍析师为带引发表指点示显反映包涉面通采进取"
              "产形具存出看现感觉得希期包括说把被向从于和与及或且但"
              "都也很还又再更最不已没未曾刚将即才只仅约按对由因当如"
              "若虽既此其该每各某谁何甚")
_SENT_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])|\n+")


# ---------------- 基础工具 ----------------

def split_sentences(text):
    """按句读切分，返回 [(start_offset, sentence_text)]。"""
    out = []
    pos = 0
    for seg in _SENT_SPLIT_RE.split(text):
        if seg is None:
            continue
        idx = text.find(seg, pos)
        if idx < 0:
            idx = pos
        if seg.strip():
            out.append((idx, seg))
        pos = idx + len(seg)
    return out


def sentence_index_of(starts, offset):
    return bisect.bisect_right(starts, offset) - 1


def has_definition_marker(text, start, end, window=30):
    """首现处 ±window 内是否存在定义性标记（即/是指/（ 等）。"""
    ctx = text[max(0, start - window): end + window]
    return any(m in ctx for m in DEFINITION_MARKERS)


def make_finding(ftype, subtype, text_hit, offset, sent_idx, detail):
    return {
        "type": ftype,
        "subtype": subtype,
        "text": text_hit,
        "offset": offset,
        "sentence_index": sent_idx,
        "detail": detail,
    }


# ---------------- 各类检查 ----------------

def check_undefined_terms(text, sent_starts):
    """首现未定义的专业词/缩写候选。每个术语只报首现。"""
    findings = []
    seen = set()

    for m in _ABBR_RE.finditer(text):
        tok = m.group(0)
        if tok in seen or not any(c.isupper() for c in tok[:2]):
            continue
        seen.add(tok)
        if not has_definition_marker(text, m.start(), m.end()):
            findings.append(make_finding(
                "undefined_term", "abbreviation", tok, m.start(),
                sentence_index_of(sent_starts, m.start()),
                "缩写首现 ±30 字内无定义标记（即/是指/（ 等），W4 私人语言警示入口"))

    for m in _JARGON_RE.finditer(text):
        tok = m.group(0)
        for sep in _JARGON_SEPARATORS:
            if sep in tok[:-2]:  # 后缀两字不切
                tok = tok.rsplit(sep, 1)[1]
        while len(tok) > 3 and tok[0] in _LEAD_TRIM:
            tok = tok[1:]
        if len(tok) < 3 or tok in seen:
            continue
        seen.add(tok)
        start = m.end() - len(tok)
        if not has_definition_marker(text, start, m.end()):
            findings.append(make_finding(
                "undefined_term", "jargon", tok, start,
                sentence_index_of(sent_starts, start),
                "专业词首现 ±30 字内无定义标记，W3 家族相似边界/W4 入口"))

    return findings


def check_ambiguity(text, sent_starts):
    """多义词出现候选 + 同词多语境冲突候选。"""
    findings = []
    for word in POLYSEMY_WORDS:
        occ = [m for m in re.finditer(re.escape(word), text)]
        if not occ:
            continue
        contexts = set()
        for m in occ:
            ctx = text[max(0, m.start() - 3): m.start()] + "|" + \
                text[m.end(): m.end() + 3]
            contexts.add(ctx)
            findings.append(make_finding(
                "ambiguous_term", "polysemy_occurrence", word, m.start(),
                sentence_index_of(sent_starts, m.start()),
                "常见多义词出现，W1 用法一致性检查入口"))
        if len(occ) >= 2 and len(contexts) >= 2:
            first = occ[0]
            findings.append(make_finding(
                "ambiguous_term", "context_conflict", word, first.start(),
                sentence_index_of(sent_starts, first.start()),
                "同一多义词出现于 %d 个不同语境（共 %d 次），疑似用法漂移候选"
                % (len(contexts), len(occ))))
    return findings


def _grab_domain(text, qend):
    """量化词后取域：跳过可选"的"，取其后 2 个汉字作域键。"""
    rest = text[qend: qend + 8]
    m = re.match(r"的?([%s]{2})" % _CJK, rest)
    return m.group(1) if m else None


def check_quantifier_mixing(text, sent_starts):
    """同一域键被全称词与存在/模态词混用。"""
    domains = {}  # domain -> {"uni": [(off, q)], "non": [(off, q)]}
    for q in UNIVERSAL_Q:
        for m in re.finditer(re.escape(q), text):
            d = _grab_domain(text, m.end())
            if d:
                domains.setdefault(d, {"uni": [], "non": []})["uni"].append(
                    (m.start(), q))
    for q in PARTIAL_Q + MODAL_Q:
        for m in re.finditer(re.escape(q), text):
            d = _grab_domain(text, m.end())
            if d:
                domains.setdefault(d, {"uni": [], "non": []})["non"].append(
                    (m.start(), q))
    findings = []
    for d, sides in sorted(domains.items()):
        if sides["uni"] and sides["non"]:
            off_u, q_u = sides["uni"][0]
            off_n, q_n = sides["non"][0]
            findings.append(make_finding(
                "quantifier_mixing", "domain_conflict", d, min(off_u, off_n),
                sentence_index_of(sent_starts, min(off_u, off_n)),
                "域「%s」被全称词「%s」(@%d) 与存在/模态词「%s」(@%d) 混用，"
                "R3 层级/口径混淆入口" % (d, q_u, off_u, q_n, off_n)))
    return findings


def check_hedging(text, sent_starts, threshold):
    """对冲词密度：返回 (逐词命中列表, 密度值, 汇总候选或 None)。"""
    hits = []
    for w in sorted(HEDGING_WORDS, key=len, reverse=True):
        for m in re.finditer(re.escape(w), text):
            # 长词优先，跳过已被更长词覆盖的区间（如"某种程度上"内含"程度"不计）
            if any(h["offset"] <= m.start() < h["offset"] + len(h["text"])
                   for h in hits):
                continue
            hits.append({"offset": m.start(), "text": w,
                         "sentence_index": sentence_index_of(sent_starts,
                                                             m.start())})
    hits.sort(key=lambda h: h["offset"])
    density = len(hits) / max(1, len(text)) * 1000.0
    finding = None
    if density >= threshold and hits:
        finding = make_finding(
            "hedging_density", "above_threshold",
            ";".join(h["text"] for h in hits[:20]), hits[0]["offset"],
            hits[0]["sentence_index"],
            "对冲词 %d 次，密度 %.1f/千字 ≥ 阈值 %.1f；W2 语境游戏辅助信号"
            % (len(hits), density, threshold))
        finding["positions"] = hits
    return hits, density, finding


def check_dangling_references(text, sent_starts):
    """"该/此/上述/这一 + 名词(2-4字)"且前文无先行词。"""
    findings = []
    dem_pattern = "|".join(DEMONSTRATIVES)
    ref_re = re.compile(r"(%s)([%s]{2,4})" % (dem_pattern, _CJK))
    for m in ref_re.finditer(text):
        dem, noun = m.group(1), m.group(2)
        while len(noun) > 2 and noun[-1] in TRIM_TAIL:
            noun = noun[:-1]
        if (dem + noun in ADV_STOP or dem + noun[:1] in ADV_STOP
                or noun[:1] in "的一是了不和在有"):
            continue
        head = noun[:2]  # 先行词按前两字匹配，降低切分噪声
        prior = text[: m.start()]
        antecedent = False
        for am in re.finditer(re.escape(head), prior):
            prev_char = prior[am.start() - 1] if am.start() > 0 else ""
            if prev_char not in "该此上述一类别等每某":  # 非指示词前缀才算先行词
                antecedent = True
                break
        if not antecedent:
            findings.append(make_finding(
                "dangling_reference", "no_antecedent", dem + noun, m.start(),
                sentence_index_of(sent_starts, m.start()),
                "「%s」的前文未找到先行词「%s」，R1 指称消解检查入口"
                % (dem + noun, head)))
    return findings


# ---------------- 主分析 ----------------

def analyze(text, hedge_threshold=15.0):
    sentences = split_sentences(text)
    sent_starts = [s[0] for s in sentences]

    findings = []
    findings += check_undefined_terms(text, sent_starts)
    findings += check_ambiguity(text, sent_starts)
    findings += check_quantifier_mixing(text, sent_starts)
    hits, density, hedge_finding = check_hedging(text, sent_starts,
                                                 hedge_threshold)
    if hedge_finding:
        findings.append(hedge_finding)
    findings += check_dangling_references(text, sent_starts)

    findings.sort(key=lambda f: f["offset"])
    counts = {}
    for f in findings:
        counts[f["type"]] = counts.get(f["type"], 0) + 1

    return {
        "stats": {
            "char_count": len(text),
            "sentence_count": len(sentences),
            "hedging_hits": len(hits),
            "hedging_density_per_1000": round(density, 2),
            "hedging_threshold": hedge_threshold,
            "finding_counts": counts,
        },
        "findings": findings,
        "notes": "全部为启发式候选（candidate），须人工对照 "
                 "references/semantic_precision.md 清单裁决；"
                 "语义审计结论 conf 记方法论档（喂引擎按 assumed）。",
    }


# ---------------- smoke ----------------

SMOKE_TEXT = (
    "近日，XYZ指数快速上升，市场普遍关注反身性机制带来的变化。"
    "分析师认为该指数可能继续走高，大概会带动相关板块，也许引发新一轮配置，"
    "某种程度上改变市场预期，基本上已成共识，似乎没有多少悬念，估计空间可观，"
    "或将吸引更多资金，有望复制此前行情，差不多的逻辑在其他市场也出现过，"
    "一般来说这种趋势难以逆转，大约在三季度兑现，多半不会失速，兴许还有惊喜。"
    "所有高校都开设了该专业。有些高校仍未公布相关课程。"
    "这里交通很方便。方便的时候请联系我。"
    "公告称该公司已完成整改，但全文未说明是哪家公司。"
)

SMOKE_CLEAN = (
    "甲公司收购了乙企业。该公司随后完成整合。"
    "有些高校开设了相关专业，部分高校公布了课程。"
)


def run_smoke():
    failures = []

    def expect(cond, msg):
        if not cond:
            failures.append(msg)

    res = analyze(SMOKE_TEXT, hedge_threshold=15.0)
    types = [f["type"] for f in res["findings"]]
    expect("undefined_term" in types, "smoke: undefined_term 未命中")
    abbr = [f for f in res["findings"]
            if f["type"] == "undefined_term" and f["subtype"] == "abbreviation"]
    expect(any(f["text"] == "XYZ" for f in abbr), "smoke: 缩写 XYZ 未命中")
    expect("ambiguous_term" in types, "smoke: ambiguous_term 未命中")
    expect(any(f["subtype"] == "context_conflict"
               for f in res["findings"]), "smoke: context_conflict 未命中")
    expect("quantifier_mixing" in types, "smoke: quantifier_mixing 未命中")
    expect("hedging_density" in types, "smoke: hedging_density 未命中")
    expect("dangling_reference" in types, "smoke: dangling_reference 未命中")
    dang = [f for f in res["findings"] if f["type"] == "dangling_reference"]
    expect(any("该公司" in f["text"] for f in dang),
           "smoke: 该公司 指称悬空未命中")

    clean = analyze(SMOKE_CLEAN, hedge_threshold=15.0)
    ctypes = [f["type"] for f in clean["findings"]]
    expect("dangling_reference" not in ctypes,
           "smoke: 干净文本误报 dangling_reference: %s"
           % [f["text"] for f in clean["findings"]
              if f["type"] == "dangling_reference"])
    expect("quantifier_mixing" not in ctypes,
           "smoke: 干净文本误报 quantifier_mixing")

    if failures:
        print("SMOKE FAILED:")
        for f_ in failures:
            print("  - " + f_)
        return 1
    print("SMOKE OK: 命中路径 %s；干净路径 zero-hit 通过"
          % res["stats"]["finding_counts"])
    return 0


# ---------------- CLI ----------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="文本语义精度初筛：未定义术语/歧义/量化词域混用/"
                    "对冲密度/指称悬空，输出候选 JSON（全部需人工裁决）。")
    p.add_argument("file", nargs="?", help="文本文件路径；缺省读 stdin")
    p.add_argument("--pretty", action="store_true",
                   help="以缩进格式输出 JSON（默认紧凑输出）")
    p.add_argument("--hedge-threshold", type=float, default=15.0,
                   help="对冲词密度阈值（次/千字，默认 15）")
    p.add_argument("--smoke", action="store_true",
                   help="运行内置合成样例自检后退出")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.smoke:
        return run_smoke()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as e:
            print("输入错误：无法读取文件 %s: %s" % (args.file, e),
                  file=sys.stderr)
            return 2
    else:
        text = sys.stdin.read()
    if not text.strip():
        print("输入错误：文本为空", file=sys.stderr)
        return 2

    result = analyze(text, hedge_threshold=args.hedge_threshold)
    json.dump(result, sys.stdout, ensure_ascii=False,
              indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
