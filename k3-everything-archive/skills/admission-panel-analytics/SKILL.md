---
name: admission-panel-analytics
description: 考研录取面板数据的校验、模式判别与轻量评分方法论，蒸馏自新东方36校面板分析档案：三录取模式判别（α一志愿过线即录/β零调剂堡垒/γ高调剂陷阱）、调剂窗口风险六层解构与三项系统性偏见警示、S/A/B/C/D五级信源置信度、迭代收敛协议（最大评分变化小于0.005且连续3轮）与五维交叉验证。内置 panel_validate/pattern_classify/score_panel 三脚本（纯标准库，--smoke 可实跑，stdin/stdout JSON）。当用户做考研择校、分析录取面板、报录比、一志愿率、调剂、复试通过率、必达分、判别录取模式、评估调剂窗口风险、搭建冲稳保链条、或做考研数据分析与院校面板评分时触发。中文名：考研面板分析台
---

# Admission Panel Analytics · 考研面板分析台

<!-- v1.0.1（2026-08-24）\这是中文解释：v12 质检 Q1 修复——data_cutoff 口径修正为输入携带+编排层补记；首版——蒸馏新东方36校面板分析范式（三录取模式+调剂窗口解构+信源分级） -->
这是中文解释：首版——蒸馏新东方36校面板分析范式（三录取模式+调剂窗口解构+信源分级） -->

## 定位

考研录取面板的**数据层分析台**：把目标校多年录取数据组为规范面板 JSON、逐字段校验、
判别三种录取模式、给出带敏感性分析的轻量评分与冲稳保分档素材。

**本技能只蒸馏"方法/范式/判别规则"**：正文与 references 不含任何真实院校数值，
示例均为脱敏合成数据；真实项目数据由使用方自带，按信源分级逐字段标注 conf。

## 五件套立场

- **data_cutoff**：录取面板强时效（招生口径年年变）。**输入**必须标注数据年份范围与
  data_cutoff；脚本输出不回显该字段，聚合方（如 unified-decision-suite）负责在
  包壳中补记；跨年外推（如用 2022-2026 推 2027）一律 conf=assumed 并显式声明外推误差风险。
- **top3_likely_wrong**：每次正式分析（非 smoke）在结论末尾给出最可能错的 3 个点
  （高频项：必达分≠录取线、调剂窗口时长缺测、缺录取实证导致模式误判）。
- **选择题式交付**：择校结论给 2-4 个候选 + 推荐项 + 理由链 + 冲稳保分档；
  不给单一"标准答案"，不利候选也要列出并说明剔除理由。
- **conf 三级**：输入逐字段标 conf（empirical/estimated/assumed），与 S/A/B/C/D 信源
  双向映射（见 `references/source_confidence.md`）；脚本输出携带 conf 与理由链。
- **收割指针**：会话结束按 cross-session-workflow-bridge 的 session_harvest 规程沉淀
  面板 JSON、判别结论与待办（安装后位于 <技能安装位>/；未安装时本指针忽略）。

## 路由表（用户信号 → 资源）

| 用户信号 | 路由 | 说明 |
|---|---|---|
| 面板字段怎么填、数据字典、缺数据怎么办 | `references/panel_schema.md` | 15 项核心指标定义+取值约束+缺测处理规范 |
| 校验面板 JSON、字段报错、通过率 | `scripts/panel_validate.py` | 逐字段类型/范围/一致性/缺测校验，输出错误清单+通过率 |
| 过线即录、零调剂、高调剂陷阱、录取模式判别 | `scripts/pattern_classify.py` + `references/admission_patterns.md` §1-2 | α/β/γ 判别规则+对一志愿考生的真实含义 |
| 调剂窗口、窗口极短、14 小时、调剂风险 | `references/admission_patterns.md` §3 + `scripts/pattern_classify.py` | 六层解构+窗口风险三因子（时长/优先级档/一志愿保护度）评级 |
| 信源可不可信、S/A/B/C/D、conf 标注 | `references/source_confidence.md` | 五级信源范式+conf 三级映射+缺失数据处置 |
| 评分、打分、冲稳保排序、权重敏感性 | `scripts/score_panel.py` | 轻量评分+权重 ±20% 扰动敏感性+诚实标注 |
| 迭代到收敛、交叉验证、版本回溯纠错 | `references/iteration_protocol.md` | 8 步流程+收敛标准+5 维验证+回溯纠错 |
| 偏见自查、结论反向检验、自我批判 | `references/admission_patterns.md` §4 | 三项系统性偏见警示清单 |

## 核心工作流（五步）

1. **组面板**：按 `references/panel_schema.md` 把目标校多年数据组为面板 JSON，逐字段标
   conf；缺测字段按缺测规范处置（宁缺毋造，null 而非 0）。
2. **校验**：`python3 scripts/panel_validate.py panel.json` → 错误清零或显式豁免后再分析；
   关键字段（total_admit/first_choice_admit）缺测的年份记录不得进入模式判别。
3. **判别模式**：`python3 scripts/pattern_classify.py school.json` → α/β/γ + 调剂窗口风险
   等级 + 置信度 + 理由链；对照 `references/admission_patterns.md` §4 做偏见自查。
4. **评分排序**：`python3 scripts/score_panel.py schools.json` → 评分 + 六项分解 + 敏感性 +
   诚实标注；按分档组装冲稳保候选（选择题式交付）。
5. **迭代收敛**：按 `references/iteration_protocol.md` 8 步流程迭代；收敛标准=最大评分变化
   小于 0.005 且连续 3 轮；未收敛前所有结论标"未收敛"并降级交付。

## 脚本用法速览

所有脚本：`--smoke` 实跑合成样例冒烟（exit=0）；否则从文件参数或 stdin 读 JSON、
向 stdout 写 JSON（`ensure_ascii=False`）。纯标准库，无需第三方依赖。

```bash
python3 scripts/panel_validate.py --smoke        # 合成校校验自测
python3 scripts/pattern_classify.py --smoke      # 合成 α/β/γ 三校判别自测
python3 scripts/score_panel.py --smoke           # 合成三校评分+敏感性自测

python3 scripts/panel_validate.py panel.json
cat school.json | python3 scripts/pattern_classify.py
python3 scripts/score_panel.py schools.json --weights '{"first_choice_rate":0.5}'
```

## 关键判别规则速记

- **α 一志愿过线即录**：一志愿复试通过率 100%（容差 ≥0.98）且调剂为补录非竞争
  （进复试者全录、调剂是计划未满的额外名额）→ 对一志愿考生=单向成功路径；
  但警惕"筛选前置"：通过率 100% 可能只是进复试的人少。
- **β 零调剂堡垒**：一志愿率 ≥90% 且连续 3 年（含）以上零调剂 → 高门槛、高保护，
  无调剂窗口风险；重点核查必达分硬门槛而非录取概率。
- **γ 高调剂陷阱**：一志愿率 <30% 且复试后大量刷人（复试通过率 <50% 或调剂率 >70%）
  → "名校落榜生避风港"，一志愿考生实为备胎；切勿误判为"双非保底校"。
- **调剂窗口**：窗口越短（如 14h），规则文本越让位于"先到先得"；
  一志愿失败≈断崖式 GAP 风险；C/D 档优先级在短窗口下实际竞争力趋近于零。
- **必达分≠录取线**：必达分低=复试线低，不代表录取线低；两者须分列核查。

## 互指

**互指**：本技能产出的规范面板数据、模式判别结论与轻量评分，是 `unified-decision-suite`
（统一决策套件，安装后位于 <技能安装位>/；未安装时本指针忽略）的**数据层输入**——
面板校验/模式判别/轻量评分在此完成；跨域综合决策（深度权重耦合、路径规划、最终择校裁定）
由 unified-decision-suite 消费本技能的输出 JSON 完成。

## 局限与边界

- 不内置任何真实院校数据；判别质量取决于输入面板的年份覆盖（建议 ≥3 年）与信源等级。
- score_panel 为 L1 原型级轻量线性评分器，权重可配；不替代 unified-decision-suite 的
  完整权重耦合决策，结论必须经敏感性分析与偏见自查后方可交付。
- 调剂窗口时长、优先级档位等字段常年缺测；缺测时风险评级自动降级并显式标注
  "窗口未知"，禁止默认按"窗口充足"处理。
