---
name: source-semantics-sentinel
description: 信源验证通道与上升机制、投毒甄别、语义精度利刃、最小作用量路由四位一体的信息入口哨兵。当用户需要信源验证/来源核查/信源评级、投毒甄别（数据投毒/AI投毒、AI生成淤泥/协同水军/引用环、蓄意或无意污染）、语义审计/歧义检测/语言精度检查（实装维特根斯坦与罗素语义学方法）、设计上升机制、信息分发验证（转述链留痕核查）、为核查任务推荐最短验证路径时使用。触发词示例："这个来源可靠吗""这批账号是不是水军""这段话有没有歧义""该走哪条验证通道"。机构/项目/产品宣传打假交给 claims-deep-audit；证据链登记、冲突消解与公开链接附链交给 evidence-chain-verifier；本技能只做其上游：信源通道分级与上升、语料污染启发式标记、文本语义精度审计、验证路径路由。中文名：信源语义哨兵
---

<!-- v1.0（2026-08-24）\这是中文解释：初版。四功能合一——①信源验证通道阶梯与 T0-T3 上升机制 ②投毒启发式甄别（蓄意/无意，AI 淤泥/协同/引用环/模板复制/统计异常/利益伪装）③语义精度利刃（维特根斯坦+罗素可操作化清单）④最小作用量路由（最短验证路径推荐）。只衔接不重造：命题评分归 claims-deep-audit，证据链登记与冲突消解归 evidence-chain-verifier，conf 双词表与 Conflict→人工铁律引自 cross-session-workflow-bridge/references/pipeline_contracts.md，严肃等级 L0-L3 引自 iteration-convergence-ops。 -->

# 信源语义哨兵（source-semantics-sentinel）

## 概述

在信息进入核查管线之前站岗：判断"这条信息从哪条通道来、该升到哪一级验证、语料是否被污染、文字本身是否有语义陷阱、哪条验证路径最短"。四大功能：

1. **信源验证通道与上升机制**——按通道阶梯给信源分级（C0 一手原始 > C1 官方/权威数据源插件 > C2 多源交叉三角 > C3 单一转述 > C4 匿名社媒），并按 T0-T3 上升机制决定验证强度，细则见 `references/verification_channels.md`；
2. **投毒甄别**——对语料库做启发式污染信号扫描（AI 生成淤泥、协同水军、引用环、模板化复制、统计异常、利益相关伪装），只输出"需人工复核的可疑模式"，禁止定罪，细则见 `references/poisoning_detection.md`；
3. **语义精度利刃**——把维特根斯坦（意义即使用/语言游戏/家族相似/私人语言论证）与罗素（摹状词理论/逻辑原子主义/类型论）可操作化为可执行审计清单，哲学引用仅作方法论类比，细则见 `references/semantic_precision.md`；
4. **最小作用量路由**——按命题风险等级与信源现状推荐最短验证路径，避免过度核查也避免核查不足，路由表见下。

三个脚本（均纯标准库，`--help` 查用法，`--smoke` 自检）：

- `scripts/semantics_audit.py`：文本语义审计（未定义术语候选、歧义候选、模糊对冲密度、指称悬空候选），输出带位置与类型的 JSON；
- `scripts/source_triage.py`：来源清单 JSONL → 通道阶梯分类 + 验证状态登记 + 上升建议；
- `scripts/poison_scan.py`：语料 JSONL → 协同信号检测（重复簇/账号集中度/时间突发/模板相似度），输出 conf 分级可疑模式报告。

## 五条立场原则（全程默念）

1. **通道 ≠ 内容**：信源等级高只说明通道可靠，不等于这条内容为真；通道分级是验证强度的输入，不是结论本身。
2. **标记 ≠ 定罪**：投毒甄别的一切输出是启发式可疑模式，永远指向人工复核，禁止输出指控性结论（铁律，见 `references/poisoning_detection.md` 第 1 节）。
3. **类比 ≠ 实证**：维特根斯坦/罗素只提供方法论类比，由此得出的审计结论 conf 一律记"方法论"档（不得标 empirical），见 `references/semantic_precision.md` 第 0 节。
4. **最短 ≠ 最省**：最小作用量路由是"够用即停"，不是偷懒通道；高风险命题强制走高通道，路由表不得向下覆盖 Conflict→人工铁律。
5. **衔接 ≠ 重造**：命题评分、证据链登记、冲突消解、公开链接附链一律转交既有技能（见「与既有技能的边界与衔接」），本技能不复制其功能与词表。

每次给出结论前，自问是否触犯其中某一条。

## 最小作用量路由表

输入两个变量：**命题风险等级**（该命题若为假，代价多大）与**当前信源通道档**（C0-C4，见 `references/verification_channels.md`；注意通道档标号 C 与上升等级标号 T 是两套体系，禁止混写）。输出最短验证路径。风险等级分级：

| 风险档 | 判据举例 |
|---|---|
| R-高 | 涉金钱/健康/法律/升学职业决策的结论；一票否决项；进入决策引擎的维度分 |
| R-中 | 影响论证走向但可后续修正的支撑性命题 |
| R-低 | 背景性、修辞性、不影响结论的信息 |

路由表（"→"为上升方向，取满足条件的**最短**路径）：

| 当前通道档 \ 风险 | R-低 | R-中 | R-高 |
|---|---|---|---|
| C0 一手原始 | 记录即采用（conf=empirical） | 记录即采用 | 记录即采用 + 抽查字段口径 |
| C1 官方/权威插件 | 记录即采用 | 记录即采用 + 标注 data_cutoff | 上升 T1：另找独立源交叉复核 |
| C2 多源交叉三角 | 记录即采用（conf=estimated） | 记录即采用 | 上升 T2：权威源/插件核验一次 |
| C3 单一转述 | 可用但标注 conf=assumed | 上升 T1 交叉复核 | 上升 T2，核验失败则按 T3 人工裁决登记 |
| C4 匿名社媒 | 仅作线索，不入结论 | 上升 T2 权威源核验 | 上升 T2；核验失败禁入结论，登记 T3 |

铁律约束（不可被路由表覆盖）：

- 任何一档出现信源间矛盾 = **Conflict，无机读映射，阻断转人工**（引自 pipeline_contracts.md conf 双词表）；禁止降级硬塞 conf 继续走。
- 进入评分引擎的数据一律走数据流层词表 `empirical/estimated/assumed`；对人的报告用 `High/Medium/Low/Conflict`，跨界先换算（见「输出纪律」）。
- R-高命题最终结论仍须经 evidence-chain-verifier 登记附链；本表只决定"验证到哪一步够用"，不替代登记。

## 功能一：信源验证通道与上升机制

1. 把来源清单（URL/出处描述）整理成 JSONL，每行至少含 `url` 或 `source_desc`；
2. 跑 `python3 scripts/source_triage.py --pretty < sources.jsonl`，得到每条来源的通道分级（tier0_primary / tier1_authoritative_plugin / tier2_cross_triangulated / tier3_single_relay / tier4_anonymous_social）、验证状态登记与上升建议（T0 自动判 → T1 交叉复核 → T2 权威源/插件核验 → T3 人工裁决）；
3. 对脚本拿不准的条目，人工按 `references/verification_channels.md` 第 1 节阶梯表定级；转述信息（被分发/转发的内容）必须按该文件第 3 节做转述链留痕；
4. 定级结果喂给路由表决定验证路径；产生的关键判断转交 evidence-chain-verifier 登记。

## 功能二：投毒甄别

1. 语料整理成 JSONL（每行含 `url`/`account`/`publish_date`/`abstract` 等，兼容 batch_*.jsonl 形态）；
2. 跑 `python3 scripts/poison_scan.py --pretty < corpus.jsonl`，得四类协同信号：文本重复簇、账号集中度、时间突发聚集、模板相似度；
3. 输出报告按 conf 分级且**全部封顶在启发式档**：任何信号单发 conf 上限 Low（数据流层 assumed），多信号叠加同簇上限 Medium（estimated），永不给 High/empirical；
4. 报告措辞只用"需人工复核的可疑模式"，附误报风险提示；禁止出现"水军""造假团伙"等定罪性措辞作为结论（作为信号类型名出现时须引号化并注明为启发式标签）；
5. taxonomy、逐信号 conf 上限与误报风险表见 `references/poisoning_detection.md`——**解读报告前先读它**。

## 功能三：语义精度利刃

1. 跑 `python3 scripts/semantics_audit.py --pretty < text.txt`（或 stdin 管道），得四类候选清单：未定义术语候选、歧义候选（一词多义语境冲突、量化词域混用）、模糊对冲密度、指称悬空候选，每条带字符位置、句序与类型；
2. 脚本只做初筛，所有候选必须人工（或主模型）对照 `references/semantic_precision.md` 的可操作化清单逐条裁决：
   - 维特根斯坦侧：用法一致性检查、语境游戏标注、家族相似边界警示、私人语言警示；
   - 罗素侧：指称消解检查、原子命题分解、层级类型混淆检测；
3. 每条裁决给触发例与处置（改写法）；哲学概念仅作方法论类比，审计结论 conf 记"方法论"档，喂引擎时按 assumed 处理；
4. 语义审计发现的实质命题（可证伪句）转入 claims-deep-audit 命题清单或 evidence-chain-verifier 登记，不在本技能内评分。

## 功能四：最小作用量路由

1. 给命题定风险档（R-高/中/低，判据见路由表）；拿不准时向上一档靠；
2. 查信源当前通道（功能一输出）；
3. 查路由表取最短路径，显式记录"为何停在这一步"（够用理由）；
4. 被 Conflict 阻断时停止路由，按 Conflict→人工铁律登记冲突双方、已做消解尝试，交用户裁决——禁止静默二选一；
5. 路由决策写入交付物的验证留痕节，供复核者检查是否过度核查或核查不足。

## 与既有技能的边界与衔接

**本技能不做（引用不复制）**：

- 命题拆解评分、八轮核查、欺诈分型 → **claims-deep-audit**（命题评分卡 JSON 契约见 pipeline_contracts.md）；
- 证据登记、confidence 四级判定、冲突消解、公开链接附链、自修正 → **evidence-chain-verifier**（`evidence_register.py` 与其 references 不在此重复）；
- conf 双词表定义、管线 JSON 契约、data_cutoff 必填规约 → **cross-session-workflow-bridge** `references/pipeline_contracts.md`（本技能只遵守，不重述全文）；
- 概念产品严肃化阶梯 L0-L3（玩具/原型/已验证/严肃）与毕业门槛 → **iteration-convergence-ops** `references/k26_fast_mode.md`。

**本技能新增（既有生态未覆盖）**：信源通道阶梯与 T0-T3 上升机制、转述链留痕规约、语料污染启发式扫描、语义精度审计（维特根斯坦+罗素可操作化）、最小作用量路由表。

**衔接方向**：本技能是上游哨兵——输出喂给：claims-deep-audit（洁净命题清单）、evidence-chain-verifier（待登记关键判断）、multi-dimensional-option-scoring（经 conf 换算后的数据点）。本技能产物如进入技能间管线，须按 pipeline_contracts.md 登记新链路（生产者→消费者表加行）后再对接。

**严肃等级自标**：本技能当前版本按 L0-L3 阶梯自评为 **L2（已验证）**——三脚本带 --smoke 合成样例自检且全绿，规则文档经内部一致性核对；未达到 L3 严肃级（未经大规模真实语料实战检验），用于高风险决策时按 L2 待遇：可用但关键结论须人工抽查。

## 输出纪律

1. **conf 双词表**：报告层（对人）用 High/Medium/Low/Conflict，键名 `confidence`；数据流层（机读）用 empirical/estimated/assumed 或 [0,1] 数值，键名 `conf`。跨界先按 pipeline_contracts.md 映射表换算，禁止跨层直接喂值。
2. **Conflict→人工铁律**：信源矛盾 = Conflict，无机读映射，阻断转人工，显式列入报告 Conflict Zone；禁止降级硬塞。
3. **data_cutoff 必填**：任何 JSON 产物顶层带 `data_cutoff`（YYYY-MM-DD），不允许留空或 null。
4. **top3_likely_wrong**：交付给人的报告必须含自我批判节，列出最可能错的三处。
5. **语义审计结论 conf 记"方法论"档**：哲学类比不产生实证置信，喂引擎按 assumed。
6. **投毒报告全档封顶**：启发式信号永不给 High/empirical（详见功能二第 3 条）。

中文名：信源语义哨兵
