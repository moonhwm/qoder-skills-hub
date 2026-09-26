# Loop 24h 自动运维×技能锻造自我迭代：防重复造轮子研究+技术路径穷举+预算 v1.0（2026-09-03）

> 委托：委托方（~¥500 预算，目的导向高保真任务）。执行：本席。omni 穷举纪律：可枚举维度完备遍历，缺席即声明。
> 研究域实证：scholar（论文逐篇核验引用数）+ web_search（仓库/产品，B/S 级信源，标注 conf）。

## 〇、手头工作清单（先答此问）
| # | 事项 | 状态 |
|---|---|---|
| 1 | 裁决单（甲承认案/乙联署/丙R4R7/丁KEYGW/戊旧案） | **等您口令**（三钟今日 16:00 UTC） |
| 2 | GitHub MCP | 等您插件面板重装（重装即授权）→我跑 get_me 验证 |
| 3 | <通道库> MCP | 重加仍断；REST 主通道稳定，MCP 复联为备（不阻塞） |
| 4 | 写回队列（伞 1.8.6+roster 22卡+自决/国际法/领域研究版本锚） | 待写回窗口（安装位只读） |
| 5 | arm-B 中性代理辩论涌现臂（MAGA 研究） | 呈批待口令 |
| 6 | 华为云失陷后续（换钥/对账/日志所见） | 等您控制台动作 |
| 7 | GLM 旧号礼赠池（死线 09-03 03:30 已过——未燃尽部分随死线失效，如实核销登记） | 已过期核销 |
| 8 | **本件：技能锻造×Loop 24h 运维** | 本文呈批 |

## 一、可行性总判（先给结论）
**能，且不需要新造底盘。** 中断的技能创建（skill-creator 管线）接入既有 Loop 工程在目标模式下自我迭代，架构上四件全部在役：cron 心跳（调度）+ goal-mode 目标状态机（迭代环）+ verifier（自验证）+ registry/锚链/REST 通道（持久化与播报）。**这正是 Voyager 架构在本生态的同构体**——学界与开源社区已把这条路走通，我们站在其肩上组合，不重复发明。

## 二、防重复造轮子：研究穷举（全部实证，信源标注）

### 2.1 学术（高水平/高引用，scholar 逐篇核验）
| 文献 | 引用 | 与本目的关系 |
|---|---|---|
| **Voyager**（Wang et al. 2023, TMLR, arXiv:2305.16291，GitHub MineDojo/Voyager，MIT） | **3280** | **技能库自我迭代的母本架构**：自动课程（curriculum）+ 技能库（可执行代码、向量检索、可组合）+ 迭代提示（环境反馈+执行错误+自验证）。我们的 registry 技能=技能库、cron=调度、verifier=自验证、omni 穷举=课程生成——一一对应 |
| **Reflexion**（Shinn et al. 2023, NeurIPS） | **7269** | 语言化自我反思强化：失败后以自然语言反思入 episodic memory 再试——我们 verifier runs/逃逸登记册同构 |
| Generative Agents（Park et al. 2023, UIST） | 7577 | 记忆-反思-规划三件套；24h 自治行为涌现的最早实证 |
| **EvoSkill / Automated Skill Discovery for Multi-Agent Systems**（arXiv:2603.02766，2026） | 新 | **直接对口「中断的技能创建」**：以失败分析自动发现与精化技能，产出即 SKILL.md 标准格式（Anthropic Agent Skills 规范）——证明「技能自动锻造」已是 2026 活跃前沿，我们不孤单 |
| Bilevel Optimization of Agent Skills via MCTS（arXiv:2604.15709，2026） | 新 | 技能库作为优化对象的正式化；SkillBench 评测警示：技能效果高度异质——我们的「技能安装安检+verifier 门禁」正是对冲 |
| Anything2Skill（arXiv:2606.09316，2026） | 新 | 外部知识编译为可复用技能——技能锻造的上游（知识→技能） |
| AgentSkillOS / SkillsBench / Anthropic Agent Skills spec | — | 技能即一等软件构件的开放标准（SKILL.md+渐进披露）——**本生态已在标准上**，无需另造格式 |

### 2.2 开源/产品（web_search 实证，conf 随注）
| 件 | 要点 | 取舍 |
|---|---|---|
| **LangGraph Platform（LangSmith）** | 内建 cron、persistence、HITL interrupt、长期记忆；ambient agents 官方路线（2026-04 博客） | $39/user/月+节点计费；若出走平台化再评估（P3） |
| **Trigger.dev** | TypeScript agent 托管：无超时、checkpoint-resume、内建调度 | 托管费；工程迁出成本中高（P4 备选） |
| **Temporal** |  durable execution 企业级，self-host 免费/Cloud $100 起 | 本规模过重 |
| Inngest/Hatchet/Restate | 事件驱动持久函数 $99/$500/$75 起 | 同上 |
| **scheduler-mcp（PhialsBasement）** | MCP 版 cron 调度器（shell/API/AI 任务），MIT | **桌面侧心跳候选（P2）**——装于 Kimi Work 桌面端即得 24h 触发器 |
| **mcp-cron（jolks）** | Go 版 robfig/cron MCP | 同上备选 |
| MineDojo/Voyager 仓库 | 技能库+课程+迭代提示全码 MIT | 算法参照，不直接部署（环境=Minecraft） |

### 2.3 结论：轮子盘点
**不需要造**：技能格式（Agent Skills spec 已采）、技能自锻造算法（Voyager/EvoSkill 已证）、调度器（Kimi cron+MCP scheduler 在役可得）、持久化（registry+锚链+REST 全在役）。**需要造的只有组合层**：心跳触发的 goal-mode 技能锻造循环（§三），这是各件拼接处，社区没有现成件（因为各件分属不同生态）。

## 三、目标架构：「燧炉」技能锻造 24h 自动运维环（呈批命名可改）

```
[cron 心跳]──触发──>[goal-mode 轮次]──>[课程生成: omni 穷举选锻造对象]
     ↑                                          │
     │                                     [锻造: init→edit→test→package]
     │                                          │
     │                                     [verifier 门禁: 判据+零明文+安检]
     │                                          │
     └────[下次心跳]<──[anchor+台账+REST广播]<──┘
```
- **课程生成**（Voyager curriculum 同构）：每轮由 omni 从候选池选一件——候选池=写回队列/逃逸派生立法/研究挂账/用户新点；
- **锻造**（Voyager iterative prompting 同构）：skill-creator 管线五步走，失败→带错误反馈重试（Reflexion 同构，逃逸登记册即 episodic memory）；
- **自验证**：verifier 新版本（v(n+1) 不覆写）+脚本实测+package 校验三门禁；
- **播报**：REST 主通道（已稳）+锚链；
- **定频**（cron-task-forge 必要性定频）：非时敏产物，**每 4h 一心跳（6 次/日）起步**，零新信息即静默休眠（goal-child 退化门+omni §10 遥测）；quota Q 档联动降级；
- **启动前提**：口令「**建心跳**」（R3 修正案回路已备：拆口令/锚号硬定/不回写声明）+本预算批准。

## 四、技术路径穷举（ROI 排序）
| 路径 | 内容 | 增量成本 | ROI 判 |
|---|---|---|---|
| **P1 平台内闭环（推荐）** | Kimi cron 心跳+goal-mode+skill-creator+REST+MaaS 燃烧 | ≈0 基建；Kimi 额度+燃烧费 | **最高**——全部件在役，零迁移 |
| P2 桌面 MCP 调度器 | scheduler-mcp/mcp-cron 装 Kimi Work 桌面，心跳更密 | 0（开源） | 高（作 P1 触发器冗余） |
| P3 LangGraph Platform | 官方 ambient agent 平台 | $39/月+节点费 | 中——能力冗余，暂不必 |
| P4 Trigger.dev/Temporal | 托管持久执行 | $0–100/月+迁移工程 | 低——本规模过重 |
| P5 GitHub Actions cron | 仓库定时跑锻造脚本 | 0（公开仓免费额） | 中——但凭证/私域数据不出域红线冲突，仅适合无密脚本 |
| P6 EvoSkill 算法引入 | 失败分析驱动的技能精化（2026 前沿） | 研究实现成本 | 中高——v2 阶段引入，先走 P1 |
**推荐：P1 为主+P2 冗余+P6 二期。**

## 五、额度测算（¥500 预算分配建议，conf=Medium 如实标注）
**成本二元结构**：外部池（MaaS，可精确测）+ Kimi 侧额度（加油包，定价不透明，标 conf=Low）。
| 项 | 测算 | 依据 |
|---|---|---|
| MaaS 锻造燃烧 | 单轮技能锻造 20–50 次调用 ≈ **¥0.5–1.5**；¥100 可跑 **70–200 轮** | 实测：GLM-5.2 ¥0.03/调用、flash ¥0.002/调用（hwc 台账） |
| Kimi 侧（心跳触发的 goal-mode 轮次） | 每 4h×6 次/日×30 日=180 轮/月；**此项为预算大头且不可精确预估**——历史镜鉴：Kimi 月消曾达 ¥10,355（重使用期），轻量心跳轮次应远低于此，但**须设闸**：建议月软警 ¥300 额度当量 | 额度状态台账+撞墙教训 |
| 机动（LangSmith 试用/外部模型甲 补充/意外） | ¥50 | — |
**建议分配：MaaS ¥100 + Kimi 侧额度预留 ¥350 + 机动 ¥50 = ¥500。** 熔断继承：Q 档只升不降，任一池超闸即停燃烧类，只读+登记继续（回滚口令「回滚日闸」在案）。

## 六、待您口令（启动序列）
1. 「**准燧炉**」（或赐名）=批准 §三架构+§五预算；
2. 「**建心跳**」=注册 4h cron（R3 修正案版）；
3. 首轮课程池优先序：写回队列清偿→arm-B→新技能候选（您也可首点一件）。
