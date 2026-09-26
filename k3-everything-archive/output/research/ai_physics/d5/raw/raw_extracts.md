# D5 原始检索返回摘录（检索留痕）
# 日期：2026-09-01；工具：web_search ×5 组、GitHub MCP search_repositories ×3 组

## 组1 web_search（step 2）
- Q: "AI for Science 科学基础模型 2025 2026 DeepMind 微软 英伟达 科学智能体 平台" → 0 结果
- Q: "OpenLAM 大原子模型 磐石科学基础大模型 2025 进展" → baike.baidu.com/item/磐石·科学基础大模型/66250177（2026-07-23）：磐石2025年11月发布V1.5，支持128K上下文工具调用，波数据预测恒星耀发、谱数据不依赖底库生成分子结构、场预测精度提升；参与GAIA/SimpleQA/HLE评测。
- Q: "AI4Science foundation model GNoME MatterGen Aurora BioEmu 2025" → jissu.tistory.com（2026-07-13）：Microsoft Research旗舰模型 MatterGen（生成TaCr2O6，目标200GPa实测169GPa）、MatterSim通用原子间势、Skala学习DFT交换关联泛函、BioEmu蛋白平衡系综单GPU每小时数千、Aurora大气基础模型；2026方向：agentic "AI lab assistants"。
- Q: "Schrodinger ... revenue 2025" → SDGR FY2025（ir.schrodinger.com，2026-02-25）：总营收$255.9M(+23.3%)，软件$199.5M(+10.6%)，药物发现$56.4M，软件毛利率74%，净亏$103.3M，现金$402.3M，ACV $198.5M(+4%)，Top20药企ACV +15.3%，2026指引ACV $218-228M。Q2'25（investing.com，2025-08-07）：营收$54.8M(+16%)。计算化学市场：2025年$15.9亿→2034年$44.4亿，CAGR 12.44%（fortunebusinessinsights，2026-08-10）。
- Q: "CAE AI 仿真 国产工业软件 2025" → 新华网重庆（2026-07-08）：北大重庆大数据研究院"北达飞易人工智能结构仿真软件"入选工信部2025年AI应用典型案例，底层算法100%自主，求解效率最高提升约4倍。

## 组2 web_search（step 3）
- Q: GitHub AI4Science 开源项目 → github.com/ai-boost(现为ai4s-research)/awesome-ai-for-science：GNoME 2.2M晶体（Nature 2023）；FAIRChem OMat24 118M+ DFT计算；Skala 1.1（MSR 2026，248+ stars）；ADiT（Meta FAIR ICML2025，310+ stars）；DeePMD-kit 1.9k+ stars（Gordon Bell 2020）；TorchMD 707；SO3LR 218；TorchSim 468（100x over ASE）；Newton（Disney/DeepMind/NVIDIA，Linux基金会，2025）；JAX-CFD 947；PennyLane 3k+。
- Q: DP-GEN DeePMD-kit ABACUS → github.com/deepmodeling/dpgen/releases（2026-05-12）：v0.11.x 持续发版，ABACUS兼容性修复频繁。
- Q: NVIDIA Earth-2 → developer.nvidia.com：PhysicsNeMo开源物理-ML框架（FourCastNet/SFNO/GraphCast/Pangu/DLWP），Earth2Studio推理；SimScale用其做离心泵基础模型；G42 UAE区域预报200m分辨率。
- Q: A股 CAE 概念股 → 虎嗅（2026-01-27）《工业软件2026三部曲》：上海霍莱沃、上海索辰、无锡飞谱、同济系觅玄、东峻等CAE厂商；国金孟灿索辰深度（知乎，2025-10-29）：2025Q1霍莱沃、索辰营收增速高于Ansys。
- Q: AI4S 概念股 → 财新（2026-08-23）：剂泰科技07666.HK单日+28%，英矽智能03696.HK、晶泰控股02228.HK涨超10%，券商AI4S关注度升温；Anthropic Claude设计15靶点蛋白结合剂14成功（2026-08-18）。
  晶泰2025年报（sina/医药魔方，2026-03-25/27）：营收8.03亿元(+201.2%)，经调整净利2.58亿元首次盈利，药物发现收入5.38亿(+418.9%)，智能机器人2.65亿(+62.6%)，覆盖全球前20药企中17家，现金70.68亿，DoveTree合作总额近60亿美元。2025年国内AI制药融资32起、超67亿元、同比+130.5%（sina，2026-04-02）。北太天元2025（baltamatica，2025-12-12）：AI重构科学计算与系统仿真，30+预训练模型、深度学习/统计工具箱扩容、规划PINNs支持。

## 组3 GitHub MCP（step 5-6）
- "user:deepmodeling"：deepmd-kit 2,029★/forks 647/push 2026-08-31；Uni-Mol 1,157★（push 2025-05-29）；jax-fem 747★（push 2026-08-20）；dpgen 396★（push 2026-08-29）；dpdata 254★；DMFF 199★；Uni-Lab-OS 176★（2025-04创建，实验室自动化）；CrystalFormer 151★；sciencepedia 151★；DeePTB 121★。
- "org:facebookresearch fairchem OR ..."：google-deepmind/alphafold 14,823★；alphafold3 8,508★；deepchem/deepchem 6,971★；NVIDIA/physicsnemo 3,211★（+physicsnemo-cfd 148、curator 60、serve 6[2026-06新建]；physicsnemo-sym 334 已归档）；facebookresearch/fairchem 2,235★；microsoft/mattergen 1,807★。
- '"AI for Science" pushed:>2025-06-01'：hyperai/awesome-ai4s 3,345★；ai4s-research/awesome-ai-for-science 1,929★（2025-10创建）；ai4s-research/ai4s-skills 202★（2026-06创建，科研智能体技能）。
- step 8 "abacus OR mace OR neuraloperator OR deepxde in:name"：lululxvi/deepxde 4,399★；neuraloperator/neuraloperator 3,854★；ACEsuit/mace 1,333★（mace-foundations 301）；abacusmodeling/abacus-develop 206★（国产第一性原理，forks 296 > stars）。

## 组4 web_search（step 7）
- OpenLAM/DPA-2：新华网（2025-03-20）：北京科学智能研究院+深势科技发起OpenLAM大原子模型计划，DPA-2覆盖元素周期表90%以上元素；《北京市"人工智能+新材料"行动计划（2025-2027）》；Uni-Mol蛋白预测能力仅次于AlphaFold3、研发成本1/400（中宏网，2025-03-21）。
- Isomorphic Labs：2025-03完成6亿美元A轮（Thrive领投）；2026-05完成B轮（财联社/QQ 2026-05：21亿美元或12亿美元口径不一，来源分别说$2.1B与$1.2B，存口径分歧）；与礼来/诺华合作潜在近30亿美元（首付4500万+3750万）；2026-01与强生合作；2026-02发布IsoDDE超越行业标杆（虎嗅，2026-02-26）。
- A股算力：新华财经（2025-12-31）：2025年AI算力核心主线，寒武纪成"股王"，工业富联市值1.23万亿A股第九，海光信息换股吸收合并中科曙光（2025-05-25公告，芯片-服务器-算力服务整合）。

## 组5 web_search（step 9）
- Microsoft Discovery：Build 2025（2025-05-19/20）发布科研智能体平台，集成NVIDIA ALCHEMI NIM（化学模拟推理优化）与BioNeMo NIM；内部200小时筛选36.7万候选发现非PFAS浸没冷却剂；与PNNL合作固态电解质候选使锂用量减70%；生态接入Synopsys、PhysicsX物理AI基础模型。
- NVIDIA SC24（2024-11-18）：cuPyNumeric、BioNeMo开源框架、ALCHEMI NIM；CUDA-Q与Google Quantum AI合作。达索3DEXPERIENCE World（2026-02-03）：BIOVIA+BioNeMo、BIOVIA+ALCHEMI、SIMULIA+CUDA-X合作（pharmaspotter）。
- 中望软件2025年报（新浪公告，2026-04-23）：标准软件收入8.26亿(+7.48%)，其中2DCAD 5.27亿、3DCAD 2.59亿、CAE 1,181.7万(+21.35%，占比仅1.43%)。
- 索辰科技（688507）2025H1（华创点评/财中社，2025-08/09）：营收5,735万(+10.82%)，归母净利-4,570万（亏损收窄31.21%），毛利率41.89%，"天工"（CAE）4,948万+"开物"（物理AI）产品线，工程仿真软件收入1,682万同比近翻倍；研发投入占营收88.27%；9/30市值约95.7亿；拟收购力控科技60%股权。
- 霍莱沃（688682）2025H1（新浪公告，2025-08-28）：营收1.02亿(-17.68%)，归母净利33.81万(-94.51%)，扣非-428万；AI+CAE研发投入增加；雪球（2026-09-01）：2025年报物理AI收入3,800万。
