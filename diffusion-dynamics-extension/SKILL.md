---
name: diffusion-dynamics-extension
description: 动态演化与干预效果量化扩展技能。当已有静态评估结论、需要回答"随时间/空间如何演化""不干预会怎样""干预 ROI 多大"时使用。触发场景：信息/舆情传播预测、人才或用户流动预测、区域分布演化、政策干预效果量化。领域无关，提供 SIRD 传染病式扩散、Fick-Gravity 空间流动、Logistic 密度场三类模型及双情景对比，内置参数置信度分级与防循环论证硬约束。中文名：演化推演器
---
<!-- v1.4（2026-08-24）\这是中文解释：新增前沿算法实验台互指——SIR 高阶算法（Gillespie/链二项式/边基分区）与谱半径免疫分配已下沉为可运行脚本，本卡负责假设审查与选型，算力实现走 quant-frontier-lab -->

# 演化推演器（diffusion-dynamics-extension）

在静态评估结论之上叠加时间/空间维度：预测演化轨迹、量化干预效果、回接修正静态评分。

应用域：信息/舆情传播预测、区域分布演化、政策干预效果量化、**人才流动推演**
（推拉-重力模型 + 制度距离 + 高校束缚评分卡，见
`references/talent_flow_model.md`）。

**互指**：SIR 高阶传染算法（Gillespie SSA / 链二项式 / 边基分区）、谱半径免疫分配、
PSM 倾向得分、Gale-Shapley 双边匹配、玩具级元学习的可运行实现位于
`quant-frontier-lab`（前沿算法实验台）的 `scripts/`（安装后位于 <技能安装位>/；
未安装时本指针忽略，本技能内置三脚本功能不阻塞）。分工约定：本技能负责模型假设
审查与严肃等级裁定，quant-frontier-lab 负责算法实现与参数归档。

## 总览

按以下六步工作流执行；三个模拟脚本在 `scripts/`，模型假设审查手册在
`references/model_assumptions_and_limits.md`（对选型、参数或措辞有任何
不确定时加载），联合报告模板在 `templates/dynamic_report.json`。

## 步骤 1：识别扩散对象与状态划分

判定扩散对象（信息/人群/资本/其他），并把研究对象映射到 SIRD 式四室：

| 室 | 通用语义 | 舆情场景映射 | 人才流动场景映射 |
|---|---|---|---|
| S 易感 | 尚未卷入的潜在对象 | 未接触信息的潜在人群 | 未考虑流动的人才池 |
| I 感染 | 活跃的扩散载体 | 主动转发/传播者 | 正在求职/流动中的人 |
| R 恢复 | 退出扩散但留存 | 不再转发/已免疫 | 已在新岗位稳定下来 |
| D 消亡 | 永久流失 | 被证伪后退出/卸载 | 退出劳动力/迁出系统外 |

在报告的 `diffusion_object.state_mapping` 中显式写出本场景的语义映射表。
若对象不适合四室结构（如纯空间渗透），跳过状态映射并说明理由。

## 步骤 2：参数估计与校准

为每个参数（β/γ/δ、A/C/d、D/r/K 等）填写校准表，**每个参数必填**：

| 参数 | 值 | conf | 校准方法 | 数据源 | 合理区间 |
|---|---|---|---|---|---|
| β | 0.35 | 估算 | 爆发初期倍增时间反推 | 平台热度曲线 7 天 | [0.2, 0.5] |

规则：
- `conf` 三档：实证（有直接数据拟合）/ 估算（类比、邻域、专家经验）/ 假设（无依据，仅合理区间）。
- 无数据时显式标 `conf="假设"`，并给出合理区间与取值依据。
- **禁止给估算参数标实证级置信度**；禁止把单点观测包装成"拟合结果"。

## 步骤 3：三模型选型决策树

```
扩散有"人传人/接触传染"机制（舆情、观念、欺诈信息、口碑）？
├─ 是 → SIRD 四室 ODE → scripts/sird_simulate.py
└─ 否 → 关注跨区域/目的地的流动或渗透（就业、迁移、门店扩张）？
    ├─ 是 → Fick-Gravity 空间流动 → scripts/gravity_diffusion.py
    │        （可导出壁垒系数 = 1 − 实际渗透/理论渗透，须标"待验证假设"）
    └─ 否 → 关注密度场的长期演化与前沿推进（产业密度、覆盖度）？
        └─ 是 → Logistic-扩散密度场 → scripts/logistic_density.py
```

模型复杂度必须与数据质量匹配：独立观测点数 ≤ 5 时只用集总模型（SIRD），
不跑空间模型。详细假设与适用边界见
`references/model_assumptions_and_limits.md`。

## 步骤 4：运行模拟（脚本用法）

三个脚本均为纯标准库、stdin 读 JSON / stdout 写 JSON，支持 `--help`。

SIRD 单情景与双情景对比：

```bash
echo '{"S0":99000,"I0":1000,"beta":0.35,"gamma":0.1,"delta":0.01,"days":120,
"params_conf":{"beta":"估算","gamma":"实证","delta":"假设"},
"intervention":{"start_day":30,"beta_scale":0.6,"gamma_scale":1.5}}' \
  | python3 scripts/sird_simulate.py
```

提供 `intervention` 即进入双情景模式：baseline 为无干预，effect 输出
峰值削减、消亡避免数、累计感染削减等差值指标。

Fick-Gravity 理论渗透与壁垒系数：

```bash
echo '{"unit":"km","destinations":[
{"name":"城市B","A":120,"d":50,"actual":800},
{"name":"城市C","A":80,"C":1.2,"d":120,"actual":150}]}' \
  | python3 scripts/gravity_diffusion.py
```

输出每目的地理论通量份额、实际/理论比、壁垒系数，并强制附
`verification_status="unverified_hypothesis（待验证假设）"`。

Logistic 密度场（∂ρ/∂t = D∇²ρ + rρ(1−ρ/K) + S − L 的简化一维实现）：

```bash
echo '{"n":101,"dx":1,"D":0.5,"r":0.2,"K":1,"days":100,
"initial":{"type":"point","position":0,"mass":0.1},
"intervention":{"start_day":40,"overrides":{"D":0.1,"L":0.02}}}' \
  | python3 scripts/logistic_density.py
```

输出逐日总量/峰值密度/前沿位置、终态剖面、前沿推进速度估计，
以及干预情景的差值。

## 步骤 5：情景模拟与干预效果量化

始终跑无干预 vs 干预双情景，差值即干预效果量化：
- 干预通道要写实：辟谣→降 β；加速澄清→升 γ；补贴迁移→升 A 或降 C；
  限制扩张→降 D（扩散系数）或升 L。
- 干预通常多通道作用，禁止只改单一参数夸大效果；对干预参数同样标 conf。
- 有干预成本数据时计算 ROI 或成本效果比；无成本数据时在报告中写"无法估计"，不得编造。

## 步骤 6：回接静态评分并输出联合报告

壁垒系数作为静态评分的修正因子，接口格式：

```
调整后静态分 = 静态总分 × (1 − barrier_coefficient × w)
  w ∈ [0,1]：壁垒维度在静态评分中的权重
```

壁垒系数验证前，`w` 只能用于敏感性分析（给出 w=0/0.5/1 三档结果），
不得输出单一"调整后得分"当作结论。

输出遵循 `templates/dynamic_report.json`，以下为必填项：
- `report_meta.data_cutoff`：**强制标注数据截止时间**；
- `parameters[]`：每个参数含 conf/校准方法/数据源；
- `scenarios`：双情景结果与 effect 差值；
- `assumptions_table`：模型假设表；
- `limitations`：至少 2 条局限性；
- `top3_likely_wrong`：**"最可能错的 3 个点"，必填**。

## 防偏硬条款（必须执行）

1. 所有参数标 conf 等级（实证/估算/假设）；禁止给估算参数实证级置信度。
2. **禁止循环论证**：理论 vs 实际的差值不得在未独立验证时直接命名为
   "壁垒系数"使用；必须标注为待验证假设，并列出计划/已收集的独立证据
   （行政壁垒清单、问卷、政策放开前后的自然实验等）。反面案例见
   `references/model_assumptions_and_limits.md` 第 4 节。
3. 模型复杂度须与数据质量匹配；结论措辞不得超出证据强度：
   实证参数→"模型显示"；估算参数→"在……假设下估计"；
   假设参数→"示意性测算，数量级参考"。
4. 报告必须含局限性与"最可能错的 3 个点"。
5. 强制标注数据截止时间（`data_cutoff`）。

## Resources

- `scripts/`：`sird_simulate.py`、`gravity_diffusion.py`、`logistic_density.py`
  （纯标准库，stdin JSON → stdout JSON）。
- `references/model_assumptions_and_limits.md`：三模型假设表、适用边界与
  循环论证案例警示。
- `references/talent_flow_model.md`：**人才流动推演**应用模块——推拉-重力模型、
  制度距离（IDU）量化刻度、高校束缚强度评分卡（0–10）、三档情景推演框架与
  医学/聚变两个应用例。
- `templates/dynamic_report.json`：静态+动态联合报告模板。

## 纪律补丁（v1.2 范式洗礼）

- **选择题式交付**：联合报告以情景选项收口（如"A 不干预 / B 干预方案甲 / C 干预方案乙"各附量化差值），由用户拍板，不替用户选干预方案。
- **落盘纪律**：报告 JSON 落盘到工作目录（遵循 `templates/dynamic_report.json`），对话内只给摘要与文件路径。
- 交付收尾时按收割规程归档：<输出区>/skills/cross-session-workflow-bridge 的 references/session_harvest.md。
