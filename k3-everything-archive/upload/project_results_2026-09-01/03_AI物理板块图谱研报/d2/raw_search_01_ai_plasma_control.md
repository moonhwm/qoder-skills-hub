# 原始检索返回 01：AI 等离子体控制（DeepMind-EPFL 后续、2025-2026）
检索式（2026-09-01 执行）:
1. "DeepMind EPFL plasma control reinforcement learning 2025 new results tokamak"
2. "AI plasma control fusion 2026 reinforcement learning tokamak news"
3. "人工智能 等离子体控制 强化学习 托卡马克 2025"

## 关键返回摘录

### [^411^] 5sigmas.com (2026-03-20, 权威度NA)
- DeepMind+EPFL TCV 强化学习磁控, Nature 2022。
- Google DeepMind × CFS 合作（2025-10, deepmind.google blog "Bringing AI to the next generation of fusion energy"）: 三轴线 = TORAX 开源模拟器(JAX)做数百万虚拟实验 + RL 优化堆运行 + 实时等离子体控制；Google 同时投资 CFS。SPARC 目标首个净能量增益(breakeven)磁约束装置。

### [^412^] 1businessworld.com (2026-03-09, 权威度NA)
- Google DeepMind × CFS 2025-10 合作, TORAX + RL 实时控制 SPARC。
- TAE Technologies 与 Google 十年合作: 仅中性束注入实现 >7000万°C 稳定等离子体, Nature Communications 2025-04 发表, 大幅简化堆设计。
- AI 控制等离子体实验已在 DIII-D(Princeton) 和 TCV(EPFL) 成功。

### [^406^] arXiv 2605.15935 (2026-05-15, 权威度S)
- "Dynamic Plasma Shape Control with Arbitrary Sensor Subsets": RL agent 训练于 NSFsim(DIII-D 配置), 120 组实验形状数据集; 零样本跟踪动态形状序列, 静态构型平均形状误差 2.01 cm; 诊断失效随机屏蔽 30% 磁传感器仍鲁棒; 非对称 actor-critic + 特权平衡信息; 策略迁移至 DIII-D 真实放电直接指挥线圈执行器完成两次动态形状机动, 并迁移到独立 GSevolve 模拟器。作者 Dmitry Sorokin。

### [^407^] iotdigitaltwinplm.com (2026-07-30, 权威度B)
- 2022 DeepMind/EPFL Nature TCV RL 控制(19 线圈, 拉长、负三角、雪花偏滤器、双等离子体)。
- 2025-2026 RL 磁控扩展至 DIII-D, 含"无平衡重构"(reconstruction-free)控制器, 原始信号直接映射执行器指令。

### [^408^] 自动化学报《强化学习在托卡马克可控核聚变中的应用研究综述》(2026-08-01, 权威度B)
- 系统综述: 按爬升/平顶/下降三阶段梳理 RL 应用。
- Degrave 等 TCV 端到端 RL 磁控(Nature 2022); Tracey 等增强(奖励塑造、积分误差、episode chunking、迁移学习) TCV 验证。
- Subbotin 等将无重构磁控推广至 DIII-D, SAC 算法。
- Dubbioso 等 ITER 垂直稳定 DDPG 端到端控制。
- Seo 等 KSTAR: TD3 + LSTM 数据驱动模拟器, βN 前馈控制; 多参数(βp, q95, li)轨迹设计。
- Zhang 等 EAST: βp 实时闭环反馈控制, LHW 功率调制 + 系统辨识 + PPO, 部署于 EAST PCS。
- DIII-D 撕裂模规避: RL 策略基于多模态动力学模型(提前 25ms 预测撕裂与 βN), 输出 NBI 功率与上三角变调节, 实现"边界巡航"。
- Paruchuri 等安全 RL 密度调节(CMDP + 拉格朗日 PPO), Greenwald 极限裕度, DIII-D 与 ITER 仿真。
- Wakatsuki 等 DEMO 爬升 ACER 算法, 磁通消耗降至经验值 60% 以下; JT-60U ITG 控制。
- 世界模型: Kit 等自编码器低维动力学; Wu 等 LSTM 高保真数据驱动模型用于 HL-3(25 个关键变量联合预测); Abbate 等 2025 元学习模型融合(TGLF-nn + gyroBohm + LSTM), 适用 DIII-D/AUG/ITER 外推。
- 挑战: 部分可观测、安全约束、仿真-现实差距、实时部署、可复现性。

### [^409^] IT之家 (2025-10-17, 权威度B)
- 谷歌 2025-10-16 博文宣布与 CFS 合作, 基于 DeepMind RL 控制托卡马克磁体研究, 开发开源模拟器 TORAX; CFS 在波士顿郊区建 SPARC(高温超导磁体), 目标史上首个磁约束能量净增益。

### [^410^] 微信公众号"AI×可控核聚变" (2025-08-25, 权威度B)
- 2022 DeepMind×EPFL 首个深度 RL 等离子体控制(19 磁线圈, D形/雪花形)。
- 2023 控制精度提升 65%, 训练时间缩短 3 倍(注: 此数字来自该公众号转述, 需交叉验证 Tracey 等论文)。
- 2024 PPPL AI 提前 300ms 预测撕裂模不稳定性(基于 DIII-D 数据)。
- 2025-06 DIII-D 团队: 首次 AI 强化学习无平衡重构磁场控制, SAC 方法。
