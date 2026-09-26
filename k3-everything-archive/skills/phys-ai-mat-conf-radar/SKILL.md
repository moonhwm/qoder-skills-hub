---
name: phys-ai-mat-conf-radar
description: 物理×AI×材料领域顶会排期雷达，重点覆盖等离子体物理学与聚变工程化应用（APS DPP、IAEA FEC、EPS、SOFT、IEEE ICOPS、ISFNT、ANS、MRS、TMS、NeurIPS/ICML/ICLR 及 AI4Science workshop 等）。当用户需要排期/追踪/提醒这些领域的会议投稿节点、制作会议日历（.ics）、规划年度投稿节奏、核验某会议当年截止日期真伪、区分摘要/全文/注册/会后专刊节点、区分主会与 workshop 档位时使用。触发词示例："聚变领域今年有哪些会要投""帮我做物理×AI 顶会排期表""SOFT 2026 摘要什么时候截止""把这些节点导成日历""等离子体会议投稿节奏怎么排"。信源分级与上升机制归 source-semantics-sentinel，关键日期证据登记归 evidence-chain-verifier，聚变院校/项目真伪核查归 fusion-program-audit，conf 词表与 JSON 契约归 cross-session-workflow-bridge；本技能只做：会议目录与周期知识、日期核验排期流水线、排期表与日历交付。中文名：顶会排期雷达
---

<!-- v1.3（2026-08-28）\这是中文解释：首轮 T2 复核——核验 APS DPP 2026 / SOFT 2026 / ICOPS 2027 / IAEA FEC 2027 / SOFE&PPC 2027 / APCOPTS 2026 共 6 条当期事实，落盘 references/data/catalog_t2_log.jsonl；修正两个目录错误：SOFT 全名是 Symposium on Fusion Technology（非 Engineering），SOFE 才是 IEEE Symposium on Fusion Engineering，二者为不同会议，目录已分条并互注防混；DPP 摘要截止窗口修正为"7 月（2026 届 7-28）"。EPS/ISFNT 入口未取得保持 tentative。 -->
<!-- v1.2（2026-08-28）\这是中文解释：自包含化——vendor paperswithcode/ai-deadlines 快照（MIT，commit b230d24，192 条）至 references/data/ 并附 ATTRIBUTION.md；新增 ai_deadlines_ingest.py 把快照转成契约 JSONL，强制 conf=assumed/T1_pending（聚合站线索纪律内置化，不可关）。 -->
<!-- v1.1（2026-08-28）\这是中文解释：迭代收敛轮——修复 ics_gen.py 全天事件 DTEND 排他端点缺陷（同日 DTEND 导致部分日历渲染为零时长，按 RFC 5545 改为 +1 天，含跨年边界断言）；deadline_triage.py 输出透传 tentative 布尔字段提升排期透明度。v1.0 初版见 iteration_log.json。 -->

# 顶会排期雷达（phys-ai-mat-conf-radar）

## 概述

回答物理×AI×材料（重点：等离子体物理与聚变工程化）研究者的三个排期问题——**有哪些会值得投？
每个节点哪天截止、这日期核验过吗？怎么落到日历里执行？** 输出：核验过的排期 JSONL + markdown 排期表 + 可导入日历的 .ics。

核心立场（每次交付前默念）：

1. **官网日期才算数**：聚合站/往届规律只是线索（C3/assumed），进排期的日期必须经官网核验（T2→empirical）
   或显式标 tentative——政策细则见 `references/verification_policy.md`。
2. **节点类型不混档**：abstract / paper / registration / journal_special 分开登记；workshop 与主会 tier 分开标。
3. **外推必须亮明身份**：从往届周期外推的日期 = tentative + assumed，禁止伪装成官宣。
4. **矛盾不静默**：官网与聚合站、官网不同页面之间日期矛盾 → Conflict 登记交人工，禁止自行二选一。

## 标准工作流（四步）

1. **圈域**：从 `references/conference_catalog.md` 按用户领域（plasma / fusion_eng / ai / ai4sci / materials /
   domestic）挑出候选会议与典型周期窗口；目录每年 1 月全表复核，发现失效先标 broken。
2. **采集核验**：按 `references/verification_policy.md` 对每个目标会议走 T1（聚合站交叉）→ T2（官网核验，
   记录 source_url + data_cutoff + tz）；官网未官宣的记月度窗口 + tentative。
3. **分诊排期**：事件整理成契约 JSONL（`references/verification_policy.md` 第 3 节），跑
   `python3 scripts/deadline_triage.py events.jsonl --pretty` 得 past/imminent/upcoming/tentative 分诊表；
   imminent 窗口默认 30 天（--window 可调）。
4. **交付日历**：`python3 scripts/ics_gen.py events.jsonl --out schedule.ics` 生成可导入日历；
   markdown 排期表 + .ics + 留痕（每节点 conf/verify_stage/source_url）一并交付。

三脚本纯标准库，`--smoke` 自检，`--help` 查用法。

## 内置种子数据（自包含 vendor）

`references/data/ai_deadlines_conferences.yml` 是 paperswithcode/ai-deadlines 的 MIT 快照
（192 条 AI 会议，含 abstract/paper 截止与时区；归属与快照信息见同目录 ATTRIBUTION.md）。
**它是 C3 聚合线索，可能已过期**——用 `scripts/ai_deadlines_ingest.py` 转成契约 JSONL
（强制 conf=assumed、verify_stage=T1_pending），再按工作流第 2 步到当届官网 T2 核验后才能进排期。
场景："先给我一份 AI 会议线索底稿" → ingest → triage → 标 tentative → 逐条 T2。

## 常见场景速路由

- "X 会议今年截止什么时候" → 工作流第 2 步单点核验，给日期 + conf + 来源链接 + 抓取日期；
- "做一份年度排期表" → 全流程四步，交付 md + ics + JSONL；
- "我们组该投哪些会" → 第 1 步圈域 + 按研究方向（物理机理→DPP/FEC/EPS；工程技术→SOFT/ISFNT/ANS/ICOPS；
  AI 方法→NeurIPS/ICML/ICLR 主会；应用快曝光→AI4Science workshop）给优先级建议，建议属判断不是事实，conf 标 assumed；
- "期刊特刊别漏" → 会后专刊节点按 journal_special 单独登记（SOFT→FED 等，见 catalog 第 5 节）。

## 输出纪律

1. 排期 JSONL 顶层带 `data_cutoff`（YYYY-MM-DD），conf 只用 empirical/estimated/assumed（数据流层词表）。
2. 每个事件带 `verify_stage`（T0-T3）与 `source_url`；缺 source_url 的日期 conf 上限 assumed。
3. 关键日期（用户据此买机票/赶稿的）转 evidence-chain-verifier 登记附链；本技能不登记。
4. 交付报告含 `top3_likely_wrong` 自我批判节（典型候选：外推日期、时区换算、目录漂移）。
5. 聚变商业公司节点/院校项目真伪问题一律转 fusion-program-audit，本技能不做真伪评级。

## 与既有技能的边界

- 信源通道分级/上升机制/conf 词表/Conflict 铁律 → source-semantics-sentinel + cross-session-workflow-bridge（引用不复制）；
- 证据登记 → evidence-chain-verifier；聚变方向真伪核查 → fusion-program-audit；
- 本技能新增：领域会议目录与周期知识、日期核验流水线、排期分诊与 .ics 日历生成。

**严肃等级自标**：L2（已验证）——脚本 --smoke 全绿、目录经内部一致性核对；会议日期逐年漂移，
未经完整年度周期实战，任何写进排期的具体日期仍以当届官网 T2 核验为准。
