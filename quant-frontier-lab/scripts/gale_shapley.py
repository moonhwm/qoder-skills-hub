#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gale_shapley.py — 院校-考生双边稳定匹配（Gale-Shapley 延迟接受算法，容量可配）。

严肃等级: L1（教学级原型）。诚实性声明：
  - 本实现是教科书版延迟接受算法，输入规模限于数百级，未做工业级并发/隐私保护。
  - 输出附稳定性自检（扫描所有阻塞对，断言为 0），但自检只验证"本输入下无阻塞对"，
    不验证偏好填报的真实性（真实志愿填报存在策略性填报问题，本脚本不处理）。
  - 结果标注 unverified：任何用于真实志愿决策的输出都须人工复核。

输入（stdin JSON）:
{
  "students": [{"id": "s1", "prefs": ["A", "B", "C"]}, ...],
  "schools":  [{"id": "A", "capacity": 2, "prefs": ["s1", "s2", ...]}, ...]
}
  - students 侧每人容量=1（考生-proposing 或院校-proposing 由 --proposer 指定，默认 students）。
  - schools 侧 capacity >= 1（多席位院校）。
  - 允许不完全偏好列表：未列出视为不可接受。

输出（stdout JSON）:
{
  "matches": [{"student": ..., "school": ...}, ...],
  "unmatched_students": [...],
  "school_rosters": {school_id: [student_ids]},
  "blocking_pairs": [],               # 自检结果，必须为 []
  "stability_check": "PASS|FAIL",
  "n_blocking_pairs": 0,
  "honesty": {"level": "L1", "unverified": true, "note": "..."}
}

冒烟：python3 gale_shapley.py --smoke   （4 考生 × 3 校合成用例）
"""
import json
import sys

HONESTY = {
    "level": "L1",
    "unverified": True,
    "note": ("教科书版 Gale-Shapley；稳定性自检仅覆盖本输入的阻塞对扫描，"
             "不验证偏好真实性；用于真实志愿填报前须人工复核。"),
}


def gale_shapley(students, schools, proposer="students"):
    """延迟接受算法。proposers 容量 1，receivers 容量 capacity。"""
    if proposer == "students":
        proposers, receivers = students, schools
        p_key, r_key = "student", "school"
    else:
        proposers, receivers = schools, students
        p_key, r_key = "school", "student"

    p_prefs = {p["id"]: list(p["prefs"]) for p in proposers}
    r_cap = {r["id"]: int(r.get("capacity", 1)) for r in receivers}
    r_rank = {r["id"]: {pid: i for i, pid in enumerate(r["prefs"])}
              for r in receivers}

    next_idx = {p["id"]: 0 for p in proposers}   # 每个 proposer 下一个要请求的对象
    held = {r["id"]: [] for r in receivers}       # receiver 当前持有的 proposer
    engaged = {}                                   # proposer -> receiver

    free = [p["id"] for p in proposers]
    while free:
        p = free.pop(0)
        prefs = p_prefs[p]
        if next_idx[p] >= len(prefs):
            continue  # 偏好耗尽，保持未匹配
        r = prefs[next_idx[p]]
        next_idx[p] += 1
        if r not in r_rank:
            # 接收方列表外（防御非法输入）：视为拒绝
            if next_idx[p] < len(prefs):
                free.append(p)
            continue
        rank = r_rank[r]
        if p not in rank:
            if next_idx[p] < len(prefs):
                free.append(p)
            continue
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
                free.append(worst)  # 被拒者重新求婚
            else:
                if next_idx[p] < len(prefs):
                    free.append(p)

    matches = [{p_key: p, r_key: r} for p, r in sorted(engaged.items())]
    return matches, engaged, held


def find_blocking_pairs(students, schools, engaged_by_student):
    """以学生-院校视角扫描所有阻塞对。阻塞对 (s, sch)：s 未匹配或更偏好 sch，
    且 sch 有空位或持有比 s 更差的在录学生。"""
    s_rank = {s["id"]: {sch: i for i, sch in enumerate(s["prefs"])} for s in students}
    sch_rank = {sch["id"]: {st: i for i, st in enumerate(sch["prefs"])} for sch in schools}
    roster = {sch["id"]: [] for sch in schools}
    for st, sch in engaged_by_student.items():
        roster[sch].append(st)
    blocking = []
    for s in students:
        sid = s["id"]
        cur = engaged_by_student.get(sid)
        for sch in schools:
            sch_id = sch["id"]
            if sch_id not in s_rank[sid] or sid not in sch_rank[sch_id]:
                continue  # 互不接受
            # s 是否更偏好 sch（含未匹配情形：任何可接受院校都优于落空）
            prefers = (cur is None) or (cur != sch_id and
                       s_rank[sid][sch_id] < s_rank[sid][cur])
            if cur == sch_id:
                continue
            if not prefers:
                continue
            cap = int(sch.get("capacity", 1))
            rank = sch_rank[sch_id]
            if len(roster[sch_id]) < cap:
                blocking.append([sid, sch_id])
            else:
                worst = max(roster[sch_id], key=lambda q: rank[q])
                if rank[sid] < rank[worst]:
                    blocking.append([sid, sch_id])
    return blocking, roster


def run(payload, proposer="students"):
    students = payload["students"]
    schools = payload["schools"]
    matches, engaged_p, _ = gale_shapley(students, schools, proposer)
    # 统一转回 student->school 视角做自检
    if proposer == "students":
        engaged_by_student = engaged_p
    else:
        engaged_by_student = {v: k for k, v in engaged_p.items()}
    blocking, roster = find_blocking_pairs(students, schools, engaged_by_student)
    unmatched = [s["id"] for s in students if s["id"] not in engaged_by_student]
    result = {
        "proposer": proposer,
        "matches": matches,
        "unmatched_students": unmatched,
        "school_rosters": {k: v for k, v in roster.items() if v},
        "blocking_pairs": blocking,
        "n_blocking_pairs": len(blocking),
        "stability_check": "PASS" if not blocking else "FAIL",
        "honesty": HONESTY,
    }
    assert not blocking, f"稳定性自检失败：存在 {len(blocking)} 个阻塞对 {blocking}"
    return result


SMOKE = {
    "students": [
        {"id": "s1", "prefs": ["A", "B", "C"]},
        {"id": "s2", "prefs": ["A", "C", "B"]},
        {"id": "s3", "prefs": ["B", "A", "C"]},
        {"id": "s4", "prefs": ["C", "B", "A"]},
    ],
    "schools": [
        {"id": "A", "capacity": 1, "prefs": ["s1", "s2", "s3", "s4"]},
        {"id": "B", "capacity": 2, "prefs": ["s3", "s1", "s4", "s2"]},
        {"id": "C", "capacity": 1, "prefs": ["s4", "s2", "s1", "s3"]},
    ],
}


def main():
    if "--smoke" in sys.argv:
        result = run(SMOKE)
    else:
        payload = json.load(sys.stdin)
        proposer = "schools" if "--proposer=schools" in sys.argv else "students"
        result = run(payload, proposer)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
