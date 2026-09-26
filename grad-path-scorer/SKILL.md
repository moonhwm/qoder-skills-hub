---
name: grad-path-scorer
description: "[项目技能] 升学路径加权评分引擎（硕士择校 × 申博衔接特化）。当用户需要评估硕士院校选择、量化「学术断头路」风险、建模申博衔接能力、模拟导师指导舒适度对读博意愿的扰动漂移、计算反悔成本非线性放大、对院校做多维加权排序并输出置信度标注时使用。触发词示例：\"硕士择校评分\"\"学术断头路\"\"申博衔接\"\"读博意愿扰动\"\"反悔成本\"\"院校加权排序\"\"权重评分系统\"。通用打分框架归 multi-dimensional-option-scoring，录取面板判别归 admission-panel-analytics，决策编排归 unified-decision-suite；本技能只做：硕博衔接特化评分引擎（去重计分/置信度展示层/层级扰动/断头路惩罚/门槛降档）。中文名：升学评分引擎"
metadata:
  version: "2.3.7"
---

# 升学评分引擎（grad-path-scorer）

硕士院校选择的加权评分引擎，特化于**申博衔接**场景。核心机制源自 2026-08-28 权重评分系统优化会话的六项决策。

<!-- v2.3.7（2026-08-29，修改人：Kimi K3）σ 量级推导（t3-02 进展）：文献链提案区间 [0.16,0.49]，占位低估 2~3 倍；冲击测试示稳健性叙事翻转（TOP6 保持 60%→16%），「终榜关扰动」升级为必要纪律；默认值不动（关键假设未验证），参数零变更 -->
<!-- v2.3.6（2026-08-29，修改人：Kimi K3）参数研究：mp×disc 可识别性攻关收官——锚表上为完全平原（315 点 ρ 全距 0.0013），机制三层证据+假想实验修复方向，U5 面板三要求操作化；t3-07 转 confirmed；参数零变更（面板到手前不动平原内现行值） -->
<!-- v2.3.5（2026-08-29，修改人：Kimi K3）合规收口轮：① 42 校基准加 deprecated_by 标记（43 校严格超集+2 勘误实证，保留作回归锚，防误用）；② 管线契约机检四要素全 PASS（data_cutoff/conf 词表/top3/降序）；③ top3 生命周期 cron 日检环节实装（daily_check.py 七项全绿后注册，协议 v2.3"禁只登记不处置"合规缺口闭合）；评分机制与参数零变更 -->
<!-- v2.3.4（2026-08-29，修改人：Kimi K3）U5 管线实弹演练：calibrate_weights.py 输入路径参数化（原 13 校 pilot 文件遗失实证——硬编码路径=玩具风险，修复后显式传参+明确报错）；43 校重建件复跑 8k 采样+坐标下降收敛，权重/折扣落 v2.0 邻域（ρ=0.9214 vs 历史 0.9252）——v2.0 收敛从"历史叙事"升级为"可复现声明（邻域级）"；σ 文献方向锚定（量级仍待样本）；评分机制与参数零变更 -->
<!-- v2.3.3（2026-08-29，修改人：Kimi K3）U3 拍板落账：用户授权主程序代决，经五维测试矩阵（T1 噪声 200 种子/T2 形态/T3 越线/T4 敏感性交互/全域排序扫描）裁决——维持 exp k=2.0（无任何替代方案在可测维度占优；A 额外保跨版本可比性）；裁决可撤销（用户保留一票恢复权）；calibration_todo 行 3 注销；评分机制与参数零变更 -->
<!-- v2.3.2（2026-08-29，修改人：Kimi K3）U4 挂账清账：--sensitivity 密集池判据升级为 gap-aware——43 校池全部 TOP6 变动归因=西南交大↔SWIP 近 tie 对互换（分差 0.30 < city 维 ±5pp 摆幅上界 0.70），近 tie 翻转改判预期行为，verdict_dense 引入 unexplained_flips 清单；frontmatter 补登 metadata.version（v2.5.1 立法）；description 加 [项目技能] 前缀（bridge 机制 C 存量对齐）；评分机制与参数零变更 -->
<!-- v2.3.1（2026-08-29，修改人：Kimi K3）打包交接前漂移修正两则：① top3_likely_wrong 与 calibration_todo 表格状态对齐 v2.0 代理锚收敛口径（权重非占位、max_penalty=22）；② --sensitivity 增补密集池口径（≥20 校时报 worst_top2/top6_changed 与 verdict_dense）——旧 <20% 判据在 43 校池恒 FAIL（0.465，原始副本同值，证实 v2.0 前即存在），校准文档已改判据而代码未跟进的裂隙就此缝合；评分机制与参数零变更；本会话产出 .skill 双保险包（安装位与 upload 均只读，包落 <输出区>/） -->
<!-- v2.3（2026-08-28，修改人：Kimi K3）top3_likely_wrong 推翻法执行：兰大核聚变学院 2025-12-26 成立+陈俊凌任常务副院长（72.32 上调）；复旦东昇聚变「晨光」托卡马克在建（73.49 上调）；SWIP 博士全员定向条款范围查实 -->
<!-- v2.2（2026-08-28，修改人：Kimi K3）同类漏洞排查收官：SWIP 学籍独立成立（定向培养条款知情）；哈工程硕士口径修正（本科特色班≠硕士方向）；中科大 52 系入库（43 单位，75.85 第 8） -->
<!-- v2.1（2026-08-28，修改人：Kimi K3）对抗性自审修复：ASIPP 与中科大科学岛重复计列合并（43→42 单位），risk 42→62 修正，合并后 87.21 居首；漏洞 2/3 循环论证与阴性漏检声明入交接 -->
<!-- v2.0（2026-08-28，修改人：Kimi K3）U1 参数收敛：权重脱离占位（锚点库 31 校代理锚校准，ρ=0.9252）；新增第七条机制——dead_end 托底折减（city/funding×0.4）；max_penalty 15→22；敏感性 0.512→0.372 -->
<!-- v1.11（2026-08-28，修改人：Kimi K3）代理锚校准 PASS（锚点库 31 校 Spearman ρ=0.907）；托底偏差发现（dead_end 校被 city/funding 托底，列入 U1 拍板包）；中山/南航 conf 升 empirical；川大锚点高估登记；山大 2025 新增核科学博士点状态变化 -->
<!-- v1.10（2026-08-28，修改人：Kimi K3）复旦大学入库（第 43 单位，聚变科学与工程一级博士点在招实证）；清华/ASIPP admission_risk 实证补录（清华统考 6 录 2 vs 科学岛差额 1.3:1）；U3 三情景分析：TOP16 排序与路径偏好无关 -->
<!-- v1.9.2（2026-08-28，修改人：Kimi K3）B档迁移校 playbook 复核：浙大/哈工程/上交/北大 四校 conf 升 empirical（上交重明装置上调至 76.15）；中山维持 estimated；头部 14 名全部实证级 -->
<!-- v1.9.1（2026-08-28，修改人：Kimi K3）governance 42 单位真闭环：北大任羽中获刑案/内蒙古科大李保卫三罪/东华理工刘庆成/浙大褚健/山大巡视问责/华南理工复试案等 9 校 flags 新增 -->
<!-- v1.9（2026-08-28，修改人：Kimi K3）锚点库全量迁移 16 校（B/C-D 档 14 + F 档参照 2），候选池 42 单位对齐 fusion-program-audit 44 校底表；迁移项三事实为评级反推、conf=estimated、待 playbook 复核 -->
<!-- v1.8.3（2026-08-28，修改人：Kimi K3）governance 26 单位全覆盖闭环：石河子魏忠在任实案+附院链、南昌大周文斌历史大案、燕大巡视整改；同名邻校噪声（内蒙古医大/新疆医大/西电）全部隔离 -->
<!-- v1.8.2（2026-08-28，修改人：Kimi K3）governance 覆盖扩至 18 单位（U11 关闭）：新增北师大刘川生/人大纪宝成一把手历史实案、川大安小予、郑大阚全程附院系、兰大/合工大中层执纪；北科大/西北师大未检出 -->
<!-- v1.8.1（2026-08-28，修改人：Kimi K3）governance 核查扩面 10 单位：清华/中科大/华科/西交挂执纪记录 flags，ASIPP 挂宋道军防误绑警示，SWIP/大工/西南交大/哈工大未检出；coverage 字段登记核查边界 -->
<!-- v1.8（2026-08-28，修改人：Kimi K3）新增 references/audit_playbook.md 初次核查操课表（装置驱动穷举/装置状态四分与在建叙事红线/名称混淆陷阱表/信源层级/最小核查清单）——把本会话误判教训固化为初次核查深度保障 -->
<!-- v1.7.1（2026-08-28，修改人：Kimi K3）南华 governance_flags 追加党委线两条：高山高升无案/唐忠阳纪检出身接任/校长空缺；2018 巡视通报科研经费病灶实证边界 -->
<!-- v1.7（2026-08-28，修改人：Kimi K3）治理风险展示层：facts 新增 governance_flags 字段（仅 A 级纪委通报/司法文书可入，零计分，禁止影射导师团队），score_engine 透传展示；南华大学挂 5 条 A 级实证 flags -->
<!-- v1.6（2026-08-28，修改人：Kimi K3）fusion-program-audit 锚点库对齐：南华大学误判自修正（68.25→43.45 入 dead_end，CN-H1 烂尾红线）+哈工大下修+郑大冲突登记+锚点迁移入库 5 校（中科大/西交/合工大/兰大/南昌大）；基准库 26 单位。机制无变更 -->
<!-- v1.5（2026-08-28，修改人：Kimi K3）长尾审计三连发现：西南交大CFQS仿星器/南华大学H-1仿星器重建中/哈工大王晓钢团队入库，西北师大（聚变支撑路径）转正；基准库扩至21单位。机制无变更 -->
<!-- v1.4（2026-08-28，修改人：Kimi K3）候选池完整性审计：基准库扩至 17 单位（补华中科技大学 J-TEXT/清华工物 SUNIST/ASIPP 三大磁约束正统遗漏）；exit_channel 采集试运行（内工大 2/17 出口案例存档，候选池各校暂无直接数据维持 null/hard）-->
<!-- v1.3（2026-08-28，修改人：Kimi K3）断头路软硬分级：classifier 新增 exit_channel 第四事实，soft 惩罚×soft_factor(0.5)；基准库扩至 14 校（新增人大王伟民团队，西北大学改判断头路，石河子改软断头）-->
<!-- v1.2（2026-08-28，修改人：Kimi K3）新增 assets/benchmark_schools_43.json：43 单位基准数据集（26 独立核查+16 锚点迁移，迁移项 conf=estimated 待复核）（含来源 URL 与 conf 分级），可作回归基准与打分样例；北师大独立核查定断（DCI 正式成员）-->
<!-- v1.1（2026-08-28，修改人：Kimi K3）新增 --sensitivity 敏感性分析（验收标准2落地）、--stress 边界压测 6 用例、scripts/dead_end_classifier.py 断头路数据层判定器（机制部分落地，数据收集仍待办）-->
<!-- v1.0（2026-08-28）重建版：六机制 + 占位参数 -->

## 六条设计纪律（不可妥协）

1. **字段只计一次**：`access`/`faculty` 等被并入 `phd` 的字段不再单独计分（`dedup_groups` 声明）。
2. **无基础常数项**：总分 = Σ(维度分×权重) − 惩罚。禁止任何 W_BASIC 式虚高常数。
3. **置信度不进总分**：`conf`（empirical/estimated/assumed）仅作展示层标签（🔵/🟡/🔴），绝不乘入分数。
4. **导师舒适度扰动**：读博意愿随硕导指导体验漂移——`phd` 维加高斯扰动，σ 按院校层级（tier1/2/3）分层。
5. **断头路惩罚非线性**：`dead_end=true` 且 `regret_intent>0` 时触发，随意向度非线性放大（默认 e 指数族 `(e^{kx}−1)/(e^k−1)`，可切 linear/threshold）。
6. **门槛级降档**：维度分低于门槛触发 tier 降档（层级可分，可整体关闭）。

## 快速开始

```bash
# 冒烟自测（交付前必跑）+ 边界压测
python3 scripts/score_engine.py --smoke
python3 scripts/score_engine.py --stress

# 评分（院校 JSON 从 stdin 或文件传入）
python3 scripts/score_engine.py --seed 42 schools.json

# 敏感性分析（逐维 ±5pp；<20 校池看排序翻转率 <20%，≥20 校密集池看 dense_pool 的 gap-aware 判定）
python3 scripts/score_engine.py --sensitivity schools.json

# 断头路自动判定 → 评分（数据层管道，推荐用法）
python3 scripts/dead_end_classifier.py facts.json | python3 scripts/score_engine.py --seed 42

# 关闭扰动 / 自定义配置
python3 scripts/score_engine.py --no-perturb --config my_cfg.json schools.json
```

**最终排序报告必须关扰动**（`--no-perturb`）或多 seed 取均值——扰动是意愿漂移模拟，不是单次决策依据。

**可审计性**：交付排序时把 `--sensitivity` 输出 JSON 随报告一并存档——口头稳健性声明不可验证，落盘才算数（v2.3.1 评估轮实测教训）。

## 输入 schema（院校 JSON）

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 院校名 |
| `phd` / `city` / `funding` / `platform` / `admission_risk` | 0–100 | 维度分（默认五维，权重见配置） |
| `access` / `faculty` | 0–100 | 被并入 phd 的字段，输入后只计一次 |
| `tier` | tier1/2/3 | 院校层级，决定扰动 σ（非法值回退 tier2） |
| `dead_end` | bool | 学术断头路标记（建议由 dead_end_classifier.py 生成，勿手填） |
| `regret_intent` | 0–1 | 反悔意向度 = **进入该校后仍想申博的强度**（越高 → 断头路代价越大 → 惩罚越重）。⚠ 语义易误读：它不是「想放弃的程度」，切勿反向使用 |
| `conf` | str | 数据置信度（展示层标签） |

判定器输入（dead_end_classifier.py）：`has_phd_program` / `advisor_phd_qualified` / `has_platform` 三事实布尔，可空——任一 false 判断头路，有 null 则 conf 强制降 assumed。v1.3 新增可选第四事实 `exit_channel`（稳定跨校申博出口）：断头路+exit_channel=true → soft（惩罚减半），否则 hard。

## 输出契约

JSON：`results[]`（按 total 降序，含 breakdown/perturbation/penalties/demotions/conf_tag）+ `data_cutoff` + `top3_likely_wrong`。可直接喂给 `multi-dimensional-option-scoring` 的 dimensions 或 `unified-decision-suite` 编排层（管线契约见 cross-session-workflow-bridge 的 pipeline_contracts.md）。

## References

- [references/audit_playbook.md](references/audit_playbook.md)：⭐ **核查任何新校前必读**——初次核查操课表：装置驱动穷举（院校名单驱动必漏）、装置状态四分与"在建叙事"红线（南华教训）、名称混淆陷阱表、三事实采集模板与信源层级、每校最小核查清单。
- [references/methodology.md](references/methodology.md)：六条纪律的推导动机与参数语义。**调参数前必读**。
- [references/calibration_todo.md](references/calibration_todo.md)：⚠ 待校准清单——权重与惩罚上限已经 v2.0 代理锚收敛（ρ=0.9252，外部实证仍待用户面板）；σ 分层/门槛值/输入量纲仍为**占位值**，使用前逐项核对。
- [assets/benchmark_schools_43.json](assets/benchmark_schools_43.json)：43 单位基准数据集（26 独立核查+16 锚点迁移，迁移项 conf=estimated 待复核）（聚变/等离子体方向，2026-08-28，含软硬分级与来源 URL 与 conf 分级）。用途：① 管道端到端演示与回归基准；② 新校核查后追加扩库；③ 维度分为估算占位，排序不可作决策依据。
