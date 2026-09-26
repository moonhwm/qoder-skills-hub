#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
letter_honesty_check.py | 套磁信诚实性与发送就绪检查（AAPP 内核层脚本化）

对一封套磁信草稿执行四类检查：
  H1 技术栈虚构检测：出现"精通/熟练掌握/expert in/proficient in"+具体技术名 → 黄警
  H2 方法论夸大检测：声称 optimization/algorithm design 等而无支撑提示 → 红警
  H3 占位符/数字一致性提示：检测未替换的 [REPLACE_WITH_*] 占位符 → 阻断
  H4 无出处引用检测：引用导师具体术语/论文但无具体出处标记 → 黄警
另输出：词数统计、核心段落完整性、时间止损提醒。
注意：段落完整性实际仅自动检查 gap_explanation 与 request 两段
（T1 模板 required_segments 共 6 段：hook/differentiation/gap/platform/interest/request），
其余 4 段由人工对照 templates/letter_templates.md 检查（v1.1 收窄 docstring 承诺，
未改检查逻辑）。

用法：
  python3 letter_honesty_check.py letter.txt
  python3 letter_honesty_check.py letter.txt --json
  cat letter.txt | python3 letter_honesty_check.py - --json

退出码：0 = 通过（可含黄警）；1 = 存在阻断项（红警/未替换占位符）。
"""
import argparse
import json
import re
import sys

TECH_TERMS = [
    "python", "matlab", "gams", "aspen", "tensorflow", "pytorch", "machine learning",
    "deep learning", "第一性原理", "dft", "分子动力学", "有限元", "comsol", "lammps",
    "quantum espresso", "vasp", "origin", "zemax", "solidworks", "ansys",
]
OVERCLAIM_WORDS = ["精通", "熟练掌握", "expert in", "proficient in", "master of", "精通于"]
METHOD_CLAIMS = [
    "optimization", "algorithm design", "model development", "designed an algorithm",
    "developed a model", "算法设计", "模型开发", "优化方法",
]
PLACEHOLDER_RE = re.compile(r"\[(?:REPLACE_WITH_[^\]]+|你的[^\]]*|YOUR_[^\]]+)\]")
CITE_HINT_RE = re.compile(
    r"(Nature|Science|Cell|PRL|Physical Review|Advanced Materials|Nano Letters|"
    r"Nature Communications|Nature Energy|JACS|Angew|NSFC|国家自然科学基金|\b20\d{2}\b)"
)
CORE_SEGMENTS = {
    "gap_explanation": ["since graduating", "gap", "毕业以来", "毕业后"],
    "request": ["would like to", "i am writing to", "could you", "希望", "恳请", "询问"],
}


def check_letter(text: str) -> dict:
    findings = []
    lower = text.lower()

    # H3 占位符（阻断项）
    placeholders = PLACEHOLDER_RE.findall(text)
    if placeholders:
        findings.append({
            "id": "H3", "severity": "critical",
            "msg": f"存在未替换占位符 {sorted(set(placeholders))}，发送前必须替换为真实信息",
        })

    # H1 技术栈虚构
    for w in OVERCLAIM_WORDS:
        if w.lower() in lower:
            for t in TECH_TERMS:
                if t in lower:
                    findings.append({
                        "id": "H1", "severity": "medium",
                        "msg": f"检测到 '{w}' + 技术词 '{t}'：面试可能被要求展示项目，确认证据库中有直接支撑",
                    })
                    break

    # H2 方法论夸大
    for m in METHOD_CLAIMS:
        if m.lower() in lower:
            findings.append({
                "id": "H2", "severity": "high",
                "msg": f"检测到方法论声称 '{m}'：若 CV/论文无对应课程或项目，降级为更保守表述（如 'applied ... to ...'）",
            })

    # H4 引用出处
    if CITE_HINT_RE.search(text):
        # 有引用迹象但未带年份或出处锚点的粗略提示
        if not re.search(r"\(?(19|20)\d{2}\)?", text):
            findings.append({
                "id": "H4", "severity": "medium",
                "msg": "引用了具体论文/项目但未标注年份或出处锚点，补充可查证出处（论文标题+年份）",
            })

    # 词数
    words_en = len(re.findall(r"[A-Za-z][A-Za-z\-']*", text))
    chars_zh = len(re.findall(r"[\u4e00-\u9fff]", text))
    word_count = words_en + chars_zh
    if words_en > 0 and words_en > 220:
        findings.append({
            "id": "LEN", "severity": "medium",
            "msg": f"英文词数 {words_en} > 220：套磁信建议 150-200 词，删减包装性段落",
        })

    # 核心段落完整性
    segments = {}
    for seg, keys in CORE_SEGMENTS.items():
        segments[seg] = any(k in lower for k in keys)
    missing = [k for k, v in segments.items() if not v]
    if missing:
        findings.append({
            "id": "SEG", "severity": "medium",
            "msg": f"可能缺少核心段落：{missing}（对照 templates/letter_templates.md 的 required_segments）",
        })

    blocked = any(f["severity"] == "critical" for f in findings) or any(
        f["severity"] == "high" for f in findings
    )
    return {
        "verdict": "BLOCK" if blocked else "PASS",
        "word_count_en": words_en,
        "char_count_zh": chars_zh,
        "core_segments": segments,
        "findings": findings,
        "reminder": "AAPP 是信息收集清单，不是决策引擎；量化评分仅供娱乐性参考，最终决策回归直觉。",
    }


def main():
    ap = argparse.ArgumentParser(description="套磁信诚实性与发送就绪检查")
    ap.add_argument("file", help="信件文件路径，或 '-' 读 stdin")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    result = check_letter(text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"判定: {result['verdict']}")
        print(f"英文词数: {result['word_count_en']} | 中文字数: {result['char_count_zh']}")
        print(f"核心段落: {result['core_segments']}")
        for f in result["findings"]:
            print(f"  [{f['severity']:>8}] {f['id']}: {f['msg']}")
        print(f"\n提醒: {result['reminder']}")

    sys.exit(1 if result["verdict"] == "BLOCK" else 0)


if __name__ == "__main__":
    main()
