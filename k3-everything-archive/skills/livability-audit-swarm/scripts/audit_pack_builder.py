#!/usr/bin/env python3
"""audit_pack_builder.py — 把文档登记表切分成 ≥5 份审计任务包（按审计角色视角）。

用法:
    python3 audit_pack_builder.py --registry registry.json [--roles 角色1,角色2,...] [--out packs.json]

默认六角色（对应 references/audit-roles.md）：
    parameter / semantic / evidence / consistency / double_count / trace
每份任务包 = {role, focus, docs[...], instructions_ref}。
语义角色按类别过滤文档；证据/一致性/重复计量/留痕角色取全量文档。
纯标准库。
"""
import argparse, json

DEFAULT_ROLES = ["parameter", "semantic", "evidence", "consistency", "double_count", "trace"]
ROLE_FOCUS = {
    "parameter": "参数设置：量表/权重链/归一化/默认值/校验断言（对照 claims-deep-audit 纪律）",
    "semantic": "语义准确性：构念漂移/同名异义/维度归属/锚点缺失（对照 evidence-chain-verifier 纪律）",
    "evidence": "证据链：conf 标注/来源可复核性/证据-语义对齐/风评类证据隔离",
    "consistency": "跨文档一致性：报告↔代码↔schema↔数据 四方矛盾登记",
    "double_count": "重复计量：同一现实因子（房价/气候/房租/住宿）多入口通道核查",
    "trace": "留痕合规：AI_READER_NOTICE 块/CHANGELOG/k3_notices 的完备性与幂等性",
}
ROLE_CATS = {
    "parameter": None,
    "semantic": None,
    "evidence": None,
    "consistency": None,
    "double_count": ["city_livability", "housing", "dorm_bathroom", "comfort_field"],
    "trace": None,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--roles", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    reg = json.load(open(a.registry, encoding="utf-8"))
    docs = reg.get("documents", [])
    roles = a.roles.split(",") if a.roles else DEFAULT_ROLES
    packs = []
    for role in roles:
        cats = ROLE_CATS.get(role)
        sel = [d["path"] for d in docs if cats is None or d["category"] in cats]
        packs.append({
            "role": role,
            "focus": ROLE_FOCUS.get(role, "自定义审计"),
            "doc_count": len(sel),
            "docs": sel,
            "instructions_ref": "references/audit-roles.md",
        })
    out = {"meta": {"registry": a.registry, "roles": roles,
                    "generated_by": "audit_pack_builder.py"},
           "packs": packs}
    s = json.dumps(out, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(s)
    print(s if not a.out else f"built {len(packs)} packs -> {a.out}")


if __name__ == "__main__":
    main()
