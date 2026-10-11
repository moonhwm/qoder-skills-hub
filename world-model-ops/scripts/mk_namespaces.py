# -*- coding: utf-8 -*-
"""mk_namespaces.py —— 建 namespaces/ 视图层（应纲要「目录结构建议」行 62）
★原则：件不动、路不迁；每 ns 一 index.md，仅指路与计数。可反复重跑（幂等）。
（中文串一律用「」）
"""
import pathlib, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"


def ls(d, pat="*", limit=8, recurse=False):
    p = pathlib.Path(d)
    if not p.exists(): return [], 0
    it = p.rglob(pat) if recurse else p.glob(pat)
    f = sorted([x for x in it if x.is_file()])
    return [x.name for x in f[:limit]], len(f)


def block(title, items, total):
    out = ["- **%s** ⇒ 共 %d 件；示例：" % (title, total)]
    for n in items[:8]:
        out.append("  - `%s`" % n[:96])
    if total > len(items[:8]):
        out.append("  - …（其余 %d 件同类）" % (total - len(items[:8])))
    return "\n".join(out)


NS = {}
i, t = ls(SEAT/"inbox"); NS["init"] = ("入手与读取通道", [block("inbox", i, t)])
i, t = ls(EX, "*总册*"); i2, t2 = ls(EX, "*勘误*"); i3, t3 = ls(EX, "*索引*")
NS["plan"] = ("规划与现行版", [block("总册与修订", i, t), block("勘误", i2, t2), block("索引", i3, t3)])
FLOW = ["stamp_time.py","termtable.py","sig_block.py","sig_verify.py","sop_check.py","mkled.py","lsbus_format_ops.py",
        "daily_nine_audit_20261010.py","doc_refresh.py","doc_archive.py","semantic_search.py","glb_anim_verify.py",
        "bootstrap.py","virtue_audit.py","mem_guard.py","quota_guard.py","netguard.py"]
have = [f for f in FLOW if (SEAT/"exp"/f).exists()]
NS["workflow"] = ("作业流程器物", [block("exp/ 之流程器", have, len(have))])
NS["env-check"] = ("环境自检", [block("bootstrap 与依赖", ["bootstrap.py（必需 numpy／PIL；可选 trimesh／pyrender／pygltflib／meshoptimizer）"], 1)])
i, t = ls(SEAT/"exp", "*probe*.py", recurse=False); i2, t2 = ls(SEAT/"exp", "*diag*.py"); i3, t3 = ls(SEAT/"exp", "ws_*.py")
NS["debug-model"] = ("排障与探针", [block("probe_*", i, t), block("diag_*", i2, t2), block("ws_*", i3, t3)])
NS["record"] = ("记录与审计", [block("ledger/", *(lambda x: (x[0], x[1]))(ls(SEAT/"ledger"))), block("总线", *(lambda x: (x[0], x[1]))(ls(EX/"bus")))])
i, t = ls(EX, "*人设*"); i2, t2 = ls(EX, "*Tripo*"); i3, t3 = ls(EX, "*姿态*")
NS["park"] = ("游乐场·世界模型", [block("人设入世", i, t), block("Tripo", i2, t2), block("四姿态", i3, t3)])
i, t = ls(SEAT/"exp", "*avatar*.glb"); i2, t2 = ls(SEAT/"exp", "*persona*")
NS["portrait"] = ("人设 3D 资产", [block("GLB 资产", i, t), block("人设脚本与形象", i2, t2)])
i, t = ls(EX, "*总账*"); i2, t2 = ls(EX, "*日更*"); i3, t3 = ls(EX, "*索引*")
NS["recap"] = ("总账与复盘", [block("总账", i, t), block("日更", i2, t2), block("索引", i3, t3)])
i, t = ls(EX, "*戒*"); i2, t2 = ls(EX, "*立法*"); i3, t3 = ls(EX, "*治理*")
NS["policy"] = ("治理与戒条", [block("戒与自查", i, t), block("立法", i2, t2), block("治理", i3, t3)])

root = SEAT/"namespaces"; root.mkdir(parents=True, exist_ok=True)
stamp = time.strftime("%Y-%m-%d %H:%M +0800")
made = []
for ns, (title, blocks) in NS.items():
    d = root/ns; d.mkdir(parents=True, exist_ok=True)
    txt = ["# `/%s` —— %s" % (ns, title), "",
           "- **依据**：纲要《OpenPlanLink全局声明与Agent-to-Agent网络建设纲要》行 62「目录结构建议」",
           "- **性质**：★视图层（**件不动、路不迁**）；仅为指路与计数，可反复重跑（幂等）",
           "- **生成**：`exp/mk_namespaces.py` ｜ " + stamp, "", "## 索引", ""] + blocks + [""]
    (d/"index.md").write_text("\n".join(txt), encoding="utf-8", newline="\n")
    made.append((ns, title, (d/"index.md").stat().st_size))
print("  ═══ namespaces/ 视图层已建 %d 个 ═══" % len(made))
for ns, title, sz in made:
    print("   /%-12s %-18s index.md %4d B" % (ns, title, sz))
print("   ⇒ 判：深度 2 级（namespaces/<ns>/index.md）｜件未移动｜可幂等重跑")
