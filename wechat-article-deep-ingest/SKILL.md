---
name: wechat-article-deep-ingest
description: 微信公众号文章的深度摄取、批判归档与建构中枢。当用户提供 mp.weixin.qq.com 链接（单条/批量/多次少量）、要求抓取公众号全文（含hub页文中链接递归）、缓存为结构化命名的 md/docx/pdf/快照并自主归档、对招商宣传式报道沥干水分、甄别「规划≠项目落地≠产业升级」、S级等信源标注为结构化指针CSV、对文章做批判分析/精确转载/第一性原理解构与再建构、提取人文风貌/特色产业/稀土/黑色金属/有色金属/能源/新兴产业/工程化线索并落地岗位指向时使用。典型触发语："帮你摄取这批公众号链接""公众号文章归档""招商文章沥干""规划落地甄别""批判分析这篇文章""准公众号范式"。中文名：公众号深摄批判台。v1.0（2026-08-25，修改人：Orchestrator/Kimi K3，源项目 med-career-transition-L + single well 公众号实战）。
---

# 公众号深摄批判台（wechat-article-deep-ingest）

> v1.0 ｜ 2026-08-25 ｜ 修改人：Orchestrator（Kimi K3）
> 生态位：**摄取与批判**（本技能）→ 信源通道分级引用 source-semantics-sentinel → 证据链登记引用 evidence-chain-verifier → 认知外骨骼三纪律贯穿（cognitive-exoskeleton：选择题式交付/证据链 conf 三级/top3_likely_wrong）。只衔接不重造。

## 五条铁律
1. **不编造正文**：抓取失败如实留痕（403/超时/需登录），摘要只基于实际获取内容，未获正文标"未获取正文"。
2. **规划≠落地≠升级**：凡规划文件/招商宣传中的产业表述，一律经三分法甄别（见 references/source-grading.md §3）后才可引用为事实；"有规划"绝不写成"已布局/已升级"。P 态必须子分类 P-slogan/P-instrumental（slogan-discrimination.md 七维判定）；**P-slogan 不得作为落地判断证据、不得进入岗位指向表**。
3. **招商宣传必沥干**：投资指南/招商公众号来源的内容默认 conf≤C，数据点须找官方/统计口径交叉后方可在分析层使用。
4. **诚实标注**：每篇归档必带【发表日期|抓取日期|来源号|关键链接|局限|适用度|skill版本】七元组。
5. **每读必留问**：每次摄取批次结束，产出 ≥3 个待复核问题（带推翻方法）写入批次报告。
6. **每篇必建档**：每篇文章（含历史已归档）必须有独立案例记录（cases/case_<slug>.json + cases_index.csv + cases.py 聚合），诚实记录判定依据与局限，人可读可追加。

## 路由表
| 用户信号 | 路由 |
|---|---|
| 给链接（单/批量/多次少量）要抓取 | 摄取流程 → [references/fetch-protocol.md](references/fetch-protocol.md) |
| 超长文截断/分片/回补队列 | [references/long-text-slicing.md](references/long-text-slicing.md) + scripts/truncation_check.py / slice_text.py |
| 要归档/缓存/指针CSV | [references/archive-schema.md](references/archive-schema.md) + scripts/pointer_csv.py |
| 要批判/沥干/甄别/解构 | [references/critique-frameworks.md](references/critique-frameworks.md) |
| 官媒规划/口号式宣传/「XX战略能否落实」 | [references/slogan-discrimination.md](references/slogan-discrimination.md)（P 态子分类+落地率回测） |
| 要岗位指向/产业线索提取 | critique-frameworks.md §4（线索→岗位对应表） |
| 要深化某领域（餐饮创业/医学/金融/审计/物理/AI/CS） | [references/interfaces.md](references/interfaces.md) |
| 要高校-地区-产业联系（人口束缚） | interfaces.md §2（接续西安/深圳既有研究） |

## 工作流（六阶段）
0. **批次接收**：链接去重规范化（scripts/link_dedup.py）；多次少量提供时按「准公众号范式」累计成批（fetch-protocol.md §4）。
1. **摄取**：web_open_url 直取（mp.weixin.qq.com 实测可达）；hub 页（目录文）提取文中链接递归二层；失败留痕不编造。节奏：每批 ≤10 条，批间隔可调。
2. **缓存**：四形态——结构化 md（主）/docx（md2docx）/pdf（可选）/快照（原始 HTML 摘要 JSON）；命名规范与目录树见 archive-schema.md。
3. **分级与指针**：每篇打信源级（A/S/B/C/D/E+通道阶梯）入指针 CSV（scripts/pointer_csv.py）；招商宣传自动触发沥干标记。
4. **批判层**：按 critique-frameworks.md 产出——批判分析/精确转载（带原文锚点）/第一性原理解构与再建构；产业线索→岗位对应表落地。
5. **归档与留痕**：自主归档（目录树+索引更新）；每篇 ≥3 待复核问题；交接段（handover 条目模板）。

## 技能开发进展声明（诚实标注）
- 实测基线（v1.1 更新）：web_open_url 直取 6/6 成功（含 hub 页）；browser 通道遇验证码墙 0/1（已入失败形态表）；**curl 源码解析=元数据辅助通道 M**（pub_date/account_id 3/3，eval-1 baseline 实证）；**未验证**：图片/视频提取、付费墙、长文截断边界、hub 递归稳定性。
- GitHub 辅助开发线索见 interfaces.md §3（候选工具登记，未集成，用前须评估许可证与合规）。

## 版本与修改痕迹
| 版本 | 日期 | 修改人 | 变更 |
|---|---|---|---|
| v1.0 | 2026-08-25 | Orchestrator（Kimi K3）/ 项目 med-career-transition-L | 首版：摄取+缓存+分级指针+沥干+三分法甄别+批判框架+岗位指向+七接口 |
| v1.1.1 | 2026-08-25 | Orchestrator（Kimi K3），依首批63篇实战（7批次并行） | pointer_csv --path 别名修复（批次5发现文档/flag不符）；INDEX 分片合并建议（并发覆盖损失实证）；通道M桌面UA技巧登记（批次3）；web_open_url 长文截断边界实证（>7000字系统性截断→通道M js_content 兜底，批次5） |
| v1.2 | 2026-08-25 | Orchestrator（Kimi K3），依用户原则审查（长沙4433口号案例） | 新增 slogan-discrimination.md（P-slogan 七维判定+落地率回测+岗位指向隔离）；铁律6每篇必建档（案例库.case.json/cases_index.csv/cases.py 三形态） |
| v1.2.1 | 2026-08-25 | Orchestrator（Kimi K3），依74篇锂电hub子篇全量摄取（批次8-15） | link_dedup.py 待支持长链形态（?__biz=&mid=&idx=&sn=）；`&scene=21#wechat_redirect` 参数触发 web_open_url audit rejected（去除后10/10成功，批次12实证）；通道M验证码墙呈波动性（批次3成功 vs 批次8-15全墙）——摄取计划须容忍元数据延迟回刷；长文截断边界复验（>7000字约50%截断率） |
| v1.2.1a | 2026-08-25 | Orchestrator（Kimi K3），attribution勘误 | slogan-discrimination.md：4433判断出自龙振波同学（非L同学） |
| v1.3 | 2026-08-25 | Orchestrator（Kimi K3），依用户"优化漫长等待自卡死"指令+回刷双组实战 | 新增 long-text-slicing.md（截断三信号检测/分片规程/回补队列反空转铁律/长短链风控差异实证）；scripts+truncation_check.py、slice_text.py（均实测）；fetch-protocol 通道阶梯修订（长链仅正文/短链才给元数据）；禁止后台轮询空转——回补一律探活+批处理 |
| v1.1 | 2026-08-25 | Orchestrator（Kimi K3），依 skill-creator swarm 评估（eval-1 六安/长丰/北京三篇，comparator 判 with_skill 胜，analyzer P1-P6） | 通道M（curl源码元数据，合规四前提）；批判第五形态「跨篇综合」；three_state 分号组合；snapshot 必填字段；内部一致性/转录保真/时效三检查层；系列触发；术语对齐 |
