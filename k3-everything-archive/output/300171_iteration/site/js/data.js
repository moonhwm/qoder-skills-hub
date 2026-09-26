// window.RPT — 所有数值均转录自 <输出区>/300171_iteration/ 磁盘文件
// 非结构化事实源：东富龙300171_分析报告_v1.0.md；K 锚：data/claims.json（K1-K15 依文件顺序编号）
window.RPT = (() => {

  // 利润拐点序列（is_20231231/20241231/20250630.csv 为 iFinD 底表；2025FY/2026H1 见 K10/K2/K3）
  const income = [
    { period: "2023FY",  kind: "fy", revenue: 56.42, np: 6.00,  eps: 0.79,   note: "iFinD 底表 5,641,696,443 元", k: "K10" },
    { period: "2024FY",  kind: "fy", revenue: 50.10, np: 1.94,  eps: 0.26,   note: "iFinD 底表 5,010,142,453 元", k: "K10" },
    { period: "2025FY",  kind: "fy", revenue: 52.33, np: 2.00,  eps: 0.26,   note: "同比 +4.4%", k: "K10" },
    { period: "2025H1",  kind: "h1", revenue: 24.29, np: 0.46,  eps: 0.0604, note: "iFinD 底表 2,428,518,867 元", k: "K10" },
    { period: "2026H1",  kind: "h1", revenue: 25.35, np: 1.08,  eps: 0.1415, yoyRev: 4.37, yoyNp: 134.49,
      note: "中报摘要 2,534,573,184.09 元；归母 107,678,132.77 元", k: "K2" },
  ];
  const h1_2026 = {
    revenue: 25.35, yoyRev: 4.37, np: 1.08, yoyNp: 134.49,
    npEx: 0.94, yoyNpEx: 270.73, eps: 0.1415,
    ocf: 0.91, yoyOcf: -67.03,
    impair: 0.72, impairPctOfTp: 47.81,
    q1np: 0.275, q2np: 0.80,
  };

  // 先行指标（中报全文合并资产负债表，K6/K7）
  const leading = {
    contractLiabEnd: 37.13, contractLiabBegin: 36.23, contractLiabChg: 2.47,
    inventory: 33.22, inventoryChg: 3.9,
    ar: 15.91, arChg: 0.3,
    goodwill: 1.69, goodwillPctAssets: 1.2,
  };

  // 2026H1 分部（中报全文分产品表 / 分地区表，K8/K9）
  const segments = [
    { name: "制剂装备事业部",       rev: 11.10, yoy: 1.73,  gm: 33.65, gmChg: -1.01,  k: "K2" },
    { name: "生物工艺装备及耗材",   rev: 7.16,  yoy: -1.15, gm: 36.41, gmChg: 18.22,  k: "K9" },
    { name: "制药工程事业部",       rev: 2.93,  yoy: 31.40, gm: 14.65, gmChg: -8.93,  k: "K8" },
    { name: "食品工程及装备",       rev: 2.56,  yoy: 15.32, gm: 27.10, gmChg: -0.62,  k: "K8" },
    { name: "售后服务与配件",       rev: 1.56,  yoy: -5.77, gm: 42.78, gmChg: -3.62,  k: "K8" },
  ];
  const regions = [
    { name: "国际", rev: 10.40, yoy: 29.24, gm: 41.30, gmChg: -6.73, share: 41.0, k: "K8" },
    { name: "国内", rev: 14.95, yoy: -7.96, gm: 25.81, gmChg: 6.36,  share: 59.0, k: "K8" },
  ];

  // 空头命题检验台（报告 §四）
  const bearBench = [
    { id: "S9", prop: "利润-现金流背离", verdict: "confirmed",
      result: "确认 · 置顶关注",
      evidence: "2026H1 经营现金流净额 0.91 亿，同比 -67.03%，与归母 +134.49% 显著背离",
      conf: "High", k: "K4", src: "中报摘要" },
    { id: "IMP", prop: "减值吞噬利润", verdict: "confirmed",
      result: "确认 · 置顶关注",
      evidence: "2026H1 资产减值损失 0.72 亿，占利润总额 47.81%；2024FY 减值 1.51 亿，属持续性侵蚀而非一次性事件",
      conf: "High", k: "K5", src: "中报全文非主营业务分析表 + iFinD 历年" },
    { id: "S6", prop: "减持/质押背离", verdict: "falsified",
      result: "证伪",
      evidence: "前十大股东（含实控人 34.08%）均无质押/冻结；2026 年 1-8 月 62 条公告无减持、无立案、无警示函",
      conf: "High", k: "K13", src: "中报摘要股东表 + 公告列表扫描" },
    { id: "GW", prop: "商誉减值悬顶", verdict: "weak",
      result: "弱风险",
      evidence: "商誉 1.69 亿，仅占总资产 1.2%，敞口有限",
      conf: "High", k: "K6", src: "中报资产负债表" },
    { id: "JG", prop: "集采传导（链 D 反向分支）", verdict: "pending",
      result: "存疑待证",
      evidence: "国内收入 -7.96% 与国内制药 capex 疲软的因果链未经独立数据验证",
      conf: "Low", k: "K8", src: "仅标注，无数值来源" },
    { id: "H2", prop: "耗材放量兑现", verdict: "partial",
      result: "部分证伪",
      evidence: "生物工艺耗材收入 -1.15% 未放量，但毛利率 +18.22pct 显示结构与降本改善；“放量”命题降级为待证",
      conf: "Medium", k: "K9", src: "中报全文分产品表" },
    { id: "H3", prop: "出海改善盈利质量", verdict: "partial",
      result: "量升价降 · 部分成立",
      evidence: "国际收入 +29.24%、占比升至 41%，但国际毛利率 -6.73pct；仍远高于国内（41.3% vs 25.8%）",
      conf: "Medium", k: "K8", src: "中报全文分地区表" },
    { id: "S2", prop: "应收恶化", verdict: "falsified",
      result: "本期未获支持",
      evidence: "应收账款 15.91 亿，较期初 +0.3%，增速低于收入增速 +4.37%",
      conf: "High/Medium", k: "K7", src: "中报全文合并资产负债表" },
  ];

  // 估值锚（报告 §五，conf=Medium 层）
  const valuation = {
    close: 14.99, closeDate: "2026-08-27", mcap: 114.8,
    peWind: 55.25, pbLf: 1.45, psTtm: 2.21,
    peSelf: 43.8, ttmSelf: 2.62, ttmFormula: "2.00 − 0.46 + 1.08",
    peer: { name: "楚天科技", code: "300358.SZ", pe: 15.92, pb: 1.18, mcap: 65.6, h1np: 1.56, h1rev: 26.2 },
  };

  // 治理与股东回报（K13/K14/K15）
  const governance = {
    dividend: "10 派 0.66 元", payoutRatio: 46.6, divBase: "760,848,039 股（扣除回购股份）",
    buyback: 498, buybackPct: 0.65,
    holders: 29299, holdersYoy: -8.73, holdersQoq: -2.82,
    actualController: "郑效东", controllerPct: 34.08, totalShares: "765,828,040 股",
  };

  // 自述链：迭代叙事（iteration_log.json + 报告 §一 + charter_v0.1/v1.0）
  const iterations = [
    { round: "R1", version: "0.1", action: "外骨骼元提问：提示词缺陷解剖",
      output: "缺陷表 v1（D1-D5）+ 宪章 v0.1", result: "发现 1 条 High 缺陷（“信息霸权”合规风险）",
      defects: 5, high: 1, ts: "2026-08-27T19:12:09+00:00" },
    { round: "R2", version: "1.0", action: "三角色并行审查（多头/空头/风控合规官）",
      output: "19 条缺陷（7 条 High）", result: "宪章 v0.1 不放行，重整出 v1.0",
      defects: 19, high: 7, ts: "2026-08-27T19:12:09+00:00" },
    { round: "R3", version: "1.0+", action: "外骨骼扰动复核（4 组反例攻击）",
      output: "缺陷表 v3（P-2/P-3/P-4 残留 Med）+ D6", result: "有条件首肯：无新增 High，放行数据轮",
      defects: 4, high: 0, ts: "2026-08-28" },
    { round: "R4", version: "1.1", action: "实战数据轮（iFinD×8 + Wind×3 + 中报原文 PDF×2 + 证据链脚本校验）",
      output: "分析报告 v1.0 + 15 条证据链", result: "脚本校验 0 错误，有限收敛达成",
      defects: 0, high: 0, ts: "2026-08-28" },
  ];
  const defectFixes = [
    ["D1", "“扫描未来 skill”不可字面执行 → 每轮迭代前 ls 技能库巡检制"],
    ["D2", "“信息霸权” → 中性化为“公开信息结构化处理流程”（合规红线，禁止回退）"],
    ["D3", "“尽量多 Swarm”与“最小作用量”矛盾 → 按命题风险分级路由 Swarm 规模"],
    ["D4", "cron 无人值守 → 自动化三角色 + 产物 L1 标注 + 首行免责锚硬编码"],
    ["D5", "未指定决策用途 → 默认“研究观察”，显式标注假设"],
    ["D6", "cron 新会话无法继承上下文 → 任务描述自包含并指向宪章落盘路径"],
  ];

  // K 锚表（data/claims.json 共 15 条，按原始顺序）
  const claims = [
    { k: "K1", claim: "300171.SZ 证券简称为东富龙，实控人郑效东持股34.08%，总股本765,828,040股",
      src: "官方底表", date: "2026-08-28", conf: "High",
      test: "深交所/巨潮资讯网查300171公司概况",
      url: null, noUrl: "iFinD插件返回(C1通道)，公开复核入口=深交所官网>300171公司资料" },
    { k: "K2", claim: "2026H1营业收入25.35亿元，同比+4.37%",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报摘要'主要会计数据'表核对2,534,573,184.09元；已与Wind 25.3457亿交叉一致",
      url: "http://www.cninfo.com.cn（巨潮资讯网>300171>2026年半年度报告摘要）", noUrl: null },
    { k: "K3", claim: "2026H1归母净利润1.077亿元，同比+134.49%；扣非归母0.944亿元，同比+270.73%",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报摘要核对107,678,132.77元与94,443,548.36元",
      url: "http://www.cninfo.com.cn（巨潮资讯网>300171>2026年半年度报告摘要）", noUrl: null },
    { k: "K4", claim: "2026H1经营活动现金流净额0.911亿元，同比-67.03%",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报摘要核对91,104,156.17元",
      url: "http://www.cninfo.com.cn（巨潮资讯网>300171>2026年半年度报告摘要）", noUrl: null },
    { k: "K5", claim: "2026H1资产减值损失0.724亿元，占利润总额47.81%，主要为存货跌价、合同履约成本及合同资产减值",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报全文非主营业务分析表核对-72,433,460.68元",
      url: "http://www.cninfo.com.cn（中报全文'非主营业务分析'表）", noUrl: null },
    { k: "K6", claim: "2026H1末合并合同负债37.13亿元，较期初36.23亿元+2.47%",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报全文合并资产负债表核对3,712,857,819.00与3,623,204,442.73；期初值与iFinD FY2025完全一致",
      url: "http://www.cninfo.com.cn（中报全文合并资产负债表）", noUrl: null },
    { k: "K7", claim: "2026H1末应收账款15.91亿元，较期初+0.3%，增速低于收入增速",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报全文合并资产负债表核对1,591,477,964.83",
      url: "http://www.cninfo.com.cn（中报全文合并资产负债表）", noUrl: null },
    { k: "K8", claim: "2026H1国际收入10.40亿元(+29.24%)，占比41.0%，毛利率41.30%；国内收入14.95亿元(-7.96%)，毛利率25.81%",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报全文'占比10%以上的产品或服务情况'分地区表核对",
      url: "http://www.cninfo.com.cn（中报全文分地区表）", noUrl: null },
    { k: "K9", claim: "2026H1生物工艺装备及耗材事业部收入7.16亿元(-1.15%)，毛利率36.41%(+18.22pct)",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报全文分产品表核对716,140,623.72元",
      url: "http://www.cninfo.com.cn（中报全文分产品表）", noUrl: null },
    { k: "K10", claim: "2025FY营收52.33亿元(+4.4%)，归母净利2.00亿元；2024FY营收50.10亿元，归母1.94亿元；2023FY营收56.42亿元，归母6.00亿元",
      src: "官方底表", date: "2026-08-28", conf: "Medium",
      test: "巨潮资讯网核对2023-2025年报利润表",
      url: null, noUrl: "iFinD插件返回(C1通道)，公开复核入口=巨潮资讯网历年年报" },
    { k: "K11", claim: "2026-08-27收盘价14.99元，总市值约114.8亿元；Wind口径PE_TTM 55.25、PB_LF 1.45（注意：该PE大概率未纳入8-27晚披露的中报，存在滞后）",
      src: "官方底表", date: "2026-08-28", conf: "Medium",
      test: "任一行情软件核对300171最新价与PE_TTM；以中报更新后TTM重算",
      url: null, noUrl: "iFinD/Wind插件返回(C1通道)" },
    { k: "K12", claim: "以中报更新后归母TTM≈2.62亿元（2.00-0.46+1.08）自算PE≈43.8倍；可比公司楚天科技PE_TTM 15.92、市值65.6亿、2026H1净利1.56亿",
      src: "官方底表", date: "2026-08-28", conf: "Medium",
      test: "Wind核对300358.SZ指标；PE自算值可用计算器复现",
      url: null, noUrl: "Wind插件返回+自算推导" },
    { k: "K13", claim: "2026H1前十大股东无质押/冻结记录；2026年1-8月公告中无减持、无立案、无警示函；2025年报与2026中报均含'计提资产减值'与'会计政策变更'公告",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "巨潮资讯网300171公告列表逐条核对",
      url: "http://www.cninfo.com.cn（中报摘要股东表+公告列表）", noUrl: null },
    { k: "K14", claim: "2026H1中期分红预案每10股派0.66元(以扣除回购股份后760,848,039股为基数)；回购专户持股498万股(0.65%)",
      src: "监管平台", date: "2026-08-28", conf: "High",
      test: "中报摘要重要提示节核对",
      url: "http://www.cninfo.com.cn（中报摘要+利润分配公告）", noUrl: null },
    { k: "K15", claim: "股东户数29,299户，同比-8.73%、环比-2.82%，筹码趋于集中",
      src: "官方底表", date: "2026-08-28", conf: "High",
      test: "中报摘要'报告期末普通股股东总数'核对",
      url: null, noUrl: "iFinD插件返回，与中报摘要股东总数29,299一致" },
  ];

  // top3_likely_wrong（报告 §七）
  const top3Wrong = [
    { n: 1, claim: "自算 PE≈43.8 倍",
      why: "TTM 分母依赖 2025H1 归母 0.46 亿的 iFinD 单源值，若该值为调整后口径差异则会偏移。",
      falsify: "巨潮资讯网下载 2025 年半年报原文核对归母净利润。" },
    { n: 2, claim: "利润修复质量有支撑（扣非增速高于归母）",
      why: "2025H1 扣非基数仅 0.25 亿，低基数下的高增速外推价值弱；且经营现金流 -67% 与之矛盾。",
      falsify: "待 2026Q3 报告验证扣非绝对额是否站上季度 0.5 亿+ 平台。" },
    { n: 3, claim: "订单企稳（合同负债 +2.47%）",
      why: "合同负债含税率与订单结构变化影响，且 2026 年存在“会计政策变更”公告，口径可比性未完全排除。",
      falsify: "读中报全文“会计政策变更”附注，核对合同负债口径是否受影响。" },
  ];

  // 语义审计（data/semantic_audit.json 原样转录）
  const semantic = {
    stats: { charCount: 5709, sentenceCount: 114, hedgingHits: 2,
             hedgingDensity: 0.35, hedgingThreshold: 15.0,
             counts: { undefinedTerm: 7, ambiguousTerm: 5, danglingReference: 2 } },
    findings: [
      { type: "undefined_term", subtype: "abbreviation", text: "L1", si: 0, detail: "缩写首现 ±30 字内无定义标记（即/是指/（ 等），W4 私人语言警示入口" },
      { type: "ambiguous_term", subtype: "polysemy_occurrence", text: "表现", si: 8, detail: "常见多义词出现，W1 用法一致性检查入口" },
      { type: "undefined_term", subtype: "abbreviation", text: "D4", si: 22, detail: "缩写首现 ±30 字内无定义标记，W4 私人语言警示入口" },
      { type: "undefined_term", subtype: "abbreviation", text: "D5", si: 23, detail: "缩写首现 ±30 字内无定义标记，W4 私人语言警示入口" },
      { type: "ambiguous_term", subtype: "polysemy_occurrence", text: "窗口", si: 27, detail: "常见多义词出现，W1 用法一致性检查入口" },
      { type: "undefined_term", subtype: "abbreviation", text: "Q1", si: 37, detail: "缩写首现 ±30 字内无定义标记，W4 私人语言警示入口" },
      { type: "undefined_term", subtype: "abbreviation", text: "YoY", si: 45, detail: "缩写首现 ±30 字内无定义标记，W4 私人语言警示入口" },
      { type: "undefined_term", subtype: "jargon", text: "制药工程", si: 49, detail: "专业词首现 ±30 字内无定义标记，W3 家族相似边界/W4 入口" },
      { type: "undefined_term", subtype: "jargon", text: "食品工程", si: 50, detail: "专业词首现 ±30 字内无定义标记，W3 家族相似边界/W4 入口" },
      { type: "dangling_reference", subtype: "no_antecedent", text: "此句为", si: 81, detail: "「此句为」的前文未找到先行词「句为」，R1 指称消解检查入口" },
      { type: "dangling_reference", subtype: "no_antecedent", text: "该值为调整", si: 87, detail: "「该值为调整」的前文未找到先行词「值为」，R1 指称消解检查入口" },
      { type: "ambiguous_term", subtype: "polysemy_occurrence", text: "平台", si: 91, detail: "常见多义词出现，W1 用法一致性检查入口" },
      { type: "ambiguous_term", subtype: "context_conflict", text: "平台", si: 91, detail: "同一多义词出现于 2 个不同语境（共 2 次），疑似用法漂移候选" },
      { type: "ambiguous_term", subtype: "polysemy_occurrence", text: "平台", si: 109, detail: "常见多义词出现，W1 用法一致性检查入口" },
    ],
    notes: "全部为启发式候选（candidate），须人工对照 references/semantic_precision.md 清单裁决；语义审计结论 conf 记方法论档（喂引擎按 assumed）。",
  };

  // 哈希链（data/hash_chain.json 全 18 节点）
  const hashChain = {
    generatedAt: "2026-08-27T19:14:43.768218+00:00",
    root: "256cf1f297841faea95bd0667614f25e60a389062c917fc4996e9d8193fa0a85",
    nodes: [
      { file: "charter_v0.1.md", sha: "641e9bd00547edf54e8df8b972f7496206acc23588fb9123069abb05eda8884e", node: "f3ea42e3df56b8e7211cb34daaa4a3caea8b81debe2d75c6379f40078e1feae6", prev: "0000000000000000000000000000000000000000000000000000000000000000" },
      { file: "charter_v1.0.md", sha: "30caddf283bb74b5ad87d61602a1961f2cf8f27ecddf5e665763b3e39583946f", node: "51893c2ef941401e219530650d182d46f4a2fa974a56057f54bced1f26607ad4", prev: "f3ea42e3df56b8e7211cb34daaa4a3caea8b81debe2d75c6379f40078e1feae6" },
      { file: "东富龙300171_分析报告_v1.0.md", sha: "edf87c24268c4c772b5353863c064c1bf156cf90fe007b0ba86a2f2d872ea560", node: "973968ca61223106b19dcdacc708921d60d12320862e6664a374bb3a2833bed0", prev: "51893c2ef941401e219530650d182d46f4a2fa974a56057f54bced1f26607ad4" },
      { file: "iteration_log.json", sha: "779915c9f32127363ba2dfa1d091164976b8769e715ac82479f5cee64af1ae67", node: "629f7cc80d0802ca9520bb4e4f11f67c0f98329958c3c590098c28ae4332cb37", prev: "973968ca61223106b19dcdacc708921d60d12320862e6664a374bb3a2833bed0" },
      { file: "schedule_status.json", sha: "c384a759efb864795d078bbbfe78837bff7cbe570d1b1b52df95cf1b4f050472", node: "b159ead4ca8975e4fecb691ec602c459f511db935c724edd9a365ce36bcce9b9", prev: "629f7cc80d0802ca9520bb4e4f11f67c0f98329958c3c590098c28ae4332cb37" },
      { file: "data/claims.json", sha: "fc818930cbb04805ed1d5bb1db99f338bc39a78cd30cc88d193d094093c7e060", node: "4102f8137b82d6e641a0c71fc4b0bcbd71bc42cf7efd1f18592c0ff6b0e1a1e8", prev: "b159ead4ca8975e4fecb691ec602c459f511db935c724edd9a365ce36bcce9b9" },
      { file: "data/semantic_audit.json", sha: "dc0fed3e398cb4326dcb446f14bdaf4e4066abba0fe660440e9469fe112dff6e", node: "236d3f3bf41c19e13f9a141cf03380b3d9c8c1a0bbe16e13c114f958b3730aa3", prev: "4102f8137b82d6e641a0c71fc4b0bcbd71bc42cf7efd1f18592c0ff6b0e1a1e8" },
      { file: "data/h1_2026_abstract.pdf", sha: "d47c237c88301fd753af2903e4e37619664d2a2ba59390d021813aed3ad425d9", node: "8ee3efb198099606932e64f9ddc1482713f4e94ae795136471aec5a91efb5033", prev: "236d3f3bf41c19e13f9a141cf03380b3d9c8c1a0bbe16e13c114f958b3730aa3" },
      { file: "data/h1_2026_full.pdf", sha: "ff03d9d239c034eb960bd6791a78f6bdb2e80dc924d788a1d5ec4490c4e23290", node: "7e49e138c3cac3cd6e02b0d8249e54c2fd1d244f50f6829bf456ebf55b86436b", prev: "8ee3efb198099606932e64f9ddc1482713f4e94ae795136471aec5a91efb5033" },
      { file: "data/stock_info.csv", sha: "bb1aa35e7518a211a730bbf3a9ce77b0ff36ad19808bd92bac25f48a7254544f", node: "49960918f67eebd00e0619701ad41fed72baf90f4a1175a8eaf21b9d58329b53", prev: "7e49e138c3cac3cd6e02b0d8249e54c2fd1d244f50f6829bf456ebf55b86436b" },
      { file: "data/fs_2025fy.csv", sha: "73c8f752e86eb539d81f9160d2d03fa41a8ed104d1f126930088daa08ddb1855", node: "24fbd9f62290b18317f63dfd5384d6268f0616f3a77c50f84a5b100582547ba4", prev: "49960918f67eebd00e0619701ad41fed72baf90f4a1175a8eaf21b9d58329b53" },
      { file: "data/is_20260630.csv", sha: "fbe1c464ef3e6822b34c8aaa484cf2f3c4598fe3c18eae06d3df993e1617b28b", node: "030457d29e211b93f5b3df62b5a6af7b6590d0df39e280e1999104d5f8ae19fa", prev: "24fbd9f62290b18317f63dfd5384d6268f0616f3a77c50f84a5b100582547ba4" },
      { file: "data/is_2026q1.csv", sha: "4a8c401725d4d279a38fa52195e05f159fd27a3f364c915394117085f4be31c8", node: "67604251719d8735b7eb549d54048dfacd7e76ed4db73a8bc7d38dc2ee58620c", prev: "030457d29e211b93f5b3df62b5a6af7b6590d0df39e280e1999104d5f8ae19fa" },
      { file: "data/seg_2025fy.csv", sha: "c9ab23cc928552463b07094c6fa824acb0e16b4bac900783ade2cb5b8109ce95", node: "d2e23703dc234d36462a38f8dc1ebda723ed013376af570fe1a2afd34420ac88", prev: "67604251719d8735b7eb549d54048dfacd7e76ed4db73a8bc7d38dc2ee58620c" },
      { file: "data/holders.csv", sha: "af6c2d6ba8a8a1e6990499df4e58b2c2e6dc912f87cf2dd3d19c445ffe7924f8", node: "ec4c5b66a0b4f05ab2edbe1dad50aecf365d8fac22e92cf8bd96a8fc755e5ec4", prev: "d2e23703dc234d36462a38f8dc1ebda723ed013376af570fe1a2afd34420ac88" },
      { file: "data/ann_recent.csv", sha: "bbedd641aaaf55286ab60d43eb2091e67ca697ad5119dc3853ce84581ac3f3a4", node: "934317efbe487ea28e10f6128d3be6ee497ba6863a4e3e01b7737049520861f9", prev: "ec4c5b66a0b4f05ab2edbe1dad50aecf365d8fac22e92cf8bd96a8fc755e5ec4" },
      { file: "data/ann_2026h1.csv", sha: "141d15ecf0c15f1a268dd296980298b3c0e2fdb9bb2180fd20387e3f98ee8276", node: "557e0e60317719c9b5ebbcb21b905e8db3769f98ac8ed062ddb1d06651d4a342", prev: "934317efbe487ea28e10f6128d3be6ee497ba6863a4e3e01b7737049520861f9" },
      { file: "data/price_rt.csv", sha: "754fc823ed57b6c3e527e42664b21962f13020b7eb2a49ca74dd62122b517e61", node: "256cf1f297841faea95bd0667614f25e60a389062c917fc4996e9d8193fa0a85", prev: "557e0e60317719c9b5ebbcb21b905e8db3769f98ac8ed062ddb1d06651d4a342" },
    ],
  };

  // 排期（schedule_status.json）
  const schedule = [
    { p: "P0", task: "cron 每日 04:00 任务上线并自检首行免责锚", acceptance: "list_cron_jobs 可见；无增量日输出跳过", status: "done" },
    { p: "P1", task: "舆情/研报维度补齐（Gildata/xhcj 路由）", acceptance: "舆情命题线索表落盘", status: "pending" },
    { p: "P1", task: "iFinD 收录中报后双源全字段对账", acceptance: "差异 <0.5% 销记，>2% 入 top3_likely_wrong", status: "pending" },
    { p: "P2", task: "2026Q3 报告季扰动复测", acceptance: "预注册触发线（扣非/现金流/合同负债）复核", status: "pending" },
  ];

  const disclaim = "L1原型级 · 自动生成未经人工复核 · 不构成投资建议 · 数据截至 2026-08-28 · 内部研究勿外传";

  return { income, h1_2026, leading, segments, regions, bearBench, valuation,
           governance, iterations, defectFixes, claims, top3Wrong, semantic,
           hashChain, schedule, disclaim };
})();
