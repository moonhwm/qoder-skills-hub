---
name: quota-ledger-ops
description: "[项目技能] 额度账本运维（额度自评）——事前估算+逐阶段记账+超限策略+结项报告的完整闭环：①预算解析（元/额度池%/token 三口径互转，价目锚点可查）②任务定档（浅/中/深三档×子代理规模→token 区间预估，给出 够/紧/不够 判决）③逐阶段记账（JSONL 哈希链账本脚本）④超限策略（50%提示/80%降档或请示/100%止损结项，衔接 quota-guard-ops Q档）⑤结项报告（账本汇总+三省吾身+尼采/萧红/海德格尔三语料文学化落款）。触发（满足任一）：用户给预算办任务（「1-2元额度包办这事」「20%额度够不够跑深度研究」）；要求评估 token 消耗/省钱方案/降本；要求任务结项报账；问「这任务花多少额度」「怎么省额度」。不触发：事中额度信号检测与 Q0-Q3 档位守护→quota-guard-ops；领券/POI/通勤/答题领券执行→daily-life-autopilot。English triggers: quota self-assessment, token budget, cost estimation, budget ledger, spending report."
---

# 额度账本运维（quota-ledger-ops）

> 能力域=管理｜输入型=预算约束/任务描述/查账请求｜输出型=估算判决+账本+结项报告｜只读性=否（写 /mnt/agents/temp/ 账本 JSONL）｜依赖=python3 标准库

## 〇、定位与正交性（先划界，再开工）

| 邻席 | 管什么 | 本技能让渡 |
|---|---|---|
| quota-guard-ops | **事中**守护：额度信号检测、Q0-Q3 档位、止损交接 | 信号判定与档位切换全归它；本技能超限事件只**衔接**不接管 |
| daily-life-autopilot | 生活执行：领券/POI/通勤/答题领券 | 一切现实事务执行归它；本技能只算账不跑腿 |

本技能唯一辖区 = **钱的事前与事后**：这事花多少（估算）、花到哪了（记账）、超了怎么办（策略）、花得值不值（结项）。

## 一、诚实边界（置顶）

Kimi 无开放额度 API，余额不可机读。一切数字 = **估算**（conf=estimated）。官方锚点（kimi.com 帮助中心）：额度池全功能共享、按月刷新、赠送额度优先消耗、**任务失败不扣额度**、参考量纲「简单 PPT≈1-2%／深度研究≈5-10%」。详见 references/pricing-anchors.md。

## 二、五环 workflow

### 环1 预算解析
把用户预算统一成可算账的量：元（CNY）／额度池百分比（%）／token 数。缺口径就问一句，别猜。
- 元 → token：用 references/pricing-anchors.md 的价目表（默认锚=DeepSeek V4-Flash 谷时价，可用环境变量 QUOTA_RATE_IN/QUOTA_RATE_OUT 覆盖）。
- % → 任务数：用官方锚点量纲（1 次深研≈5-10%）。

### 环2 任务定档（给判决）
| 档 | 形态 | 典型 token 区间 | 适用 |
|---|---|---|---|
| T1 浅 | 单线程，≤2 次搜索，无子代理 | 数万-十几万 | 口令/答案/事实核查 |
| T2 中 | 单线程+少量工具，或 ≤2 子代理 | 十几万-几十万 | 网点调查、小报告 |
| T3 深 | 多子代理 swarm/大批量摄取 | 几十万-数百万 | 深度研究、技能创建 |

输出**判决**：预算 够 / 紧（给降本项）/ 不够（给降级路径，含免费通道清单）。

### 环3 逐阶段记账
每个阶段结束记一笔（阶段名+估算 in/out token）。脚本：
```bash
python3 scripts/quota_ledger.py init <任务名> --budget 1.5 --unit cny
python3 scripts/quota_ledger.py log <任务名> <阶段名> --in 40000 --out 6000
python3 scripts/quota_ledger.py status <任务名>     # 总量+占预算%+警戒级
python3 scripts/quota_ledger.py report <任务名>     # 结项 Markdown 表
python3 scripts/quota_ledger.py estimate --in 50000 --out 8000   # 单价换算
```
账本落 `/mnt/agents/temp/quota_ledger/<任务名>.jsonl`（禁 /tmp），行级哈希链防篡改。

### 环4 超限策略（三级）
- **50%**：提示一次，继续。
- **80%**：降档（T3→T2→T1：砍子代理、砍搜索轮次、骨架先行）或请示用户，二选一明示。
- **100%**：止损结项——成果即刻落盘，出 report，并把额度信号**交接 quota-guard-ops**（其 Q 档只升不降，本技能不复位）。
宕机/死循环防御参照 pricing-anchors.md 的 dsh-budget 模式（block/alert + warnRatio）。

### 环5 结项报告
骨架：①账本汇总表（report 子命令产出）②三省吾身：哪阶段超估/哪阶段省成/下次定档修正 ③**文学化落款**（≤2 行）——三语料用法与现状见 references/voices.md：萧红走 FTS 实引（机器底座在役），尼采拟箴言须标「拟」，海德格尔**缺藏在册、禁伪引**。

## 三、铁则

1. 估算是估算，绝不冒充账单；无价格模型的任务标注 estimated=true。
2. 省钱不省纪律：红线、写类例外、回读比对全档有效。
3. 账本字段一律脚本生成，禁人肉补全（ESC-004 同款）。
