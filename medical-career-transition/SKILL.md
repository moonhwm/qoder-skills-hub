---
name: medical-career-transition
description: 医学背景者的转行与就业特化决策支持。当用户讨论医学转行、医学生就业、医生转行、医学生职业规划、离职、规培退出、医学硕士/博士不进临床的出路时触发；覆盖 MSL（医学联络官）、医学事务（MA）、医学写作、医学编辑、CRA、CRC、医药代表/器械销售、大专/中职教师（护理/临床专业）、医学物理师、放疗物理、医疗AI/医疗信息化、执业药师、公务员/卫健委/疾控、保险核保理赔、医药专利代理、医学可视化/科普等方向的门槛-收益-风险评估、硬约束一票否决初筛、多维评分排序与 90 天行动排期；也支持物理/工程背景（聚变/高温超导/AI4S）向医学装备与医疗 AI 的反向跨界评估。中文名：医学转行指南针
---

<!-- v1.6（2026-08-24）\这是中文解释：综合优化——新增 case_anchor_method 案例锚点册（五方法模式+单案例外推纪律）+ L 谱系节（ppp 沉淀溯源+城市维度最短光路委派指针）；v1.5.1 整合排期落位——补条件存档激活条件与主线接口注记（crossover↔fusion-program-audit 边界钉死）；v1.5 新增人才束缚图谱与松绑路径（法律效力三级+四步松绑规程） -->

# 医学转行指南针（medical-career-transition）

> 版本：v1.6（2026-08-24）企业生态、学术共同体、人才束缚、条件存档 + 案例锚点与 L 谱系。
> **免责声明**：本技能输出为信息性决策支持，不构成职业、法律或投资意见。收入区间如无官方统计一律标注 conf 等级，禁止当作承诺。

## 概述

将"医学背景往哪转"转化为可复核的量化流程：人物画像建档 → 转行动因确认 → 选项库初筛（硬约束一票否决）→ 三维评估（门槛/收益/风险）→ 对接 multi-dimensional-option-scoring 评分排序 → 输出带证据链的排序报告 + 90 天行动排期。方法论来源于一份已完成的转行指南实战案例（医学写作 🥇 / 大专教师 🥈 / MSL 🥉 的排序结论），本技能是其一般化。

## 铁律（证据链纪律，全程执行）

1. **conf 三级标注**：所有关键断言标注 conf=实证（官方文件/统计/可查事实）/ conf=估算（行业报告/招聘信息间接推断）/ conf=假设（无公开依据的推断）；结论置信度不得高于其最弱支撑证据。
2. **公开可查链接**：每个关键判断给官方入口首页 + 检索路径；禁止编造深链；查不到就显式标"无公开入口，conf=假设"。
3. **证据优先于提问**：能查证（收入区间、报考条件、招聘公告节奏）就不问用户；只有个人约束（城市、家庭、风险偏好）才提问，且附已查到的部分结果。
4. **top3_likely_wrong**：每份报告末尾列本次最可能错的 3 个点及各自影响方向。
5. **data_cutoff**：报告首页标注数据截止时间与建议复核日期（默认 12 个月，招聘/认证政策类 6 个月）。
6. **落盘纪律**：画像、证据登记表、评分 JSON、排序报告、排期文件全部写文件，命名 `{主题}_{类型}_{日期}`；禁止只在对话里留结论。
7. **选择题式交付**：排序报告以 2–4 个带推荐项的去向呈现（标推荐项+一句理由），不出开放问答。

## 工作流

### 第 1 步：人物画像快速建档

建档为 JSON（落盘 `profile_{日期}.json`），字段：

| 字段 | 说明 |
|------|------|
| 学历/专业 | 层次 + 专业（临床/护理/药学/基础/影像等） |
| 执业状态 | 有无执业证/规培状态（在培/结业/退出）/职称 |
| 城市约束 | 可接受城市清单；是否可远程 |
| 家庭约束 | 收入底线、照护责任、购房压力 |
| 风险动因 | 为什么转：夜班/工时/收入/执业风险/其他 |
| 核心标准 | 用户不可让步项（如"双休""无夜班""月入 8000+"），用于一票否决 |

建档时遵循证据优先：核心标准直接引用用户原话；缺失的个人约束才提问。

### 第 2 步：转行动因确认

- 若动因含执业/刑事风险（医疗事故、非法行医担忧），联动 **medical-malpractice-criminal-review** 做风险量化：引用其责任比例、责任等级、罪名建议等输出，**只引用不复制**其评分逻辑。
- 区分"逃离型动因"（怕夜班/怕风险）与"追求型动因"（想要双休/高收入/稳定编制）；逃离型动因必须量化核对（临床实际工时 vs 用户底线），避免情绪化决策。
- 动因结论写入画像 JSON 的 `motivation` 字段，附 conf。

### 第 3 步：选项库初筛（硬约束先行）

读 [references/option_library.md](references/option_library.md)，对每个选项先查一票否决项：

- **年龄**：公务员/编制教师多数限 35 岁（部分岗位 40 岁）；超龄直接淘汰。
- **编制/证书**：执业药师要求药学岗位工作年限；教师要求教师资格证；无证书且不愿考则淘汰。
- **学历**：MSL 通常要求硕士起；大专教师多数要求硕士起（部分护理岗位本科）。
- **城市**：公务员/教师绑定当地编制；医学写作/医疗信息化部分岗位可远程。
- **核心标准冲突**：用户要求"无夜班"则淘汰仍含夜班的岗位形态。

被否决的选项记录否决原因，不进入评分。剩余候选进入第 4 步。物理/工程背景或用户提及聚变/超导/AI4S 时，另读 [references/crossover_paths.md](references/crossover_paths.md) 补充交叉选项。

### 第 4 步：企业生态与学术资产盘点

对每个幸存候选做两项盘点，结论写入画像 JSON 后进入第 5 步：

1. **企业生态归层**：读 [references/enterprise_ecosystem.md](references/enterprise_ecosystem.md)，按文末映射表把候选归入药企/器械/CRO/保险/互联网医疗AI/医院集团六层之一，用该层的门槛、医学背景杠杆点、风险与天花板校准后续三维评估的评分口径；层级结论不替代选项库的单选项 conf 标注。
2. **学术共同体资产盘点**：读 [references/academic_community.md](references/academic_community.md)，逐项登记用户的学会任职、职称、师门网络、论文课题记录，按去向（企业/教职/公务员）分别估可迁移性；同时执行反向风险检查——学术沉没成本误判、头衔贬值曲线、职称临界点时机，结论写入画像 JSON 的 `academic_assets` 字段。该文件断言多为 conf=估算/假设，输出时必须复述"经验性判断非数据结论"声明。

3. **束缚清单盘点**：读 [references/talent_mobility_medical.md](references/talent_mobility_medical.md)，逐项盘点用户的规培/服务期协议、编制人事关系、执业注册状态、竞业条款、安家费/户口服务期，按"硬约束/软约束/伪约束"三级定级并给出松绑路径与时间线，结论写入画像 JSON 的 `mobility_constraints` 字段；束缚强度只影响转行时机与成本计价，不单独否决转行（时机逻辑接 academic_community.md 的职称临界点讨论）。

用户无学术资产（应届/无职称无论文）时，本步第 2 项可记录"无学术共同体资产"后跳过；候选不含企业场景时第 1 项可跳过；用户为在读学生或无在职束缚（未签任何服务期/补贴协议）时第 3 项可记录"无在职束缚"后跳过。跳过项在报告中注明理由。

### 第 5 步：三维评估（门槛/收益/风险）

对每个候选按三维打分（0-10），每维写证据与 conf：

1. **门槛**：证书/学历/经验达标度（不达标程度即转行成本）。
2. **收益**：预期年收入区间 + 3 年成长空间（收入一律标 conf=估算，除非有官方统计）。
3. **风险**：岗位稳定性、行业周期、退出成本（沉没成本 0-10）。

### 第 6 步：评分桥接与排序

用 `scripts/transition_scoring_bridge.py` 把候选转成 multi-dimensional-option-scoring 兼容输入：

```bash
cat candidates.json | python3 scripts/transition_scoring_bridge.py > scored_input.json
python3 -c "import json; d=json.load(open('scored_input.json')); \
  json.dump([{'option':o['option'],'dimensions':o['dimensions'],'negative_items':o['negative_items']} \
  for o in d['options']], open('engine_input.json','w'), ensure_ascii=False)"
cat engine_input.json | python3 <技能安装位>/multi-dimensional-option-scoring/scripts/scoring_engine.py
```

- 输入字段与硬约束一票否决标记规则见脚本 `--help`（docstring）。
- 硬约束未达标的候选在桥接输出中带 `vetoed=true`，直接淘汰，不喂入评分引擎。
- 排序结果按 multi-dimensional-option-scoring 的 A–F 分级解读；`rank_stability < 0.8` 时必须明示"排名对权重敏感"。

### 第 7 步：输出排序报告 + 90 天行动排期

报告结构（落盘 `transition_report_{日期}.md`）：

1. 人物画像摘要与核心标准表（标准 vs 现岗位匹配度）。
2. 初筛结果：淘汰清单 + 否决原因。
3. 排序结果：选项总分/等级/敏感性，各维度分值与证据摘要（含 conf、公开核查入口）。
4. top3_likely_wrong。
5. data_cutoff 与下次复核日期。
6. 机器可读 JSON 附录。

90 天行动排期（落盘 `action_plan_90d_{日期}.md/json`）：

- 以周为粒度列行动项（P0/P1/P2）：第 1-2 周完成核心选项定向调研；第 3-6 周补齐证书/作品/技能短板（如首篇医学写作、教资报名）；第 7-10 周投递与面试；第 11-13 周复盘收敛。
- 排期按 **iteration-convergence-ops** 的"排期即交付物"纪律：每项含完成判据与状态字段，每轮迭代后更新状态文件并 `ls` 核验落盘。
- 交付收尾时按收割规程归档：<输出区>/skills/cross-session-workflow-bridge 的 references/session_harvest.md。

## 脚本用法

`scripts/transition_scoring_bridge.py`（纯标准库，stdin/stdout）：

```bash
python3 scripts/transition_scoring_bridge.py --help
```

输入转行候选数组（中文或英文键均可）：

```json
[{"名称": "医学写作",
  "门槛达标度": 0.8, "预期年收入下限": 8, "预期年收入上限": 12,
  "三年成长空间": 7, "风险": 3, "沉没成本": 4, "城市约束匹配": 1.0,
  "硬约束达标": true, "conf": "estimated"}]
```

输出顶层含 `data_cutoff` 的 `{"options": [...]}`，每个 option 的 `dimensions` 元素含 `{name, score, weight, conf}`（conf 为 empirical/estimated/assumed），可直接喂入 multi-dimensional-option-scoring 的 scoring_engine.py。硬约束不达标者输出 `vetoed=true` 并附 `veto_reasons`。

## 参考资源

| 文件 | 用途 | 加载条件 |
|------|------|----------|
| `references/option_library.md` | 12+ 医学转行选项库：门槛/典型路径/收入区间(conf 标注)/退出成本/公开核查入口 | 第 3、5 步必读 |
| `references/crossover_paths.md` | 物理/工程↔医学双向跨界路径（放疗物理师、MRI/超导磁体工程、质子重离子装置、医用同位素、AI4S→医疗） | 用户有物理/工程背景或提及聚变/超导/AI4S 时必读 |
| `references/enterprise_ecosystem.md` | 企业级就业生态六层（药企/器械/CRO/保险/互联网医疗AI/医院集团）：门槛/杠杆点/天花板 + 与选项库映射表 | 第 4 步必读（候选含企业场景时） |
| `references/academic_community.md` | 学术共同体资产（学会任职/职称/师门/论文课题）的转行杠杆与贬值风险，多为 conf=估算/假设 | 第 4 步必读（用户有学术资产时） |
| `references/talent_mobility_medical.md` | 医疗人才束缚图谱（规培/服务期/编制/执业注册/竞业/安家费/户口）法律效力三级定级 + 四步松绑规程，法规类 conf=实证附 URL | 第 4 步必读（用户在职且涉辞职/违约金/编制/户口问题时） |
| `references/case_anchor_method.md` | 案例锚点与方法论溯源：实战案例S 脱敏蒸馏的五个方法模式（冲突矩阵/逃离动因量化/窗口期/城市折中/四粒度行动清单）+ 单案例外推纪律 | 方法论溯源、复核本技能流程设计依据时读 |
| `scripts/transition_scoring_bridge.py` | 候选→评分引擎输入的桥接器，含一票否决标记 | 第 6 步使用 |

上下游互指：domain-exoskeleton（安装后位于 <技能安装位>/；未安装时本指针忽略，功能不阻塞）的 `references/domain_medical.md` 提供医学→金融/法律/审计衍生映射并回指本技能选项库与交叉路径；执行衍生方向评估时加载该文件。

## 排期立场与主线接口（2026-08-24 整合排期落位）

- **条件存档**：本技能平时休眠。激活条件——①考研路径失败需 fallback 医学就业；
  ②用户主动重估转行方向；③用户或他人咨询医学背景职业转换。触发即解档，
  其余时间不进入路由推荐。
- **主线接口**：用户当前主线为物理/核方向考研；`references/crossover_paths.md`
  的聚变/高温超导/AI4S 跨界册与 fusion-program-audit 同源，涉及聚变期权判定
  时以 fusion-program-audit 的锚点与要旨为准，本技能只供职业侧映射。
- **L 谱系**：med-career-transition-L 项目（集群甲侧实战线）已沉淀出
  ppp-city-verdict-audit（城市结论 PPP 复核台）。本技能涉城市维度时按
  最短光路委派：城市结论清单复核→ppp-city-verdict-audit；通勤成本实测→
  travel-commute-planner；城市/宿舍舒适度→livability-audit-swarm；
  本技能不自建城市评估模块（奥卡姆）。

## 元范式核查清单（交付前逐条确认）

- [ ] 所有收入区间与门槛断言已标 conf 三级
- [ ] 每个关键断言附官方入口 + 检索路径，无编造深链
- [ ] 一票否决项全部显式记录原因
- [ ] 报告含 top3_likely_wrong、data_cutoff、下次复核日期
- [ ] 评分经 transition_scoring_bridge.py → scoring_engine.py 端到端跑通
- [ ] 90 天排期落盘且每项有完成判据
