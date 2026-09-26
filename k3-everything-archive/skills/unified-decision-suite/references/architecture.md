# 四层架构与端到端时序（v1.0 落实 v0.9 设计提案 §1/§4/§9.5）

> 严肃化等级：L1 原型 | unverified：是 | data_cutoff：2026-08-24
> 本文是统一决策套件的架构宪章：层职责、引擎接入方式、失败传播规则。
> 接口 schema 快照见 `interface_contracts.md`；9 月锁校实装见 `september_lock_protocol.md`。

## 1. 四层架构总览

```
┌─ 交付层  选择题式交付 + top3_likely_wrong + 收割指针（session_harvest）
├─ 引擎层  路径级：hrank / NSGA-II / MCTS / Nested Sampling（decision-sys，转述接入）
│          院校级：scoring_engine / gale_shapley(9月锁校) / psm_balance / meme_calibrator
├─ 证据层  conf 三级(empirical/estimated/assumed) × S/A/B/C/D 信源分级映射表
│          对接 cross-session-workflow-bridge/references/pipeline_contracts.md
└─ 数据层  新东方PDF面板(35/36校×5年) / 57校JSON / 官方A级信源登记册
```

| 层 | 职责 | 输入来自 | 输出去往 | 现有资产 |
|---|---|---|---|---|
| 数据层 | 原始事实的登记与版本化，不做推断 | 外部信源 | 证据层 | 院校实战排序_2026-08-24.json；新东方 PDF（另一会话，待移交）；fusion-program-audit 锚点库 |
| 证据层 | 给每个数据点打 conf + 信源等级 + data_cutoff | 数据层 | 引擎层 | pipeline_contracts 双词表；evidence-chain-verifier |
| 引擎层 | 路径级与院校级算法分工计算 | 证据层 | 交付层 | decision-sys v68.64（转述，代码不在场）；quant-frontier-lab / multi-dimensional-option-scoring 脚本（在场） |
| 交付层 | 面向人的选择题式结论与自我批判 | 引擎层 | 用户 / 下次会话 | iteration-convergence-ops 四行记录；session_harvest 收割规程 |

**设计纪律（三层铁律）**：

1. 数据层产物**禁止含推断结论**（只登记事实与出处）。
2. 引擎层**禁止引入未在证据层登记的数值**。
3. 交付层**必须含 top3_likely_wrong**（pipeline_contracts 对报告类产物的必填项）。

## 2. 引擎分工与接入方式

分工原则：**路径级回答"走哪条轨"，院校级回答"轨内报哪所"**。路径级引擎输出
（如"9 月模考≥55 则解锁数一依赖轨"）作为院校级引擎的门控开关，而非分数项——
避免把路径判断稀释进加权平均（hrank 的门槛性质教训）。

| 引擎 | 层级 | 用途 | 现状 | 接入方式 |
|---|---|---|---|---|
| hrank 分层序列法 | 路径级 | 六轨主排序，层间不可补偿 | decision-sys v68.64，**代码不在场** | 转述适配器（见下节），禁止重实现 |
| NSGA-II 三目标帕累托 | 路径级 | (max Q, max feasibility, min cost) 前沿分层 | 同上 | 同上 |
| MCTS 时序决策 | 路径级 | 9 月→次年 1 月动作序列（UCT） | 同上 | 同上 |
| Nested Sampling 后验 | 路径级 | 数一技能后验，55 分=质变点 | 同上 | 同上 |
| scoring_engine.py | 院校级 | 五维加权总分+A–F 等级+±20% 扰动敏感性 | 在场可用，已实战 | decision_pipeline.py score 段子进程转发 |
| gale_shapley.py | 院校级 | 9 月锁校稳定匹配 | 在场可用，已复核 | decision_pipeline.py match 段子进程优先、内联回退 |
| psm_balance.py | 院校级 | 公平对比：按协变量匹配后比 SMD | 在场可用，未实战 | decision_pipeline.py psm 段子进程转发 |
| meme_calibrator.py | 院校级 | 热度项校准（±50% 截断，权重 ≤0.05 外挂维度） | 在场可用，未实战 | 直接调用 quant-frontier-lab 脚本 |

## 3. 转述适配器纪律（decision-sys 四引擎）

**代码资产未移交**（v0.9 依赖 D1），因此四个路径级引擎只以"转述适配器"接入：

1. 凡源自 decision-sys 会话的数值（Q 值、后验概率、0.811/0.714/0.666/0.526、
   55 分后验 61.2%、重构误差 0.6013 等），统一打 `conf="assumed"` 并附
   `provenance="decision-sys会话转述"`，在证据映射中单列"转述"级（D 级）。
2. **严禁重实现后冒充原厂**：本套件及调用方不得用 scoring_engine 或其他脚本
   近似 hrank/NSGA-II/MCTS/Nested Sampling 后宣称"复现了 decision-sys"。
   移交后若需重实现，必须显式声明"按 v68.64 描述重写"并标注忠实度风险。
3. 移交前，转述数值**不得作为 L2+ 决策依据**；若 D1 永久缺席，套件砍路径级宣称，
   改名"院校级决策套件"（v0.9 top3_likely_wrong 第 1 条的既定纠偏）。
4. 适配器消息格式（`engine / version / inputs_digest / outputs / honesty` 字段）
   见 `interface_contracts.md` §6.5 快照。

## 4. 端到端数据流时序（一次完整跑批）

```
新东方PDF / 57校JSON / 信源登记册
  → 证据层：逐条打 (source_tier, conf, data_cutoff, provenance)，Conflict 阻断
  → 路径级门控：decision-sys 转述适配器读 math1_proven → 输出可选轨集合
  → scoring_engine：可选集内院校五维加权 + ±20%×500 扰动 → 总榜+档位
  → meme_calibrator：热度信号修正（外挂维度 ≤0.05，±50% 截断）→ 复跑敏感性
  → psm_balance：跨轨对比前协变量平衡自检（|SMD|<0.1 门槛）
  → gale_shapley：9 月锁校匹配（容量=面板实数）→ 阻塞对=0 自检
  → 交付层：选择题式选项 + top3_likely_wrong + 四行记录 + 收割指针
```

其中 `scoring_engine → gale_shapley` 的院校级主链已由
`scripts/decision_pipeline.py` 的 `full` 段编排（可选 gate 实现数一门控）；
meme_calibrator 与 psm_balance 按场景旁路调用，不进默认主链。

## 5. 失败传播规则

1. **Conflict→人工**：证据层出现 conf=Conflict 时整链暂停转人工（无机读映射）。
   decision_pipeline.py 以 exit=3 显式阻断，禁止静默吞掉。
2. 任一引擎输出 `honesty.unverified=true` 或稳定性自检 FAIL（如阻塞对>0、
   |SMD|≥0.1）时，交付层必须在对应结论行**内联标注**，禁止省略。
3. 引擎脚本不在场时，编排器仅交付"契约校验通过"声明（result.notice 注明），
   **不得把校验声明当计算结果引用**；下游脚本非零退出时编排器 exit=4 原样上抛。
4. 校验失败（契约不符、缺 data_cutoff、conf 越界）exit=2，由调用方修正输入后重跑。

## 6. 本套件在架构中的位置

unified-decision-suite 是**引擎层与交付层之间的薄编排层**（L1 原型）：
不持有数据、不登记证据、不重实现引擎；只负责契约校验、引擎路由、
统一包壳（data_cutoff / conf / honesty / top3_likely_wrong）与失败上抛。
