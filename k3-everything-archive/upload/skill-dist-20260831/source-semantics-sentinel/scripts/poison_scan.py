#!/usr/bin/env python3
"""poison_scan.py

语料协同信号启发式扫描工具（source-semantics-sentinel 功能二的自动化部分）。

铁律：本工具输出 = 启发式标记 ≠ 定罪。只输出"需人工复核的可疑模式"，
禁止作为指控性结论使用；全部信号 conf 封顶：单信号 assumed（Low），
多信号同簇叠加 estimated（Medium），永不给 High/empirical。
（规约全文见 references/poisoning_detection.md）

检测四类信号：
  S1 文本重复簇   摘要字符 5-gram shingles Jaccard ≥ 阈值（默认 0.6）的
                  跨条目近重复，并查集聚类（≥2 条）
  S2 账号集中度   头部账号占比 ≥ --top-share（默认 0.30）且条目数 ≥3，
                  或 HHI ≥ --hhi（默认 0.25）
  S3 时间突发聚集 按小时（带时刻）或按日分桶，桶计数 ≥ max(--burst-min,
                  --burst-factor × 非空桶中位数)（默认 5 与 3 倍）
  S4 模板相似度   剥离数字/西文词/标点后骨架完全一致的条目 ≥ --template-min
                  （默认 3）

输入：JSONL（位置参数文件路径，可省略读 stdin），兼容 batch_*.jsonl：
  {"id": "...", "url": "...", "account": "...", "publish_date": "...", "abstract": "..."}
  字段均可选；缺 abstract 的条目不参与 S1/S4，缺 account 不参与 S2，
  缺 publish_date 不参与 S3（field_coverage 中如实统计）。

输出：向 stdout 写入 JSON：
  - signals: 数组，每项含 signal / cluster_id / members / evidence / conf /
             false_positive_risk / next_step；多信号成员重叠 ≥50% 时
             相关信号 conf 升 estimated 并注明 multi_signal_overlap
  - summary / field_coverage / data_cutoff / params / disclaimer

仅使用 Python 标准库。退出码：0 正常；1 --smoke 断言失败；2 输入错误。
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime

DISCLAIMER = ("本报告为启发式可疑模式标记，非定罪结论：所有信号仅表示"
              "需人工复核的可疑模式；信号类型名（如协同水军/AI 淤泥）为"
              "启发式标签，不构成对任何主体的指控。conf 封顶规则：单信号 "
              "assumed，多信号同簇叠加 estimated，永不给 High/empirical。")

FP_RISK = {
    "S1": "误报风险高：新闻通稿正常转载、官方公告合规引用、系列报告（月报等）"
          "天然相似；同一事件的多媒体正常报道亦成簇。",
    "S2": "误报风险很高：小众话题活跃者本少、垂直社区意见领袖正常高产、"
          "采集渠道偏差均可致集中；单独出现几乎不构成复核价值。",
    "S3": "误报风险很高：突发新闻（发布会/政策/事故）必然造成时间聚集，"
          "这是正常舆论的典型形态，须结合 S1/S4 才有指向性。",
    "S4": "误报风险中：行业通稿、年报固定章节、法律文书套话天然模板化。",
}

NEXT_STEP = {
    "S1": "人工抽簇内 3 篇原文逐句对比，查是否同一通稿/各自独立采写。",
    "S2": "人工查头部账号注册时间、历史发文主题、是否披露利益关系。",
    "S3": "人工核对窗口前后是否有对应现实事件（发布会/公告/新闻）。",
    "S4": "人工比对骨架差异槽位，查是否同一来源通稿改发。",
}

_DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M", "%Y-%m-%d",
)


# ---------------- 基础工具 ----------------

# 归一化剥离字符类（显式 \u 转义中文弯引号，避免 ASCII 引号截断字符串）
_STRIP_CLASS = (
    "[\\s，。！？、；："
    "“”‘’"  # " " ' '
    "（）《》〈〉【】\\[\\](),.!?;:'\"<>-]+"
)
_STRIP_RE = re.compile(_STRIP_CLASS)


def normalize_text(s):
    return _STRIP_RE.sub("", s or "")


def shingles(s, n=5):
    s = normalize_text(s)
    if len(s) < n:
        return {s} if s else set()
    return {s[i: i + n] for i in range(len(s) - n + 1)}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)


def skeleton(s):
    """模板骨架：小写化后剥数字、西文词、空白与标点。"""
    s = (s or "").lower()
    s = re.sub(r"\d+", "", s)
    s = re.sub(r"[a-z]+", "", s)
    return _STRIP_RE.sub("", s)


def parse_dt(s):
    s = (s or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt), ("H" in fmt)
        except ValueError:
            continue
    return None, False


class UnionFind:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


# ---------------- 各信号 ----------------

def scan_s1(items, sim_threshold):
    """近重复簇：返回 [{members, sim_range}]，members 为条目 id。"""
    docs = [(it["id"], shingles(it.get("abstract", ""))) for it in items
            if it.get("abstract")]
    docs = [(i, s) for i, s in docs if s]
    uf = UnionFind(len(docs))
    sims = {}
    for a in range(len(docs)):
        for b in range(a + 1, len(docs)):
            sim = jaccard(docs[a][1], docs[b][1])
            if sim >= sim_threshold:
                uf.union(a, b)
                sims[(a, b)] = sim
    clusters = {}
    for idx in range(len(docs)):
        clusters.setdefault(uf.find(idx), []).append(idx)
    out = []
    for members in clusters.values():
        if len(members) < 2:
            continue
        pair_sims = [v for (a, b), v in sims.items()
                     if a in members and b in members]
        out.append({
            "members": sorted(docs[i][0] for i in members),
            "sim_range": [round(min(pair_sims), 3), round(max(pair_sims), 3)],
        })
    return out


def scan_s2(items, top_share, hhi_threshold):
    counts = Counter(it["account"] for it in items if it.get("account"))
    total = sum(counts.values())
    if total < 2:
        return None
    top_acc, top_n = counts.most_common(1)[0]
    share = top_n / total
    hhi = sum((n / total) ** 2 for n in counts.values())
    if (share >= top_share and top_n >= 3) or hhi >= hhi_threshold:
        return {
            "members": ["account:%s" % a for a, _ in counts.most_common(5)],
            "top_account": top_acc, "top_share": round(share, 3),
            "top_count": top_n, "hhi": round(hhi, 3), "total": total,
        }
    return None


def scan_s3(items, burst_min, burst_factor):
    buckets = Counter()
    member_of = {}
    has_time = False
    for it in items:
        dt, with_time = parse_dt(it.get("publish_date", ""))
        if not dt:
            continue
        has_time = has_time or with_time
        key = dt.strftime("%Y-%m-%dT%H:00") if with_time else dt.strftime("%Y-%m-%d")
        buckets[key] += 1
        member_of.setdefault(key, []).append(it["id"])
    if len(buckets) < 2:
        return []
    counts = sorted(buckets.values())
    med = counts[len(counts) // 2] if len(counts) % 2 else \
        (counts[len(counts) // 2 - 1] + counts[len(counts) // 2]) / 2
    threshold = max(burst_min, burst_factor * med)
    out = []
    for key, n in sorted(buckets.items()):
        if n >= threshold:
            out.append({
                "members": sorted(member_of[key]),
                "window": key, "count": n,
                "median_bucket": med, "threshold": threshold,
                "bucket_unit": "hour" if has_time else "day",
            })
    return out


def scan_s4(items, template_min, template_sim):
    """近模板聚类：骨架 3-gram shingles Jaccard ≥ template_sim（默认 0.8，
    作为"共享 ≥80% 字符"的近似），簇内 ≥ template_min 条。"""
    docs = [(it["id"], skeleton(it.get("abstract", ""))) for it in items]
    docs = [(i, s) for i, s in docs if len(s) >= 10]
    sh = [(i, {s[k: k + 3] for k in range(len(s) - 2)}) for i, s in docs]
    uf = UnionFind(len(sh))
    for a in range(len(sh)):
        for b in range(a + 1, len(sh)):
            if jaccard(sh[a][1], sh[b][1]) >= template_sim:
                uf.union(a, b)
    clusters = {}
    for idx in range(len(sh)):
        clusters.setdefault(uf.find(idx), []).append(idx)
    out = []
    for members in clusters.values():
        if len(members) < template_min:
            continue
        rep = docs[members[0]][1]
        out.append({"members": sorted(docs[i][0] for i in members),
                    "count": len(members),
                    "skeleton_excerpt": rep[:40]})
    return out


# ---------------- 主流程 ----------------

def run(text, params):
    items, errors = [], []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append({"line": lineno, "error": "非法 JSON: %s" % e})
            continue
        if not isinstance(obj, dict):
            errors.append({"line": lineno, "error": "行不是 JSON 对象"})
            continue
        obj.setdefault("id", "L%d" % lineno)
        items.append(obj)

    signals = []

    for i, c in enumerate(scan_s1(items, params["sim_threshold"]), 1):
        signals.append({
            "signal": "S1", "cluster_id": "S1-C%d" % i,
            "members": c["members"],
            "evidence": "摘要近重复：%d 条，两两相似度区间 %s"
                        % (len(c["members"]), c["sim_range"]),
            "conf": "assumed",
            "false_positive_risk": FP_RISK["S1"],
            "next_step": NEXT_STEP["S1"],
        })

    s2 = scan_s2(items, params["top_share"], params["hhi"])
    if s2:
        signals.append({
            "signal": "S2", "cluster_id": "S2-C1",
            "members": s2["members"],
            "evidence": "账号集中：头部账号「%s」%d/%d 条（占比 %.1f%%），"
                        "HHI=%.3f" % (s2["top_account"], s2["top_count"],
                                     s2["total"], s2["top_share"] * 100,
                                     s2["hhi"]),
            "conf": "assumed",
            "false_positive_risk": FP_RISK["S2"],
            "next_step": NEXT_STEP["S2"],
        })

    for i, c in enumerate(scan_s3(items, params["burst_min"],
                                  params["burst_factor"]), 1):
        signals.append({
            "signal": "S3", "cluster_id": "S3-C%d" % i,
            "members": c["members"],
            "evidence": "时间突发：%s 桶（%s）内 %d 条 ≥ 阈值 %s"
                        "（非空桶中位 %s）"
                        % (c["bucket_unit"], c["window"], c["count"],
                           c["threshold"], c["median_bucket"]),
            "conf": "assumed",
            "false_positive_risk": FP_RISK["S3"],
            "next_step": NEXT_STEP["S3"],
        })

    for i, c in enumerate(scan_s4(items, params["template_min"],
                                  params["template_sim"]), 1):
        signals.append({
            "signal": "S4", "cluster_id": "S4-C%d" % i,
            "members": c["members"],
            "evidence": "模板骨架一致：%d 条共享骨架「%s…」"
                        % (c["count"], c["skeleton_excerpt"]),
            "conf": "assumed",
            "false_positive_risk": FP_RISK["S4"],
            "next_step": NEXT_STEP["S4"],
        })

    # 多信号叠加：成员集合 Jaccard ≥ 0.5 → 双方 conf 升 estimated（封顶）
    for a in range(len(signals)):
        for b in range(a + 1, len(signals)):
            ma, mb = set(signals[a]["members"]), set(signals[b]["members"])
            if ma and mb and jaccard(ma, mb) >= 0.5:
                for s in (signals[a], signals[b]):
                    if s["conf"] == "assumed":
                        s["conf"] = "estimated"
                        s["evidence"] += "；与 %s 成员重叠 ≥50%%，多信号叠加" \
                                         % (signals[b] if s is signals[a]
                                            else signals[a])["cluster_id"]

    field_cov = {
        "abstract": sum(1 for it in items if it.get("abstract")),
        "account": sum(1 for it in items if it.get("account")),
        "publish_date": sum(1 for it in items if it.get("publish_date")),
    }
    return {
        "signals": signals,
        "summary": {
            "items": len(items),
            "signal_counts": dict(Counter(s["signal"] for s in signals)),
            "max_conf": "estimated" if any(s["conf"] == "estimated"
                                           for s in signals) else
                        ("assumed" if signals else "none"),
        },
        "field_coverage": field_cov,
        "errors": errors,
        "data_cutoff": date.today().isoformat(),
        "params": params,
        "disclaimer": DISCLAIMER,
    }


DEFAULT_PARAMS = {
    "sim_threshold": 0.6, "top_share": 0.30, "hhi": 0.25,
    "burst_min": 5, "burst_factor": 3.0, "template_min": 3,
    "template_sim": 0.8,
}


# ---------------- smoke ----------------

def _mk(i, acc, day, txt):
    return {"id": "P%d" % i, "url": "https://example.com/%d" % i,
            "account": acc, "publish_date": day, "abstract": txt}


# 命中语料：5 篇同模板近重复（仅数字槽位/结尾微差；S1 全文 5-gram 命中
# 其中 4 篇——数字改动较大的一篇落在 0.6 阈值下，S4 骨架命中全部 5 篇）
# 集中在同一小时窗口（S3：5 ≥ max(5, 3×中位1)）；acc-a 占 4/10=40% ≥ 30%
# 且 ≥3（S2）；另 5 篇分散正常文。干净语料 6 篇分散独立文应零命中。
_AB = "【重磅】某地重大项目正式落地，总投资 12 亿元，预计带动就业 3000 人，"
HIT_CORPUS = [
    _mk(1, "acc-a", "2026-08-20T14:05:00", _AB + "当地群众纷纷表示期待。"),
    _mk(2, "acc-b", "2026-08-20T14:20:00",
        "【重磅】某地重大项目正式落地，总投资 15 亿元，预计带动就业 3200 人，当地群众纷纷表示期待。"),
    _mk(3, "acc-c", "2026-08-20T14:40:00", _AB + "当地群众纷纷表示期待。"),
    _mk(4, "acc-a", "2026-08-20T14:50:00", _AB + "当地群众纷纷表示期待已久。"),
    _mk(10, "acc-a", "2026-08-20T14:55:00", _AB + "当地群众纷纷表示期待万分。"),
    _mk(5, "acc-a", "2026-08-21T09:00:00", "昨夜一场小雨过后，老城的路面积水很快退去，环卫工人凌晨四点开始清扫。"),
    _mk(6, "acc-d", "2026-08-22T10:00:00", "读书会在社区中心举办，主题是宋代山水画的留白与意境，参与者讨论了两个小时。"),
    _mk(7, "acc-e", "2026-08-23T11:00:00", "马拉松赛事周末开跑，组委会公布了补给点分布与交通管制方案。"),
    _mk(8, "acc-f", "2026-08-24T12:00:00", "农贸市场新设公平秤，摊主与顾客都觉得方便了不少。"),
    _mk(9, "acc-g", "2026-08-25T13:00:00", "图书馆延长开放时间至晚上十点，备考的学生表示非常实用。"),
]

CLEAN_CORPUS = [
    _mk(1, "acc-a", "2026-08-20T09:00:00", "清晨的公园里有老人打太极，湖边柳树刚抽新芽。"),
    _mk(2, "acc-b", "2026-08-21T15:00:00", "城南高架桥完成检修，明早六点恢复通行。"),
    _mk(3, "acc-c", "2026-08-22T18:00:00", "社区医院新增了夜间门诊，覆盖内科与儿科。"),
    _mk(4, "acc-d", "2026-08-23T08:00:00", "今年的桂花比往年开得早，香气已经飘进了地铁站。"),
    _mk(5, "acc-e", "2026-08-24T20:00:00", "青年路菜市场改造后重新开业，摊位增加了遮雨棚。"),
    _mk(6, "acc-f", "2026-08-25T07:00:00", "公交集团新开三条接驳线路，衔接地铁站与产业园。"),
]


def run_smoke():
    failures = []

    def expect(cond, msg):
        if not cond:
            failures.append(msg)

    hit_text = "\n".join(json.dumps(o, ensure_ascii=False) for o in HIT_CORPUS)
    res = run(hit_text, dict(DEFAULT_PARAMS))
    sig_types = {s["signal"] for s in res["signals"]}

    expect("S1" in sig_types, "smoke: S1 文本重复簇未命中")
    expect("S3" in sig_types, "smoke: S3 时间突发未命中")
    expect("S4" in sig_types, "smoke: S4 模板骨架未命中")
    expect("S2" in sig_types, "smoke: S2 账号集中度未命中")
    upgraded = [s for s in res["signals"] if s["conf"] == "estimated"]
    expect(upgraded, "smoke: 多信号叠加应至少一条 conf=estimated")
    expect(all(s["conf"] in ("assumed", "estimated") for s in res["signals"]),
           "smoke: conf 越界（只允许 assumed/estimated）")
    expect("非定罪" in res["disclaimer"] or "≠ 定罪" in DISCLAIMER,
           "smoke: disclaimer 缺非定罪声明")

    clean_text = "\n".join(json.dumps(o, ensure_ascii=False) for o in CLEAN_CORPUS)
    cres = run(clean_text, dict(DEFAULT_PARAMS))
    expect(cres["signals"] == [],
           "smoke: 干净语料应零命中，实为 %s"
           % [(s["signal"], s["cluster_id"]) for s in cres["signals"]])

    if failures:
        print("SMOKE FAILED:")
        for f_ in failures:
            print("  - " + f_)
        return 1
    print("SMOKE OK: 命中路径 %s（max_conf=%s）；干净路径零命中通过"
          % (res["summary"]["signal_counts"], res["summary"]["max_conf"]))
    return 0


# ---------------- CLI ----------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="语料协同信号启发式扫描（S1 重复簇/S2 账号集中度/"
                    "S3 时间突发/S4 模板相似度）。输出为可疑模式标记，"
                    "非定罪结论，conf 封顶 assumed/estimated。")
    p.add_argument("file", nargs="?", help="JSONL 文件路径；缺省读 stdin")
    p.add_argument("--pretty", action="store_true",
                   help="以缩进格式输出 JSON（默认紧凑输出）")
    p.add_argument("--sim-threshold", type=float, default=0.6,
                   help="S1 近重复 Jaccard 阈值（默认 0.6）")
    p.add_argument("--top-share", type=float, default=0.30,
                   help="S2 头部账号占比阈值（默认 0.30）")
    p.add_argument("--hhi", type=float, default=0.25,
                   help="S2 HHI 阈值（默认 0.25）")
    p.add_argument("--burst-min", type=int, default=5,
                   help="S3 桶计数绝对下限（默认 5）")
    p.add_argument("--burst-factor", type=float, default=3.0,
                   help="S3 中位数倍数（默认 3.0）")
    p.add_argument("--template-min", type=int, default=3,
                   help="S4 模板骨架一致最小条数（默认 3）")
    p.add_argument("--template-sim", type=float, default=0.8,
                   help="S4 模板骨架相似度阈值（默认 0.8）")
    p.add_argument("--smoke", action="store_true",
                   help="运行内置合成语料自检（命中+零命中两路径）后退出")
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
        print("输入错误：输入为空", file=sys.stderr)
        return 2

    params = {
        "sim_threshold": args.sim_threshold, "top_share": args.top_share,
        "hhi": args.hhi, "burst_min": args.burst_min,
        "burst_factor": args.burst_factor, "template_min": args.template_min,
        "template_sim": args.template_sim,
    }
    result = run(text, params)
    json.dump(result, sys.stdout, ensure_ascii=False,
              indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
