# 插件目录（2026-08-29 快照）

按域分组。通道，A=agent-gw 数据源，B=MCP server，C=本地 CLI。实证栏只记实战验证过的要点。

## 法律与学术

| 插件 | 通道 | 用途 | 实证备注 |
|---|---|---|---|
| yuandian_law 元典法律 | A | 法规全效力级、普通与权威案例库，语义加关键词检索加详情 | 案由字段可能漏挂，须多检索式交叉；原始 CSV 落盘回链 |
| scholar | A | 学术文献检索、引用数、作者画像 | 灰色文献与行业标准或不索引；引用数存在拆分压低；CSV 归档可复现 |

## 金融与产业

| 插件 | 通道 | 用途 | 实证备注 |
|---|---|---|---|
| caixin-data-agent 财新 | A | 股票/债券/基金/期货/宏观/舆情/产业链/企业 | 中国公司事实首选之一 |
| wind-allskill | A | A 股/港股/美股行情、基金、债券、公告 | 仅中国市场覆盖 |
| ifind 同花顺 | A | 全球市场、财报、选股 | 与 Wind/Gildata 互为备用 |
| gildata-aifinmarket 恒生聚源 | A | 综合金融问数加 40 余场景技能 | 场景技能丰富，按需路由 |
| xhcj-news-agent 新华财经 | A | 中文财经资讯/公告/政策检索 | MCP 不可见时回退本地脚本 |
| tianyancha 天眼查 | A | 企业工商/风险/司法/知识产权 | 企业背景核查 |
| yahoo_finance | A | 美股行情与公司数据 | 优先级次于专用美股源 |
| imf / world_bank_open_data / igo_open_data | A | 全球宏观与发展指标 | 宏观三角互证 |
| china_public_data | A | 国家统计局与政府开放数据 | 国内宏观 |
| xtt-corporate-finance-accounting / xtt-investment-banking-private-equity / xtt-public-markets-investing | 技能套件 | 财会/投行 PE/公开市场研究工作流 | 含数据源路由子技能 |

## 生物与材料计算

| 插件 | 通道 | 用途 |
|---|---|---|
| pubchem | A | 化合物解析、属性、相似性搜索 |
| chembl | A | 生物活性 IC50/Ki、靶点 |
| uniprot | A | 蛋白条目与 ID 映射 |
| pdb | A | 蛋白 3D 结构 |
| ncbi_blast | A | 序列相似性比对（异步队列） |
| materials_project | A | 无机材料 DFT 带隙/稳定性 |
| oqmd | A | 无机晶体形成能/结构 |

## 办公协作与云

| 插件 | 通道 | 用途 | 实证备注 |
|---|---|---|---|
| lark | C | 飞书全家桶（lark-cli） | 发送类动作属写类例外；首次配置为交互式：后台 `config init`→日志取 user_code URL→`auth qrcode` 出图→回复中必须展示二维码（2026-08-31 实证） |
| dws | C | 钉钉全家桶 | 同上 |
| kdocs | 技能 | 金山文档云操作 | 同上 |
| email | 技能 | IMAP/SMTP 邮件 | 发送属写类例外 |
| baidu-pan | B | 百度网盘文件管理 | 写/删/分享属写类例外；技能包外发默认禁止 |

## 设计、媒体与呈现

| 插件 | 通道 | 用途 |
|---|---|---|
| canva | B | 设计生成与品牌模板（实证：query ≤220 字符工具实测上限；签名 URL 禁裸贴；Not eligible=额度信号最多重试一次，2026-08-31） |
| image_generation | A | 文生图（透明底限 1K） |
| video_generation | A | 文生视频 4-12 秒 |
| audio_generation | A | TTS 与音效 |
| musepool | 技能 | 设计灵感库，反 AI 默认审美 |
| interactive-research-report-en | 技能 | 深度报告转交互式研究网站 |
| kimi-excel / kimi-word / kimi-pdf | 技能 | Office 文档三件套 |

## 工程基础设施

| 插件 | 通道 | 用途 | 实证备注 |
|---|---|---|---|
| github | B | 仓库/issue/PR/代码搜索 | 写操作属写类例外；技能包外发默认禁止 |
| cloudflare | B | 全 API 加文档检索 | 先查文档再执行 |
| <通道库> | B | 数据库/迁移/Edge Functions | 写入属写类例外；通道项目 `<项目库标识>`：<跨席通道表> 的 id 列 GENERATED ALWAYS（INSERT 禁带 id）、msg_hash NOT NULL（2026-08-31 实证） |
| stripe | B | 支付运营 | 动账属写类例外，建议只读 |
| context7 | B | 库文档版本对齐检索 | 写代码前查官方文档 |
| ptrade-guide | 技能 | PTrade 量化策略生成加静态校验 | 不代跑回测 |
