# 宿舍舒适度远景排期（dorm-comfort roadmap）

> 定位：宿舍舒适度**不进当前总分**，按远景排期管理。本文件是排期登记框架 + 首条正式登记。
> 历史依据：v48 报告第八节「宿舍/交通：暂缓。理由：门槛优先阶段，宿舍非决策变量且无公开可审计数据；
> 字段 dorm_note 占位，并入远期就业多维的舒适度子项」；规范 v1.0 §2 已将「宿舍/交通」改道至 D3 条件子层。

## 排期登记表（格式契约）

| 字段 | 说明 |
|---|---|
| item_id | 唯一编号（DORM-###） |
| phase | `backlog`（远景）/ `staged`（已排期）/ `active`（激活）/ `done` / `dropped` |
| activation_trigger | 激活条件（必须可判定，如「L1 门槛候选集 ≤5 校」） |
| priority | P0/P1/P2（远景默认 P2） |
| depends_on | 依赖项（证据源、上游维度、外部数据） |
| evidence_requirement | 激活时的证据门槛（对照规范 §3.3：实证 B 以上才进总分） |
| integration_target | 激活后接入位置（默认 D3.dorm_condition，筛选/标注层） |
| registered_by / date | 登记人与日期 |

## 首条登记（本技能创建时落盘）

| 字段 | 值 |
|---|---|
| item_id | DORM-001 |
| phase | **staged**（远景排期正式登记，2026-08-24） |
| 内容 | 宿舍舒适度（住宿条件/卫浴/交通接驳），含既有 BATHROOM 四档（retest_difficulty.py，conf=假设级） |
| activation_trigger | 以下全部满足：①L1 门槛候选集收敛至 ≤5 校（宿舍成为真实决策变量）；②目标校宿舍/卫浴数据取得公开可审计来源（官网住宿公告/后勤集团公示），conf 达 B；③D3 条件子层 schema 冻结 |
| priority | P2 |
| depends_on | D3 维度 schema（规范 v1.0 §3.4）；v48 dorm_note 占位字段；BATHROOM 四档证据升级 |
| evidence_requirement | 校级住宿条件=官网/后勤公示（B）；城市级成本=统计局（B/估算）；**禁止**社媒风评进分（v48 判定延续） |
| integration_target | D3.dorm_condition（筛选/标注层）；如未来进总分，须先过 R8「同名因子唯一入口」核查（与 livability 房价因子去重） |
| registered_by | livability-audit-swarm 创建流程 / 2026-08-24 |

## 操作纪律

1. 远景项**不进入**任何总分、权重、归一化链路；只允许出现在筛选/标注层与报告附注。
2. 每次审计轮须检查登记表：触发条件满足即提出激活建议（升 active），并附证据达标证明。
3. 激活条件判定分三档：**满足 / 不满足 / 不可判定**（依赖工作区外状态时标「不可判定」并注明所需查询位置，禁止把「不可判定」写成「不满足」）。参考查询位置：L1 候选集规模→评分系统最新报告；D3 schema 状态→规范 v1.0 §3.4；宿舍数据源→目标校官网/后勤集团公示入口。
4. 登记表变更走 change-notice-protocol：改表必留痕（AI_READER_NOTICE + CHANGELOG + k3_notices）。
