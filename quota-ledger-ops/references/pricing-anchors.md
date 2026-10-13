# 价目与通道锚点（穷举尽调 2026-09-22，全部为估算口径非账单）

## 1. Kimi 官方（kimi.com/help/agent/agent-quota-and-billing）
- 统一额度池：Agent/深研/PPT/文档/表格/Kimi Code/Kimi Work/Kimi Claw 共享，按实际 token 消耗扣。
- 消耗优先级：赠送额度先扣，套餐额度后扣；按月随订阅周期刷新。
- 量纲锚点（Moderato 例）：简单 PPT≈1-2%／一次深度研究≈5-10%。
- 失败不扣额度；查看路径：网页 我的→设置→订阅（最近 10 条明细，有延迟）。

## 2. DeepSeek API 价目（源：Mr-Koala/deepseek-price-calculator，2026-08-17 起峰谷价；高峰=9-12/14-18 点=谷时×2）
| 模型 | 时段 | 缓存命中 | 未命中 | 输出 |
|---|---|---|---|---|
| V4-Pro | 谷 | ¥0.15/M | ¥4.5/M | ¥13.5/M |
| V4-Pro | 峰 | ¥0.30/M | ¥9/M | ¥27/M |
| V4-Flash | 谷 | ¥0.05/M | ¥1.5/M | ¥4.5/M |
| V4-Flash | 峰 | ¥0.10/M | ¥3/M | ¥9/M |

本技能默认锚=V4-Flash 谷时未命中（1.5/4.5），可用 QUOTA_RATE_IN/OUT 覆盖。

## 3. 工程模式（源：Wanbinyu/dsh-billing + deepseek-harness #3228/#2553）
- BillingProjection：totalCost + 分 model + unpricedModels（**无价模型不伪造费用**，quota.estimated=true）+ latestTurn；usage 按 (turn,step) 去重防重复计费。
- 警戒色 50%/80%/100% 逐级增强 → 本技能三级超限策略同源。
- dsh-budget：按 次/时/日 设上限，`overLimit: block|alert`，`warnRatio: 0.8`  webhook 预警，`/budget` 查量。
- 死循环三类：确认循环（反复 search）/重试风暴/单轮超长——熔断提案 maxStepsPerTurn/maxTokensPerSession/maxCostCents，触发即明确失败码非静默停。

## 4. 免费/降级通道（源：Hibop.github.io#92 + isnl/deepseek-free + scnet.cn 超算商城）
| 通道 | 权益 | 备注 |
|---|---|---|
| 国家超算平台（scnet.cn） | 新注册送 1000 万 tokens | MiniMax-M2.5/DeepSeek-V3.2/Qwen3-235B/R1-0528 等 |
| NVIDIA NIM（build.nvidia.com） | 免费 API，40 RPM | 含 kimi k2.5 等开源模型，国内手机可验 |
| 魔搭社区 | 2000 次/天 | 需绑阿里云，单模型≤500 次 |
| 火山引擎方舟 | 新人 30 元体验金 | DeepSeek-R1 等 |
| 腾讯元宝/腾讯云/知乎直达 | 免费对话+联网 | 轻任务分流用 |

降级路由原则：预算「紧/不够」判决时，轻任务分流免费通道，主额度留给高价值阶段。

## 5. 遥测灵感
softmutiny/kindle-ai-quota-dashboard：跨 WiFi 在 Kindle 屏实时显示 Claude/Codex/Kimi/DeepSeek 用量——「消耗可视化」理念同源；本技能承担其中的 Kimi 自评账本角色。
