#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
decision_pipeline.py — 统一决策套件薄编排器（纯标准库，无第三方依赖）。

严肃等级: L1（原型级编排层）。诚实性声明：
  - 本脚本只做【编排、契约校验与统一包壳】，不重实现任何下游引擎算法：
    scoring_engine（多维打分）与 psm_balance（PSM 公平对比）仅做契约校验+子进程转发；
     Gale-Shapley 仅在 quant-frontier-lab 脚本不在场时使用内联教科书版回退（输出注明 engine=inline）。
  - decision-sys 四引擎（hrank/NSGA-II/MCTS/Nested Sampling）代码资产未移交，
    本脚本【不实现、不模拟】其任何数值；相关数值一律 conf=assumed + provenance=转述，
    详见 references/architecture.md 与 references/interface_contracts.md。
  - 所有输出固定 honesty={level:"L1", unverified:true}：用于真实志愿填报前必须人工复核。

输入（stdin JSON）:
{
  "stage": "score" | "match" | "psm" | "full",
  "data_cutoff": "YYYY-MM-DD",          # 公共必填（亦可放入 payload）
  "conf": "empirical|estimated|assumed", # 可选，缺省保守取 assumed
  "payload": { ... 逐段契约见下 ... }
}

分段 payload：
  score: scoring_engine 契约——单个对象或数组，每项
         {option, dimensions:[{name, score(0-10), weight(>0), conf}],
          negative_items?:[{name, score, weight(<0), conf}], evidence_refs?:[...]}
  match: {students:[{id, prefs:[school_id...]}],
          schools:[{id, capacity:int>=1, prefs:[student_id...],
                    capacity_source?:..., prefs_basis?:...}],
          proposer?:"students"|"schools"}
  psm:   {covariates:[...], rows:[{id, treated:0|1, outcome, ...}]}
  full:  {score:<score payload>, match:<match payload>,
          gate?:{math1_mock_score:float, threshold?:55, gated_schools:[school_id...]}}
         依次执行 门规过滤(可选)→score→match。

输出（stdout JSON 统一包壳）:
{stage, version, result, engine, data_cutoff, conf,
 honesty:{level:"L1", unverified:true, note}, top3_likely_wrong:[3 条]}

引擎解析顺序（逐段独立，路径可配）：
  CLI 参数(--scoring-script/--gs-script/--psm-script) > 环境变量
  (UDS_SCORING_SCRIPT/UDS_GS_SCRIPT/UDS_PSM_SCRIPT) > 常见安装位
  (<技能安装位>/... 与 skills 同级目录)。

失败传播：校验失败 exit=2；conf 出现 Conflict 整链阻断转人工 exit=3；
下游脚本非零退出原样上抛 exit=4。

冒烟：python3 decision_pipeline.py --smoke   （score 小样例 + 4 考生×3 校匹配，exit=0）
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v1.0（2026-08-24）"
CONF_VOCAB = ("empirical", "estimated", "assumed")  # 对齐 scoring_engine.parse_conf
HONESTY = {
    "level": "L1",
    "unverified": True,
    "note": ("薄编排层：仅编排与契约校验，未重实现下游引擎；decision-sys 数值"
             "不在场（conf=assumed+转述）；真实决策前须人工复核。"),
}
SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SCRIPT_DIRS = [
    Path("<技能安装位>"),
    SKILL_DIR.parent,  # 技能同级目录（如 <输出区>/skills/）
]


class PipelineError(Exception):
    """契约校验/编排错误，exit=2。"""


class ConflictBlocked(PipelineError):
    """证据层 Conflict：整链阻断转人工，exit=3。"""


class DownstreamError(PipelineError):
    """下游引擎脚本非零退出，exit=4。"""


# ---------------------------------------------------------------- 公共校验

def check_conf(value, where):
    """校验 conf 词表；Conflict 无机读映射，阻断转人工（铁律）。"""
    if isinstance(value, (int, float)):
        if not 0.0 <= float(value) <= 1.0:
            raise PipelineError("%s 的 conf 数值须在 [0,1]，收到 %r" % (where, value))
        return float(value)
    key = str(value).strip()
    if key.lower() == "conflict":
        raise ConflictBlocked("%s 出现 conf=Conflict：无机读映射，整链暂停转人工。" % where)
    if key.lower() not in CONF_VOCAB:
        raise PipelineError("%s 的 conf 必须是 empirical/estimated/assumed 之一或 [0,1] 数值，"
                            "收到 %r" % (where, value))
    return key.lower()


def check_data_cutoff(value):
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise PipelineError("公共必填字段 data_cutoff 缺失或格式非 YYYY-MM-DD：%r" % (value,))
    return value


def find_script(cli_path, env_var, rel):
    """按 CLI > 环境变量 > 常见安装位解析下游脚本路径；找不到返回 None。"""
    for cand in ([cli_path] if cli_path else []) + ([os.environ.get(env_var)] if os.environ.get(env_var) else []):
        p = Path(cand).expanduser()
        if p.is_file():
            return p
        raise PipelineError("显式指定的脚本路径不存在：%s" % cand)
    for base in DEFAULT_SCRIPT_DIRS:
        p = base / rel
        if p.is_file():
            return p
    return None


def run_script(script, payload, extra_args=()):
    """子进程调用下游引擎脚本（stdin/stdout JSON），原样返回其 stdout 解析结果。"""
    proc = subprocess.run(
        [sys.executable, str(script)] + list(extra_args),
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        raise DownstreamError("下游脚本 %s 退出码 %s：%s" % (script, proc.returncode,
                              proc.stderr.strip()[:400]))
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise DownstreamError("下游脚本 %s 的 stdout 不是合法 JSON：%s" % (script, e))


# ---------------------------------------------------------------- score 段

def validate_score_payload(raw):
    """按 scoring_engine 契约校验并归一化（不重实现其计算）。"""
    options = raw if isinstance(raw, list) else [raw]
    if not options or not isinstance(options, list):
        raise PipelineError("score 段 payload 须为对象或非空数组")
    norm = []
    for i, opt in enumerate(options):
        where = "score 段第 %d 项(%s)" % (i + 1, opt.get("option", "未命名") if isinstance(opt, dict) else "?")
        if not isinstance(opt, dict) or not opt.get("option"):
            raise PipelineError("%s 缺少 option 字段" % where)
        dims = opt.get("dimensions")
        if not dims:
            raise PipelineError("%s 缺少非空 dimensions" % where)
        for kind, items, sign in (("dimension", dims, +1),
                                  ("negative_item", opt.get("negative_items", []), -1)):
            for it in items:
                for f in ("name", "score", "weight", "conf"):
                    if f not in it:
                        raise PipelineError("%s 的 %s 缺少字段 %r" % (where, kind, f))
                if not 0.0 <= float(it["score"]) <= 10.0:
                    raise PipelineError("%s 的 %s %r 分值须在 0-10" % (where, kind, it["name"]))
                w = float(it["weight"])
                if kind == "dimension" and w <= 0:
                    raise PipelineError("%s 的维度 %r 权重必须 > 0" % (where, it["name"]))
                if kind == "negative_item" and w >= 0:
                    raise PipelineError("%s 的负权重项 %r 权重必须 < 0" % (where, it["name"]))
                check_conf(it["conf"], "%s 的 %s %r" % (where, kind, it["name"]))
        norm.append(opt)
    return norm if isinstance(raw, list) else norm[0]


def stage_score(payload, args):
    norm = validate_score_payload(payload)
    script = find_script(args.scoring_script, "UDS_SCORING_SCRIPT",
                         "multi-dimensional-option-scoring/scripts/scoring_engine.py")
    if script:
        result = run_script(script, norm)
        engine = {"mode": "subprocess", "script": str(script)}
    else:
        # 诚实降级：引擎不在场时只交付"契约校验通过"的归一化载荷，绝不代算。
        result = {"validated_payload": norm,
                  "notice": ("scoring_engine.py 不在场：本段仅完成契约校验与转发格式化，"
                             "未执行加权计算；安装 multi-dimensional-option-scoring 后重跑。")}
        engine = {"mode": "validate_only", "script": None}
    return result, engine


# ---------------------------------------------------------------- 匹配段

def gale_shapley_inline(students, schools, proposer="students"):
    """教科书版延迟接受（内联回退实现）。proposer 容量 1，receiver 容量 capacity。"""
    if proposer == "students":
        proposers, receivers = students, schools
    else:
        proposers, receivers = schools, students
    p_prefs = {p["id"]: list(p["prefs"]) for p in proposers}
    r_cap = {r["id"]: int(r.get("capacity", 1)) for r in receivers}
    r_rank = {r["id"]: {pid: i for i, pid in enumerate(r["prefs"])} for r in receivers}
    next_idx = {p["id"]: 0 for p in proposers}
    held = {r["id"]: [] for r in receivers}
    engaged = {}
    free = [p["id"] for p in proposers]
    while free:
        p = free.pop(0)
        prefs = p_prefs[p]
        if next_idx[p] >= len(prefs):
            continue
        r = prefs[next_idx[p]]
        next_idx[p] += 1
        if r not in r_rank or p not in r_rank[r]:
            if next_idx[p] < len(prefs):
                free.append(p)
            continue
        rank = r_rank[r]
        if len(held[r]) < r_cap[r]:
            held[r].append(p)
            engaged[p] = r
        else:
            worst = max(held[r], key=lambda q: rank[q])
            if rank[p] < rank[worst]:
                held[r].remove(worst)
                held[r].append(p)
                engaged[p] = r
                del engaged[worst]
                free.append(worst)
            elif next_idx[p] < len(prefs):
                free.append(p)
    return engaged


def find_blocking_pairs(students, schools, engaged_by_student):
    """阻塞对扫描（学生-院校视角），契约要求结果为 []。"""
    s_rank = {s["id"]: {sch: i for i, sch in enumerate(s["prefs"])} for s in students}
    sch_rank = {sch["id"]: {st: i for i, st in enumerate(sch["prefs"])} for sch in schools}
    roster = {sch["id"]: [] for sch in schools}
    for st, sch in engaged_by_student.items():
        roster[sch].append(st)
    blocking = []
    for s in students:
        sid, cur = s["id"], engaged_by_student.get(s["id"])
        for sch in schools:
            sch_id = sch["id"]
            if cur == sch_id or sch_id not in s_rank[sid] or sid not in sch_rank[sch_id]:
                continue
            if cur is not None and s_rank[sid][sch_id] >= s_rank[sid][cur]:
                continue
            rank = sch_rank[sch_id]
            if len(roster[sch_id]) < int(sch.get("capacity", 1)) or \
                    rank[sid] < rank[max(roster[sch_id], key=lambda q: rank[q])]:
                blocking.append([sid, sch_id])
    return blocking, roster


def validate_match_payload(payload):
    if not isinstance(payload, dict):
        raise PipelineError("match 段 payload 须为对象 {students, schools}")
    students, schools = payload.get("students"), payload.get("schools")
    if not students or not schools:
        raise PipelineError("match 段缺少非空 students/schools")
    for side, rows in (("students", students), ("schools", schools)):
        ids = set()
        for r in rows:
            if "id" not in r or not isinstance(r.get("prefs"), list):
                raise PipelineError("match 段 %s 每行须含 id 与 prefs 数组" % side)
            if r["id"] in ids:
                raise PipelineError("match 段 %s 存在重复 id：%r" % (side, r["id"]))
            ids.add(r["id"])
        if side == "schools":
            for r in rows:
                if int(r.get("capacity", 1)) < 1:
                    raise PipelineError("院校 %r 的 capacity 必须 >= 1" % r["id"])
    known = {s["id"] for s in schools}
    for s in students:
        unknown = [p for p in s["prefs"] if p not in known]
        if unknown:
            raise PipelineError("考生 %r 的 prefs 含未知院校 id：%r" % (s["id"], unknown))
    if payload.get("conf"):
        check_conf(payload["conf"], "match 段")
    proposer = payload.get("proposer", "students")
    if proposer not in ("students", "schools"):
        raise PipelineError("proposer 仅支持 students|schools，收到 %r" % proposer)
    return students, schools, proposer


def stage_match(payload, args):
    students, schools, proposer = validate_match_payload(payload)
    script = find_script(args.gs_script, "UDS_GS_SCRIPT",
                         "quant-frontier-lab/scripts/gale_shapley.py")
    extras = {s["id"]: {k: s[k] for k in ("capacity_source", "prefs_basis") if k in s}
              for s in schools}
    extras = {k: v for k, v in extras.items() if v}
    if script:
        fwd = {"students": students, "schools": schools}
        result = run_script(script, fwd,
                            ("--proposer=schools",) if proposer == "schools" else ())
        engine = {"mode": "subprocess", "script": str(script)}
    else:
        engaged = gale_shapley_inline(students, schools, proposer)
        if proposer != "students":
            engaged = {v: k for k, v in engaged.items()}
        blocking, roster = find_blocking_pairs(students, schools, engaged)
        assert not blocking, "稳定性自检失败：存在 %d 个阻塞对 %r" % (len(blocking), blocking)
        result = {
            "proposer": proposer,
            "matches": [{"student": s, "school": sch} for s, sch in sorted(engaged.items())],
            "unmatched_students": [s["id"] for s in students if s["id"] not in engaged],
            "school_rosters": {k: v for k, v in roster.items() if v},
            "blocking_pairs": blocking,
            "n_blocking_pairs": len(blocking),
            "stability_check": "PASS" if not blocking else "FAIL",
            "note": "quant-frontier-lab gale_shapley.py 不在场，使用内联教科书版实现。",
        }
        engine = {"mode": "inline", "script": None}
    if extras:
        result["contract_extras"] = extras  # §6.2 增补：容量/偏好依据随结果传递
    if result.get("stability_check") == "FAIL":
        raise PipelineError("Gale-Shapley 稳定性自检 FAIL（阻塞对 %d 个），按失败传播规则上抛。"
                            % result.get("n_blocking_pairs", -1))
    return result, engine


# ---------------------------------------------------------------- psm 段

def stage_psm(payload, args):
    if not isinstance(payload, dict) or not payload.get("covariates") or not payload.get("rows"):
        raise PipelineError("psm 段 payload 须含非空 covariates 与 rows")
    for r in payload["rows"]:
        for f in ("id", "treated", "outcome"):
            if f not in r:
                raise PipelineError("psm 段 rows 每行须含 id/treated/outcome")
        if r["treated"] not in (0, 1):
            raise PipelineError("psm 段 treated 仅取 0|1，收到 %r" % r["treated"])
    if payload.get("conf"):
        check_conf(payload["conf"], "psm 段")
    script = find_script(args.psm_script, "UDS_PSM_SCRIPT",
                         "quant-frontier-lab/scripts/psm_balance.py")
    if script:
        fwd = {k: payload[k] for k in ("covariates", "rows")}
        result = run_script(script, fwd)
        engine = {"mode": "subprocess", "script": str(script)}
    else:
        # 不重实现 PSM（诚实铁律）：仅交付校验通过声明。
        result = {"validated_payload": {"covariates": payload["covariates"],
                                        "n_rows": len(payload["rows"])},
                  "notice": ("psm_balance.py 不在场：本段仅完成契约校验，未执行匹配计算"
                             "（套件不重实现 PSM）；安装 quant-frontier-lab 后重跑。")}
        engine = {"mode": "validate_only", "script": None}
    return result, engine


# ---------------------------------------------------------------- 完整段

def apply_gate(payload, gate):
    """数一门规：模考分 < 阈值时把数一依赖校移出可选集（候选池切换）。"""
    score = float(gate["math1_mock_score"])
    threshold = float(gate.get("threshold", 55))
    gated = set(gate.get("gated_schools", []))
    if score >= threshold or not gated:
        return payload, {"gate_open": True, "math1_mock_score": score,
                         "threshold": threshold, "removed": []}
    match = payload["match"]
    removed = [s["id"] for s in match["schools"] if s["id"] in gated]
    payload = dict(payload)
    payload["match"] = {
        "students": [{**s, "prefs": [p for p in s["prefs"] if p not in gated]}
                     for s in match["students"]],
        "schools": [s for s in match["schools"] if s["id"] not in gated],
    }
    return payload, {"gate_open": False, "math1_mock_score": score,
                     "threshold": threshold, "removed": removed,
                     "note": "数一模考 <55：数一依赖校移出可选集（见 september_lock_protocol.md）"}


def stage_full(payload, args):
    if not isinstance(payload, dict) or "score" not in payload or "match" not in payload:
        raise PipelineError("full 段 payload 须含 score 与 match 两个子载荷")
    gate_info = None
    if payload.get("gate"):
        if "math1_mock_score" not in payload["gate"]:
            raise PipelineError("full 段 gate 缺少 math1_mock_score")
        payload, gate_info = apply_gate(payload, payload["gate"])
    score_result, score_engine = stage_score(payload["score"], args)
    match_result, match_engine = stage_match(payload["match"], args)
    result = {"gate": gate_info, "score": score_result, "match": match_result}
    engine = {"score": score_engine, "match": match_engine}
    return result, engine


# ---------------------------------------------------------------- 包壳与冒烟

TOP3 = {
    "score": [
        "权重体系为主观设定：±20% 扰动下中段名次可能互换，按档位而非名次使用。",
        "维度 conf 可能高估（B 级证据给了 A 级置信度）；存疑应向下取档。",
        "引擎不在场时本段仅契约校验未实际计算（见 result.notice），勿当成分数结果引用。",
    ],
    "match": [
        "院校偏好=预估分（conf=assumed 教学示范），非真实选拔规则文本，升级所需三项数据见 references/september_lock_protocol.md。",
        "容量若非新东方面板统考名额实数（capacity_source 缺省），匹配结果不提供超出分数序的信息。",
        "稳定性自检 PASS ≠ 填报最优：真实填报存在策略性行为，本算法不处理。",
    ],
    "psm": [
        "PSM 仅平衡已观测混淆，未观测混淆仍致偏误。",
        "协变量清单属领域判断，必须人工确认（引擎 hard_notice 同）。",
        "引擎不在场时本段仅契约校验未实际匹配（见 result.notice）。",
    ],
    "full": [
        "数一门规为转述级阈值（Nested Sampling 后验 55 分，conf=assumed），代码资产移交前不得升级为实证。",
        "score 段名次扰动敏感，match 段偏好为假想同侪——两误差沿链路叠加，结论按 L1 使用。",
        "任一子段引擎不在场时对应子结果仅为校验通过声明（见 result.*.notice），不得当作计算结果。",
    ],
}


def envelope(stage, result, engine, data_cutoff, conf):
    return {
        "stage": stage,
        "version": VERSION,
        "engine": engine,
        "result": result,
        "data_cutoff": data_cutoff,
        "conf": conf,
        "honesty": HONESTY,
        "top3_likely_wrong": TOP3[stage],
    }


SMOKE_INPUT = {
    "stage": "full",
    "data_cutoff": "2026-08-24",
    "conf": "assumed",
    "payload": {
        "score": [
            {"option": "示范校A", "dimensions": [
                {"name": "方向契合", "score": 8.0, "weight": 0.3, "conf": "estimated"},
                {"name": "录取安全", "score": 7.0, "weight": 0.3, "conf": "assumed"}]},
            {"option": "示范校B", "dimensions": [
                {"name": "方向契合", "score": 6.0, "weight": 0.3, "conf": "estimated"},
                {"name": "录取安全", "score": 8.5, "weight": 0.3, "conf": "empirical"}]},
        ],
        "match": {
            "students": [
                {"id": "s1", "prefs": ["A", "B", "C"]},
                {"id": "s2", "prefs": ["A", "C", "B"]},
                {"id": "s3", "prefs": ["B", "A", "C"]},
                {"id": "s4", "prefs": ["C", "B", "A"]},
            ],
            "schools": [
                {"id": "A", "capacity": 1, "prefs": ["s1", "s2", "s3", "s4"],
                 "capacity_source": "假想", "prefs_basis": "estimated_score"},
                {"id": "B", "capacity": 2, "prefs": ["s3", "s1", "s4", "s2"]},
                {"id": "C", "capacity": 1, "prefs": ["s4", "s2", "s1", "s3"]},
            ],
        },
        "gate": {"math1_mock_score": 60, "threshold": 55, "gated_schools": ["C"]},
    },
}


def smoke(args):
    out = dispatch(SMOKE_INPUT, args)
    checks = [
        ("包壳五键齐全", all(k in out for k in
         ("result", "data_cutoff", "conf", "honesty", "top3_likely_wrong"))),
        ("honesty L1+unverified", out["honesty"]["level"] == "L1" and out["honesty"]["unverified"] is True),
        ("match 阻塞对=0", out["result"]["match"]["n_blocking_pairs"] == 0
         and out["result"]["match"]["stability_check"] == "PASS"),
        ("match 产出 4 考生", len(out["result"]["match"]["matches"]) == 4),
        ("门规开（60>=55，C 保留）", out["result"]["gate"]["gate_open"] is True),
        ("top3 恰 3 条", len(out["top3_likely_wrong"]) == 3),
    ]
    failed = [name for name, ok in checks if not ok]
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    if failed:
        print("SMOKE FAIL: %s" % "; ".join(failed), file=sys.stderr)
        return 1
    # 门规关闭路径再验一次（<55 → 数一依赖校移除）
    closed = dict(SMOKE_INPUT)
    closed["payload"] = dict(SMOKE_INPUT["payload"])
    closed["payload"]["gate"] = {"math1_mock_score": 40, "threshold": 55, "gated_schools": ["C"]}
    out2 = dispatch(closed, args)
    g2 = out2["result"]["gate"]
    if g2["gate_open"] is not False or g2["removed"] != ["C"]:
        print("SMOKE FAIL: 门规关闭路径异常 %r" % g2, file=sys.stderr)
        return 1
    print("SMOKE PASS: score 小样例 + 4考生×3校匹配 + 门规开/关两路径全部通过"
          "（score=%s, match=%s）" % (out["engine"]["score"]["mode"], out["engine"]["match"]["mode"]))
    return 0


STAGES = {"score": stage_score, "match": stage_match, "psm": stage_psm, "full": stage_full}


def dispatch(req, args):
    stage = req.get("stage")
    if stage not in STAGES:
        raise PipelineError("stage 必须是 score|match|psm|full，收到 %r" % (stage,))
    payload = req.get("payload")
    if payload is None:
        raise PipelineError("缺少 payload")
    data_cutoff = check_data_cutoff(req.get("data_cutoff")
                                    or (payload.get("data_cutoff") if isinstance(payload, dict) else None))
    conf = check_conf(req.get("conf", "assumed"), "包壳")
    result, engine = STAGES[stage](payload, args)
    return envelope(stage, result, engine, data_cutoff, conf)


def main():
    p = argparse.ArgumentParser(description="统一决策套件薄编排器（L1 原型；纯标准库）")
    p.add_argument("--smoke", action="store_true", help="自测：score 小样例 + 4考生×3校匹配")
    p.add_argument("--scoring-script", default=None, help="scoring_engine.py 路径（覆盖自动探测）")
    p.add_argument("--gs-script", default=None, help="gale_shapley.py 路径（覆盖自动探测）")
    p.add_argument("--psm-script", default=None, help="psm_balance.py 路径（覆盖自动探测）")
    args = p.parse_args()
    try:
        if args.smoke:
            return smoke(args)
        req = json.load(sys.stdin)
        out = dispatch(req, args)
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    except json.JSONDecodeError as e:
        print("错误：stdin 不是合法 JSON: %s" % e, file=sys.stderr)
        return 2
    except ConflictBlocked as e:
        print("CONFLICT→人工: %s" % e, file=sys.stderr)
        return 3
    except DownstreamError as e:
        print("下游引擎失败: %s" % e, file=sys.stderr)
        return 4
    except PipelineError as e:
        print("契约校验失败: %s" % e, file=sys.stderr)
        return 2
    except AssertionError as e:
        print("稳定性断言失败: %s" % e, file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
