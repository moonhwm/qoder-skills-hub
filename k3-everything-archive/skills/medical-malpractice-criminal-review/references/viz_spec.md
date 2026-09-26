# 可视化输出格式规范

> 为 `data-viz-gen` 模块提供的标准化输出格式
> 版本: 1.1.1 | 更新日期: 2026-08-23

---

## 一、雷达图数据格式

```json
{
  "chart_type": "radar",
  "title": "医疗事故刑事案件五维评分对比",
  "data": [
    {
      "case_id": "韩杰案",
      "dimensions": {
        "医疗过错程度": 65,
        "因果关系强度": 75,
        "损害后果严重性": 95,
        "注意义务违反": 50,
        "免责/减责事由": 75
      }
    },
    {
      "case_id": "李建雪案",
      "dimensions": {
        "医疗过错程度": 60,
        "因果关系强度": 50,
        "损害后果严重性": 95,
        "注意义务违反": 45,
        "免责/减责事由": 60
      }
    }
  ],
  "max_value": 100,
  "color_scheme": ["#FF6B6B", "#4ECDC4", "#45B7D1"]
}
```

## 二、责任比例条形图

```json
{
  "chart_type": "horizontal_bar",
  "title": "责任比例对比",
  "x_axis": "责任比例 (%)",
  "y_axis": "案件",
  "data": [
    {"case_id": "韩杰案", "value": 39.1, "color": "#FFA500", "label": "同等责任"},
    {"case_id": "李建雪案", "value": 29.2, "color": "#FFD700", "label": "次要责任"},
    {"case_id": "温红案", "value": 23.6, "color": "#90EE90", "label": "次要责任"}
  ],
  "thresholds": [
    {"value": 30, "label": "犯罪门槛", "color": "#FF0000"},
    {"value": 50, "label": "主要责任", "color": "#FF4500"}
  ]
}
```

## 三、罪名分布饼图

```json
{
  "chart_type": "pie",
  "title": "罪名分布",
  "data": [
    {"label": "不构成犯罪", "value": 3, "color": "#90EE90"},
    {"label": "医疗事故罪", "value": 2, "color": "#FFA500"},
    {"label": "过失致人死亡罪", "value": 1, "color": "#FF4500"},
    {"label": "非法行医罪", "value": 1, "color": "#FF0000"}
  ]
}
```

## 四、司法风险热力图

```json
{
  "chart_type": "heatmap",
  "title": "司法风险矩阵",
  "x_axis": ["致命", "重大", "一般", "参考"],
  "y_axis": ["韩杰案", "李建雪案", "温红案", "南阳吴某案"],
  "data": [
    [0, 1, 1, 2],
    [1, 0, 0, 1],
    [0, 0, 0, 2],
    [0, 1, 0, 1]
  ],
  "color_scale": ["#FFFFFF", "#FFE4E1", "#FFA07A", "#FF4500", "#8B0000"]
}
```

## 五、收敛过程折线图

```json
{
  "chart_type": "line",
  "title": "迭代收敛过程",
  "x_axis": "迭代轮次",
  "y_axis": "总分",
  "data": [
    {
      "case_id": "韩杰案",
      "points": [
        {"x": 0, "y": 72.5},
        {"x": 1, "y": 74.8},
        {"x": 2, "y": 75.1}
      ]
    }
  ]
}
```

## 六、完整可视化报告结构

```json
{
  "report_version": "1.1.1",
  "report_type": "medical_malpractice_review",
  "generated_at": "2026-08-23T01:45:00+08:00",
  "charts": [
    {"type": "radar", "data": {...}},
    {"type": "horizontal_bar", "data": {...}},
    {"type": "pie", "data": {...}},
    {"type": "heatmap", "data": {...}},
    {"type": "line", "data": {...}}
  ],
  "summary": {
    "total_cases": 17,
    "crime_type_distribution": {...},
    "average_liability_ratio": 35.2,
    "convergence_rate": 0.95
  }
}
```
