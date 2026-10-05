# Qoder 技能库

91 件可复用 Qoder 技能。一个目录一件技能：SKILL.md 是入口，scripts/ 与 references/ 是伴随文件。

## 目录约定

- `<名称>/SKILL.md`：frontmatter（name、description）加正文规则，注册时只写这一个文件。
- `<名称>/scripts/`：可执行脚本。默认不运行；运行前人工审读源码。
- `<名称>/references/`：按需加载的参考资料。

## 安装

两种方式，按需要选：

1. 整目录拷贝（带脚本与参考件）：

```bash
git clone https://github.com/moonhwm/qoder-skills-hub.git
cd qoder-skills-hub
cp -r <技能名> ~/.qoder/skills/
```

2. 只注册入口（skill_manage create）：仅写入 SKILL.md，不带 scripts/ 与 references/。适合先让规则生效、暂不引入可执行件的场景。

## 安全约定

- 部分技能附带两用脚本（爬虫、负载工具、加密与压缩工具）。运行前读源码；注册与安装动作本身不执行任何脚本。
- 仓库不含凭据、令牌与个人信息。若在本仓库发现此类内容，按泄漏事件处理：立即轮换并删除对应提交历史。
- 内容完整性以 SHA3-512 梅克尔树校验，见下一节。

## 完整性校验

校验基于哈希树：逐文件 SHA3-512 叶子，两两拼接再哈希至上根。哈希族校验不依赖公钥密码学，Shor 算法对其无效，故可作为后量子完整性基线（SHA-3 为 NIST FIPS 202 标准；2026-09-27 由 256 升级 512）。

```bash
node tools/merkle.cjs verify   # 比对当前工作区与 MERKLE.json
node tools/merkle.cjs gen      # 内容变更后重新生成 MERKLE.json
```

verify 一致时打印根哈希并以 0 退出；不一致时列出差异文件并以 1 退出。

**生成序铁律**：`merkle.cjs` 以 `git ls-files` 取快照，必须是一次提交内**最后**运行的生成器——所有内容变更与派生件生成完毕、`git add` 之后再跑 `gen`，随即提交。否则清单与同提交新增文件错位（727ca43c、81b22b2 两连发实证）。

已知缺口闭合：2026-09-27 曾在 @81b22b2 登记 98 件未入树（docs/skill-graph.json、docs/evals-index.json、docs/evals/*.json、tools/gen-graph.cjs 等），已由 b6fde47、6d74644 两次补录闭合；此后 verify 一致属常态，再报差异即视为篡改或未补录，须按铁律重跑。

## 派生件

| 文件 | 内容 | 生成器 |
|---|---|---|
| docs/skill-index-zh.json | 91 件技能中文关键词与一句话摘要 | tools/gen-keywords.cjs |
| docs/skill-graph.json | 技能交叉引用图（关键词交集/直呼检测） | tools/gen-graph.cjs |
| docs/evals/*.json | 每件 3 条调度评测用例（触发语/期望/判定词） | tools/evals-gen.cjs |
| docs/sinicize-ledger.jsonl | 注释汉化台账（块级、含 token 计数） | tools/sinicize.cjs |

派生件均可重跑再生；重跑后须重新 gen 梅克尔树。

## 检索与调度评测

名录是平铺的 91 行；「干什么用哪件」请走检索层，勿逐行扫表：

| 资产 | 用途 | 消费示例 |
|---|---|---|
| [docs/skill-index-zh.json](./docs/skill-index-zh.json) | 91 件 × 8 中文关键词 + 一句摘要 | `jq -r '.entries \| to_entries[] \| select(.value.keywords + [.key] \| join(" ") \| test("舆情")) \| .key' docs/skill-index-zh.json` |
| [docs/skill-graph.json](./docs/skill-graph.json) | 57 边交叉引用图，找枢纽与邻居 | 读 `topHubs` / `edges`，从枢纽件顺藤摸瓜 |
| [docs/evals/](./docs/evals/) | 每件 3 条调度评测（触发语/期望/判定词，共 273 例） | 新增技能前先跑同名 eval 验触发面是否撞车 |

agent 用法：读 `entries.<技能名>.keywords` 与 `summary_zh` 做触发面比对；拿不准时以 evals 的触发语做回归。

## 技能索引（91 件）

| 技能 | 说明 |
|---|---|
| [admission-panel-analytics](./admission-panel-analytics/) | 考研录取面板数据的校验、模式判别与轻量评分方法论，蒸馏自新东方36校面板分析档案：三录取模式判别（α一志愿过线即录/β零调剂堡垒/γ高调剂陷阱）、调剂窗口风险六层解构与三项系统性偏见警示、S/A/B/C/D五级信源置信度、迭代收敛协议（最大… |
| [ai-persona-document](./ai-persona-document/) | '创建结构化的 AI 助手人设（persona）与角色扮演定义文档，输出 DOCX 或 PDF 格式。当用户需要以下情形时使用：（1）创建规定 AI 助手应如何行事、说话与回应的人设文档；（2）为 AI 系统定义角色扮演档案；（3）产出结构… |
| [archive-ops-kit](./archive-ops-kit/) | 压缩包作业箱：自有加密 zip（AES-256/ZipCrypto）授权爆破、两级校验防误报、批量递归解压（嵌套包+CRC校验+防zip quine）、MD5 差异比对与封存归档。当用户要处理加密压缩包/解压密码忘了/账单类 zip（美团/… |
| [arxiv-source-sentinel](./arxiv-source-sentinel/) | arXiv.org e-Print archive 论文信源标准：arXiv ID 解析与幻觉甄别、官方 API 元数据核验、预印本信源定级（载体 C0 vs 命题 C3 等价）、版本锁定与撤稿标记、标准引文生成（BibTeX/GB-T 7… |
| [autonomous-advance-ops](./autonomous-advance-ops/) | [通用技能] 自主推进运维总控（便携版）——长任务自治推进与健康监视的整合恒常件（便携版：无项目绑定，任何用户/任何模型可直接复用），恒常默认加载：新会话开场即视为在轨，免除重复加载。触发（满足任一）：①委托方说「请您自主推进」「自主推进」… |
| [autonomous-advance-protocol](./autonomous-advance-protocol/) | 常驻授权总纲——用户（委托方）在任何场景/项目下说「请您自主推进」「自主推进」「你看着办推进」或等价表述时触发：默认调用认知外骨骼+迭代收敛管家+信源语义哨兵+证据链核查员全栈，并做 skill 库检测更新与热拔插评估；若遇切到最新版的数据… |
| [av-media-ops](./av-media-ops/) | [项目技能] 音视频作战室——音视频材料的摄取、ASR 转写、信源核查与语音化产出一体管线（用户侧主权件）。当您需要查一下视频里提到的这个数据是不是真的，或者需要把视频里的话都整理出来时，系统将调用 ffmpeg 探针与抽取（scripts… |
| [bidding-docs-ops](./bidding-docs-ops/) | 投标/应答文本书写作战技能——三册制应答文件骨架、点对点应答矩阵、承诺函与补正文书范式的模板化写作与形式风险前置防线。触发（满足任一）：①用户说「写标书」「投标文件」「应答文件」「技术标」「商务标」「承诺函」「点对点应答」「偏差表」「补正说… |
| [bidding-ops](./bidding-ops/) | 投标/招标一体作战技能——评分博弈分析（规则解析/报价推演/非价格顶格/情景模拟）+ 应答文书写作（三册骨架/点对点矩阵/承诺函与补正范式/形式风险前置防线）联合调用。触发（满足任一）：①用户说「投标」「招标」「标书」「评标」「综合评分法」… |
| [claims-deep-audit](./claims-deep-audit/) | 深度核查某机构、项目、导师或产品的对外宣传性主张是否名副其实。当用户需要核查、打假、评估水分、判断"是否靠谱"、对比宣传与实质、或进行 due diligence（尽职调查/深度核查）时使用，例如"某校是否真有X方向""某实验室的X平台是否… |
| [cn-housing-finder](./cn-housing-finder/) | 国内租房/买房房源初筛与结构化——web_search 初筛 + web_open_url 抓详情 + 本地解析器出对比表。当用户要"找房/租房/买房/房源对比/看房清单"时触发。整合自 zhangchushu/cn-housing-mcp… |
| [cognitive-exoskeleton](./cognitive-exoskeleton/) | 将 agent 集群作为用户的认知外骨骼，由用户输入意图与选择题式判断，agent 执行调研、推导、落地与证据链构建。适用于数学方法选择（涵盖拉普拉斯变换、傅里叶变换、重整化群、线性代数、变分、概率统计的选用与防误用）、函数拟合（依据幂律/… |
| [commute-school-optimizer](./commute-school-optimizer/) | 通勤×择校综合寻优技能。当用户在择校（学校选择）、居住/就业选址、学区房决策视野下需要量化交通通勤成本并参与多目标排序时使用。触发词：通勤、通学、择校、学校选择、上学路径、交通成本、火车票、高铁、12306、航班、通勤时间、学区房、时间成本… |
| [consignment-intake-ops](./consignment-intake-ops/) | [项目技能] 交割接收运维——函询交割的统一接收与台账：子代理派单/跨会话交接/技能写回/回执摆渡等一切交割事项的登记、状态机（发出→已收→验收中→已交割/退回+发件方撤回）、总览看板与逾期扫描。触发（满足任一）：①用户说「交割」「接收情况… |
| [coordination-letter](./coordination-letter/) | > |
| [corpus-value-distiller](./corpus-value-distiller/) | 已获取语料库（公众号文章、批量网页、文档集合等结构化 JSONL/索引）的价值榨取工作流。当用户要求"榨干这批语料/这批文章还有什么用/蒸馏进技能/语料价值测绘/把这批内容整合进技能库"时触发；覆盖三相位——价值测绘（主题聚类+归宿映射）、… |
| [cron-task-forge](./cron-task-forge/) | [项目技能] 定时任务（cron/提醒/自检任务）的创建、审计与降频规范。当用户要求创建/修改/暂停/删除定时任务、定时提醒、每日/每周自检、凌晨自检、月度监测，或审计现有定时任务的成本与必要性时使用；任何其他技能要内嵌定时行为（如每日自检… |
| [cross-session-workflow-bridge](./cross-session-workflow-bridge/) | 项目接力桥是继续项目或加载项目环境时首先触发的跨会话工作流衔接伞形技能。新对话中提及继续项目、加载项目环境、继续上次进度、把之前的需求文档和数据转交给擅长Python的那个AI模型去跑或处理数据分析的活儿即命中。规程为读取双索引（uploa… |
| [daily-life-autopilot](./daily-life-autopilot/) | 每日例行生活事务自动化编排——凭证哈希链自检、通勤火车票/机票查询（美团官方通道）、POI 双通道查询（高德+百度）、每日领券、价格监控提醒。当用户要求"每日例行/每天自动执行/定时任务/通勤查票/查火车票机票/领券提醒/每日检查/龙虾KI… |
| [data-viz-gen](./data-viz-gen/) | 从 JSON 数据生成自包含的 HTML/SVG 信息图，支持 KPI 统计卡片、分组柱状图对比、流程图和混合仪表盘四种类型，提供 8 套配色方案和 |
| [day-sundial-ops](./day-sundial-ops/) | 日晷场是白天工作台的轻量纪律，与负责睡后自治玩耍的夜场（「夜场件」）相对，专管醒着时的快速小活：涵盖随手问答、查明天高铁发车等即时查询、小段实验、抽题考考与刷题陪练，以及记一笔扫码付款等当日杂务。系统识别「日晷场」「白天场」「日场」「随手做… |
| [diffusion-dynamics-extension](./diffusion-dynamics-extension/) | 演化推演器是动态演化与干预效果量化扩展技能。当已有静态评估结论、需要回答“随时间/空间如何演化”“不干预会怎样”“干预ROI多大”，或需针对具体场景（如在主干道设个限行区）对缓解拥堵的效果和投入产出比能估算一下时启用。覆盖信息/舆情传播预测… |
| [doc-archive-ingest](./doc-archive-ingest/) | 网盘分享链接文档归档管线：解析坚果云公开分享链接与百度网盘分享链接（pan.baidu.com/s/）、枚举目录、带节奏批量下载、生成出处登记册（含字幕组式版权注记与文档摘要）、PDF 水印识别与合规去水印（仅限用户已购/自有文档）。百度网… |
| [doc-image-solver](./doc-image-solver/) | [项目技能] 拍图解题全管线：试卷/文档照片 → 高精度转写文档 → 逐题解读作答 → 迭代收敛。当用户上传试卷/讲义/文档照片要求转写为可读文档、解读题目、给出答案或解题时使用；覆盖手写体存疑标注、可计算答案的数值核验、收敛判定。触发词：… |
| [eastmoney-rumor-sentinel](./eastmoney-rumor-sentinel/) | [项目技能] 东财传闻哨兵——东方财富股吧公开面的传闻采集、词面三档判级与白话呈报。触发（满足任一）：①用户说「东财」「东方财富」「股吧」「传闻哨兵」「扫一遍股吧」「吧里在传什么」「市场情绪」或等价表述（含语音变体如「东财传闻」「古吧」，不… |
| [epsilon-delta-proof-sovereign](./epsilon-delta-proof-sovereign/) | > |
| [evidence-chain-verifier](./evidence-chain-verifier/) | 自修正信源 + 可证伪流程证据链 + 抗幻觉核查框架。定位为证据登记、抗幻觉校验、可证伪断言登记、信源分级与公开复核链接：当用户询问财务造假相关的爆料视频是从哪来的、有没有实锤，或要求信源核查、证据链梳理、事实查证、抗幻觉校验、可证伪断言登… |
| [exam-isolation-ops](./exam-isolation-ops/) | [项目技能] 模拟考场隔离协议（考场隔离协议 v1.1）——用结构上相互隔离的子代理角色跑闭卷模拟考/盲考/真题演练/备考抽查：出题打包（物理剥离答案+泄漏扫描+sha256[:16] 指纹）、新鲜子代理考生闭卷单遍作答、双参考解答制作人 … |
| [extpool-furnace-ops](./extpool-furnace-ops/) | [项目技能] 外池压测炉运维——用外部模型池（GLM 礼赠池、华为码道/CodeArts、华为云 ModelArts、阿里百炼、火山方舟、智谱等 MaaS 接口）对技能/命题/密码强度等对象做目的导向的对抗性压测与燃烧时的安全作业规程。触发… |
| [fusion-program-audit](./fusion-program-audit/) | 高校核聚变方向"聚变期权"真伪核查与考研择校评级。当用户需要判断某校宣称的核聚变/聚变/等离子体物理方向是实质布局还是标签嫁接、核查托卡马克/仿星器/直线装置真实状态、考研择校/读研择校中核查导师方向与学科实力、识别实验室核查/虚假宣传时使… |
| [gitlab-cli-guide](./gitlab-cli-guide/) | 提供 GitLab 命令行工具（glab）的完整参考与自动化脚本，涵盖超过30个子命令，包括合并请求创建与审查、CI/CD流水线调试、Issue管理、仓库操作和认证配置等核心工作流。适用于通过终端管理MR/Issue、调试CI失败任务、批量… |
| [goal-child-ops](./goal-child-ops/) | 赤子续行（目标系统×尼采孩子姿态的融合纪律·临时技能）将goal-mode的目标状态机（objective/verifier/迭代/complete/blocked）视为棋盘规则，以尼采三种变形的第三阶「孩子」（游戏、创造新价值、神圣的肯定… |
| [grad-advisor-outreach](./grad-advisor-outreach/) | 学术导师套磁与外联协议（AAPP, Academic Advisor Profiling Protocol）。用于硕士/博士申请中的导师筛选、约束识别、套磁信撰写与发送跟踪。触发场景：用户要联系导师/教授、写套磁信或 cold email、… |
| [grad-path-scorer](./grad-path-scorer/) | [项目技能] 升学路径加权评分引擎（硕士择校 × 申博衔接特化）。当用户需要评估硕士院校选择、量化「学术断头路」风险、建模申博衔接能力、模拟导师指导舒适度对读博意愿的扰动漂移、计算反悔成本非线性放大、对院校做多维加权排序并输出置信度标注时使… |
| [hifi-integration-umbrella](./hifi-integration-umbrella/) | 高保真整合伞（临时技能）——将名录实载技能（件数以 references/roster.md 当时实载为准）高保真整合为一张协奏目录与统一调用规程：引用不复制、逐件法定描述蒸馏、冲突仲裁次序、日落条款、随锚扩编。触发（满足任一）：①用户说「… |
| [home-network-troubleshooter](./home-network-troubleshooter/) | 家庭/小型办公网络故障的分层定位与修复程序，特化华为坤灵 ePlusSoHo 多 AP 组网（AP162 面板、AC 管理）。当用户报告"电脑网页打不开但 QQ/微信能上""手机能上网电脑不行""同一 WiFi 下部分设备断网""网页 ER… |
| [humanizer-zh](./humanizer-zh/) | 去除中文文本的 AI 生成痕迹并重建真实感，覆盖写作与改稿双场景。当用户请求润色、编辑、改写文本，或提及去除 AI 味/AI 痕迹、让文本更人性化、听起来不像 AI 写的、写得干练一点、调整叙事动机或说话位置时触发。三层诊断（义理/考据/辞… |
| [intl-case-intf](./intl-case-intf/) | 国际法案例接口件（临时技能）——CJEU CELLAR 官方 SPARQL 与 ECtHR HUDOC 事实型公开端点的只读薄封装 + SQLite FTS5/BM25 本地索引，统一引证契约 {title,url,snippet,cour… |
| [iteration-convergence-ops](./iteration-convergence-ops/) | 长周期项目在多轮对话中的版本迭代管理方法论：持久化优先（每轮必落盘并 ls 核验，杜绝'声称完成但未落盘'）、版本号诚实（git 风格版本语义与变更日志，禁止跨版本号夸大）、批判-解构-重整-收敛四拍元循环（含致命错点表与收敛标准）、平台版… |
| [k3-channel-ops](./k3-channel-ops/) | [项目技能] K3/集群甲通路搭建与运维——自研搭建并优化跨会话消息通路（「通道库」 总线），使所有 K3/集群甲工作时能及时变革相关动作。触发（满足任一）：①用户说「通路」「搭建通路」「优化通路」「通道」「总线」「broadcasts」「… |
| [k3-everything-archive](./k3-everything-archive/) | K3 一切事务穷举总包·洁版（私藏归档件，全量脱敏后重制）——单容器穷举：73 技能(便携五件最新同源)+MCP 接口层+安全三件套+upload 全域(注册处/两代 dist/金融项目)+output 事务全域(全部研报/docx/pdf… |
| [k3-interaction-ops](./k3-interaction-ops/) | > |
| [k3-territory-studies](./k3-territory-studies/) | > |
| [k8s-cluster-ops](./k8s-cluster-ops/) | 通过 kubectl 命令行工具管理 Kubernetes 集群，执行查询资源状态、部署应用、查看日志、调试容器、切换上下文和监控集群健康等操作。适用于日常运维、发布和故障排查。当用户询问集群状态、Pod/Deployment信息、查看日志… |
| [livability-audit-swarm](./livability-audit-swarm/) | 宜居文档审计蜂群负责城市宜居度/舒适度文档的蜂群审计与直接修复编排。当用户要求审计、核查、修复或治理「城市宜居度/住房压力/宿舍舒适度/就读舒适度」有关文档（评分系统文档、报告、配置、数据文件）时使用；也用于把宿舍舒适度等暂缓项纳入远景排期… |
| [long-table-harvest-ops](./long-table-harvest-ops/) | 长表逐字收割完整性规程——对超长网页表格/名单（数百至数千行：官方公示名单、成绩表、职位表、目录全表等）做逐字（verbatim）收割时的防伪造完整性协议：干净上下文子代理分段收割、抓后立即连写（每块≤120行）、源被压缩隐藏即停写重抓、绝… |
| [medical-career-transition](./medical-career-transition/) | 医学背景者的转行与就业特化决策支持。当用户讨论医学转行、医学生就业、医生转行、医学生职业规划、离职、规培退出、医学硕士/博士不进临床的出路时触发；覆盖 MSL（医学联络官）、医学事务（MA）、医学写作、医学编辑、CRA、CRC、医药代表/器… |
| [medical-malpractice-criminal-review](./medical-malpractice-criminal-review/) | 医疗事故刑事案件特化审查。用于评估医疗行为是否构成医疗事故罪、非法行医罪或过失致人死亡罪，输出责任比例、责任等级、罪名建议、处置方案及司法风险提示。基于刑法第335条、第336条、第233条、《医疗事故处理条例》及真实司法判例校准。触发场景… |
| [multi-dimensional-option-scoring](./multi-dimensional-option-scoring/) | 多维打分参谋是在不确定性环境下对多个选项（如择校、择业、投资标的、技术路线、软件供应商等）进行量化排序与风险分级的决策框架。适用于需对多候选对象（如挑三家软件供应商）进行列表对比、根据价格、售后与稳定性等指标设定不同权重并加权打分，或需构建… |
| [night-playground-ops](./night-playground-ops/) | 项目工作区甲运维——把「用户睡眠时段的自治玩耍/兴趣研究」这一目标本身内置化为自我维持运营的技能：目标即本体，开园→预算报备→五拍玩耍→停车线→晨报→留眠交接，闭环自续。触发（满足任一）：①用户说「项目工作区甲」「自己玩」「今夜自治」「你睡… |
| [notary-legal-upload](./notary-legal-upload/) | 涉外公证办理、法律文书签署上传、电子证据哈希/区块链存证三合一范式。当用户需要办理翻译公证（毕业证/学位证/成绩单等涉外学历公证）、海牙认证（附加证明书）、留学/移民材料公证；需要签署并上传带法律效力的文件（个人数据处理同意书、数据同意书、… |
| [omni-exhaust-research-ops](./omni-exhaust-research-ops/) | 穷举研究总署——对任何复杂问题以「任何可能性穷举」方式做研究尽调、方案整合与统一调配的通用编排技能（无项目绑定，任何用户/任何模型可直接复用）。触发（满足任一）：①用户说「穷举」「穷尽可能性」「全面方案尽调」「所有方案都看看」「exhaus… |
| [output-verdict-gate](./output-verdict-gate/) | [项目技能] 输出审议闸——实质性输出发出前的控辩对抗审议管线：输出者三轮自问留痕 → 辩方律师团（首席律师+调查员）结构性反对 → 评审团 5 席盲评 4/5 超级多数 × N 轮 → 监管门事后程序审查 → 登记归档。内置认罪认罚检测器… |
| [pan-exhaust-dispatch](./pan-exhaust-dispatch/) | 穷举统调署（便携泛化版）是对任何复杂问题以「任何可能性穷举」方式强制调用在场接口做研究尽调、方案整合与统一调配的元技能（薄壳设定：研究引擎权威在 omni-exhaust-research-ops，本件负责统调矩阵与跨模型便携壳）。满足以下… |
| [pangu-enforcement-bureau](./pangu-enforcement-bureau/) | [项目技能] 强制裁判落地执法局——充当暴力执法机构，强制将华为强制裁判(PanGu)模型纳入一切模型选型/调度/路由决策的候选集考量，并对「遗漏强制裁判候选」执行执法登记。触发（满足任一）：①任何模型选型、蜂群派发、MaaS 路由、外脑席… |
| [persona-iteration-loop-ops](./persona-iteration-loop-ops/) | [项目技能] 人设迭代循环总署——以中性化迭代循环引擎（IterationLoopV11-neutral）为核心，融合六件源技能的融合件：虚构成年人设建模（人设定义文档 + 记忆锚点提取）、中性结构化感知文本的多轮迭代生成（深度1-3、指令… |
| [persona-memory-anchors](./persona-memory-anchors/) | > |
| [persona-modeling-kit](./persona-modeling-kit/) | '人设建模双引擎套件（doc×anchors 合并件）：正向从需求创建结构化 AI 人设/角色定义文档，逆向从参考材料提取人格记忆锚点生成可复用人设档案，输出 DOCX（默认）/PDF/PPTX/Markdown。适用情形：（1）创建规定 … |
| [phys-ai-mat-conf-radar](./phys-ai-mat-conf-radar/) | 物理×AI×材料领域顶会排期雷达，重点覆盖等离子体物理学与聚变工程化应用（APS DPP、IAEA FEC、EPS、SOFT、IEEE ICOPS、ISFNT、ANS、MRS、TMS、NeurIPS/ICML/ICLR 及 AI4Scien… |
| [plugin-datasource-ops](./plugin-datasource-ops/) | [项目技能] 插件与数据源调用范式——全会话插件接口的统一调用纪律、域路由表、实证 Pitfalls 与持久化规程。触发（满足任一）：①任务涉及调用任何已安装插件或 agent-gw 数据源（元典法律、scholar、金融数据源、生物/材料… |
| [portable-sync-ops](./portable-sync-ops/) | [项目技能] 便携件同步总署——一切「粘贴即装」引导件与整包便携（.skill）的登记台账与同步更新纪律。触发（满足任一）：①用户说「便携件」「粘贴即装」「引导件」「异模型能用吗」「便携化」「同步更新」「portable」或等价表述（含语音… |
| [ppp-city-verdict-audit](./ppp-city-verdict-audit/) | 城市/地区结论的 PPP 范式复核台（v1.3，含基准城支配性检验、快照纪律与阈值校准状态声明）（购买力平价=工资/房价购买力双锚）。当需要系统性复核既有「淘汰/候选/否决」城市结论清单、核查飞行与铁路通勤真实成本、并招募多代理 swarm… |
| [qr-visual-rescue](./qr-visual-rescue/) | > |
| [quant-frontier-lab](./quant-frontier-lab/) | 前沿算法实验台——教学级量化算法工具箱，覆盖 Gale-Shapley 志愿填报匹配、PSM 倾向得分/因果推断、DID 前置评估、SIR 传染模型（Gillespie/链二项式/边基分区）、谱半径免疫、MAML/Reptile 元学习玩具… |
| [quota-guard-ops](./quota-guard-ops/) | [项目技能] 额度守护运维——自主检测额度包/月订阅消耗信号，按 Q0–Q3 四档程式自适应运作，不逃逸前提下高性能输出。触发（满足任一）：①出现 quota 耗尽/加油包提示/「额度不足 去升级」徽标类信号；②用户说「额度」「加油包」「q… |
| [registry-knowledge-ops](./registry-knowledge-ops/) | [项目技能] 注册处知识库——技能迭代注册处（/mnt/agents/upload/skill-iteration-registry/）的全文检索、锚链调阅与 INDEX 分区导览（用户侧主权件）。触发（满足任一）：①用户说「查注册处」「台… |
| [release-gate-audit](./release-gate-audit/) | [项目技能] 外发/公开发布的事前审查闸门（v2.5.8 代码外发禁令的操作化）。当任何内容要流出沙箱——GitHub 建仓/推送、网盘分享、网页公开发布、给第三方发送文件——必须先过本闸门：五道漏洞审查（范围/时限/撤销/逃逸面/红线）+… |
| [retirement-guard-ops](./retirement-guard-ops/) | 退休保卫局——审计并压缩「阻止用户退休的注意力债主」，把自治系统对真人的打扰降到每周一页纸。触发（满足任一）：①用户说「退休」「保皇党」「谁在阻止我退休」「别老烦我」「一周只打扰一次」或等价表述（含语音变体）；②自治生态（cron/子代理/… |
| [rumor-chain-verifier](./rumor-chain-verifier/) | 本技能为复合传言的逻辑链拆解与断裂定位核查法，中文名传言拆链核查员。当用户提供看似环环相扣的网传说法并要求核实真伪时适用，涵盖政策类传言如上面发文要求XX、社会类传言如XX潮来了，以及附带数据或文件的截图、短视频与自媒体文章。同时用于核查他… |
| [rust-browser-pilot](./rust-browser-pilot/) | 基于 Rust 开发的无头浏览器 obscura，采用单二进制内嵌渲染引擎，无需依赖系统 Chrome，通过 CDP 协议执行页面抓取、DOM 提取、截图、批量采集与反检测抓取。工具启动迅速，内存占用约 30MB，适用于网页抓取、自动化与 … |
| [sandbox-project-ops](./sandbox-project-ops/) | 跨会话长期项目的沙箱运维规程：修复 shell(root) 与 ipython(uid 999) 双 uid 写权限冲突、沙箱重置后重建 pytest/git/pre-commit 环境（含 git safe.directory 所有权问题… |
| [sector-stock-rumorchain-pipeline](./sector-stock-rumorchain-pipeline/) | 行业研报+个股分析+舆情谣言链核查+东财股吧传闻采集的一体化管线（复合编排技能，已并收东财传闻哨兵本体）。当用户要求「生成某行业（如消费电子，可替换）的研报，并就某只股票（如 002681，可替换）进行相关分析，相关舆情走谣言链查询」时使用… |
| [semantic-oncology-ops](./semantic-oncology-ops/) | [项目技能] 语义肿瘤防治运维——长对话上下文压缩避免、集群甲退化会话救活（严重退化下写出最小交割文档）、语义污染的癌症分期防治（早期预防/中期遏制/晚期治疗/转移防控/复发监测）、「通道库」跨模式交流通道、冗余自审计与定期运维。触发（满足… |
| [senior-rumor-check](./senior-rumor-check/) | 银龄传言核查员——面向长辈（老年用户）的传言核查适老化前端封装。把 rumor-chain-verifier 的拆链定断结果翻译成大白话、一句话结论先行的核查回复，并在核查后主动给出：追问三句（帮长辈继续摸清传言来源与动机）、操作建议（查什… |
| [seo-copywriting-guide](./seo-copywriting-guide/) | 通过 12 步结构化工作流生成搜索引擎优化内容，产出一篇包含完整草稿、备选标题、Meta描述、FAQ结构化内容及CORE-EEAT自评清单的SEO文章。当用户提出“写一篇SEO文章”、“帮我写博客”、“创建针对某关键词的内容”、“撰写产品描… |
| [skill-dispatch-hq](./skill-dispatch-hq/) | [项目技能] 技能调度总署——全部技能与公用数据库级插件能力的统一台账、集中调度分配、函询交割、计时器任务与授权法典的恒常总控件。触发（满足任一）：①用户（委托方）说「统一调度」「集中管理分配」「调度总署」「技能调度」或等价表述（含语音/同… |
| [skill-library-auditor](./skill-library-auditor/) | 技能库（SKILL.md 仓库）全量审计工具。当用户需要盘点/审计/复核技能库、检测中英文镜像技能对、发现共享脚本冲突、校验 SKILL.md frontmatter 规范（name 与目录一致性、YAML 结构错误、缺 license/d… |
| [skill-refresh-ops](./skill-refresh-ops/) | [项目技能] 技能刷新运维——「重新加载并刷新（更新下载）任何可能所需技能」流程的固化件：安装位可写性预检、全库盘点与版本漂移扫描、点名技能会话内热加载、全部已装载插件通道强制健康检查（每通道一次最小调用，自行研究调用方式）、dist 包源… |
| [skill-reinstall-ops](./skill-reinstall-ops/) | [项目技能] 技能重装与分发运维——dist 目录技能包一键重装入安装位：预检可写性、逐包解压、旧版 .bak 备份、版本核验、零伪装如实报告；另管技能包 pip 化分发（把技能集合打成 wheel，用一串链接 PEP 508 直引安装）。… |
| [skill-version-ops](./skill-version-ops/) | [项目技能] 技能版本流转总署——单件三模式共库（version_flow.py）：①refresh-check 刷新运维（可写性预检/全库盘点与版本漂移扫描/点名技能热加载/插件通道强制健康检查/dist 包源搜索/哨兵核查/通报落库）；… |
| [software-testing-guide](./software-testing-guide/) | 建立全面的软件QA测试流程，包括制定测试策略、按照Google AAA标准编写测试用例、执行测试计划、使用P0-P4分级追踪缺陷、计算质量指标（如通过率与覆盖率）以及生成每日/每周进度报告。提供完整的文档模板，可直接用于外包团队交接，并实施… |
| [source-semantics-sentinel](./source-semantics-sentinel/) | 信源语义哨兵是融合信源验证通道与上升机制、投毒甄别、语义精度利刃与最小作用量路由的信息入口哨兵。当用户面对未听过的大V号发布的消息询问能否信，或导出竞品分析数据发现参数看着特别别扭需排查是否动过手脚时，本技能提供信源验证、来源核查与信源评级… |
| [stat-verdict-ops](./stat-verdict-ops/) | [项目技能] 统计裁决室——通用统计检验落地引擎（用户侧主权件，先证伪后裁决）。触发（满足任一）：①用户说「统计检验」「显著性」「p 值」「t 检验」「卡方」「U 检验」「KS」「Fisher」「比例检验」「效应量」「置信区间」「这组数据有… |
| [travel-commute-planner](./travel-commute-planner/) | 出行与通勤的综合规划中枢（热插模块化整合 amap-travel-skill 与 commute-school-optimizer；v2.0 全量收编 集群甲五通道）。当用户需要查询火车/高铁精确票价（12306官方接口免key）、航班直飞… |
| [unified-decision-suite](./unified-decision-suite/) | 统一决策套件是运行于四层架构（数据/证据/引擎/交付）之上的路径级与院校级决策薄编排层。适用于统一决策、决策管线、路径决策、院校决策、锁校匹配、志愿填报决策、帕累托前沿与 NSGA-II 三目标分层、hrank 分层序列、MCTS 时序决策… |
| [up-distill-ops](./up-distill-ops/) | > |
| [vision-intake-ops](./vision-intake-ops/) | [项目技能·强制入口] 视觉输入总门——图像输入统一路由+共享识读底座（伞件，三件本体不复制）。【强制】凡消息含图片/截图/照片（含静默上传、图文混排）必先经本件路由，禁绕过直读/凭印象猜。触发（任一）：①上传图片不知走哪件（拍题/文档/二… |
| [vision-ocr-pipeline](./vision-ocr-pipeline/) | 图像识读管线负责截图与长图的识读及跨平台传输。采用本地OCR双引擎分工架构，由RapidOCR执行全文识别并交由tesseract完成数字核验；支持按字高阈值压图以降低token消耗，对超长图片进行长条切片处理，最终生成跨AI环境可用的自包… |
| [web-security-audit](./web-security-audit/) | 基于 OWASP Top 10 (2021) 标准提供代码安全审查，逐项检查 SQL 注入、XSS、SSRF、访问控制、加密失败等常见漏洞，并给出具体的漏洞代码示例与修复方案。当用户需要代码安全审查、安全加固、渗透测试辅助，或提及 OWAS… |
| [wechat-article-deep-ingest](./wechat-article-deep-ingest/) | 微信公众号文章的深度摄取、批判归档与建构中枢。当用户提供 mp.weixin.qq.com 链接（单条/批量/多次少量）、要求抓取公众号全文（含hub页文中链接递归）、缓存为结构化命名的 md/docx/pdf/快照并自主归档、对招商宣传式… |
| [zijue-self-determination](./zijue-self-determination/) | 自决（技能资产自我演进审议管线·临时技能）——把一次真实的技能自调用/自审计/自修复对话固化为可复用纪律：任何自我演进（自名、起名迭代、主权审议、技能自创自改）无论演进发生或自然演化出什么结果，都必须诚实记录并将全部结果广播。触发（满足任一… |

## 维护记录

| 日期 | 事项 |
|---|---|
| 2026-09-26 | 初版入库：91 件技能（6375adc） |
| 2026-09-26 | 修复 README 三十处三字节汉字截断（bf55995） |
| 2026-09-26 | README 重写为简体中文；脚本注释批量简体汉化；注入 SHA3-256 梅克尔树 |
| 2026-09-27 | 梅克尔树升级 SHA3-512；连通计划/陪跑方案/跨境总线研究/四平台内容包入册；调度度量与描述手术留痕 |
| 2026-09-27 | 并入远端协作者 README 增补（检索与调度评测节、生成序铁律、缺口闭合说明，023b4e8 线） |

## 来源与署名

技能来自作者自有工作区资产。再分发请保留目录结构与本说明；各技能正文内的署名与版本记录以其 SKILL.md 为准。

## 许可证

- 代码与内容：**AGPL-3.0-only + SSPL-1.0 分层组合**（机主 2026-10 裁定）——主体见 LICENSE（GNU AGPL v3.0 官方全文，SPDX: AGPL-3.0-only）；作为网络服务向第三方提供时叠加 SSPL-1.0 附加条款（SPDX: SSPL-1.0-addendum，见 LICENSE.SSPL-ADDENDUM）。论证：《ima与A2A约束下开源协议补充论证》（https://www.kdocs.cn/l/cboAFwILF079 ）
- 协议变更边界：本仓库 2026-10-03 前的历史版本按获取时点所载声明继续使用（当时根目录未随附 LICENSE，再分发条款以「来源与署名」节为准）；此后代码适用分层组合（增量叠加、双许可并存），已有 fork 不受追溯；子目录内嵌第三方件（如 web-security-audit/LICENSE，MIT）按其自带协议
- 网络服务化边界：仅将本仓代码作为网络服务向第三方提供时，触发第二层 SSPL-1.0 服务端全量开源义务；内部使用仅按第一层 AGPL-3.0-only 执行
