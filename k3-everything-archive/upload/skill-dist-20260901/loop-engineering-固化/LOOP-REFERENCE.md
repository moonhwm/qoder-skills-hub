# LOOP-REFERENCE.md — Loop 工程凝缩参考（固化件 v1.0 · 2026-09-02）

> 用途：技能创建/循环设计时可直接引用的凝缩卡。源：Loop-Engineering-Handbook 全文 + scholar 实查五论文 + 项目既有立法对照。
> 安装位只读：本件在 skill-dist 镜像，待用户重装后生效跨会话（写回队列第 8 次登记）。

## 一句话
设计让 Agent 自跑的系统：人不是按「下一步」的发动机，而是自驱系统的架构师。Loop≠while True——无硬门禁的循环=烧钱机。

## 学术五模式（scholar 直抵已验）
- ReAct arXiv:2210.03629 — Thought/Action/Observation 单步环
- Reflexion arXiv:2303.11366 — 失败写经验入下轮（≈项目逃逸登记回灌）
- Self-Refine arXiv:2303.17651 — 自批判自修订（≈三镜反问法）
- Tree of Thoughts arXiv:2305.10601 — 多路并行评估剪枝
- Plan-and-Solve arXiv:2305.04091 — 先规划后分步执行
- （彩蛋）LATS arXiv:2310.04406 — 树搜索统一推理/行动/规划

## 六组件（Osmani）
Automations 心跳｜Worktrees 隔离｜Skills 知识｜MCP 连接｜Sub-agents 分工（**Maker/Checker 分离：生成者永不自判 done**）｜Memory/State 持久（外部文件/数据库，不靠上下文窗口）

## 四层堆叠（LangChain）
L1 执行环（工具循环至完成）→ L2 验证环（LLM-as-Judge/机检硬门禁，不达标带反馈重做）→ L3 事件环（cron/webhook/消息触发）→ L4 改进环（用历史 trace 改 prompt/工具/模型）

## 五误区（见信号即停）
1. 把 Loop 当 while 循环（无 Checker/无外部 State）
2. 忽视退出条件（无硬门禁=烧钱）
3. 生成者自判 done（核心错误）
4. 盲目堆子代理（只在第二意见值得付费处开）
5. 认知投降（留 Loop 假期，读关键 diff，视 Loop 为实习生非替身）

## 项目独有增量（治理层 Loop 工程）
锚链不可篡改史｜逃逸登记册（只追加不清零，bad 计数永在）｜ε-δ 退化判据+双时钟｜公认程序（宣告说：审查制+异议期）｜预授权信封体系（E1-E5+死守级信封外）

## 成本四杠杆
分级模型（Maker 便宜/Checker 强）｜外部 STATE 切片读｜低频心跳（/goal 优于密集 cron）｜子代理按需

## 何时不用 Loop
一次性探索任务｜无可自动判定的成功条件｜人本就在场的工作
