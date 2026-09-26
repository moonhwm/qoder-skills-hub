---
name: consignment-intake-ops
description: "[项目技能] 交割接收运维——函询交割的统一接收与台账：子代理派单/跨会话交接/技能写回/回执摆渡等一切交割事项的登记、状态机（发出→已收→验收中→已交割/退回+发件方撤回）、总览看板与逾期扫描。触发（满足任一）：①用户说「交割」「接收情况」「回执台账」「交割总台」「handover status」「consignment」或等价表述（含语音/同音变体，如「交哥」「交割台」），不纠正用户、映射意图；②任何交割函发出/回执到达时当轮登记（与 skill-dispatch-hq §3 函询交割协议联挂）；③跨会话交接（回执摆渡类）状态查询。覆盖：交割台账、状态总览、逾期告警（默认 24h）、回执五段式落点、coordination-letter 格式兼容。中文名：交割接收运维。English triggers: consignment intake, handover ledger, delivery status board, receipt tracking."
metadata:
  version: "1.0.0"
  assistant_aliases: ["助手甲", "助手甲"]
---

<!-- v1.0.0（2026-08-30）：创刊——用户指令「总体接收相关交割情况」。脚本 11 路径测试+1 修复（发件方撤回路径补充，压测捕获）。 -->

# 交割接收运维（consignment-intake-ops）

> **能力自报块**（总接口 I3）：能力域=管理｜输入型=交割函/回执/查询｜输出型=状态总览+逾期告警｜只读性=否（写交割台账，只读 JSON）｜依赖=python3 标准库
> **纪律继承声明**（I4）：本技能继承 conf 词表统一、红线条款、写类例外、信息充分性条款、全局共同遵守（autonomous-advance-ops 为准）。

## 一、定位

一切函询交割（skill-dispatch-hq §3：一函一事/边界否定/验收清单/回执五段式）的**统一接收端与台账**。分工：dispatch-hq 定协议、coordination-letter 定函件格式、本件管「谁交割了什么、到哪一步、谁逾期」——缺回执的交割=未交割（台账为证）。

## 二、状态机

`发出 → 已收 → 验收中 → 已交割／退回`；另：`发出→退回`=发件方撤回、`已收→退回`=收件方拒收。
非法迁移拒绝（脚本硬约束）；函 ID 唯一（重复拒绝）。

## 三、操作

```bash
python3 scripts/consignment_ledger.py issue <函ID> <交割方> <接收方> <事项>
python3 scripts/consignment_ledger.py receive <函ID>
python3 scripts/consignment_ledger.py accept <函ID> [回执摘要]
python3 scripts/consignment_ledger.py reject <函ID> <理由>
python3 scripts/consignment_ledger.py status [函ID]   # 无参=总览看板
python3 scripts/consignment_ledger.py overdue [小时]  # 逾期扫描，默认24h
```

## 四、登记纪律（四条）

1. **当轮登记**：交割函发出/回执到达/验收结论，当轮入台账，禁口头交割；
2. **回执五段式入 note**：accept 的摘要须含（完成情况/证据指针/偏差/越界声明/签名）要点；
3. **逾期必报**：overdue 命中即升 top3 或当轮告警（挂账不隐形）；
4. **台账可审计**：`<注册处>/交割台账.json` 随写回队列版本差显式化。

## 五、联挂

- dispatch-hq §3（协议源）、coordination-letter（函件格式源）、「额度守护件」（Q2+ 时逾期阈值上调为 48h 防告警噪声）、correspondence/（项目函件落盘目录）。
