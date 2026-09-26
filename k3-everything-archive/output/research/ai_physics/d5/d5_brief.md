# D5 简报：理论物理/计算物理 × AI 工程化应用板块现状

**研究日期：2026-09-01 ｜ 维度：AI4Science（科学智能）技术-商业化-开源-A股映射**
**原始返回落盘：<输出区>/research/ai_physics/d5/raw/raw_extracts.md（含全部检索式与关键摘录）**

---

## 检索路径留痕（5 组检索式 + 3 组 GitHub 实调）

| # | 通道 | 检索式 | 时间 |
|---|------|--------|------|
| 1 | web_search | AI for Science 科学基础模型 2025 2026 DeepMind 微软 英伟达 / OpenLAM 磐石 / GNoME MatterGen Aurora BioEmu / Schrodinger revenue 2025 / CAE AI 国产工业软件 | 2026-09-01 |
| 2 | web_search | GitHub AI4Science 开源项目 star / DP-GEN DeePMD-kit ABACUS / NVIDIA Earth-2 BioNeMo / A股 CAE 索辰 中望 霍莱沃 / AI4S 概念股 晶泰 深势 | 2026-09-01 |
| 3 | GitHub MCP search_repositories | `user:deepmodeling`；`org:facebookresearch/microsoft/NVIDIA/deepchem/google-deepmind` 组合 | 2026-09-01 |
| 4 | web_search | 深势科技 Bohrium OpenLAM DPA-2 / Isomorphic Labs 融资 / A股算力 寒武纪 海光 中科曙光 | 2026-09-01 |
| 5 | GitHub MCP + web_search | `abacus OR mace OR neuraloperator OR deepxde in:name`；Microsoft Discovery / 中望 索辰 霍莱沃年报 / NVIDIA ALCHEMI BioNeMo | 2026-09-01 |

---

## 一、技术侧：AI4Science 总框架现状（科学基础模型/科学智能体 2025-2026）

**总体判断**：2025-2026 年 AI4Science 已从"单点模型"进入"基础模型 + 智能体平台"双层架构竞争期；大厂路线分化为"开源生态派"（微软、Meta、NVIDIA）与"闭源商业化派"（DeepMind→Isomorphic Labs）。

**海外旗舰**：
- **微软**：Build 2025 发布科研智能体平台 **Microsoft Discovery**（基于 Graph-RAG 知识引擎，覆盖假设生成-实验模拟闭环），内部用其 200 小时筛选 36.7 万种候选物发现非 PFAS 数据中心浸没冷却剂（微软/凤凰科技，2025-05-20）；研究院模型矩阵：MatterGen（材料生成，生成 TaCr₂O₆ 目标 200GPa 实测 169GPa）、MatterSim（通用原子间势）、Skala（学习 DFT 交换关联泛函，Skala 1.1 于 2026 年开源，248+ stars）、BioEmu（蛋白平衡系综，单 GPU 每小时数千构象）、Aurora（大气基础模型）（tistory 综述，2026-07-13）；2026 年方向为 agentic "AI lab assistants"（同上）。
- **DeepMind/Alphabet**：AlphaFold 3 后转向闭源商业化，Isomorphic Labs 2025-03 完成 6 亿美元 A 轮（Thrive 领投），2026-05 完成 B 轮（21 亿美元 vs 12 亿美元两口径并存，财联社 2026-05-12 与腾讯 2026-05-18 报道不一致，注意核实）；与礼来/诺华合作潜在总额近 30 亿美元（首付款 4500 万 + 3750 万美元），2026-01 新增强生合作，2026-02 发布 IsoDDE 模型自称超行业标杆（虎嗅，2026-02-26）。材料侧 GNoME 发现 220 万种新晶体结构（Nature 2023，经 awesome-ai-for-science 转引）。
- **NVIDIA**：走"物理 AI 基础设施"路线——PhysicsNeMo（开源物理-ML 框架，Apache 2.0）、Earth-2（天气气候）、BioNeMo NIM（药物）、ALCHEMI NIM（材料化学模拟推理加速，SC24 2024-11 发布；第三方称筛选加速达 10,000×，substack 2026-01，可信级低需复核）、cuPyNumeric；与微软 Discovery 深度集成（NVIDIA 博客，2025-05-19）；达索 3DEXPERIENCE World 2026-02 宣布 BIOVIA+BioNeMo/ALCHEMI、SIMULIA+CUDA-X 合作（pharmaspotter 转引）。
- **Meta FAIR**：2025-05 发布 OMol25 数据集与 UMA 通用原子模型（300 亿原子训练）（掘金转引，2025-05-20）；FAIRChem OMat24 含 1.18 亿+ DFT 计算（awesome 列表）。

**国内**：
- **中科院"磐石·科学基础大模型"**：2025-11 发布 V1.5，支持 128K 上下文工具调用，新增波数据（恒星耀发预测）、谱数据（无底库分子结构生成）、场预测能力，参与 GAIA/SimpleQA/HLE 评测（百度百科，2026-07-23 更新）。
- **OpenLAM/DPA-2**：北京科学智能研究院 + 深势科技联合发起大原子模型计划，DPA-2 覆盖元素周期表 90% 以上元素；北京市发布《"人工智能+新材料"行动计划（2025-2027）》（新华网，2025-03-20）。Uni-Mol 蛋白预测能力被称仅次于 AlphaFold3、研发成本为其 1/400（中宏网，2025-03-21，单方表述）。
- 产业动态：深势科技（Bohrium 平台）据传接近上市（新浪财经，2026-04-02）；Anthropic 用 Claude 设计蛋白结合剂 15 靶点成功 14 个（财新，2026-08-23）——大模型厂商开始进入科学发现一线。

## 二、计算物理软件与平台商业化

**标杆公司薛定谔（SDGR）FY2025 财报**（ir.schrodinger.com，2026-02-25）：总营收 2.559 亿美元（+23.3%）；软件收入 1.995 亿（+10.6%），毛利率 74%；药物发现收入 5,640 万（2024 年为 2,720 万）；净亏损收窄至 1.033 亿（2024 年亏 1.871 亿）；软件 ACV 1.985 亿（+4%），Top20 药企 ACV +15.3%；2026 年指引软件 ACV 2.18-2.28 亿美元（+10-15%），目标 2028 年调整后 EBITDA 转正。材料科学收入由 1,500 万增至 1,700 万美元（GuruFocus，2026-02-26）。
**市场规模**：全球计算化学市场 2025 年 15.9 亿美元，预计 2034 年 44.4 亿美元，CAGR 12.44%；北美占 38.99%（Fortune Business Insights，2026-08-10）。
**国内对标**：
- **晶泰控股（2228.HK）**：2025 年营收 8.03 亿元（+201.2%），经调整净利 2.58 亿元，成为港股 AI4S 首家盈利公司；药物发现收入 5.38 亿（+418.9%），覆盖全球前 20 大药企中 17 家，与 DoveTree 签订近 60 亿美元合作（AI 制药领域最大单笔订单）（医药魔方/新浪，2026-03-25/27）。2025 年国内 AI 制药融资 32 起、超 67 亿元、同比 +130.5%（新浪，2026-04-02）。
- **CAE+AI（工业软件）**：索辰科技（688507）2025H1 营收 5,735 万元（+10.82%），亏损收窄 31.21%，划分"天工（CAE）+开物（物理AI）"双产品线，工程仿真软件收入 1,682 万同比近翻倍，毛利率 41.89%（华创证券点评，2025-09-04）；霍莱沃（688682）2025H1 营收 1.02 亿（-17.68%），AI+CAE 研发投入致扣非转亏，2025 年报披露物理 AI 收入 3,800 万（公司公告 2025-08-28；雪球 2026-09-01）；中望软件（688083）2025 年 CAE 收入仅 1,181.7 万元（+21.35%，占比 1.43%）（年报，2026-04-23）。北达飞易（北大重庆大数据研究院）AI 结构仿真软件入选工信部 2025 年 AI 应用典型案例，求解效率最高提升约 4 倍（新华网，2026-07-08）。
- **风险提示**（中银证券，2025-06-30 经 EET 转引）：物理 AI "快速仿真"依赖足够多高质量训练数据，数据受限可能致推广不及预期——这是 CAE+AI 商业化的核心约束。

## 三、代码域实调：GitHub 代表开源项目活跃度（GitHub API 实查，2026-09-01）

| 项目 | 归属 | Stars | 最近 push | 备注 |
|------|------|-------|-----------|------|
| google-deepmind/alphafold | DeepMind | 14,823 | 2026-09-01 | AF2 代码库 |
| google-deepmind/alphafold3 | DeepMind | 8,508 | 2026-09-01 | AF3 推理管线 |
| deepchem/deepchem | DeepChem 社区 | 6,971 | 2026-09-01 | 药物发现/量子化学 |
| lululxvi/deepxde | 陆路（布朗大学系） | 4,399 | 2026-09-01 | PINN/SciML 库 |
| neuraloperator/neuraloperator | Caltech 系 | 3,854 | 2026-09-01 | FNO 神经算子 |
| NVIDIA/physicsnemo | NVIDIA | 3,211 | 2026-09-01 | 物理-ML 框架；sym 子库已归档，2026-06 新建 Rust 推理服务 physicsnemo-serve（6★） |
| facebookresearch/fairchem | Meta FAIR | 2,235 | 2026-08-31 | OMat24/UMA 生态 |
| deepmodeling/deepmd-kit | 深势科技/DeepModeling | 2,029 | 2026-08-31 | Gordon Bell 奖 2020；forks 647 |
| microsoft/mattergen | 微软研究院 | 1,807 | 2026-09-01 | 材料生成 |
| ACEsuit/mace | 剑桥 ACEsuit | 1,333 | 2026-09-01 | 等变 MLIP；mace-foundations 301★ |
| deepmodeling/Uni-Mol | DeepModeling | 1,157 | **2025-05-29** | ⚠ 主仓 15 个月未更新 |
| deepmodeling/dpgen | DeepModeling | 396 | 2026-08-29 | 主动学习势函数生成，持续发版（v0.11.x，2026-05） |
| abacusmodeling/abacus-develop | 国产第一性原理 | 206 | 2026-08-05 | forks(296) > stars，工程贡献活跃但社区关注度低 |
| deepmodeling/Uni-Lab-OS | DeepModeling | 176 | 2026-08-30 | 2025-04 新建，实验室自动化平台，代表"AI+机器人实验室"新方向 |
| hyperai/awesome-ai4s / ai4s-research/awesome-ai-for-science | 社区索引 | 3,345 / 1,929 | 2026-08-31 / 09-01 | 后者 2025-10 创建即近 2k star，反映赛道热度 |

**结论**：头部项目（AlphaFold、PhysicsNeMo、FairChem、DeePMD-kit）持续高频更新，生态健康；国产 DeepModeling 系工程活跃（2026-08 底仍有 push），但 star 量级（<2.5k）与海外头部（1.5 万）差一个数量级；Uni-Mol 主仓停滞值得注意。2025-2026 新趋势：智能体化科研工具（ai4s-skills 202★、Uni-Lab-OS）和推理服务化（physicsnemo-serve）。

## 四、A 股映射

**直接标的（科学计算/CAE/物理 AI）**：
- 索辰科技（688507，CAE+物理 AI，2025H1 营收 5,735 万 +10.8%，市值约 95.7 亿元 @2025-09-30）
- 霍莱沃（688682，电磁仿真+物理 AI，2025 年报物理 AI 收入 3,800 万）
- 中望软件（688083，CAD/CAE，CAE 收入占比仅 1.43%）
- 板块叙事：2025Q1 霍莱沃、索辰营收增速均高于 Ansys（国金证券孟灿深度，2025-10-29）；券商 2026-08 起对"科学智能 AI4S"关注度升温（财新，2026-08-23）。
**算力服务/芯片（AI4S 底层）**：寒武纪（2025 年成 A 股"股王"）、海光信息（换股吸收合并中科曙光，2025-05-25 公告，形成芯片-服务器-算力服务全链）、中科曙光、工业富联（市值 1.23 万亿，A 股第九，2025-12-31 新华财经）。2025 年算力板块为市场核心主线。
**港股对照（非 A 股，注意口径）**：晶泰控股（2228.HK）、英矽智能（03696.HK）、剂泰科技（07666.HK，2026-05-27 上市首日 +126%）——AI4S 纯正标的集中于港股 18A，A 股缺少"纯 AI4S"标的，只能以 CAE/工业软件+算力间接映射。
**EDA 邻近板块**：华大九天、广立微、概伦电子（雪球梳理，2025-01-01）。

## 五、缺口声明（缺席/存疑维度）

1. **理论物理（高能物理、宇宙学、凝聚态理论）专门的 AI 工程化应用**：本轮检索未覆盖如 CERN/LHC 的 AI 管线、引力波数据分析（如 LIGO 的 ML）等细分，仅触及计算物理/材料/化学侧——此为本维度"理论物理"部分的明确缺口。
2. **磐石大模型**细节仅来自百度百科单一来源（2026-07-23），未见官方技术报告原始数据；**OpenLAM/DPA-3 2026 年最新迭代**未检得。
3. **Isomorphic Labs B 轮金额存在 21 亿美元 vs 12 亿美元两个口径**（财联社 vs 腾讯新闻，均为 2026-05），未定论。
4. GitHub star 数为 2026-09-01 时点快照；commit 活跃度仅看 pushed_at，未做 commit 频率统计。
5. A 股相关财务数据截至各公司 2025 中报/年报披露；未检索 2026 年 H1 数据（部分公司尚未披露或本轮未命中）。
6. 计算化学市场规模、ALCHEMI "10,000× 加速"等第三方数据来自行业研究/自媒体，权威级较低，已标注。
