# FORGE_REPORT —— vector-verdict-ops（向量会裁复核署）

- 锻造日期：2026-09-29 ｜ 管线：skill-forge-pipeline v2.4.1（主链 N-C-D + 短链 N⇄D，MAX_ROUNDS=3）
- 组阁闸：3 异质族 × 3 路由过闸（Kimi 不充数）——qwen3.8-flash@阿里百炼 compatible-mode / glm-4.5-flash@智谱 z.ai 直端点 / minimax-m3@腾讯 TokenHub 广州
- 基线快照：v1.0.0 → .bak-r1（锻造现场 /tmp/forge2/vector-verdict-ops.bak-r1）

## 票数纪事

| 轮 | 对象 | qwen | glm | minimax | 多数 |
|---|---|---|---|---|---|
| R1 首评 | v1.0.0 | REVISE (14,875 tok) | REVISE (9,529 tok) | REVISE (14,916 tok) | REVISE 3/3 |
| R2 复评（嵌 R1 摘要） | v1.1.0 | 超时无票 | REVISE | REVISE | REVISE 2/2 |
| R3 复评（嵌 R2 摘要） | v1.2.0 | 超时无票 | 超时无票 | REVISE | REVISE 1/1 |

R3 触顶：三轮 keep 链完整（无 FAIL/worse），收敛判据不满足 → 按管线强制出链，版本标 MAX_ROUNDS_REACHED，残余修复后移交机主裁量是否再开新轮。

## 判官抓包与修复（R1 七项 → v1.1.0；R2 四项 → v1.2.0；R3 四项 → v1.2.1）

- R1：背景不足静默出 OUT 自伤（修：端到端 UNDETERMINED）；IN 语义 ALL→≥2 通道对齐判定表；空通道禁判 OUT；通道 <2 硬闸 exit 2；维度漂移登记 meta；背景去 [:32] 截断；触发词「正交判定」移除消路由冲突；smoke 18 断言（含 3 端到端 mock）。
- R2：merge_verdicts 残缺路径双向封顶（UNDET+OUT→EDGE）；judge_channel z=None 防御闸；cmd_review 坏行 PARSE_FAIL 续跑 + append_ledger 尾坏行容错；背景前置闸零嵌入调用；smoke 22 断言。
- R3（触顶残余修复，未再续轮）：VERSION 常量漂移修正（v1.2.1 同步）；docstring embed 示例更正（字面文本非文件路径）；main() 背景早到引导（BG_MISSING/BG_LT_MIN stderr 预警）；case-ledger.md channels 字段口径对齐。

## 残余与已知边界（移交机主）

1. qwen/glm 席在 R2/R3 各有一次 180s 读超时（推理族长思维链），票档缺两行——未补票，如实登记。
2. 厂商端点/模型可能下线或变更（PROVIDERS 注册表为 2026-09-29 快照），漂移走失败模式表登记。
3. smoke 为 mock 端到端（零网络），真实 API 行为以首次实跑为准；判官 d8 分低位主因在此。
4. 判定结论为「当前通道名册+当前背景集」相对结论，换背景/换通道须重测（诚实边界在案）。

## 验证凭证

`python3 scripts/verdict_panel.py smoke` → SMOKE PASS: 22 assertions (incl. 12 negative, 3 end-to-end) OK, zero network（v1.2.1 复跑通过）；改必验闸 verify_edit 逐处通过。
