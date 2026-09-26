# 城市宜居度有关文档登记（优先审计对象）

> 用途：技能触发后**先聚焦**本清单；清单由 `scripts/livability_doc_scanner.py` 全量扫描校准，
> 下表为人工整理的核心层（静态维护，扫描脚本负责发现新增）。

## 核心层（每轮必审）

| 文档 | 路径 | 语义角色 | 已知风险（首轮审计遗产） |
|---|---|---|---|
| 城市宜居模块 | `评分系统_优化版/scoring_system/city_livability.py` | C5 城市宜居（产业/宜居/向往度 0-1） | 未接总分但命名与 livability 撞「宜居」（CF-5）；数据源 conf=B/C |
| 住房压力模块 | `评分系统_优化版/scoring_system/livability.py` | C4/D3 成本子层（HPI+房租，进总分） | conf=估算(B)；与 C5 房价因子潜伏重叠 |
| 城市分级配置 | `归档/.../9_工具脚本与开发代码/city_tier_config.py` | C6 生活压力反指标（含气候舒适度） | 已裁定归档封存；自标 conf=A 的质性判断 |
| 生活成本文章 | `<输出区>/核聚变方向高校生活成本与住宿条件对比_V17.md` | V17 证据底座（6校生活成本/住宿/气候） | 散文用法「生活舒适」；web_search 引用需复核时效 |
| v48 报告 | `评分系统_优化版/v48_report.md` | 暂缓项判定（宿舍/交通→舒适度子项；风评不实装） | 「宜居分只保留纯住房项」声明与 v66.9 实现矛盾（CF-5） |
| CHANGELOG | `评分系统_优化版/CHANGELOG.md` | 变更记录源 | 缺 v35–v50 段；v67 起才见澡堂/宜居条目 |
| 规范 v1.0 | `<输出区>/舒适度判定规范_v1.0.md` | D1/D2/D3 + R1–R11 判定基准 | 本身是被维护对象；变更须留痕 |

## 扩展层（扫描发现后纳入）

- `评分系统_优化版/scoring_system/engine.py`（exit/city/livability 计分通道）
- `评分系统_优化版/config/weights_v*.json`（reality_weights.city/exit 权重）
- `评分系统_优化版/data/schools.json`（comfort/city_tier 字段数据）
- `评分系统_优化版/scoring_system/retest_difficulty.py`（BATHROOM 四档，宿舍舒适度远景排期唯一存量资产）
- `评分系统_优化版/scoring_system/param_registry.py`、`tests/test_engine.py`（city_livability 引用点）

## 登记纪律

1. 每轮审计开始先跑 `livability_doc_scanner.py --root <项目根>`，将新增命中文档补入扩展层。
2. 文档 semantic 角色变更（如某模块改语义）须更新本表「语义角色」列并留痕。
3. 本表不含的目录（如 `资料归档/` 镜像副本）默认不审，避免双副本噪声。

## 外部检索登记

- 与 `references/retrieval-paths.md` 的关系：本表登记「被审文档」，retrieval-paths.md 登记「文档引用参数的外部信源与检索路径」——前者是审计对象清单，后者是复核依据清单，二者经 evidence 角色（按偏差阈值表比对）衔接。
- **存放约定**：检索条目统一落 `workspace/retrieval/entries.json`（顶层数组，schema 见 retrieval-paths.md 第 4 节）；每轮审计一个工作区一份，多轮复检追加条目并更新 check_date，不覆盖历史条目。
- 每次改动 entries.json 后必跑 `scripts/retrieval_registry_check.py`：exit 1 先修正再进入审计汇总；WARNING（超期/隔离层/C 级进总分）转交 evidence 角色随报告处理。
- 登记纪律（首页+检索路径、可达性抽查、有效期 6/12 个月、no_public_url_reason）以 retrieval-paths.md 第 3 节为单源，本处不复述。
