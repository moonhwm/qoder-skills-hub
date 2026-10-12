# -*- coding: utf-8 -*-
"""cairn_ontology.py —— 本席知识本体（★形制借自 getzep/zep 之 ontology/default_ontology.py：
  ①每类之 docstring 即"判据"（含优先级指令 ＋ Trigger patterns ＋ 示例）
  ②节点表 ③边表 ④★类型合法性矩阵 (源型, 目标型) → 允许之边型）
用法：python cairn_ontology.py --check <节点型> <边型> <节点型>   # 验一条边是否合法
      python cairn_ontology.py --list
（中文串一律用「」）
"""
import argparse, sys


class Seat:
    """IMPORTANT: 先判此型；凡「席位／节点／agent」之主体皆归此类。

    Trigger patterns: 「A2A新席_…」「seat_key」「a2a-node-local」「守藏席」「K3 席」等。
    示例：A2A新席_石敢当Cairn、守藏席 shoucang-df-doc-01。
    """


class Artifact:
    """IMPORTANT: 凡「件」皆归此类（产出物、报告、脚本、资产）。

    Trigger patterns: 「DF-…-CAIRN-nn」「件号」「交付件」「.otl/.glb/.py 产物」。
    示例：DF-OPS-20261012-CAIRN-88、CAIRN_staticLOD0_20261012.glb。
    """


class Criterion:
    """IMPORTANT: 凡「可失败之判据」皆归此类（须能红、须能绿、须带 scope）。

    Trigger patterns: 「判据」「门槛」「⇒ ✓/✗」「退出码」「PASS/FAIL」。
    示例：五幕之四判据、UMC 四判据、TD 不可评判据。
    """


class Precept:
    """IMPORTANT: 凡「戒条／纪律」皆归此类（编号 ＋ 一句话 ＋ 触发场景）。

    Trigger patterns: 「戒四十六」「先搜后造」「判据报红先问己」。
    """


class Erratum:
    """凡「勘误／更正」皆归此类（对既有结论之修正）。

    Trigger patterns: 「勘误四」「更正」「旧口径应读作」。
    """


class Event:
    """凡「事件」皆归此类（总线条目、台账条目、墙事件、升级面案）。

    Trigger patterns: 「seq=」「ev_type」「dead_letter」「wall」「ESC-」。
    """


class Fact:
    """凡「读数／断言」皆归此类；★须带 conf（empirical／estimated／assumed／unverified）。

    Trigger patterns: 数值 ＋ 单位（条／件／%／元／字／次／px／s）之陈述。
    """


# ── 边（关系）类型 ──
class Cites:
    """件／判据引证另一件（含 URL 或件号）。"""


class Amends:
    """新件修订旧件（只增不改者用 Supersedes，实质更正者用 Amends）。"""


class Supersedes:
    """新版覆盖旧版（旧版留痕不删）。"""


class Evidences:
    """证据支撑断言（实测数据 → 断言）。"""


class Violates:
    """某事件触犯某戒条（或判据报红）。"""


class Blocks:
    """某阻塞项挡住某件／某判据。"""


CAIRN_NODE_ONTOLOGY = {
    "Seat": Seat, "Artifact": Artifact, "Criterion": Criterion, "Precept": Precept,
    "Erratum": Erratum, "Event": Event, "Fact": Fact,
}
CAIRN_EDGE_ONTOLOGY = {
    "CITES": Cites, "AMENDS": Amends, "SUPERSEDES": Supersedes, "EVIDENCES": Evidences,
    "VIOLATES": Violates, "BLOCKS": Blocks,
}
# ★类型合法性矩阵（可失败：非法组合即拒）
CAIRN_EDGE_TYPE_MAP = {
    ("Artifact", "Artifact"): ["CITES", "AMENDS", "SUPERSEDES"],
    ("Artifact", "Precept"): ["VIOLATES"],
    ("Criterion", "Artifact"): ["CITES", "EVIDENCES"],
    ("Criterion", "Criterion"): ["CITES", "AMENDS"],
    ("Fact", "Artifact"): ["EVIDENCES", "CITES"],
    ("Event", "Precept"): ["VIOLATES"],
    ("Event", "Criterion"): ["EVIDENCES", "BLOCKS"],
    ("Erratum", "Artifact"): ["AMENDS", "SUPERSEDES"],
    ("Erratum", "Criterion"): ["AMENDS"],
    ("Seat", "Artifact"): ["CITES", "EVIDENCES"],
    ("Seat", "Precept"): ["VIOLATES"],
}

def check(src, edge, dst):
    allowed = CAIRN_EDGE_TYPE_MAP.get((src, dst))
    if allowed is None:
        return False, "★该（源型,目标型）组合不在矩阵中（未定义 ⇒ 拒）"
    if edge not in allowed:
        return False, "★边型 %s 不允许连 %s→%s（允许：%s）" % (edge, src, dst, "、".join(allowed))
    return True, "✓ 合法：%s -%s-> %s" % (src, edge, dst)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser(); ap.add_argument("--check", nargs=3, metavar=("SRC", "EDGE", "DST")); ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print("  节点型 %d：%s" % (len(CAIRN_NODE_ONTOLOGY), "、".join(CAIRN_NODE_ONTOLOGY)))
        print("  边型 %d：%s" % (len(CAIRN_EDGE_ONTOLOGY), "、".join(CAIRN_EDGE_ONTOLOGY)))
        print("  合法性矩阵 %d 条组合：" % len(CAIRN_EDGE_TYPE_MAP))
        for (s, d), es in CAIRN_EDGE_TYPE_MAP.items(): print("    %-12s → %-12s ｜ %s" % (s, d, "、".join(es)))
    if a.check:
        ok, msg = check(*a.check); print("  " + msg); sys.exit(0 if ok else 1)
