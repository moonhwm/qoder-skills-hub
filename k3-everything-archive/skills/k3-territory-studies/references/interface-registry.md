# 接口统摄清单（interface-registry）v0.1 — 2026-09-01 当值快照

> 用途：疆域研究中的"国家基础设施"底账。研究需要数据时先查本表定位接口；会话插件集变化时须更新。
> 纪律：金融/事实数据优先用专业插件，不用模型记忆；引用须随文标注来源与截止时间；认证/超时错误按"待解决"报告，不得当作空结果。

## 一、金融数据接口（核心统摄对象）

### A 股 / 港股 / 中国市场
| 接口 | 覆盖 | 疆域研究中的典型用途 |
|---|---|---|
| Wind（wind-allskill：wind / wind-mcp-skill） | A股/港股/基金ETF/指数板块/债券/宏观EDB/公告新闻 | 市场数据权威源；候选地区"经济实力"类比指标 |
| iFinD（同花顺） | 全球行情、财报、业务分部、公告、股东、预测、智能选股 | 与 Wind 互备交叉验证 |
| Gildata（gildata-aifinmarket，40+ 子技能） | 选股选基、异动归因、晨会纪要、研报、舆情、组合模拟 | 议题级分析（晨会总结、行业速报、舆情风险） |
| 财新数据（caixin-data-agent，11 库） | 股票/债券/基金/期货/宏观/货币银行保险/产业链/舆情/科创/企业/人物研报 | 产业链图谱、失信与处罚记录（地区"合规性"类比） |
| 新华财经（xhcj-news-agent） | 中文财经资讯、公告关键词检索、政策向量检索 | 政策与舆情证据 |
| 中国公共数据（china_public_data） | 国家统计局 11,789 指标、公共数据登记平台、省级开放目录 | 宏观与区域统计类比素材 |

### 美股 / 国际市场
| 接口 | 覆盖 | 用途 |
|---|---|---|
| SEC EDGAR（sec_edgar） | 10-K/10-Q/8-K、XBRL、内部人交易、机构持仓 | 美股档案级证据 |
| Yahoo Finance | 行情、公司资料、财务指标、分析师覆盖 | 轻量行情；三席皆无时方用 |
| IMF | WEO（GDP/通胀/债务/失业/贸易）+ COFER 储备币种 | 跨国宏观比较 |
| World Bank Open Data | 29,000+ 发展指标，1960 至今 | 发展经济学类比素材 |
| IGO 开放数据（igo_open_data） | WHO/Eurostat/ECB/UNICEF/OECD/FAO/UNSD + FRED | 国际组织统计 |

### 企业与法律
| 接口 | 覆盖 | 用途 |
|---|---|---|
| 天眼查（tianyancha） | 工商/风险/司法/知识产权/投资/关系 17 大类 226 接口 | 实体识别与关系穿透 |
| 元典法律（yuandian_law） | 大陆法规与案例（语义+关键词、效力级别、法院、地区多维过滤） | 法理类比的实在法对照（仅作比较素材） |
| 中国标准（china_standards） | 国标/行标/地标/团标 | 制度"标准化"类比 |

### 学术与文献
| 接口 | 用途 |
|---|---|
| scholar | 学术论文检索、作者画像、h-index——理论研究主力 |
| PubMed | 生医文献（本议题基本不用） |

### 金融工作流套件（方法论资源）
- xtt-public-markets-investing（11 主技能：问题路由/公司研究/估值/宏观策略/组合管理/报告生产等）
- xtt-investment-banking-private-equity（10 主技能：交易流程/尽调/模型/估值/基金生命周期）
- xtt-corporate-finance-accounting（9 主技能：关账/对账/营运资本/FP&A/审计控制/基金会计/中国税务）
- ptrade-guide（量化策略生成与静态校验）
> 用途：制度设计章的"评级/尽调/评分卡"方法借鉴；不直接跑金融数据。

## 二、生信与材料（非本议题主线，登记备查）
chembl / pubchem / pdb / uniprot / ncbi_blast / materials_project / oqmd

## 三、效率与协作（治理设施类接口）
飞书 lark 全家桶（文档/多维表格/日历/IM/邮箱/任务/OKR/妙记/知识库/画板/妙搭部署）、钉钉 dws、金山文档 kdocs、GitHub MCP、<通道库> MCP（库表/迁移/分支/Edge Functions）、Cloudflare MCP、百度网盘、email（IMAP/SMTP）、canva、stripe（支付，写操作需反复确认）、kimi-excel / kimi-word / kimi-pdf

## 四、生成类接口
image_generation / video_generation / audio_generation / search_image_by_text(by_image)

## 五、平台与浏览
browser_*（访问/点击/截图/滚动）、context7（库文档垂直检索）、cron 三件套（add/list/update/remove_cron_job）、website_version_manager

---
**统摄规则**：①事实数据一律走接口不走记忆；②同域多源时按金融插件路由规则选主源（中国：Wind/iFinD/Gildata/财新；美国：SEC→Gildata→Yahoo）；③任何接口返回的引用元数据才可入 citation，禁止编造。

**分层视角**（eval-1 回灌）：宏观层（IMF/世界银行/IGO/国家统计局）→ 市场层（Wind/iFinD/Gildata/财新/SEC/Yahoo）→ 企业层（天眼查/财新企业/SEC 申报）；跨层引用时注明层级，宏观类比不得直接推及企业结论。各接口实际可用字段、调用额度与授权范围以当值接入实况为准，本表不构成能力承诺。
