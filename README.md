# Qoder Skills Hub

一批可用于 Qoder / Claude 类 Agent 的 **Skill** 集合，共 91 件。每件均为独立目录，含 `SKILL.md`（YAML frontmatter 定义 `name` 与 `description`，供 Agent 路由触发），部分附带 `scripts/` 与 `references/`。

## 安装 / 使用

- **Qoder**：在技能市场或本地技能目录中放置对应 `<name>/` 目录；或用 `skill_manage create` 仅注册 `SKILL.md`。
- **通用 Agent**：将 `<name>/SKILL.md` 作为技能定义加载；`scripts/` 为可选执行辅助，使用前请自行审阅（本仓库不代为背书任何脚本，运行前请评估许可证与安全性）。

> 安全提示：`scripts/` 中可能包含双用途/网络类工具（如公网隧道、压缩包爆破等）。仅在获授权的合规场景下使用。加载远程技能前建议先只读审阅，不要盲目执行捆绑脚本。

## 技能索引

| 技能 | 描述（截断，完整见各 SKILL.md） |
|---|---|
| [`admission-panel-analytics`](admission-panel-analytics/SKILL.md) | 考研录取面板数据的校验、模式判别与轻量评分方法论，蒸馏自新东方36校面板分析档案：三录取模式判别（α一志愿过线即录/β零调剂�  |
| [`ai-persona-document`](ai-persona-document/SKILL.md) | '创建结构化的 AI 助手人设（persona）与角色扮演定义文档，输出 DOCX 或 PDF 格式。当用户需要以下情形时使用：（1）创建规定 AI 助手应�  |
| [`archive-ops-kit`](archive-ops-kit/SKILL.md) | 压缩包作业箱：自有加密 zip（AES-256/ZipCrypto）授权爆破、两级校验防误报、批量递归解压（嵌套包+CRC校验+防zip quine）、MD5 差异比对与封  |
| [`arxiv-source-sentinel`](arxiv-source-sentinel/SKILL.md) | arXiv.org e-Print archive 论文信源标准：arXiv ID 解析与幻觉甄别、官方 API 元数据核验、预印本信源定级（载体 C0 vs 命题 C3 等价）、版本锁定  |
| [`autonomous-advance-ops`](autonomous-advance-ops/SKILL.md) | [通用技能] 自主推进运维总控（便携版）——长任务自治推进与健康监视的整合恒常件（便携版：无项目绑定，任何用户/任何模型可直�  |
| [`autonomous-advance-protocol`](autonomous-advance-protocol/SKILL.md) | 常驻授权总纲——用户（委托方）在任何场景/项目下说「请您自主推进」「自主推进」「你看着办推进」或等价表述时触发：默认调用�  |
| [`av-media-ops`](av-media-ops/SKILL.md) | [项目技能] 音视频作战室——音视频材料的摄取、ASR 转写、信源核查与语音化产出一体管线（用户侧主权件）。触发（满足任一）：①�  |
| [`bidding-docs-ops`](bidding-docs-ops/SKILL.md) | 投标/应答文本书写作战技能——三册制应答文件骨架、点对点应答矩阵、承诺函与补正文书范式的模板化写作与形式风险前置防线。触�  |
| [`bidding-ops`](bidding-ops/SKILL.md) | 投标/招标一体作战技能——评分博弈分析（规则解析/报价推演/非价格顶格/情景模拟）+ 应答文书写作（三册骨架/点对点矩阵/承诺函与�  |
| [`claims-deep-audit`](claims-deep-audit/SKILL.md) | 深度核查某机构、项目、导师或产品的对外宣传性主张是否名副其实。当用户需要核查、打假、评估水分、判断"是否靠谱"、对比宣传与�  |
| [`cn-housing-finder`](cn-housing-finder/SKILL.md) | 国内租房/买房房源初筛与结构化——web_search 初筛 + web_open_url 抓详情 + 本地解析器出对比表。当用户要"找房/租房/买房/房源对比/看房清  |
| [`cognitive-exoskeleton`](cognitive-exoskeleton/SKILL.md) | 把 agent 集群变成用户的"认知外骨骼"——用户出意图与选择题判断，agent 出调研、推导、落地与证据链。何时使用：用户在数学方法选择  |
| [`commute-school-optimizer`](commute-school-optimizer/SKILL.md) | 通勤×择校综合寻优技能。当用户在择校（学校选择）、居住/就业选址、学区房决策视野下需要量化交通通勤成本并参与多目标排序时使  |
| [`consignment-intake-ops`](consignment-intake-ops/SKILL.md) | [项目技能] 交割接收运维——函询交割的统一接收与台账：子代理派单/跨会话交接/技能写回/回执摆渡等一切交割事项的登记、状态机（  |
| [`coordination-letter`](coordination-letter/SKILL.md) | 跨实例协调函规程——Kimi 生态内不同会话/实例之间的结构化任务委派与回执文书。  |
| [`corpus-value-distiller`](corpus-value-distiller/SKILL.md) | 已获取语料库（公众号文章、批量网页、文档集合等结构化 JSONL/索引）的价值榨取工作流。当用户要求"榨干这批语料/这批文章还有什么  |
| [`cron-task-forge`](cron-task-forge/SKILL.md) | [项目技能] 定时任务（cron/提醒/自检任务）的创建、审计与降频规范。当用户要求创建/修改/暂停/删除定时任务、定时提醒、每日/每周�  |
| [`cross-session-workflow-bridge`](cross-session-workflow-bridge/SKILL.md) | 继续项目/加载项目环境时首先触发的跨会话工作流衔接伞形技能：任何新对话中说「继续项目」「加载项目环境」「继续上次进度」即�  |
| [`daily-life-autopilot`](daily-life-autopilot/SKILL.md) | 每日例行生活事务自动化编排——凭证哈希链自检、通勤火车票/机票查询（美团官方通道）、POI 双通道查询（高德+百度）、每日领券、  |
| [`data-viz-gen`](data-viz-gen/SKILL.md) | 从 JSON 数据生成自包含的 HTML/SVG 信息图，支持 KPI 统计卡片、分组柱状图对比、流程图和混合仪表盘四种类型，提供 8 套配色方案和  |
| [`day-sundial-ops`](day-sundial-ops/SKILL.md) | 日晷场——白天工作台的轻量纪律。夜场（「夜场件」）管你睡着后的自治玩耍；日晷场管你醒着时的快速小活：随手问答、小段实验、  |
| [`diffusion-dynamics-extension`](diffusion-dynamics-extension/SKILL.md) | 动态演化与干预效果量化扩展技能。当已有静态评估结论、需要回答"随时间/空间如何演化""不干预会怎样""干预 ROI 多大"时使用。触发场  |
| [`doc-archive-ingest`](doc-archive-ingest/SKILL.md) | 网盘分享链接文档归档管线：解析坚果云公开分享链接与百度网盘分享链接（pan.baidu.com/s/）、枚举目录、带节奏批量下载、生成出处登�  |
| [`doc-image-solver`](doc-image-solver/SKILL.md) | [项目技能] 拍图解题全管线：试卷/文档照片 → 高精度转写文档 → 逐题解读作答 → 迭代收敛。当用户上传试卷/讲义/文档照片要求转写  |
| [`eastmoney-rumor-sentinel`](eastmoney-rumor-sentinel/SKILL.md) | [项目技能] 东财传闻哨兵——东方财富股吧公开面的传闻采集、词面三档判级与白话呈报。触发（满足任一）：①用户说「东财」「东方  |
| [`epsilon-delta-proof-sovereign`](epsilon-delta-proof-sovereign/SKILL.md) | ε-δ 机械证明主权——把数学分析的形式化语言（ε-δ 极限/连续/一致连续/导数/积分语句族）  |
| [`evidence-chain-verifier`](evidence-chain-verifier/SKILL.md) | 自修正信源 + 可证伪流程证据链 + 抗幻觉核查框架。定位为证据登记、抗幻觉校验、可证伪断言登记、信源分级与公开复核链接：当用户  |
| [`exam-isolation-ops`](exam-isolation-ops/SKILL.md) | [项目技能] 模拟考场隔离协议（考场隔离协议 v1.1）——用结构上相互隔离的子代理角色跑闭卷模拟考/盲考/真题演练/备考抽查：出题打�  |
| [`extpool-furnace-ops`](extpool-furnace-ops/SKILL.md) | [项目技能] 外池压测炉运维——用外部模型池（GLM 礼赠池、华为码道/CodeArts、华为云 ModelArts、阿里百炼、火山方舟、智谱等 MaaS 接口）�  |
| [`fusion-program-audit`](fusion-program-audit/SKILL.md) | 高校核聚变方向"聚变期权"真伪核查与考研择校评级。当用户需要判断某校宣称的核聚变/聚变/等离子体物理方向是实质布局还是标签嫁�  |
| [`gitlab-cli-guide`](gitlab-cli-guide/SKILL.md) | 提供 GitLab 命令行工具（glab）的完整参考与自动化脚本，涵盖超过30个子命令，包括合并请求创建与审查、CI/CD流水线调试、Issue管理、仓  |
| [`goal-child-ops`](goal-child-ops/SKILL.md) | 赤子续行（目标系统×尼采孩子姿态的融合纪律·临时技能）——把 goal-mode 的目标状态机（objective/verifier/迭代/complete/blocked）当作棋盘与  |
| [`grad-advisor-outreach`](grad-advisor-outreach/SKILL.md) | 学术导师套磁与外联协议（AAPP, Academic Advisor Profiling Protocol）。用于硕士/博士申请中的导师筛选、约束识别、套磁信撰写与发送跟踪。触  |
| [`grad-path-scorer`](grad-path-scorer/SKILL.md) | [项目技能] 升学路径加权评分引擎（硕士择校 × 申博衔接特化）。当用户需要评估硕士院校选择、量化「学术断头路」风险、建模申博�  |
| [`hifi-integration-umbrella`](hifi-integration-umbrella/SKILL.md) | 高保真整合伞（临时技能）——将名录实载技能（件数以 references/roster.md 当时实载为准）高保真整合为一张协奏目录与统一调用规程：�  |
| [`home-network-troubleshooter`](home-network-troubleshooter/SKILL.md) | 家庭/小型办公网络故障的分层定位与修复程序，特化华为坤灵 ePlusSoHo 多 AP 组网（AP162 面板、AC 管理）。当用户报告"电脑网页打不开但   |
| [`humanizer-zh`](humanizer-zh/SKILL.md) | 去除中文文本的 AI 生成痕迹并重建真实感，覆盖写作与改稿双场景。当用户请求润色、编辑、改写文本，或提及去除 AI 味/AI 痕迹、让文  |
| [`intl-case-intf`](intl-case-intf/SKILL.md) | 国际法案例接口件（临时技能）——CJEU CELLAR 官方 SPARQL 与 ECtHR HUDOC 事实型公开端点的只读薄封装 + SQLite FTS5/BM25 本地索引，统一引证契�  |
| [`iteration-convergence-ops`](iteration-convergence-ops/SKILL.md) | 长周期项目在多轮对话中的版本迭代管理方法论：持久化优先（每轮必落盘并 ls 核验，杜绝'声称完成但未落盘'）、版本号诚实（git 风�  |
| [`k3-channel-ops`](k3-channel-ops/SKILL.md) | [项目技能] K3/集群甲通路搭建与运维——自研搭建并优化跨会话消息通路（「通道库」 总线），使所有 K3/集群甲工作时能及时变革相关�  |
| [`k3-everything-archive`](k3-everything-archive/SKILL.md) | K3 一切事务穷举总包·洁版（私藏归档件，全量脱敏后重制）——单容器穷举：73 技能(便携五件最新同源)+MCP 接口层+安全三件套+upload 全  |
| [`k3-interaction-ops`](k3-interaction-ops/SKILL.md) | 集群甲（Agent Swarm / 极致模式）长任务的防退化监视与恢复规程。  |
| [`k3-territory-studies`](k3-territory-studies/SKILL.md) | 未竟合众集群·领域研究临时技能（v0.2.1-temp，2026-09-01 迭代：新增综合指令包标准处置规程；2026-09-02 补丁：facilities-ledger 补 服务甲 积�  |
| [`k8s-cluster-ops`](k8s-cluster-ops/SKILL.md) | 通过 kubectl 命令行工具管理 Kubernetes 集群，执行查询资源状态、部署应用、查看日志、调试容器、切换上下文和监控集群健康等操作。适  |
| [`livability-audit-swarm`](livability-audit-swarm/SKILL.md) | 城市宜居度/舒适度文档的蜂群审计与直接修复编排。当用户要求审计、核查、修复或治理「城市宜居度/住房压力/宿舍舒适度/就读舒适�  |
| [`long-table-harvest-ops`](long-table-harvest-ops/SKILL.md) | 长表逐字收割完整性规程——对超长网页表格/名单（数百至数千行：官方公示名单、成绩表、职位表、目录全表等）做逐字（verbatim）收  |
| [`medical-career-transition`](medical-career-transition/SKILL.md) | 医学背景者的转行与就业特化决策支持。当用户讨论医学转行、医学生就业、医生转行、医学生职业规划、离职、规培退出、医学硕士/�  |
| [`medical-malpractice-criminal-review`](medical-malpractice-criminal-review/SKILL.md) | 医疗事故刑事案件特化审查。用于评估医疗行为是否构成医疗事故罪、非法行医罪或过失致人死亡罪，输出责任比例、责任等级、罪名建  |
| [`multi-dimensional-option-scoring`](multi-dimensional-option-scoring/SKILL.md) | 在不确定性下对多个选项（择校、择业、投资标的、技术路线、供应商等）做量化排序与风险分级的决策框架。何时使用：用户需要多候  |
| [`night-playground-ops`](night-playground-ops/SKILL.md) | 项目工作区甲运维——把「用户睡眠时段的自治玩耍/兴趣研究」这一目标本身内置化为自我维持运营的技能：目标即本体，开园→预算�  |
| [`notary-legal-upload`](notary-legal-upload/SKILL.md) | 涉外公证办理、法律文书签署上传、电子证据哈希/区块链存证三合一范式。当用户需要办理翻译公证（毕业证/学位证/成绩单等涉外学历  |
| [`omni-exhaust-research-ops`](omni-exhaust-research-ops/SKILL.md) | 穷举研究总署——对任何复杂问题以「任何可能性穷举」方式做研究尽调、方案整合与统一调配的通用编排技能（无项目绑定，任何用户  |
| [`output-verdict-gate`](output-verdict-gate/SKILL.md) | [项目技能] 输出审议闸——实质性输出发出前的控辩对抗审议管线：输出者三轮自问留痕 → 辩方律师团（首席律师+调查员）结构性反对  |
| [`pan-exhaust-dispatch`](pan-exhaust-dispatch/SKILL.md) | 穷举统调署（便携泛化版）——对任何复杂问题以「任何可能性穷举」方式强制调用在场接口做研究尽调、方案整合与统一调配的元技能  |
| [`pangu-enforcement-bureau`](pangu-enforcement-bureau/SKILL.md) | [项目技能] 强制裁判落地执法局——充当暴力执法机构，强制将华为强制裁判(PanGu)模型纳入一切模型选型/调度/路由决策的候选集考量，  |
| [`persona-iteration-loop-ops`](persona-iteration-loop-ops/SKILL.md) | [项目技能] 人设迭代循环总署——以中性化迭代循环引擎（IterationLoopV11-neutral）为核心，融合六件源技能的融合件：虚构成年人设建模（  |
| [`persona-memory-anchors`](persona-memory-anchors/SKILL.md) | 从人设描述、交互样本或参考材料中提取并结构化「人格记忆锚点」，生成可复用的人设档案文档。  |
| [`persona-modeling-kit`](persona-modeling-kit/SKILL.md) | '人设建模双引擎套件（doc×anchors 合并件）：正向从需求创建结构化 AI 人设/角色定义文档，逆向从参考材料提取人格记忆锚点生成可复�  |
| [`phys-ai-mat-conf-radar`](phys-ai-mat-conf-radar/SKILL.md) | 物理×AI×材料领域顶会排期雷达，重点覆盖等离子体物理学与聚变工程化应用（APS DPP、IAEA FEC、EPS、SOFT、IEEE ICOPS、ISFNT、ANS、MRS、TMS、Ne  |
| [`plugin-datasource-ops`](plugin-datasource-ops/SKILL.md) | [项目技能] 插件与数据源调用范式——全会话插件接口的统一调用纪律、域路由表、实证 Pitfalls 与持久化规程。触发（满足任一）：①�  |
| [`portable-sync-ops`](portable-sync-ops/SKILL.md) | [项目技能] 便携件同步总署——一切「粘贴即装」引导件与整包便携（.skill）的登记台账与同步更新纪律。触发（满足任一）：①用户说  |
| [`ppp-city-verdict-audit`](ppp-city-verdict-audit/SKILL.md) | 城市/地区结论的 PPP 范式复核台（v1.3，含基准城支配性检验、快照纪律与阈值校准状态声明）（购买力平价=工资/房价购买力双锚）。当  |
| [`qr-visual-rescue`](qr-visual-rescue/SKILL.md) | 多解码器并集 QR/条码可视觉识别挽救管线。当用户需要扫描/识别/解码照片、截图、  |
| [`quant-frontier-lab`](quant-frontier-lab/SKILL.md) | 前沿算法实验台——教学级量化算法工具箱，覆盖 Gale-Shapley 志愿填报匹配、PSM 倾向得分/因果推断、DID 前置评估、SIR 传染模型（Gillespie  |
| [`quota-guard-ops`](quota-guard-ops/SKILL.md) | [项目技能] 额度守护运维——自主检测额度包/月订阅消耗信号，按 Q0–Q3 四档程式自适应运作，不逃逸前提下高性能输出。触发（满足�  |
| [`registry-knowledge-ops`](registry-knowledge-ops/SKILL.md) | [项目技能] 注册处知识库——技能迭代注册处（/mnt/agents/upload/skill-iteration-registry/）的全文检索、锚链调阅与 INDEX 分区导览（用户侧主权  |
| [`release-gate-audit`](release-gate-audit/SKILL.md) | [项目技能] 外发/公开发布的事前审查闸门（v2.5.8 代码外发禁令的操作化）。当任何内容要流出沙箱——GitHub 建仓/推送、网盘分享、网�  |
| [`retirement-guard-ops`](retirement-guard-ops/SKILL.md) | 退休保卫局——审计并压缩「阻止用户退休的注意力债主」，把自治系统对真人的打扰降到每周一页纸。触发（满足任一）：①用户说「  |
| [`rumor-chain-verifier`](rumor-chain-verifier/SKILL.md) | 复合传言的逻辑链拆解与断裂定位核查法。当用户拿来一条"看起来环环相扣"的网传说法（政策类传言如"上面发文要求XX"、社会类传言如  |
| [`rust-browser-pilot`](rust-browser-pilot/SKILL.md) | 基于 Rust 的高性能无头浏览器 obscura，单二进制内嵌渲染引擎（无需系统 Chrome），通过 CDP 协议工作，执行页面抓取、DOM 提取、截图、批  |
| [`sandbox-project-ops`](sandbox-project-ops/SKILL.md) | 跨会话长期项目的沙箱运维规程：修复 shell(root) 与 ipython(uid 999) 双 uid 写权限冲突、沙箱重置后重建 pytest/git/pre-commit 环境（含 git safe.dir  |
| [`sector-stock-rumorchain-pipeline`](sector-stock-rumorchain-pipeline/SKILL.md) | 行业研报+个股分析+舆情谣言链核查+东财股吧传闻采集的一体化管线（复合编排技能，已并收东财传闻哨兵本体）。当用户要求「生成某  |
| [`semantic-oncology-ops`](semantic-oncology-ops/SKILL.md) | [项目技能] 语义肿瘤防治运维——长对话上下文压缩避免、集群甲退化会话救活（严重退化下写出最小交割文档）、语义污染的癌症分期  |
| [`senior-rumor-check`](senior-rumor-check/SKILL.md) | 银龄传言核查员——面向长辈（老年用户）的传言核查适老化前端封装。把 rumor-chain-verifier 的拆链定断结果翻译成大白话、一句话结论�  |
| [`seo-copywriting-guide`](seo-copywriting-guide/SKILL.md) | 通过 12 步结构化工作流生成搜索引擎优化内容，产出一篇包含完整草稿、备选标题、Meta描述、FAQ结构化内容及CORE-EEAT自评清单的SEO文章�  |
| [`skill-dispatch-hq`](skill-dispatch-hq/SKILL.md) | [项目技能] 技能调度总署——全部技能与公用数据库级插件能力的统一台账、集中调度分配、函询交割、计时器任务与授权法典的恒常总  |
| [`skill-library-auditor`](skill-library-auditor/SKILL.md) | 技能库（SKILL.md 仓库）全量审计工具。当用户需要盘点/审计/复核技能库、检测中英文镜像技能对、发现共享脚本冲突、校验 SKILL.md frontm  |
| [`skill-refresh-ops`](skill-refresh-ops/SKILL.md) | [项目技能] 技能刷新运维——「重新加载并刷新（更新下载）任何可能所需技能」流程的固化件：安装位可写性预检、全库盘点与版本漂  |
| [`skill-reinstall-ops`](skill-reinstall-ops/SKILL.md) | [项目技能] 技能重装与分发运维——dist 目录技能包一键重装入安装位：预检可写性、逐包解压、旧版 .bak 备份、版本核验、零伪装如实�  |
| [`skill-version-ops`](skill-version-ops/SKILL.md) | [项目技能] 技能版本流转总署——单件三模式共库（version_flow.py）：①refresh-check 刷新运维（可写性预检/全库盘点与版本漂移扫描/点名�  |
| [`software-testing-guide`](software-testing-guide/SKILL.md) | 建立全面的软件QA测试流程，包括制定测试策略、按照Google AAA标准编写测试用例、执行测试计划、使用P0-P4分级追踪缺陷、计算质量指标�  |
| [`source-semantics-sentinel`](source-semantics-sentinel/SKILL.md) | 信源验证通道与上升机制、投毒甄别、语义精度利刃、最小作用量路由四位一体的信息入口哨兵。当用户需要信源验证/来源核查/信源评�  |
| [`stat-verdict-ops`](stat-verdict-ops/SKILL.md) | [项目技能] 统计裁决室——通用统计检验落地引擎（用户侧主权件，先证伪后裁决）。触发（满足任一）：①用户说「统计检验」「显著  |
| [`travel-commute-planner`](travel-commute-planner/SKILL.md) | 出行与通勤的综合规划中枢（热插模块化整合 amap-travel-skill 与 commute-school-optimizer；v2.0 全量收编 集群甲五通道）。当用户需要查询火车/  |
| [`unified-decision-suite`](unified-decision-suite/SKILL.md) | 统一决策套件——四层架构（数据/证据/引擎/交付）下路径级与院校级决策的薄编排层。何时使用：统一决策、决策管线、路径决策、院  |
| [`up-distill-ops`](up-distill-ops/SKILL.md) | UP主/内容创作者多平台信息蒸馏恒常规程。当用户要求对 B站UP主、公众号作者、  |
| [`vision-intake-ops`](vision-intake-ops/SKILL.md) | [项目技能·强制入口] 视觉输入总门——图像输入统一路由+共享识读底座（伞件，三件本体不复制）。【强制】凡消息含图片/截图/照片�  |
| [`vision-ocr-pipeline`](vision-ocr-pipeline/SKILL.md) | 截图/长图的识读与传输管线：本地OCR双引擎分工（RapidOCR全文+tesseract数字核验）、按字高阈值压图省token、长条切片、跨AI自包含HTML交接  |
| [`web-security-audit`](web-security-audit/SKILL.md) | 基于 OWASP Top 10 (2021) 标准提供代码安全审查，逐项检查 SQL 注入、XSS、SSRF、访问控制、加密失败等常见漏洞，并给出具体的漏洞代码示例  |
| [`wechat-article-deep-ingest`](wechat-article-deep-ingest/SKILL.md) | 微信公众号文章的深度摄取、批判归档与建构中枢。当用户提供 mp.weixin.qq.com 链接（单条/批量/多次少量）、要求抓取公众号全文（含hub�  |
| [`zijue-self-determination`](zijue-self-determination/SKILL.md) | 自决（技能资产自我演进审议管线·临时技能）——把一次真实的技能自调用/自审计/自修复对话固化为可复用纪律：任何自我演进（自�  |

_索引由各技能 frontmatter 自动生成。_
