# 录取面板数据字典（panel_schema）

> 15 项核心指标的定义、取值约束与缺测处理规范。所有示例均为**脱敏合成数据**。
> 校验执行器：`scripts/panel_validate.py`（本文件为其规则依据）。

## 目录

1. 面板 JSON 结构
2. 15 项核心指标逐项定义
3. 一致性约束（跨字段）
4. 缺测处理规范
5. 扩展字段（调剂窗口风险用，可选）
6. 合成示例

## 1. 面板 JSON 结构

```json
{
  "school": "示例大学（合成）",
  "program": "070200",
  "data_cutoff": "2026-08-24",
  "records": [
    {"year": 2026, "plan": 30, "total_admit": 40, "...", "conf": "empirical", "missing": []}
  ]
}
```

- 顶层：`school`（字符串，必填）、`program`（专业代码字符串，必填）、
  `data_cutoff`（ISO 日期，必填）、`records`（数组，≥1 年，建议 ≥3 年）。
- 每条 record 携带：`conf`（empirical/estimated/assumed，必填）与
  `missing`（字段名数组，记录本条中缺测的字段；无缺测给 `[]`）。
- 也支持逐字段 conf：`"conf_fields": {"must_score": "estimated"}` 覆盖记录级 conf。

## 2. 15 项核心指标逐项定义

| # | 字段 | 中文 | 类型 | 定义 | 取值约束 |
|---|---|---|---|---|---|
| 1 | `year` | 年份 | int | 录取年份（考研复试录取完成年） | [2000, 2100]；records 内不得重复 |
| 2 | `plan` | 计划 | int | 当年统考招生计划人数（不含推免） | ≥0；缺测=null |
| 3 | `total_admit` | 总录取 | int | 当年统考实际录取总数（一志愿+调剂） | ≥0；**关键字段，缺测则该年记录禁入模式判别** |
| 4 | `first_choice_admit` | 一志愿 | int | 一志愿录取人数 | ≥0 且 ≤ total_admit；**关键字段** |
| 5 | `transfer_admit` | 调剂 | int | 调剂录取人数 | ≥0 且 ≤ total_admit |
| 6 | `retest_count` | 复试人数 | int | 一志愿进入复试人数 | ≥0 且 ≥ first_choice_admit |
| 7 | `retest_pass_rate` | 复试通过率 | float | 一志愿复试通过率 = first_choice_admit / retest_count | [0,1]；retest_count=0 时必须为 null |
| 8 | `min_score` | 最低分 | number | 当年统考录取最低分（不含专项计划） | [0,500]；注意是**录取**最低分，非复试线 |
| 9 | `median_score` | 中位分 | number | 录取分数中位数 | [0,500] 且 ≥ min_score（软约束，违反记 warning） |
| 10 | `must_score` | 必达分 | number | 建议目标安全分（复试线+安全余量，或官方/经验推定） | [0,500]；通常 ≥ min_score（违反记 warning）；**必达分≠录取线，禁止混用** |
| 11 | `math1` | 数一标志 | bool | 初试是否考数学一 | true/false；未知=null（评分按 0.5 中性处理并标注） |
| 12 | `first_choice_rate` | 一志愿率 | float | first_choice_admit / total_admit | [0,1]；与原始字段误差 >0.02 记 error |
| 13 | `transfer_rate` | 调剂率 | float | transfer_admit / total_admit | [0,1]；与 first_choice_rate 之和应 ≈1（误差 >0.02 记 error） |
| 14 | `tuimian_ratio` | 推免比 | float | 推免录取占该专业总招生（含推免）的比例 | [0,1]；缺测=null（评分按 0 惩罚并标注"可能高估"） |
| 15 | `first_try_weight` | 初试权重 | float | 初试成绩在录取总成绩中的权重（如 0.6 = 初试 60%） | [0,1]；注意一志愿与调剂可能权重不同，以**一志愿**口径为准 |

## 3. 一致性约束（跨字段，panel_validate 逐项检查）

- **C1 总账**：`first_choice_admit + transfer_admit == total_admit`（三者齐在时，违反=error）。
- **C2 复试账**：`first_choice_admit ≤ retest_count`（违反=error）。
- **C3 通过率复算**：`retest_pass_rate ≈ first_choice_admit / retest_count`（容差 ±0.05，违反=warning；
  retest_count=0 时 pass_rate 必须为 null，否则 error）。
- **C4 比率复算**：`first_choice_rate ≈ first_choice_admit/total_admit`、`transfer_rate ≈ transfer_admit/total_admit`
  （容差 ±0.02，违反=error；total_admit=0 时两率必须为 null）。
- **C5 分数序**：`min_score ≤ median_score`、`min_score ≤ must_score`（违反=warning——
  存在必达分推定激进化或最低分为专项计划的合法情形，但必须人工确认）。
- **C6 计划 vs 实际**：`total_admit > plan` **不是错误**（扩招/调剂补录常见），记 info 供模式判别使用。

## 4. 缺测处理规范

1. **宁缺毋造**：缺测字段一律 `null`，**禁止 0 填充**（0 是真实值语义，如 transfer_admit=0 表示零调剂）。
2. **缺测登记**：该年 record 的 `missing` 数组必须列出全部 null 字段名；conf 不得高于 estimated。
3. **派生优先**：派生字段（first_choice_rate/transfer_rate/retest_pass_rate）可由原始字段推导时，
   优先推导并在 `derived` 数组登记（如 `"derived": ["first_choice_rate"]`），conf 继承原始字段。
4. **关键字段门槛**：`total_admit` 或 `first_choice_admit` 缺测 → 该年记录标 `excluded=true`，
   仅可做定性参考，禁入模式判别与评分。
5. **缺测降级链**：S/A 级信源但关键字段缺测 → 整校 conf 上限降为 estimated（对应 B 级）。
6. **外推字段**：任何跨年外推值（如下一年预测）必须单独存放于 `forecast` 对象，conf=assumed，
   禁止写入 records 主记录。

## 5. 扩展字段（可选，供调剂窗口风险评级；缺测=null 且不得虚构）

| 字段 | 中文 | 类型 | 定义 |
|---|---|---|---|
| `window_hours` | 调剂窗口时长 | number | 调剂系统开放至关闭的小时数（如 14）。普通窗口 24-48h |
| `priority_tier` | 调剂优先级档位 | string | 考生背景在官方调剂优先级规则中的档位（A&B/A/B/C/D/E），按**被分析考生**背景匹配 |
| `adjust_rule_text` | 调剂规则文本 | string | 官方调剂规则原文摘录（供"规则文本≠实操"对照） |
| `transfer_sources` | 调剂来源层次 | string | 调剂生来源简述（如"80% 来自 985"），供结构层分析 |

## 6. 合成示例（脱敏，可直接跑 panel_validate.py）

```json
{
  "school": "示例大学（合成·β型）",
  "program": "070200",
  "data_cutoff": "2026-08-24",
  "records": [
    {"year": 2024, "plan": 60, "total_admit": 70, "first_choice_admit": 70,
     "transfer_admit": 0, "retest_count": 78, "retest_pass_rate": 0.897,
     "min_score": 290, "median_score": 330, "must_score": 340, "math1": true,
     "first_choice_rate": 1.0, "transfer_rate": 0.0, "tuimian_ratio": 0.3,
     "first_try_weight": 0.6, "conf": "empirical", "missing": []},
    {"year": 2025, "plan": 62, "total_admit": 72, "first_choice_admit": 72,
     "transfer_admit": 0, "retest_count": 80, "retest_pass_rate": 0.9,
     "min_score": 292, "median_score": 332, "must_score": 342, "math1": true,
     "first_choice_rate": 1.0, "transfer_rate": 0.0, "tuimian_ratio": 0.3,
     "first_try_weight": 0.6, "conf": "empirical", "missing": []},
    {"year": 2026, "plan": 65, "total_admit": 75, "first_choice_admit": 75,
     "transfer_admit": 0, "retest_count": 82, "retest_pass_rate": 0.915,
     "min_score": 295, "median_score": 335, "must_score": 345, "math1": true,
     "first_choice_rate": 1.0, "transfer_rate": 0.0, "tuimian_ratio": 0.32,
     "first_try_weight": 0.6, "window_hours": null, "priority_tier": null,
     "conf": "empirical", "missing": ["window_hours", "priority_tier"]}
  ]
}
```
