---
name: arxiv-source-sentinel
description: arXiv.org e-Print archive 论文信源标准：arXiv ID 解析与幻觉甄别、官方 API 元数据核验、预印本信源定级（载体 C0 vs 命题 C3 等价）、版本锁定与撤稿标记、标准引文生成（BibTeX/GB-T 7714/APA）。当用户需要核验某篇 arXiv 论文是否真实存在、检查参考文献中的 arXiv 引用真伪、给 arXiv 论文定信源等级、处理预印本/发表版取舍、生成或规范化 arXiv 引文、批量校验文献清单中的 arXiv 条目时使用。触发词示例："这个 arXiv 引用是真的吗""帮我查 2301.07041""这批参考文献里有幻觉吗""预印本能作为论据吗""按国标生成这条 arXiv 引文"。通用信源通道分级/投毒甄别/语义审计归 source-semantics-sentinel，命题评分归 claims-deep-audit，证据链登记归 evidence-chain-verifier；本技能只做 arXiv 特化：ID 与元数据核验、预印本定级政策、引文标准。中文名：arXiv 信源哨兵
---

<!-- v1.3（2026-08-28）\这是中文解释：swarm 盲评闭环（配额恢复后补做）——独立盲评判 with_skill 胜（证据链与认识论纪律优势），其指出的两条缺陷转化为输出纪律第 6、7 条：行话翻译义务（内部代号首现须配自然语言解释）与核验步骤留痕义务（声称做过的动作须有产物）。 -->
<!-- v1.2（2026-08-28）\这是中文解释：排期 P2 项落地——arxiv_cite.py GB/T 7714 姓名序加入常见中文姓氏启发式（"Li Wei"→"LI W" 不再误判为 "WEI L"），带回归断言；citation_standards.md 第 4 节人工核对点同步更新（启发式非穷尽，生僻姓氏仍须人工核对）。 -->
<!-- v1.1（2026-08-28）\这是中文解释：迭代收敛轮——修复 arxiv_id_check.py 对旧式带子类 ID（math.AG/astro-ph.GA 等）与 q-fin 合法 archive 的 unknown_old_archive 误报（High 级缺陷：对真实论文误报幻觉嫌疑）；新增回归断言。v1.0 初版见 iteration_log.json。评估限制：swarm 对照评估因账户配额降级为主代理自评估+对抗测试两轮，未做第三方盲评。 -->

# arXiv 信源哨兵（arxiv-source-sentinel）

## 概述

arXiv 论文进入核查/写作管线之前的标准化入口：回答四个问题——**ID 形制合法吗？论文真实存在吗？
这条命题该按什么信源等级对待？引文怎么写才标准？** 是 source-semantics-sentinel 的 arXiv 特化下游：
通用通道阶梯（C0-C4）与上升机制（T0-T3）、路由表、conf 双词表一律引用其定义，本技能只做 arXiv 场景映射。

核心立场（每次给结论前默念）：

1. **载体 ≠ 内容**：arXiv 页面/原文对"论文说了什么"是 C0/C1；arXiv 是**无强制同行评审的作者自存档**，
   论文内的命题默认按作者单方声称对待（C3 等价，conf 封顶 assumed）——定级细则见
   `references/channel_policy.md` 第 1 节，引用时永远说清在引哪一层。
2. **查不到 ≠ 不存在**：网络失败/限流只是"本次未核验"，绝不写成"论文不存在"；
   确认不存在必须经人工网页复核 + Conflict 登记（`references/arxiv_api.md` 第 5 节）。
3. **无版本号 = 引文事故隐患**：arXiv 各版本是不同文档，引文必须锁 `vN`（`references/citation_standards.md` 第 2 节）。
4. **撤稿论文原则上不引**：确需引用必须显式标 [WITHDRAWN]（`references/channel_policy.md` 第 3 节）。

## 标准工作流（四步）

1. **ID 校验（离线，永远先做）**：`python3 scripts/arxiv_id_check.py <IDs...>` 或 `--extract` 从文本提取。
   区分"格式错误"与"形制合法但可疑"（未来年月、2015 后 4 位序号——幻觉 ID 高频形态）。
   形制规范见 `references/arxiv_api.md` 第 1 节。
2. **元数据核验（联网，反幻觉主工序）**：`python3 scripts/arxiv_fetch.py --ids <IDs...>` 调官方 API，
   得标题/作者/年月/最新版本/journal_ref/DOI/withdrawn。API 用法与限速纪律见 `references/arxiv_api.md` 第 2-4 节。
   幻觉引用按 F1 全幻觉 / F2 张冠李戴 / F3 内容编造三型分型处置（`references/channel_policy.md` 第 4 节）。
3. **定级与上升决策**：按 `references/channel_policy.md` 第 2 节定级表 + source-semantics-sentinel 路由表
   决定验证停在哪一步；R-高命题（健康/金钱/安全相关的方法有效性声称）升 T2 核验发表状态，失败按 T3 人工裁决。
4. **引文生成**：核验过的 JSONL 喂 `python3 scripts/arxiv_cite.py --format bibtex|gbt7714|apa`，
   人工核对点（作者序、大小写、年份口径）见 `references/citation_standards.md` 第 4 节。

三脚本均纯标准库、带 `--smoke` 离线自检、`--help` 查用法。网络不可用时第 2 步退化为人造：
人工打开 `https://arxiv.org/abs/<id>` 核对并把元数据手工填成同构 JSONL 继续走第 3-4 步。

## 常见场景速路由

- "这个 arXiv 引用是真的吗" → 工作流 1+2，按 F1/F2/F3 出结论，Conflict 交人工；
- "批量检查参考文献" → ID 清单文件 → `arxiv_id_check.py --file` → `arxiv_fetch.py --ids-file`，
  汇总 NOT_RETURNED 与元数据不符清单；若怀疑批量投喂污染，转 source-semantics-sentinel 功能二；
- "预印本能不能引/当论据" → `references/channel_policy.md` 第 1-2 节：看引的是载体还是命题、命题风险档；
- "生成标准引文" → 工作流 2+4（未经核验的元数据禁止直接生成引文）；
- "读论文正文/源码" → PDF `https://arxiv.org/pdf/<id>`、源码 `https://arxiv.org/src/<id>`，限速同 API。

## 输出纪律

1. 任何 JSON 产物顶层带 `data_cutoff`（YYYY-MM-DD）；核验留痕结构按 `references/channel_policy.md` 第 5 节契约。
2. conf 双词表遵守 cross-session-workflow-bridge `pipeline_contracts.md`：报告层 High/Medium/Low/Conflict，
   数据流层 empirical/estimated/assumed，跨界先换算。
3. 幻觉确认、撤稿引用、R-高命题定级等关键判断转 evidence-chain-verifier 登记附链；本技能不登记。
4. 交付报告含 `top3_likely_wrong` 自我批判节。
5. 核查结论措辞：幻觉分型是"经核验的事实判定"（有 API + 网页双重证据时可给 High/empirical），
   但对**论文内容真伪**的判断永不超出信源定级允许的上限——"引用是假的"可以实证，"论文是错的"不行。

## 与既有技能的边界

- 通用信源分级/上升机制/转述链/投毒甄别/语义审计 → **source-semantics-sentinel**（本技能引用其定义与路由表）；
- 命题评分 → **claims-deep-audit**；证据登记与 Conflict 消解 → **evidence-chain-verifier**；
- 本技能新增：arXiv ID 形制校验、官方 API 核验工序、预印本"载体/内容"双层定级、版本与撤稿引文纪律、三格式引文生成。

**严肃等级自标**：按 L0-L3 阶梯（iteration-convergence-ops）自评 **L2（已验证）**——三脚本 --smoke 全绿，
规则文档经内部一致性核对；未经大规模真实文献清单实战，R-高场景关键结论须人工抽查。
