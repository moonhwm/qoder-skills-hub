# 深化接口与生态衔接（interfaces）

> v1.0 ｜ 2026-08-25 ｜ 修改人：Orchestrator（Kimi K3）

## §1 领域深化接口（预留挂载点，按需激活）
| 接口 | 触发信号 | 衔接动作 |
|---|---|---|
| 餐饮创业 | 文章涉餐饮/食品产业/消费赛道 | 提取→创业可行性框架（成本结构/客流模型），供参考不做承诺 |
| 医学 | 生物医药/医疗体系/医院 | 衔接项目既有医疗档案（stages/）；职业发展轨迹比对 |
| 金融 | 基金/母基金/上市/募资 | 招股书追溯（source-grading.md §4）；金融插件引用须带来源元数据 |
| 审计 | 财务数据/产值口径冲突 | 口径核查清单（参照 xtt-corporate-finance-accounting 插件思路，只衔接） |
| 物理 | 新材料/半导体/能源技术 | 技术成熟度分层（实验室/中试/量产），工程化线索强化 |
| AI/计算机 | 人工智能/软件/算力 | 产业-岗位映射（算法/工程/产品/运维族） |
| 通用 | 任何深化请求 | 产出统一走批判四形态（critique-frameworks.md §1） |

## §2 高校-可及地区-产业联系（人口束缚因素）
接续项目既有研究（西安/深圳案例：高校在校数×本地产业承接力×人口流动约束）：
- 模型骨架：**高校供给（在校/毕业生）× 产业需求（岗位族×三态）× 人口束缚（户籍/家庭/迁移成本）→ 可及性矩阵**；
- 既有工件位置：项目 stages/ 与 livability-audit-swarm 案例3/4（六城检索）——重接管路时先查 INDEX 与 verdict_register；
- 本技能职责：摄取中发现"高校-产业"耦合线索（如"南京20多所生物医药院校/基础人才输出全国之首"）时，落指针 CSV `industry_tags=高校产业耦合` 并回写项目档案。

## §3 GitHub 辅助开发线索（登记未集成，用前评估）
- 候选方向（须自行核实许可证与现状）：公众号文章抓取（wechatarticles/WechatSogou 类）、markdown→docx（pandoc）、网页快照（singlefile 类）。
- 红线：不集成任何逆向微信接口/爬虫框架为本技能依赖；GitHub 工具仅限离线处理（格式转换/命名/去重）。
- 当前全部摄取走 web_open_url 合规通道；如未来官方 API 可用再升级。

## §4 生态技能衔接（只引用不重造）
- source-semantics-sentinel：通道阶梯 C0-C4、投毒甄别
- evidence-chain-verifier：五步证据链登记
- cognitive-exoskeleton：三纪律（选择题交付/conf 三级/top3_likely_wrong）
- ppp-city-verdict-audit：岗位可得性判定（本技能不承诺可得性）
- docx/pdf 技能：四形态缓存的转换层

## §5 持续更新生命力
- 每次实战后：新失败形态→fetch-protocol.md；新宣传话术→source-grading.md §2 信号表；新线索类型→critique-frameworks.md §3。
- 版本行必带修改人+日期+实战来源（见 SKILL.md 版本表）。
