# Verdict Register（结论登记与留痕）模板

> v1.0 ｜ 修改人：Orchestrator（Kimi K3），2026-08-25
> 留痕是硬要求：每条判定的修改人/日期/证据路径/旧结论原文缺一不可。

## JSON Schema（机器可读，可用 scripts/verdict_register.py 生成/追加）
```json
{
  "city": "沈阳",
  "original_verdict": "淘汰",
  "original_reason": "回家只有普速24小时（距离否决）",
  "original_source": "stages/17b-xxx.md",
  "original_threshold": null,
  "threshold_assumption": "原理由'压线'未给阈值，假设为年全包15万并做±敏感性",
  "new_verdict": "候选",
  "change_type": "翻案",
  "evidence_chain": [
    "市直个案年到手约15万（B-，st21_shenyang.md）",
    "房价收入比≈5.6倍（二手0.79-0.81万×90㎡≈73万）",
    "长沙直飞3h9m ¥670起 每周103班（C快照，2026-08-25）",
    "省考医学岗进面52-53分（B-）"
  ],
  "red_flags": ["冬季-9℃×近6个月", "财政缺口335亿（间接锚）"],
  "modified_by": "Orchestrator（Kimi K3）",
  "date": "2026-08-25",
  "evidence_files": ["stages/raw/st21_shenyang.md", "stages/raw/st21_rail.csv"],
  "review_after": "2026-11-24"
}
```

## Markdown 总表（人读）
| 城市 | 原结论(理由) | 新判定 | 关键证据 | 修改人/日期 |
|---|---|---|---|---|
| 沈阳 | 淘汰(普速24h) | **翻案→候选** | 到手13-15万/房价收入比5.6x/直飞3h9m | Orchestrator, 2026-08-25 |

## 规则
1. `change_type` 枚举：维持 / **维持·理由重构** / 翻案 / 上调 / 下调 / 存疑待复核
1b. 原理由含「压线/偏低/偏高」时必登 `original_threshold`；不可得填 `threshold_assumption` 并做 ±敏感性（脚本 v1.3 起两字段分别对应 --threshold 与 --threshold-assumption）
2. 翻案必须 evidence_chain ≥2 条独立证据
3. `review_after` 默认 3 个月后；涉当年政策（引才包/津贴）随公告滚动
4. register 文件建议命名 `verdict_register_<项目名>.json`，与项目迭代日志同目录
