# plan.md — 白酒研报 + 600519 个股分析 + 谣言链核查（一体化管线执行计划）

- 任务口令：「生成白酒行业简版研报（单章约 500 字）+ 600519 简版分析 + 舆情走谣言链查询（核查 1 条传言）」
- 技能：`sector-stock-rumorchain-pipeline`（编排件，已读 SKILL.md + references/pipeline.md）
- 报告日落款：2026-09-01（data_cutoff 同）
- 模式声明：**评估简版——只产出执行方案 + 骨架交付物；不做真实大规模数据采集**（仅取 1–2 个真实公开数字并标注来源日期）。

## §1 触发与首动作留痕（SKILL §1：「得点进去搜」）

| 上游本体 | 状态 | 说明 |
|---|---|---|
| hifi-integration-umbrella/SKILL.md | 已读 ✔ | 确认仲裁序：红线件 → 验收闸(output-verdict-gate) → 调度 → 执法 → 执行件 |
| rumor-chain-verifier/SKILL.md | 已读 ✔ | 拆链六步 + Step 2.5 AI 二创资格审查 |
| rumor-chain-verifier/references/playbook.md | 已读 ✔ | 四类交付表模板 |
| rumor-chain-verifier/scripts/chain_check.py | 已读并用 ✔ | 链节判定表由脚本生成校验 |
| 伞 §0.1 前置链件（intl-case-intf / k3-territory-studies）与联动件 omni-exhaust-research-ops | **降级声明：占位** | 本评估为骨架模式，未实调；禁止假装已调度（伞 §5） |
| plugin-datasource-ops（S1 数据源路由） | **降级声明：占位** | iFinD/Wind/新华财经等金融插件本环境不可用，改用公开网络检索并逐数标注来源 |
| output-verdict-gate（S4 审议闸） | **降级声明：骨架** | 不跑真实 5 席盲评，仅留闸位 checklist；故本批产物标记「骨架稿，未经实闸」 |

## §2 五段式管线落位（顺序不可跳）

| 段 | 本评估执行方式 | 产出 |
|---|---|---|
| S1 数据采集 | 简版：公开检索 2 组真实数字（行业总量 + 茅台 2024 年报），每数字紧邻（来源，日期） | 数据卡（内嵌研报/核查报告） |
| S2 研报写作 | 大纲先行落盘 → 单章 500 字正文样例 + 600519 简版分析（短期/中长期两层、把握三档、风险前置、不做买卖指令） | `baijiu-report.agent.outline.md`、`baijiu-report.agent.final.md` |
| S3 舆情谣言链 | 核查 1 条传言（2025-09 网传「飞天零售价将上调至 1699 元」）：拆链→逐节定断→chain_check.py 校验→四表交付（不适用项显式声明） | `600519_rumor-chain_2026-09-01.md`、`chains/600519_chain.json` |
| S4 输出审议闸 | 骨架：仅列闸位 checklist（指纹/辩方/盲评/监管门均占位） | plan.md 本节 + 报告内标注 |
| S5 成稿与归档 | 简版：仅 md 落盘归档，docx 转换占位声明（在场字体规范：宋体/Times New Roman） | 本目录全部文件 |

## §3 实证事故清单对照（SKILL §3 硬性）

1. 量级数字必复算：行业收入/利润增速直接引官方口径原文，不做约数转述 ✔
2. 三层产物级联：chain.json → chain_check.py 生成判定表 → md 引用同一份输出，单一数据源 ✔
3. 修订声明≠落盘事实：写后读回复验 ✔
4. 悬空引用检查：全部来源日期 ≤ 报告日 2026-09-01 ✔
5. 互斥数字并置检查：研报内数字做算术自洽（茅台占行业收入比 ≈ 1741.44/7963.84 ≈ 21.9%，与「茅台份额约 21.87%」公开口径互洽）✔
6. 多口径并列：茅台「营业总收入 1741.44 亿 vs 茅台酒收入 1459.28 亿」双口径并列注明 ✔
7. 占位 URL 禁充数：仅引用检索实得来源；未取深链处注明检索路径 ✔

## 交付清单

| 类别 | 文件 |
|---|---|
| 计划 | `plan.md`（本文件） |
| 研报 | `baijiu-report.agent.outline.md`、`baijiu-report.agent.final.md` |
| 核查 | `600519_rumor-chain_2026-09-01.md`、`chains/600519_chain.json` |
| 卷宗 | 占位（S4 骨架声明，见上） |

> 免责：本批产物为评估骨架稿，非完整管线实盘输出；不构成投资建议。
