# 技能间管线数据契约（pipeline contracts）

任何技能把产出交给下游技能消费时，走统一 JSON 契约。字段要求分两级：

**必填（缺一则下游拒收）**：

| 字段 | 类型 | 含义 |
|---|---|---|
| `data_cutoff` | string, YYYY-MM-DD | 数据截止日，过期数据必须标注 |

**按产物类型分级**：

| 字段 | 类型 | 要求 |
|---|---|---|
| `conf` | string 等级或 number | 允许字符串等级 `empirical` / `estimated` / `assumed`（与 multi-dimensional-option-scoring 的 `scoring_engine.parse_conf` 对齐，该函数亦接受 [0,1] 数值）；建议每个数据点/维度分别标注 |
| `top3_likely_wrong` | array[string] | **报告类产物必填**（任何交付给人的报告必须含自我批判节）；**数据流 JSON 可选**（技能间机读传递时不强制） |

## 生产者 → 消费者 → schema 对照表

| 生产者技能 | 产出 | 消费者技能 | 消费为 | 必备字段（除上述分级字段外） |
|---|---|---|---|---|
| claims-deep-audit | 命题评分卡 JSON（**目标 schema**；当前 `paper_direction_classifier.py` 未输出全部字段，属待办） | multi-dimensional-option-scoring | `dimensions` 输入 | `claim_id`, `verdict`(支持/存疑/证伪), `score`(0-100), `evidence_refs` |
| commute-school-optimizer | 通勤评分桥接 JSON（`commute_scoring_bridge.py` 实际输出） | multi-dimensional-option-scoring | `options` 数组逐项作引擎输入（每项含 `option`/`dimensions`/`negative_items`） | `option`, `dimensions`(name/score/weight/conf/anchor/key_metric), `cost_breakdown`（中文嵌套键：`时间成本`/`金钱成本`/`机会成本`/`月综合成本元_金钱加机会`）, `rating_endpoint_payload`；`data_cutoff` 在顶层。**school_quality 不在本桥输出中，由下游补充**（该技能 SKILL.md 已声明不核算学校质量） |
| （新链路） | — | — | — | 建立新链路时先在本表登记再对接 |

## 命题评分卡 JSON 示例（claims-deep-audit → multi-dimensional-option-scoring）

```json
{
  "conf": 0.72,
  "data_cutoff": "2026-08-24",
  "top3_likely_wrong": [
    "调剂占比口径可能混入非全名额",
    "导师名额为 2025 数据，2026 未公示",
    "装置状态引用的是校方新闻稿"
  ],
  "claims": [
    {
      "claim_id": "CLM-001",
      "text": "南华聚变方向连续五年调剂占比超 25%",
      "verdict": "支持",
      "score": 85,
      "evidence_refs": ["NAN-V01", "招生数据表 2022-2026"]
    }
  ]
}
```

消费者侧映射规则：`claims` 中每条评分卡按主题聚合成一个 dimension，`score` 加权进维度分，`verdict=证伪` 的 claim 对应维度分封顶 40。

## 规程

1. 生产 JSON 前先查本表：已有链路按既有 schema 产出；新链路先在本表加行再写代码。
2. `data_cutoff` **不允许留空或写 null**；确实无法估计 conf 时写 `assumed` 并在报告类产物的 top3_likely_wrong 第一条说明原因。
3. 消费者收到缺字段的 JSON 时，拒绝静默兜底——向生产者（或用户）明确指出缺哪个字段。
4. 跨会话传递的管线 JSON 优先落盘到 `<上传区>/`（最稳定）；`<输出区>/` 根实测可跨会话保留（见 SKILL.md 持久层地图），可作副本位。文件名含版本与日期。
