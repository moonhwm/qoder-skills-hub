---
name: vector-verdict-ops
description: "向量会裁复核署——多厂商向量模型（阿里百炼/腾讯TokenHub/智谱z.ai/火山引擎等 OpenAI 兼容嵌入端点）的对比使用、相似度会裁判定与案例复核台账：判定权交给向量函数与算术（双通道均达标方可 IN，单通道上限 EDGE，缺凭据/缺背景如实 UNDETERMINED），每次判定出带 sha256 的裁定卡并 append 进哈希链台账，历史案例可一键复核重审。触发（满足任一）：①用户说「向量对比」「向量模型」「embedding 对比」「会裁」「相似度会裁」「相似度判定」「案例复核」「重审」或等价表述（技能正交熔铸判定不在此列——归 tongtu-hub orthocheck，见「不覆盖」）；②需对两段文本/两个技能/两个命题做客观相似性定级且要求可复现时；③需对比多家向量模型（百炼 v3 vs kinfra-4b vs embedding-3 vs doubao-embedding）实测差异时；④向量判定历史台账需要校验/复核/统计时。不覆盖：技能正交熔铸本体的判定归 tongtu-hub orthocheck（本件为通用会裁引擎与案例台账）；任何内容级语义裁判（向量只测相似度，不测对错）。中文名：向量会裁复核署。English triggers: vector verdict panel, embedding model comparison, similarity verdict card, case review ledger."
metadata:
  version: "1.2.1"
---

# 向量会裁复核署（vector-verdict-ops）v1.2.1（MAX_ROUNDS_REACHED）

<!-- v1.2.1（2026-09-29，短链 R3 触顶强制出链，残余修复不再续轮）：①VERSION 常量与 frontmatter 同步递增（R3 判官抓到 v1.2.0 漂移）；②docstring embed 示例更正（--texts 为字面文本非文件路径）；③main() 背景早到引导（BG_MISSING/BG_LT_MIN stderr 预警，避免误判为模型故障）；④case-ledger.md channels 字段口径对齐（厂商名列表，模型/族/维度在 meta）。R3 票况：minimax REVISE（4 残余即上述）、qwen/glm 超时无票；三轮 keep 链完整无 worse，按管线触顶条款出链，残余全登记 FORGE_REPORT，移交机主裁量。 -->

<!-- v1.2.0（2026-09-29，短链 R2 delta，复评 2×REVISE 抓包四项全修）：①merge_verdicts 残缺路径双向封顶——UNDETERMINED+OUT 混合不再出 OUT，一律上限 EDGE（对齐铭文「通道残缺→上限 EDGE」）；②judge_channel 防御闸：z=None 误入判 UNDETERMINED；③cmd_review 坏行记 PARSE_FAIL 入 breaks 续跑不硬崩，append_ledger 尾坏行跳过取最近可解析卡为链头；④cmd_pair 背景前置闸：bg<8 不发起任何嵌入调用（零配额消耗），smoke 增 4 断言至 22。 -->

<!-- v1.1.0（2026-09-29，短链 R1 delta，外池三判官首评 3×REVISE 抓包七项全修）：①背景不足/零方差通道端到端判 UNDETERMINED（修静默退化 OUT 自伤）；②merge_verdicts IN 语义对齐判定表「≥2 通道 IN_CANDIDATE」（修 ALL 误写）；③空通道判 UNDETERMINED 不判 OUT；④通道数 <2 硬闸拒判（exit 2）；⑤维度漂移检：实返维度 vs 注册表登记入裁定卡 meta（dim_registered/dim_returned/dim_drift）；⑥背景全量送入，去除 [:32] 截断；⑦触发词移除「正交判定」消路由冲突；⑧smoke 扩至 18 断言（含 3 条端到端 mock 负断言）。基线快照 .bak-r1 在案。 -->

> 立法锚：**「判定权交给多厂商向量函数与相似度算术；人只立法、不臆断。」**
> 任何个人或团队均不得基于主观经验、直觉判断或未经核实的粗略比对擅自作出正交性/相似性结论。

## 核心方法论（一句话）

双通道会裁定级（IN/EDGE/OUT/UNDETERMINED 四级）＋裁定卡哈希链台账（每案可复核、可重审、可证伪）。

## 判定规则（立法常数，改动须版本递增）

| 级 | 条件 |
|---|---|
| IN | ≥2 通道均 top5 命中且 z 均 ≥ 1.0 |
| EDGE | 单通道在轨命中，或 z 均值带 [0.7,1.0)，或通道残缺（含 UNDETERMINED 时的上限） |
| OUT | 其余 |
| UNDETERMINED | 凭据缺失/调用失败/背景不足（<8 条或零方差）/空通道——**如实登记，绝不编造向量，禁静默退化为 OUT** |

**IN 的唯一通道**：≥2 通道均 IN_CANDIDATE 且无任何 UNDETERMINED（机检于 `merge_verdicts`，与上表逐字对齐）。
**通道残缺一律上限 EDGE**（含 UNDETERMINED 与 OUT 混合——残缺禁出强结论，双向封顶）；**单通道结论上限 EDGE**；**通道数 <2 硬闸拒判**（exit 2，不进入裁定）——负断言在 smoke 第 3/6/13/15/18/20 条。

## 工作流

1. **取材定对**：明确待判二元对（文本甲/乙），写明判定问题（「是否内容级重复？」）——问题不写清不动手。
2. **组通道**：`--channels` 至少两路（如 `bailian,zai`；<2 路脚本硬闸拒判 exit 2）；只有一路在轨时预期上限即 EDGE，不得期待 IN。
3. **备背景**：`--bg` 背景样本 ≥8 条（z 分母；不足 8 时前置闸直接全通道 UNDETERMINED、零嵌入调用零配额消耗，禁硬算；背景全量送入，无截断）。
4. **会裁**：`python3 scripts/verdict_panel.py pair --a "…" --b "…" --channels bailian,zai --bg bg.txt --ledger ledger.jsonl` → 裁定卡（含每通道 sim/z/判定、维度漂移登记 dim_registered/dim_returned/dim_drift、规则铭文、card_sha）。
5. **复核**：`review --ledger ledger.jsonl` 校验哈希链完整性与判定分布；链断即停查。
6. **归档**：裁定卡引用进上游文书（技能锻造/研究报告），注明通道名册与规则版本。

## 失败模式（if-then）

| 触发 | 一线处置 | 兜底 |
|---|---|---|
| 某通道 NO_KEY / CALL_FAIL | 该通道记 UNDETERMINED，其余通道续行，整体上限 EDGE | 三通道全缺 → UNDETERMINED 收官，向用户索要凭据 |
| 背景样本 <8 条 | 前置闸：不发嵌入调用，全通道 UNDETERMINED（exit 3） | 请用户补背景或改用 top-rank 口径并注明降级 |
| 背景零方差（全同背景） | z=None，该通道判 UNDETERMINED | 换背景集 |
| 台账哈希链断裂/含坏行 | review 报 breaks（坏行记 PARSE_FAIL）并续跑复核后续行；链断则停止引用该台账 | 定位断点起重新建链，旧链封存备查 |
| 厂商返回维度与注册表不符 | 漂移标记 dim_drift=true 与实返/注册双维度登记入裁定卡 meta，禁臆改注册表 | 版本递增时修订注册表并在变更说明登记 |
| 通道数 <2 | 脚本拒判（CHANNELS_LT2，exit 2），不出裁定卡 | 补通道后再判；单通道需求降级为 embed 探针模式 |

## 🔴 显性检查点

- 开判前：通道数 ≥2（不足脚本硬闸拒判）？背景 ≥8？判定问题已成文？
- 出卡后：card_sha 在？规则铭文在？单通道结果未冒充 IN？dim_drift 有漂移必已登记？背景不足通道确为 UNDETERMINED 而非 OUT？
- 复核时：chain_ok=true 才可引用台账。

## 反模式黑名单

| # | 反模式 | 替代做法 |
|---|---|---|
| 1 | 凭经验/直觉判「这两个很像」 | 走会裁：向量+算术+四级判定卡 |
| 2 | 单通道结果写「IN」 | 单通道上限 EDGE（机检强制） |
| 3 | 缺凭据时编造相似度数字 | 如实 UNDETERMINED 并索要凭据 |
| 4 | 背景不足 8 条硬算 z | 自动 UNDETERMINED；补背景或降级口径 |
| 5 | 判定不留卡、口头传达 | 每判定必出带 sha 的裁定卡入链 |

## 诚实边界

- 向量只测**相似度**，不测内容对错、不测语义真伪——内容级裁判归人/归上游技能。
- 判定是对「当前通道名册+当前背景集」的相对结论；换背景/换通道结论可迁移性须重测。
- 与 tongtu-hub 的关系：技能正交熔铸判定归其 orthocheck 探针；本件是通用会裁引擎+案例台账，引用不复制。

## 自检

`python3 scripts/verdict_panel.py smoke` —— 22 断言（含 12 负断言与 3 条端到端 mock 断言：单通道禁 IN、通道残缺双向封顶 EDGE（含 UNDET+OUT 混合）、空通道禁判 OUT、≥2 通道 IN 语义、背景不足端到端 UNDETERMINED 且零嵌入调用、维度漂移登记、通道 <2 拒判、judge_channel 防御闸、台账坏行续跑、无钥禁编造、链断可检出），零网络，PASS 字样为凭。

## Runtime 中立

纯标准库（urllib），Python ≥3.8；凭据仅经环境变量读取（BAILIAN_API_KEY/TOKENHUB_API_KEY/ZAI_API_KEY/VOLCENGINE_API_KEY），零凭据落盘；网络缺席时 smoke 与 review 照常可用。
