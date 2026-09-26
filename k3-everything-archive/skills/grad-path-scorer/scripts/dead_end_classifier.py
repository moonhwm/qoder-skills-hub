#!/usr/bin/env python3
"""
dead_end_classifier.py — 学术断头路数据层判定器
把 methodology §5 的三条定性规则引擎化，替代手填 dead_end 字段。
纯标准库。管道设计：输出可直接喂 score_engine.py。

用法：
  cat schools_facts.json | python3 dead_end_classifier.py | python3 score_engine.py
  python3 dead_end_classifier.py --smoke

输入字段（三事实清单，可空；v1.3 新增可选第四事实）：
  has_phd_program       bool|null  相关方向有无博士点
  advisor_phd_qualified bool|null  目标导师有无博导资格
  has_platform          bool|null  院校层面有无延续平台（装置/中心/团队）
  exit_channel          bool|null  有无稳定跨校申博出口记录（v1.3，软/硬断头路分级）

判定规则：
  任一 === false        → dead_end=true（断头路，附依据）
                          └ exit_channel=true → grade=soft（出口尚可，惩罚减半）
                            否则              → grade=hard
  无 false 但有 null    → dead_end=false + conf 强制降 assumed + unknown_fields 列出未知项
  全部 true             → dead_end=false
"""
import json, sys, argparse

RULES = [
    ("has_phd_program", "无相关方向博士点"),
    ("advisor_phd_qualified", "导师梯队无博导资格"),
    ("has_platform", "无延续平台（装置/中心/团队缺失）"),
]


def classify(school):
    reasons = [label for key, label in RULES if school.get(key) is False]
    unknown = [key for key, _ in RULES if school.get(key) is None]
    out = dict(school)
    if reasons:
        out["dead_end"] = True
        out["dead_end_reasons"] = reasons
        out["dead_end_grade"] = "soft" if school.get("exit_channel") is True else "hard"
    else:
        out["dead_end"] = False
        if unknown:
            out["conf"] = "assumed"  # 有未知项，置信度强制降档
            out["unknown_fields"] = unknown
    return out


SMOKE_CASES = [
    ({"name": "真断头", "has_phd_program": False, "advisor_phd_qualified": True,
      "has_platform": True}, True, "hard"),
    ({"name": "软断头", "has_phd_program": False, "advisor_phd_qualified": False,
      "has_platform": False, "exit_channel": True}, True, "soft"),
    ({"name": "信息不全", "has_phd_program": True, "advisor_phd_qualified": None,
      "has_platform": True}, False, None),
    ({"name": "全通", "has_phd_program": True, "advisor_phd_qualified": True,
      "has_platform": True}, False, None),
    ({"name": "双断头", "has_phd_program": False, "advisor_phd_qualified": False,
      "has_platform": None}, True, "hard"),
]


def smoke():
    for school, expect, grade in SMOKE_CASES:
        got = classify(school)
        assert got["dead_end"] == expect, f"{school['name']} 判定错误"
        if expect:
            assert got["dead_end_grade"] == grade, f"{school['name']} 分级错误: {got.get('dead_end_grade')}"
    info = classify(SMOKE_CASES[2][0])
    assert info["conf"] == "assumed" and info["unknown_fields"] == ["advisor_phd_qualified"]
    print(json.dumps([classify(s) for s, _, _ in SMOKE_CASES], ensure_ascii=False, indent=2))
    print("\n[SMOKE OK] 五用例判定 + 软硬分级 + 未知降档 全部通过", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="学术断头路数据层判定器")
    ap.add_argument("schools", nargs="?", help="院校事实 JSON（缺省读 stdin）")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        smoke(); return
    raw = open(args.schools, encoding="utf-8").read() if args.schools else sys.stdin.read()
    schools = json.loads(raw)
    if isinstance(schools, dict):
        schools = schools.get("schools", [schools])
    print(json.dumps([classify(s) for s in schools], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
