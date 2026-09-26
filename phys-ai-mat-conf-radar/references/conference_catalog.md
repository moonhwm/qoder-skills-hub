# 会议目录：物理 × AI × 材料（等离子体物理与聚变工程化重点）

## 目录
- 第 0 节 使用纪律（先读）
- 第 1 节 等离子体物理与聚变工程（重点域）
- 第 2 节 AI 顶会与 AI4Science 交叉场
- 第 3 节 材料科学顶会
- 第 4 节 物理综合与交叉计算场
- 第 5 节 国内会议与期刊快投通道

## 第 0 节 使用纪律（先读）

1. 本目录的"典型窗口"是**历史周期规律**，不是当年官宣日期——每年日期都会漂移，
   任何写进排期的具体日期必须按 `verification_policy.md` 走 T2 官网核验并记录 data_cutoff。
2. 目录只列入口与周期；是否"顶会"因子领域而异，tier 列是社区通行认知的粗略分档（核心/重要/交叉），
   用于排期优先级参考，不作学术评价结论。
3. 新会议、停办、更名是常态——发现目录与官网矛盾时，以官网为准并登记 Conflict，
   顺手在排期交付物里标注目录待修。
4. 已做 T2 核验的条目以 `data/catalog_t2_log.jsonl` 为准（含 source_url 与 data_cutoff）；
   目录表格是周期规律，T2 日志是当期事实，两者冲突时以日志为准。

## 第 1 节 等离子体物理与聚变工程（重点域）

| 会议 | 主办 | 频率/典型窗口 | 典型节点节奏 | 官方入口 | tier |
|---|---|---|---|---|---|
| APS DPP Annual Meeting | 美国物理学会等离子体物理分会 | 每年，10-11 月 | 摘要截止约在 7 月中 | engage.aps.org/dpp | 核心 |
| IAEA Fusion Energy Conference (FEC) | 国际原子能机构 | 两年一届（奇数年），10 月 | 摘要/全文早一年底至当年春 | iaea.org/events | 核心（聚变旗舰） |
| EPS Conference on Plasma Physics | 欧洲物理学会 | 每年，6-7 月（欧洲） | 摘要约在当年 3-4 月 | eps.org / 当年承办方站点 | 核心 |
| SOFT (Symposium on Fusion **Technology**) | 欧洲聚变界（2026 届 CEA IRFM 主办） | 两年一届（偶数年），9 月 | 摘要约当年 1-2 月（2026 届 01-05~02-28），全文约当年 10 月底（2026 届 10-31） | 当届官网（2026: soft2026.org） | 工程核心 |
| SOFE (IEEE Symposium on Fusion **Engineering**) | IEEE NPSS | 不定期，常与 PPC 联合（2027 届 06-20~24 San Diego） | 以 IEEE NPSS 公告为准 | ieee-npss.org | 工程核心（⚠️ 与 SOFT 是两个不同会议，勿混） |
| IEEE ICOPS | IEEE 核与等离子体科学会 | 每年，5-6 月（美洲轮办） | 摘要约当年 1-2 月 | ieee-npss.org / 当届官网 | 核心 |
| ISFNT (Int. Symp. on Fusion Nuclear Technology) | 国际聚变核技术界 | 两年一届 | 摘要约前一年 | 当届官网 | 工程核心 |
| ANS Annual / Winter Meeting | 美国核学会 | 每年两届 | 摘要约开会前 4-5 个月 | ans.org/meetings | 重要（聚变工程/材料分会场） |
| ITPA 各专题组会议 | ITER 框架下 | 每年多轮 | 邀请制，走渠道而非投稿 | iter.org | 核心（不公开投稿） |
| 全国等离子体科学技术会议 | 中国物理学会等离子体物理分会等 | 两年一届 | 以当届通知为准 | 承办方/分会通知 | 国内核心 |
| 中国物理学会秋季学术会议 | 中国物理学会 | 每年，9-10 月 | 摘要约当年 6-7 月 | cps-net.org.cn | 国内综合（含等离子体专题） |

聚变工程化特别关注节点：
- **SOFT / ISFNT / ANS** 是工程技术（磁体、包层、材料、遥操作、氚工艺）主战场；
- IAEA FEC 偏物理与堆概念；IEEE ICOPS 偏等离子体技术与应用；
- 商业聚变公司动态（CFS、TAE、Helion、能量奇点、星环聚能等）常借 APS DPP / SOFT 发声，
  但公司声称属 C3 单一自述，引用时走信源定级，不得与同行评审内容混档。

## 第 2 节 AI 顶会与 AI4Science 交叉场

| 会议 | 频率/典型窗口 | 投稿截止典型节奏 | 官方入口 | tier |
|---|---|---|---|---|
| NeurIPS | 每年 12 月 | 摘要+全文约当年 5 月 | neurips.cc | 核心 |
| ICML | 每年 7 月 | 约当年 1 月底-2 月 | icml.cc | 核心 |
| ICLR | 每年 4-5 月 | 约前一年 9 月底-10 月 | iclr.cc | 核心 |
| AAAI | 每年 2-3 月 | 约前一年 8 月（两轮制常见） | aaai.org | 核心 |
| KDD | 每年 8 月 | 约前一年 8 月与当年 2 月（两轮） | kdd.org | 数据挖掘核心 |
| NeurIPS/ICLR AI4Science workshop 群 | 随主会 | 截止约主会前 2-3 个月 | 各 workshop 页 | 交叉首选曝光位 |

AI×科学投稿策略提示：方法创新走主会；面向等离子体/材料的应用型成果，
workshop 周期短、反馈快，适合抢时间窗，但学术权重低——排期时两类分开登记，
避免把 workshop 录用当主会成果（conf 与 tier 字段分开标）。

## 第 3 节 材料科学顶会

| 会议 | 主办 | 频率/典型窗口 | 官方入口 | tier |
|---|---|---|---|---|
| MRS Spring / Fall Meeting | 美国材料研究学会 | 每年两届（春 4 月/秋 11-12 月） | mrs.org | 核心 |
| TMS Annual Meeting | 美国矿物金属与材料学会 | 每年 2-3 月 | tms.org | 核心（冶金/核材料方向强） |
| APS March Meeting | 美国物理学会 | 每年 3 月 | aps.org/meetings | 凝聚态核心（含材料计算） |
| ICMAT | 新加坡材料学会 | 两年一届（奇数年，6-7 月） | mrs.org.sg | 亚太重要 |
| C-MRS 中国材料大会 | 中国材料研究学会 | 每年，约 7 月 | cmrs.org.cn | 国内核心 |
| Fusion / 聚变材料专场（如 ICFRM 国际聚变堆材料会议） | 国际聚变材料界 | 两年一届 | 当届官网 | 聚变材料核心 |

## 第 4 节 物理综合与交叉计算场

| 会议 | 典型窗口 | 说明 | 入口 |
|---|---|---|---|
| APS April Meeting | 每年 4 月 | 偏核物理/粒子/引力，等离子体内容少 | aps.org |
| SIAM Conference on CSE | 两年一届（奇数年） | 计算科学工程交叉，AI 模拟方法合适 | siam.org |
| SciPy / 各计算物理软件会 | 每年 | 工具链曝光 | scipy.org |

## 第 5 节 国内会议与期刊快投通道

- 国内学术会议信息常以承办高校官网/公众号通知为准，属 C3 转述通道，
  任何日期必须回溯到学会或承办方正式通知原文（T2）；
- 会议论文快速转化期刊通道：SOFT→Fusion Engineering and Design 专刊、
  ICOPS→IEEE Transactions on Plasma Science 等，排期时把"会后全文/专刊截止"作为独立节点登记；
- 中文核心与 SCI 期刊的聚变/等离子体栏目（NF、PPCF、FST、FED、POP、核聚变与等离子体物理等）
  属滚动收稿，不占排期表，但特刊截稿要登记。

> 目录维护：每年 1 月做一次全表 T2 复核；任何条目官网失效先标 broken 再人工更新，禁止凭记忆改表。
