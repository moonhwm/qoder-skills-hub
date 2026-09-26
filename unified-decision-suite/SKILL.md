---
name: unified-decision-suite
description: 统一决策套件——四层架构（数据/证据/引擎/交付）下路径级与院校级决策的薄编排层。何时使用：统一决策、决策管线、路径决策、院校决策、锁校匹配、志愿填报决策、帕累托前沿与 NSGA-II 三目标分层、hrank 分层序列、MCTS 时序决策、Nested Sampling 数一门规（数一模考≥55 触发候选池切换）、9 月锁校 Gale-Shapley 稳定匹配、多维打分编排、conf 三级证据标注、S/A/B/C/D 信源映射、decision-sys 转述适配器接入等场景。decision-sys 四引擎仅转述接入、严禁重实现冒充原厂；输出固定 L1+unverified。中文名：统一决策套件
---
<!-- v1.0（2026-08-24）\这是中文解释：首版——落实 v0.9 设计提案，四层架构+引擎编排契约 -->

# 统一决策套件（unified-decision-suite）

## 定位

**L1 原型级薄编排层**：把路径级（decision-sys，转述接入）与院校级（本会话管线，
脚本在场）决策资产统一在同一数据契约下协同，以 2026-09 数一模考与锁校填报为
第一个联合实战场景。本技能是《统一决策套件设计提案 v0.9》的 v1.0 落实。

**编排层而非重实现**：

- 不重实现任何下游引擎——scoring_engine / gale_shapley / psm_balance /
  meme_calibrator 均由 `scripts/decision_pipeline.py` 校验契约后子进程转发；
  Gale-Shapley 仅在 quant-frontier-lab 脚本不在场时用内联教科书版回退（输出注明）。
- decision-sys 四引擎（hrank / NSGA-II / MCTS / Nested Sampling）**代码资产未移交**，
  仅以转述适配器接入：全部 DS 数值 `conf=assumed + provenance=转述`，
  **严禁重实现后冒充原厂**（纪律见 references/architecture.md §3）。
- 所有输出固定 `honesty={level:"L1", unverified:true}` + `top3_likely_wrong`，
  真实志愿填报前必须人工复核。

## 路由表（用户信号 → 资源）

| 用户信号 | 路由 | 说明 |
|---|---|---|
| 统一决策、决策管线、四层架构、数据/证据/引擎/交付、失败传播、Conflict 转人工 | `references/architecture.md` | 四层职责、端到端时序、转述适配器纪律 |
| 接口契约、stdin/stdout schema、conf 词表、S/A/B/C/D 映射、honesty.L、data_cutoff | `references/interface_contracts.md` | v0.9 §6 快照冻结：逐引擎契约+公共必填 |
| 9 月锁校、锁校匹配、志愿填报决策、数一门规、模考≥55、候选池切换、容量实数 | `references/september_lock_protocol.md` + `scripts/decision_pipeline.py` | 面板实数容量 / 假想偏好标注 / ≥55 解锁西南交大+南华轨，<55 锁不考数一池 |
| 院校打分、多维加权、敏感性、A–F 分级 | stage=score（转发 scoring_engine） | 校验 scoring_engine 契约格式后子进程转发；不在场则仅校验留 notice |
| Gale-Shapley、稳定匹配、阻塞对 | stage=match | 子进程优先（quant-frontier-lab）、内联回退；阻塞对断言为 0 |
| PSM、公平对比、SMD | stage=psm | 仅转发 psm_balance.py；不在场仅校验，**不重实现** |
| 端到端跑批、门控+打分+匹配 | stage=full（可选 gate 实现数一门规） | gate→score→match，结果分段留痕 |
| hrank、NSGA-II、帕累托前沿、MCTS、Nested Sampling、路径决策 | `references/interface_contracts.md` §6 转述适配器 | 不计算只搬运；移交前不得作 L2+ 依据 |
| 热度校准、meme_strength | quant-frontier-lab `meme_calibrator.py`（直接调用） | 外挂维度权重 ≤0.05，±50% 截断 |

## 用法速览

```bash
# 自测（score 小样例 + 4 考生×3 校匹配 + 门规开/关两路径，exit=0）
python3 scripts/decision_pipeline.py --smoke

# 分段调用（stdin JSON，stdout 统一包壳）
echo '{"stage":"match","data_cutoff":"2026-08-24","payload":{"students":[...],"schools":[...]}}' \
  | python3 scripts/decision_pipeline.py

# 端到端：数一门规 + 打分 + 锁校匹配
echo '{"stage":"full","data_cutoff":"2026-08-24","payload":{"score":[...],"match":{...},
  "gate":{"math1_mock_score":52,"threshold":55,"gated_schools":["西南交通大学070200","南华大学082700"]}}}' \
  | python3 scripts/decision_pipeline.py
```

- 输出统一包壳：`{stage, version, engine, result, data_cutoff, conf, honesty, top3_likely_wrong}`。
- 引擎路径可配：`--scoring-script/--gs-script/--psm-script` 或环境变量
  `UDS_SCORING_SCRIPT/UDS_GS_SCRIPT/UDS_PSM_SCRIPT`；缺省自动探测
  `<技能安装位>/` 与技能同级目录。
- 退出码：0 正常；2 契约校验失败；3 conf=Conflict 阻断转人工；4 下游引擎失败。
- 纯标准库，无第三方依赖。

## 五件套立场

- **data_cutoff**：所有输入/输出强制携带（公共必填，YYYY-MM-DD），缺失即拒收（exit=2）。
- **top3_likely_wrong**：每次输出固定 3 条自我批判（按 stage 生成，含"若错则后果"语义）；
  报告类交付同样必填，逐条给纠偏动作。
- **选择题式交付**：交付层不给单一"最优解"命令句，给 2–4 个互斥选项
  （如 A：模考≥55 走西南交大+南华双投 / B：坚持不考数一走大工 070205 / C：保录取走新疆），
  每选项附触发条件、代价、conf、退出路径。
- **conf 三级**：empirical/estimated/assumed 机读词表 × S/A/B/C/D 信源分级映射
  （S/A↔empirical、B↔estimated、C/D↔assumed，转述单列）；**Conflict 无机读映射，
  整链阻断转人工**（exit=3）。
- **收割指针**：每次正式交付末尾指向 cross-session-workflow-bridge/references/session_harvest.md
  收割规程（产出清单→追问清单→迭代排期更新），保证跨会话可接力。

## 参考文档

- `references/architecture.md` — 四层架构、端到端时序、失败传播规则、转述适配器纪律。
- `references/interface_contracts.md` — 逐引擎 stdin/stdout JSON schema（v0.9 §6 快照）、
  公共必填、conf×信源映射、统一包壳契约。
- `references/september_lock_protocol.md` — 9 月锁校 Gale-Shapley 实装规程：容量=面板实数、
  院校偏好=预估分（assumed 教学示范+升级三项数据）、数一模考≥55 门规与候选池切换。

## 互指

- **quant-frontier-lab**（前沿算法实验台）：Gale-Shapley / PSM / 热度校准的引擎实体，
  本套件 match/psm 段子进程转发对象，安装后位于 <技能安装位>/（未安装时 match 段
  内联回退、psm 段仅校验）。
- **multi-dimensional-option-scoring**（多维打分参谋）：scoring_engine 契约与引擎实体，
  本套件 score 段转发对象，安装后位于 <技能安装位>/（未安装时仅校验留 notice）。
- **admission-panel-analytics**：新东方面板数据源（35/36 校×5 年统考名额实数等），
  安装后位于 <技能安装位>/；未安装时本指针忽略，容量缺口按规程标注、禁止臆造。
