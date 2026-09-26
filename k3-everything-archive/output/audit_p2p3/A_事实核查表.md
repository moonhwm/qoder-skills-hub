# A席·事实核查表 —— 方案二/三事实断言核查

- 审计对象：`<输出区>/audit_p2p3/proposal_text.txt`（启信慧眼×华为云OfficeAce/AgentArts整合提案）
- 审计范围：方案二（自定义技能/AgentArts工作流调启信官网REST API）、方案三（AgentArts客商风控智能体）及其依赖的事实断言
- 核查时间：2026-08-31 前后（以核查时官方页面展示为准）
- 证据等级：C0=一手（官网接口详情页直连）/ C1=官方（华为云/启信官方文档、公告）/ C2=多源交叉 / C3=单一转述

---

## 一、断言组1：启信慧眼官网 REST API（方案二事实底盘）

| # | 原文摘要 | 核查结论 | 证据来源URL | 证据等级 | 风险注记 |
|---|---|---|---|---|---|
| 1.1 | 接口地址形如 `https://api.qixin.com/APIService/{模块}/{方法}`，JSON返回，HTTP/HTTPS GET（部分支持GET、POST） | 证实 | https://data.qixin.com/api-detail?apiId=1.41 （/enterprise/getBasicInfo，GET）；https://data.qixin.com/api-detail?apiId=55.29 （/reportData/getAllRiskInfoByName，GET,POST） | C0 | 无。多接口详情页逐一核对，URL形态、数据格式、请求方式均一致。 |
| 1.2 | 鉴权为请求头携带 Auth-Version: 2.0、appkey、timestamp、sign（appkey+timestamp+secret_key 的32位MD5小写） | 证实 | https://data.qixin.com/api-detail?apiId=1.50 等全部接口详情页"请求参数（Headers）"节；第三方代码实现佐证：https://blog.csdn.net/m0_70325779/article/details/132324922 | C1+C2 | 需额外配置API IP白名单（未配置报错"104 未添加IP白名单"），方案二开发时应纳入步骤。timestamp近10分钟有效。 |
| 1.3 | 工商照面 1.41（/enterprise/getBasicInfo）=0.15元/次 | 证实 | https://data.qixin.com/api-detail?apiId=1.41 | C0 | 页面带"限时优惠"图标，价格为活动价，可能回调；提案已作提示。 |
| 1.4 | 经营异常 1.55（/enterprise/getAbnormals）=0.15元/次 | 证实 | https://data.qixin.com/api-detail?apiId=1.55 | C0 | 接口路径与提案一致。 |
| 1.5 | 失信被执行企业 5.5=0.15元/次 | 证实 | https://data.qixin.com/api-detail?apiId=5.5 （/execution/getExecutionListByName） | C0 | 无。 |
| 1.6 | 行政处罚 32.1=0.15元/次 | 证实 | https://data.qixin.com/api-detail?apiId=32.1 | C0 | 实际路径为 /APIService/v2/adminPunish/getAdminPunishByName（含v2段），提案未列路径，不影响结论。 |
| 1.7 | 合作风险排查 55.29（/reportData/getAllRiskInfoByName）=5元/次 | 证实 | https://data.qixin.com/api-detail?apiId=55.29 | C0 | 路径、价格、GET+POST均一致。 |
| 1.8 | 客户信息尽调 47.51=3元/次 | 证实 | https://data.qixin.com/api-detail?apiId=47.51 （/reportData/getAllEntInfoByName） | C0 | 无。 |
| 1.9 | 企业基础工商信息 1.8=2元/次（含照面+主要人员+变更+股东+经营异常） | 证实 | https://data.qixin.com/api-detail?apiId=1.8 （/enterprise/getDetailAndContactByName） | C0 | 官方描述另含"工商公示企业联系方式"，提案未提，属遗漏而非错误。 |
| 1.10 | 企业模糊搜索 1.31=0.01元/次 | 证实 | https://data.qixin.com/api-detail?apiId=1.31 （/v2/search/advSearch） | C0 | 无。 |
| 1.11 | 接口覆盖19个官方分类、全量28页、页面直接展示单价 | 部分证实 | https://data.qixin.com/api-list 及各详情页侧栏 | C1 | 详情页侧栏可见17个分类（搜索查询/工商信息/司法风险/经营风险/经营信息/知识产权/关联关系/企业报告/企业评分/企业标签/新闻舆情/企业发展/客商关系/集团信息/证券信息/地产建筑/特色专区）；"19个分类、28页"未经登录逐页复核，且提案自身已在"待确认事项"中标注。 |

**小结**：方案二所引8个接口的ID、路径、单价共8/8条全部与官网页面一致（C0/C1级），仅"19分类/28页"的规模性描述部分证实。成本测算（基础尽调≈0.60元/家、深度≈5.60元/家）的单价基础成立，但价格为活动展示价，存在回调风险。

---

## 二、断言组2：启信官方 MCP 服务（方案一依赖，方案二/三备用语境）

| # | 原文摘要 | 核查结论 | 证据来源URL | 证据等级 | 风险注记 |
|---|---|---|---|---|---|
| 2.1 | 启信慧眼官方MCP封装200+企业数据能力 | 证实 | 启信官网新闻：https://b.qixin.com/news/child...（"标准化打通200余项企业数据能力"）；静安区政府网：https://www.jingan.gov.cn/rmtzx/003001/20260826/db3764b4-14b5-45af-b689-3d430531869d.html ；搜狐报道：https://www.sohu.com/a/1066960913_122850697 | C2 | "200+"为官方宣传口径（"200余项数据接口"），非可逐一点数的清单。 |
| 2.2 | 启信慧眼MCP已落地腾讯WorkBuddy | 证实 | 启信官网2026-07-10公告"启信慧眼MCP正式接入腾讯WorkBuddy"；腾讯云开发者社区实测文：https://developer.cloud.tencent.com/news/4258194 ；新浪财经：https://finance.sina.com.cn/stock/relnews/cn/2026-08-25/doc-inipkvru2032123.shtml | C2 | 同期上架QoderWork/ima/千问办公/TraeWork/MiniMax Agent；提案只举WorkBuddy，无误。MCP具体接入方式、密钥形式、计费规则仍需与启信方确认（提案已标注）。 |

---

## 三、断言组3：OfficeAce 能力（方案二技能路径依赖）

| # | 原文摘要 | 核查结论 | 证据来源URL | 证据等级 | 风险注记 |
|---|---|---|---|---|---|
| 3.1 | 自定义技能本质是"提示词+脚本资源包"（SKILL.md规范），支持手动导入 | 证实 | https://support.huaweicloud.com/usermanual-officeace/officeace_02_0014.html （导入要求：根目录必须包含SKILL.md；单文件≤1MB、≤100个文件、总≤4MB；内置技能详情可见SKILL.md+资源目录结构） | C1 | 文件大小上限（4MB总量）对方案二签名脚本+模板打包足够，但应在实施时知悉。 |
| 3.2 | 技能内置Python/Node运行时 | 部分证实 | 技能文档页未见运行时说明；旁证：OfficeAce Stdio连接器支持以 python/node/npx/uvx 命令启动本地服务（officeace_02_0016.html） | C3 | 官方技能文档未明示技能沙箱运行时细节，建议实施前以客户端实测为准。 |
| 3.3 | MCP连接器支持Stdio/Streamable HTTP/SSE三种传输，推荐Streamable HTTP接第三方SaaS | 证实 | https://support.huaweicloud.com/usermanual-officeace/officeace_02_0016.html （三种传输对比表：Streamable HTTP推荐度★★★★★，适用第三方SaaS接入） | C1 | 连接器超时上限120秒（默认60秒），批量场景需注意。 |
| 3.4 | 环境变量可配置敏感值加密、支持自定义Headers | 证实 | 同上（环境变量/Headers勾选"敏感"后密文显示、存储加密保护） | C1 | 无。 |
| 3.5 | 支持飞书、微信（ClawBot）、钉钉、小艺等IM接入及定时推送 | 部分证实 | 产品简介：https://support.huaweicloud.com/qs-officeace/introduction.html （"支持飞书、微信、钉钉、小艺等多平台接入；支持微信一键扫码对接"）；定时任务文档：https://support.huaweicloud.com/usermanual-officeace/officeace_02_0017.html （定时任务可推送至飞书/微信/钉钉/小艺） | C1 | 官方表述为"微信一键扫码直连"，未出现"ClawBot"字样；"ClawBot"应为第三方微信机器人网关的调研表述，建议改用官方表述。 |
| 3.6 | OfficeAce个人版四档：体验版赠500积分、标准版2,000/月、高级版4,000/月、旗舰版10,000/月 | 证实 | https://support.huaweicloud.com/price-officeace/officeace_05_0002.html ；officeace_05_0001.html | C1 | 人民币价格官方未在文档列出（"以客户端实际展示为准"），提案表述一致。500积分为一次性发放不按月刷新。 |
| 3.7 | 官方连接器文档以天眼查MCP（https://mcp.tianyancha.com/v1）为同类示例 | 证实 | officeace_02_0016.html 图3（Streamable HTTP示例服务器名"天眼查"、地址 https://mcp.tianyancha.com/v1） | C1 | 无。 |

---

## 四、断言组4：AgentArts 能力（方案三事实底盘）

| # | 原文摘要 | 核查结论 | 证据来源URL | 证据等级 | 风险注记 |
|---|---|---|---|---|---|
| 4.1 | HTTP请求节点响应时限50秒、不支持OAuth、不支持流式 | 证实 | https://support.huaweicloud.com/usermanual-agentarts/http_node.html （约束限制：仅POST/GET；仅API Key认证暂不支持OAuth；不支持流式接口；API响应时间不能超过50秒） | C1 | 启信官网REST API使用自定义MD5签名头，恰好可经HTTP节点自定义请求头实现（API Key鉴权可放Header），不受OAuth限制影响；50秒时限对批量扫描需控节奏，提案提示合理。 |
| 4.2 | 自定义API插件（支持OpenAPI导入） | 证实 | 插件介绍：https://support.huaweicloud.com/lowcode-agentarts/agentarts_05_0123.html ；最新动态：https://support.huaweicloud.com/function-agentarts0/index.html （"插件导入能力增强：可导入符合OpenAPI3.0规范的JSON文件"，公测） | C1 | OpenAPI导入功能处于公测阶段；另支持.jsonl整插件导入。 |
| 4.3 | MCP服务节点密钥KMS加密 | 证实 | https://support.huaweicloud.com/usermanual-agentarts0/agentarts_05_0136.html （Streamable HTTP/SSE接入时默认"KMS加密+默认密钥kms-agentarts/default"派生DEK加密存储）；最新动态确认创建插件/MCP等均支持AgentArts加密与KMS加密 | C1 | KMS实例免费、每月2万次免费解密调用，敏感数据多时可超额，量级风险低。AgentArts的MCP接入另支持OAuth2.0鉴权（与HTTP节点不同）。 |
| 4.4 | 触发器定时任务（周期性自动风险监测） | 证实 | https://support.huaweicloud.com/lowcode-agentarts/agentarts_05_0052.html （周期触发：每日/每周/每月；间隔触发：天/小时/分钟/秒；同步/异步调用方式） | C1 | 无。 |
| 4.5 | 智能体发布后对外提供RESTful API：POST /runtimes/{runtime_name}/invocations | 证实 | https://support.huaweicloud.com/api-agentarts/agentarts_07_0046.html （步骤三明确API接口 POST /runtimes/{runtime_name}/invocations，Authorization: Bearer {api_key}） | C1 | 前置条件：须先接入MaaS付费模型或自接第三方模型，免费token不可用于API调用——方案三成本测算需计入模型费用。 |
| 4.6 | 体验版免费：2成员、20CU、50应用、1GB知识库、赠200万tokens | 部分证实 | https://support.huaweicloud.com/price-agentarts/agentarts_08_0003.html | C1 | 2成员/20CU/50应用/1GB均证实（20CU为一次性赠送非每月重置）；"赠200万tokens"实为**MaaS模型即服务首次开通**赠送（关联服务），并非AgentArts体验版自身权益，提案表述有归因偏差，且退订重开不再赠送。 |
| 4.7 | 付费档：团队标准10人/80CU月、团队高级50人/780CU月、企业专业200人/3000CU月、企业旗舰1000人 | 证实 | 同上（计费项表1） | C1 | 旗舰版另为10,880CU/月、10,000应用、800GB知识库，提案仅列人数，属不完整但无误。各档CU不结转。 |
| 4.8 | 截至2026-08付费版未开放公开售卖，需提交工单咨询 | 证实 | 同上（2026-08-11更新原文："当前AgentArts团队标准版、团队高级版、企业专业版、企业旗舰版未开放，如果需要购买，请提交工单咨询购买相关事宜"） | C1 | 提案据此建议先工单确认商务条件，处置恰当。 |
| 4.9 | OfficeAce为AgentArts平台下子产品 | 证实 | 华为云产品页：https://www.huaweicloud.com/product/agentarts/officeace.html （OfficeAce挂在AgentArts产品族下） | C1 | 无。 |

---

## 五、断言组5：云商店启信宝接口（方案三备用通道）

| # | 原文摘要 | 核查结论 | 证据来源URL | 证据等级 | 风险注记 |
|---|---|---|---|---|---|
| 5.1 | 卖家为上海生腾数据科技有限公司 | 证实 | 店铺页：https://marketplace.huaweicloud.com/seller/0688dc4db680264b0fd0c019fe1c97a0 ；data.qixin.com页脚ICP备案主体同为上海生腾；失信/商标/工商联系方式等多个商品页卖家均为该公司 | C1 | 上海生腾为合合信息全资子公司（启信宝运营主体），与启信官网同源，备用通道数据一致性预期较好。 |
| 5.2 | 购买后由APIG网关下发AppKey/AppSecret，支持签名认证或简单身份认证（AppCode） | 证实 | https://support.huaweicloud.com/ug-marketplace/zh-cn_topic_0203254658.html （认证信息由APIG网关统一创建；提供签名认证与AppCode两种调用步骤） | C1 | 无。 |
| 5.3 | 支持"按需"与"按需套餐包（按次预付费）" | 证实 | https://support.huaweicloud.com/usermanual-marketplace/zh-cn_topic_0198020621.html （API类商品适用计费模式=按需、按需套餐包；按需套餐包为预付费额度抵扣） | C1 | "按次预付"准确对应"按需套餐包"定义；额度用尽可配置自动复购（0元/限购规格除外）。 |
| 5.4 | 仅HTTP 2XX计为有效调用扣次 | 证实 | https://support.huaweicloud.com/ug-marketplace/zh-cn_topic_0203254658.html （API商品计费规则表：HTTP 2XX [200,300)） | C1 | 非2XX不计费有利于批量扫描容错，提案未展开此优点。 |
| 5.5 | 0元体验套餐包同一用户限购一次 | 证实 | 商家发布规范：https://support.huaweicloud.com/usermanual-marketplace/sp_topic_0000031.html （"API类商品如设置0元套餐包规格，不可设置为同一用户订购次数多次，须改为一次"）；启信宝在售商品普遍挂￥0.00元/3次规格 | C1 | 系平台强制发布规范，故启信宝0元体验规格必然限购一次；提案将其限定为测试用途的建议合理。 |

---

## 六、方案二/三事实底盘总评

方案二/三的事实底盘整体**扎实可信，未发现证伪项**。五个断言组共31条细项中：证实26条、部分证实5条（1.11分类页数规模、3.2技能内置运行时、3.5微信ClawBot措辞、4.6体验版200万tokens归因、4.7旗舰版CU数不完整）、未证实0条、证伪0条。核心承重事实——启信官网REST API的地址形态、Auth-Version 2.0+MD5签名鉴权、8个选用接口的ID/路径/单价——均经官网接口详情页逐一直核（C0/C1级），方案二成本测算（0.60元/家、5.60元/家）的单价基础成立；平台侧关键约束（HTTP节点50秒/仅API Key/不流式、触发器定时、对外invocations API、体验版与付费档配额、"付费版截至2026-08未公开售卖需工单"）均有2026年8月版华为云官方文档原文支撑，方案三的可行性判断与商务风险提示成立。需提请关注的三处瑕疵均属表述精度而非方向错误：①"赠200万tokens"系MaaS首开通赠送而非AgentArts体验版权益，成本测算时应将API调用所需MaaS付费模型费用单列（官方明确免费token不可用于API调用）；②"微信ClawBot"建议改为官方表述"微信一键扫码直连"；③启信"19分类/28页"与OfficeAce技能内置运行时尚未获官方页面直接佐证，实施前需登录控制台复核——但提案自身已在"风险与待确认事项"中如实披露大部分此类缺口，自我标注与外部核查结果一致，未发现隐瞒或夸大。结论：方案二可按现有事实底盘推进至实施；方案三技术路径成立，但立项前必须完成AgentArts付费版工单商务确认与模型费用测算两件事。
