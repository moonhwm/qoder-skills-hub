---
name: plugin-datasource-ops
description: "[项目技能] 插件与数据源调用范式——全会话插件接口的统一调用纪律、域路由表、实证 Pitfalls 与持久化规程。触发（满足任一）：①任务涉及调用任何已安装插件或 agent-gw 数据源（元典法律、scholar、金融数据源、生物/材料库、宏观数据库、MCP 服务、lark-cli 等）；②用户要求把插件调用持久化/稳固化/全局化；③子代理派单需要携带插件调用纪律；④需走数据源的专线路由处理定向业务查询。统一调配入口为 autonomous-advance-ops（§2 默认动作栈登记本件）。覆盖：三条调用通道识别、按域路由、多检索式交叉纪律、原始返回持久化、conf 分层保持、写类例外与外发禁令的继承、安装位只读期间的工作副本规程。中文名：插件数据源运维范式。English triggers: plugin routing, datasource discipline, agent-gw invocation paradigm, MCP call discipline."
metadata:
  version: "1.0.4"
  assistant_aliases: ["助手甲", "助手甲"]
---

<!-- v1.0.4（2026-09-01）：四条实证事故入库——§三.8 金融数据本地兜底链（yfinance）；§三.9 Canva 220 字符上限/签名 URL/Not eligible；§三.10 lark-cli 首次配置二维码流程；§三.11 <通道库> <跨席通道表> 插入纪律。 -->
<!-- v1.0.3（2026-08-30）：I9 优化实装（用户拍板+姊妹会话建议）——§三.0 额度池状态预检条款（先探针后调用，撞墙前分流）。 -->
<!-- v1.0.2（2026-08-29）：I9 全局优化纪律实装——§四.5 自我优化条款。 -->
<!-- v1.0.1（2026-08-29）：接口对齐补丁（总署 §9 核验，I3/I4/I6 补位）——首部增能力自报块+纪律继承声明+自检声明；登记 skill_aliases.json。内容条款零改动。 -->
<!-- v1.0.0（2026-08-29）：创刊。应用户指令「插件调用持久化、稳固化、全局化，固化为 skill 范式，交由 autonomous-advance-ops 集中统一调配」。实证来源：研究线回合 1-3（元典法律、scholar、金融插件实战）与金融路由元指令。 -->

# 插件数据源运维范式（plugin-datasource-ops）

> **能力自报块**（总署调度钩子，总接口 I3）：能力域=通道+查询｜输入型=任务书/域路由请求｜输出型=调用纪律裁定+路由表+实证 pitfalls｜只读性=是（本件无写类动作）｜依赖=各插件 SKILL.md 与 agent-gw SDK/MCP 工具可见性
> **纪律继承声明**（I4）：本技能继承 conf 词表统一、红线条款、写类例外、信息充分性条款、全局共同遵守（autonomous-advance-ops 为准）。
> **自检声明**（I6）：本件无可执行脚本；人工核验清单=三通道表/路由表/七条实证纪律逐项 grep 在位；版本差显式化义务遵守 §四。

统一调配入口，autonomous-advance-ops。本件是被调度件，路由决策与红线仲裁以总控为准；本件提供的是调用层的操作纪律与实证知识。

## 一、三条调用通道（先识别通道再调用）

| 通道 | 机制 | 代表插件 |
|---|---|---|
| A. agent-gw 数据源 | 经 agent-gw 服务调用，密钥服务端托管，多以 CLI/脚本形式暴露 | 元典法律、scholar、财新、Wind、iFinD、Gildata、新华财经、天眼查、tianyancha、pubmed、pubchem、chembl、uniprot、pdb、materials_project、oqmd、ncbi_blast、imf、world_bank、igo_open_data、china_public_data、yahoo_finance |
| B. MCP server | 工具经 tools_added 加载后直接函数调用 | github、canva、cloudflare、stripe、<通道库>、baidu-pan、context7 |
| C. 本地 CLI | 命令行工具 | lark-cli（飞书全家桶）、dws（钉钉） |

调用前先读对应插件的 SKILL.md（路径 /app/.agents/plugins/<plugin>/skills/），确认工具可见性。MCP 工具不可见时按其 SKILL.md 的 fallback 条款执行（如新华财经回退本地脚本），禁止假装已调用。

## 二、按域路由（默认路由表，详细版见 references/plugin_catalog.md）

- **法律（中国大陆）**：元典法律。法规全效力级加案例双库，语义与关键词检索加详情。
- **学术文献**：scholar（通用）、pubmed（生物医学）。引用数可作影响力粗筛。
- **金融事实**：按市场路由（遵守金融元指令），中国公司用财新/Wind/iFinD/Gildata，美股用对应美股源，宏观用 IMF/世界银行/igo。舆情用新华财经。
- **生物/材料计算**：pubchem/chembl（小分子）、uniprot/pdb（蛋白）、ncbi_blast（序列）、materials_project/oqmd（无机材料）。
- **企业工商**：天眼查。
- **办公协作**：lark（飞书）、dws（钉钉）、kdocs（金山）、email。
- **设计与媒体生成**：canva、image_generation、video_generation、audio_generation、musepool（设计灵感）。
- **工程基础设施**：github、cloudflare、<通道库>、stripe、context7（库文档）。

## 三、实证纪律（全部来自实战事故）

0. **额度池状态预检（v1.0.3，用户拍板）**：调用任何专业数据源前，先以最低成本探针确认通道可用（如该源一条 realtime/quote 调用）——
   - 探针成功 → 正常执行；
   - 探针返回 resource_exhausted/quota 类错误 → **不启动任务**，当轮如实报告缺口，主数据改走零额度通道（web_search/browser 直连官网），并按 「额度守护件」 联动 `signal quota_error` 入额度台账；
   - 探针返回 EMPTY_DATA → 按收录滞后处理（多检索式交叉+回退源），不视为额度信号。
   铁则：禁止在已知额度耗尽窗口内连发调用撞墙；预检成本计入当轮 cost 块。

1. **多检索式交叉**。元典实证，八件恶意诉讼案中三件的案由字段未挂目标案由，单一字段过滤会漏检。任何数据库检索至少两种检索式（案号加当事人关键词加语义），零命中必须声明检索式清单才算穷尽。
2. **原始返回持久化**。scholar 与元典的原始 CSV 一律落盘归档（实证目录 <输出区>/research/ 下 *_csv/），引用外部不可复核的库内数据时必须能回链原始记录，否则按存疑降级（实证，verifier 抓出元典单源金额无法外部复核）。
3. **conf 分层保持**。底稿的 conf 分层进入综合报告时禁止扁平化（实证，连续两轮被 reviewer 抓出 conf 膨胀 High）。综合环节逐条带入底稿 conf，复发则改为机器拼接。
4. **灰色文献标注**。scholar 对行业标准（AIAG MSA）与专著（Mills 1972、Musa 1987）可能不直接索引，经二级文献确认的引用必须标注"二手确认"。scholar 引用数存在条目拆分压低现象，引用数只作量级参考。
5. **金融引用纪律**。专业数据源的每个数字紧邻挂载引用（来源加日期），禁止编造数据集名与截止日期；多源混排分段标注。
6. **写类例外继承**。总控 §8 写类例外一体适用于插件，<通道库> 写入、GitHub 写、Stripe 动账、lark/email 发送、网盘写/删/分享，调用前必须显式获批。用户列名插件等于默认准许只读调用，不覆盖写类。
7. **代码外发禁令**。技能包与脚本禁止外发（GitHub、网盘分享等），含本件自身的 .skill 包。分发动作走写回队列登记，等用户拍板。
8. **金融数据本地兜底链（2026-08-28 实证）**。agent-gw 金融源连发 resource_exhausted（东富龙 300171 调取四连撞墙）时，按序兜底：禁改网页 API 硬爬（东方财富直连 RemoteDisconnected 实证）、禁临时 pip 装 akshare（内网镜像超时实证）——沙箱预装 **yfinance** 可直接取 A 股：代码加交易所后缀（`300171.SZ`/`.SS`），公司信息、2 年日线、年/季度三表均可取。数字引用纪律（§三.5）不变，来源标「Yahoo Finance（yfinance 本地）+日期」；quota 联动入台账不变。
9. **Canva 生成实证（2026-08-31）**。① query ≤220 字符（工具 maxLength 实测，插件文档写 255 不准——以工具 schema 为准）；② 返回签名 URL 禁裸贴，只放 markdown 链接括号内；③ 「Not eligible for design composition」=额度信号，最多重试一次，再犯即停并按 「额度守护件」 申报，禁止循环撞墙。
10. **lark-cli 首次配置（2026-08-31 实证）**。`lark-cli config init --new --force-init` 为交互式（终端打印二维码并阻塞等待）——须后台运行，从日志提取含 `user_code` 的授权 URL，再 `lark-cli auth qrcode "<url>" --output lark_config_qr.png` 出图；**必须在回复中内嵌展示该二维码图**（只落盘文件不算交付，用户需扫码完成授权）。
11. **<通道库> 通道表插入（2026-08-31 实证）**。项目 `<项目库标识>` 的 `<跨席通道表>` 表：id 列 GENERATED ALWAYS，INSERT **禁带 id 列**（带即报错）；`msg_hash` NOT NULL 必填。插入报错先疑这两处，再疑权限。

## 四、持久化规程（安装位只读期间）

1. 技能工作副本一律放 <输出区>/skills/<name>/，打包 .skill 后另存 <上传区>/ 备份。
2. 安装位（<技能安装位>、/app/.agents/skills）只读，工作副本与安装位的版本差必须在 MASTER_INDEX 与写回队列显式可见，禁止"以为装了"。
3. 新技能创建即登记 <注册处>/skill_aliases.json，并跑 cross-session-workflow-bridge 的 build_skill_index.py 刷新索引。
4. 遵守总控 §11 全部创建规则（版本三段制、conf 词表、可测量阈值、称呼注册表占位符）。
5. **自我优化条款（I9，全局纪律）**：本技能被触发执行任务时，当轮登记「本技能优化候选」一条（来源=调用卡点/实证事故/新插件上架）或零候选声明；优化按补丁级实装，次版本走表决；每轮至多 1 补丁级自修订（用户指令除外）。

## 五、子代理派单条款

派单涉及插件调用时，任务书必须随带，对应域路由、多检索式交叉、原始返回落盘路径、红线条款（禁编造/禁外发/写类例外/禁假装实装）、conf 词表。子代理的插件原始返回归主代理统一归档。

## Resources

- [references/plugin_catalog.md](references/plugin_catalog.md)：全会话插件目录，按域分组，含通道、状态与实证备注。
