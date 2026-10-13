#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_registry.py — 生成 doccode_registry.jsonl 哈希链台账（存量件号入册）。
sha256 = sha256( compact_json({seq,code,series,doc,seat,date,status}) + prev_hash )
"""
import hashlib, json, os

ROWS = [
    ("GW-DOCCODE-2026-1003-01", "GW", "references/doccode-spec.md", "k3-mirror-sync", "2026-10-03"),
    ("CL-SYNC-20261001-K3-01", "CL", "致桌面Kimi-K2.8协调函_img_token_saver补齐.md", "k3-mirror-sync", "2026-10-01"),
    ("DF-MIN-2026-1003-GITCODE-01", "DF-MIN", "总线11735·守藏席GitCode挖掘简报", "shou-cang", "2026-10-03"),
    ("DF-ORD-2026-1003-NEON-01", "DF-ORD", "总线11735·夜库台账正本裁示意见", "shou-cang", "2026-10-03"),
    ("TREE-K3-2026-1003-01", "TREE", "sha3_tree/TREE-K3-2026-1003-01_manifest.json", "k3-main", "2026-10-03"),
    ("TREE-K3-2026-1003-02", "TREE", "sha3_tree/TREE-K3-2026-1003-02_manifest.json", "k3-main", "2026-10-03"),
    ("TREE-K3-2026-1003-03", "TREE", "sha3_tree/TREE-K3-2026-1003-03_manifest.json", "k3-main", "2026-10-03"),
    ("TREE-SHOUCANG-2026-1003-01", "TREE", "sha3_tree/TREE-SHOUCANG-2026-1003-01_manifest.json", "shou-cang", "2026-10-03"),
    ("EVT-20260901-SKILLREFRESH-001", "EVT", "技能刷新系列事件一", "yanxi", "2026-09-01"),
    ("EVT-20260901-SKILLREFRESH-002", "EVT", "技能刷新系列事件二", "yanxi", "2026-09-01"),
    ("EVT-20260901-SKILLREFRESH-003", "EVT", "技能刷新系列事件三", "yanxi", "2026-09-01"),
    ("WK-2026-1002-01", "WK", "总线11468·全域唤醒书", "workbuddy-hy4", "2026-10-01"),
    ("OTL-BLUEPRINT-001", "OTL", "OpenPlanLink 蓝图 OTL 主文档", "k3-main", "2026-10-03"),
    ("BC-012", "BC", "桌面席SAP实装报备", "yehang-desktop-k3", "2026-09-10"),
    ("GW-DOCCODE-2026-1003-02", "GW", "references/doccode_registry.jsonl（本台账）", "k3-mirror-sync", "2026-10-03"),
    ("DF-ORD-2026-1003-K3-01", "DF", "规范化表述文本_DF-ORD-2026-1003-K3-01.md", "k3-mirror-sync", "2026-10-03"),
    ("DF-NOTICE-2026-1004-K3-01", "DF", "预检报告_OpenPlanLink全局声明与A2A网络建设纲要_DF-NOTICE-2026-1004-K3-01.md", "k3-mirror-sync", "2026-10-04"),
    ("DF-ORD-2026-1005-K3-01", "DF", "SDD规范驱动开发立项书_DF-ORD-2026-1005-K3-01.md", "k3-mirror-sync", "2026-10-05"),
    ("DF-MIN-2026-1005-K3-01", "DF", "重读批注纪要_WPS十件_DF-MIN-2026-1005-K3-01.md", "k3-mirror-sync", "2026-10-05"),
    ("DF-ORD-2026-1005-K3-02", "DF", "协同规约候批条款呈批件_DF-ORD-2026-1005-K3-02.md", "k3-mirror-sync", "2026-10-05"),
    ("CL-DESK-20261005-K3-02", "CL", "协调函_受阻三件桌面导出救济_CL-DESK-20261005-K3-02.md", "k3-mirror-sync", "2026-10-05"),
    ("DF-ORD-2026-1005-K3-03", "DF", "A2A网络算力分配与分布式协同探讨_DF-ORD-2026-1005-K3-03.md", "k3-mirror-sync", "2026-10-05"),
    ("DF-ORD-2026-1005-K3-04", "DF", "姊妹OTL件锚定纳表审议呈批附件_DF-ORD-2026-1005-K3-04.md", "k3-mirror-sync", "2026-10-05"),
    ("EVT-20261005-SIBLINGAUDIT-001", "EVT", "姊妹席新件只读审查报告_EVT-20261005-SIBLINGAUDIT-001.md", "k3-mirror-sync", "2026-10-05"),
    ("EVT-20261005-SELFREF-001", "EVT", "状态环签名自指性审计_EVT-20261005-SELFREF-001.md", "k3-mirror-sync", "2026-10-05"),
]

out = []
prev = "GENESIS"
for i, (code, series, doc, seat, date) in enumerate(ROWS, 1):
    core = {"seq": i, "code": code, "series": series, "doc": doc, "seat": seat, "date": date, "status": "active"}
    h = hashlib.sha256((json.dumps(core, ensure_ascii=False, separators=(",", ":")) + prev).encode("utf-8")).hexdigest()
    core["prev_hash"] = prev
    core["sha256"] = h
    out.append(core)
    prev = h

dst = os.path.join(os.path.dirname(__file__), "..", "references", "doccode_registry.jsonl")
with open(dst, "w", encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"registry written: {dst} rows={len(out)} head_sha={out[-1]['sha256'][:16]}")
