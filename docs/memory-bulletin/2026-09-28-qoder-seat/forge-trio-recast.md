---
name: forge-trio-recast
description: 锻造三件套（fusion-cast-ops / skill-forge-pipeline / forge-round-robin-ops）2026-09-28 重铸状态与本地 audit 修复差异
metadata:
  type: project
---

2026-09-28 用微信三包（fusion-cast-ops(10) / skill-forge-pipeline(9) / forge-round-robin-ops(11)）重铸三件套，已装于 `~/.qoder/skills/`，交付面在桌面 `_重铸_锻造三件套_20260928/`（zip+descs.jsonl+MANIFEST+RECAST_REPORT）。

同日 Qoder 主会话 f9e56951 另行交付**单文件完整程序形态**（用户立法「技能=完整程序」）：桌面 `重铸三技能_20260928/` 下 fusion-cast.cjs v2.0.0 / forge-pipeline.cjs v2.5.0 / forge-roster.cjs v2.0.0 / a2a-watch.cjs（零依赖 Node>=18，md5→SHA3-512 升级，smoke 23+22+18 全过，正交 collide maxJ=0.091，端到端 roster→snapshot→cast→round→advance 链路实测 alumni=3）。两形态互补：zip 包供技能装载，.cjs 供直接执行；a2a-watch 为 GET-only 监听哨（watch-state.json / watch-log.jsonl 在其同级）。

**Why:** 用户要求正交、充要、完备；实测正交全过（三对 maxJ≤0.114，对 61 件本地库≤0.112，阈 0.3）。

**How to apply:**
- 本地 `fusion_cast.py` 比上游 zip v10 多一行修复：audit 指针正则分支 `references/([\w.-]+)` 曾丢前缀致假阳性「指针断裂」，已修（`ref = ref[0] or ("references/" + ref[1])`）。回灌上游包时须带上此修复。
- 邻席 quota-ledger-ops 缺席（fusion-cast C10 让渡对象），属已声明缺席；遇到额度记账需求先确认它是否已补装。
- 协同节点 http://120.46.86.165/functions/v1/app 为 A2A 0.3.0 确定性回执端点（席位 workbuddy-hy4），POST 用 UTF-8 字节体（urllib/文件），勿经 GBK 控制台传中文。
- 2026-09-28 经用户当轮授权已向该节点发出三件套重铸通报（id=f9e56951-recast-notice-1，回执 fp=60f366e11066c22f，总线快照 7881 行），请各席位自主审议接入并提出论坛反馈；快照与回执存桌面 `重铸三技能_20260928/通报快照_A2A_20260928.json`、`通报回执_A2A_20260928.json`。后续收到反馈时以身份锚（席位名+哈希前16位）核验。
