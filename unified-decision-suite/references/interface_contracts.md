# 接口契约：逐引擎 stdin/stdout JSON schema（v0.9 提案 §6 快照冻结）

> 严肃化等级：L1 原型 | unverified：是 | data_cutoff：2026-08-24
> 本文快照自《统一决策套件设计提案 v0.9》§3/§6，为套件内引擎契约的唯一权威版本。
> 契约未尽事宜（报告层双词表、四行记录）以 cross-session-workflow-bridge/references/pipeline_contracts.md 为准。

## 1. 公共必填（所有引擎，缺一下游拒收）

```json
{
  "data_cutoff": "2026-08-24",
  "conf_vocab": "empirical|estimated|assumed",
  "honesty": {"level": "L0|L1|L2|L3", "unverified": true, "note": "..."}
}
```

- `data_cutoff`：必填，YYYY-MM-DD；decision_pipeline.py 校验缺失即 exit=2。
- `conf` 词表固定三档，对齐 `scoring_engine.parse_conf`：empirical=1.0 / estimated=0.6 / assumed=0.3；parse_conf 同时兼容 [0,1] 数值。
- `honesty.level`（L 字段）：必填；L0/L1 禁止在报告/排期中作为决策依据引用（iteration-convergence-ops 铁律）。套件全部输出固定 `level="L1", unverified=true`。

### 1.1 信源分级（S/A/B/C/D）↔ conf 三级映射表

| 信源级 | 定义 | 例 | 映射 conf（机读） | 映射 confidence（报告层） |
|---|---|---|---|---|
| S | 官方一手实证（研招网公示/校官网原文/官方公告） | 新东方面板所汇总的研招网公示录取数 | `empirical` (1.0) | High |
| A | 可核验的权威转述/多源交叉一致 | 南开-新奥实验室（校新闻网+复查一致） | `empirical` (1.0) | High |
| B | 单源内部文档/有依据估计 | NCST 装置评级 55（未独立复核） | `estimated` (0.6) | Medium |
| C | 推断/类比/教学假设 | 假想同侪预估分 316-380 | `assumed` (0.3) | Low |
| D | 转述且代码/原文不在场 | decision-sys 的 NSGA-II/MCTS 数值 | `assumed` (0.3) + 标"转述" | Low |

- **S/A ↔ empirical，B ↔ estimated，C/D ↔ assumed**；"转述"（D 级）单列：
  凡源自 decision-sys 会话的数值，打 `conf="assumed"` 并附
  `provenance="decision-sys会话转述"`，v1.0 代码资产移交后逐条复核升降级。
- **Conflict 无机读映射，阻断转人工**（decision_pipeline.py exit=3）。

### 1.2 证据登记条目 schema（数据层→证据层→引擎层的唯一通行证）

```json
{
  "evidence_id": "EVD-2026-0001",
  "claim": "西南交大070200 2026年82人一志愿进复试82人录取",
  "source_tier": "S",
  "conf": "empirical",
  "data_cutoff": "2026-08-24",
  "provenance": "新东方PDF面板(研招网公示汇总)",
  "ref": "新东方PDF/西南交大070200.pdf p.2"
}
```

## 2. scoring_engine.py（§6.1 现状快照 → 契约冻结）

引擎实体：multi-dimensional-option-scoring/scripts/scoring_engine.py（在场，直接调用）。

- **stdin**：单个对象或数组；每项
  `{option, dimensions:[{name, score(0-10), weight(>0), conf}], negative_items?:[{name, score, weight(<0), conf}]}`。
- **stdout**：`{meta:{perturbation, samples, thresholds, conf_map}, results:[{option, total, grade, grade_label, conf_weighted_score, avg_conf, rank, sensitivity:{rank_stability, grade_stability, worst_rank, best_rank}}]}`。
- **套件扩展**：输入层新增 `evidence_refs:[evidence_id]`（可选），把维度分回溯到证据层条目；**不改 parse_conf 词表**。
- 等级阈值（默认，`--thresholds` 可覆盖）：A ≥ 8.0 优质；B ≥ 6.5 可行；C ≥ 5.0 谨慎；D ≥ 3.5 高风险；F < 3.5 欺诈性或不可行。

## 3. gale_shapley.py（§6.2，9 月锁校主引擎）

引擎实体：quant-frontier-lab/scripts/gale_shapley.py（在场；decision_pipeline.py 子进程优先、内联回退）。

- **stdin**：`{"students":[{"id","prefs":[school_id...]}], "schools":[{"id","capacity":int>=1,"prefs":[student_id...]}], "data_cutoff", "conf", "honesty"}`；
  未列出=不可接受；`--proposer=schools` 可切提议方。
- **stdout**：`{matches, unmatched_students, school_rosters, blocking_pairs:[], n_blocking_pairs:0, stability_check:"PASS|FAIL", honesty:{level:"L1", unverified:true, ...}}`。
- **契约增补（v0.9 草案保留）**：每个 school 增加 `capacity_source:"新东方面板统考名额实数|假想"`
  与 `prefs_basis:"estimated_score|admission_rule"`，把"容量/偏好的依据等级"显式随结果传递
  （decision_pipeline.py 以 `contract_extras` 透传）。

## 4. psm_balance.py（§6.3，公平对比）

引擎实体：quant-frontier-lab/scripts/psm_balance.py（在场，未实战；套件不重实现）。

- **stdin**：`{"covariates":["x1",...], "rows":[{"id","treated":0|1,"outcome",x...}], "data_cutoff","conf","honesty"}`。
- **stdout**：`{propensity_scores, matches(卡钳0.2×SD(logit)), smd_table(|SMD|<0.1 平衡), att_estimate(附强烈警示), hard_notice(混淆变量人工确认), honesty}`。
- **套件用法**：比较"数一依赖轨 vs 不考数一轨"的上岸结果前，先按本科背景/模考分/地域做匹配；
  |SMD|≥0.1 的协变量必须在交付中点名。

## 5. meme_calibrator.py（§6.4，热度项）

引擎实体：quant-frontier-lab/scripts/meme_calibrator.py（在场，未实战；仅合规公开信号）。

- **stdin**：`{"entries":[{"school","base_score","signals":[{type:"search_count|public_index", ..., "sampled_at"}]}], "weights"?, "data_cutoff","honesty"}`。
- **stdout**：每校 `{base_score, 信号归一化贡献, calibrated_score(±50%截断), conf:"估算"}` + `sampling_log` + honesty。
- **套件用法**：仅作 scoring_engine 的"热度修正"外挂维度，权重 ≤0.05，防止炒作信号过冲（脚本内建截断保留）。

## 6. decision-sys 转述适配器（§6.5，不实现算法）

```json
{
  "engine": "decision-sys.hrank|nsga2|mcts|nested_sampling",
  "version": "v68.64/v10",
  "data_cutoff": "2026-08-24",
  "conf": "assumed",
  "provenance": "decision-sys会话转述",
  "inputs_digest": {"tracks": 6, "math1_proven": false},
  "outputs": {"ranking": ["..."], "trigger": "9月数一模考>=55", "q_values": {}},
  "honesty": {"level": "L1", "unverified": true,
              "note": "数值为会话内产出，代码资产不在本会话；移交前禁止作为L2+依据"}
}
```

纪律：适配器只搬运与标注，**不计算**；严禁用院校级引擎近似后冒充原厂输出
（见 architecture.md §3）。

## 7. decision_pipeline.py 统一包壳（套件编排出口）

- **stdin**：`{"stage":"score|match|psm|full", "data_cutoff", "conf"?, "payload":{...}}`
  （各段 payload 按上文 §2–§4 契约；full 段含 score/match 子载荷与可选 gate）。
- **stdout**：`{stage, version, engine, result, data_cutoff, conf, honesty:{level:"L1", unverified:true, note}, top3_likely_wrong:[3 条]}`。
- **退出码**：0 正常；2 契约校验失败；3 conf=Conflict 阻断转人工；4 下游引擎非零退出/稳定性断言失败。
