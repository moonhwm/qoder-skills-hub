---
name: stat-verdict-ops
description: "[项目技能] 统计裁决室——通用统计检验落地引擎（用户侧主权件，先证伪后裁决）。触发（满足任一）：①用户说「统计检验」「显著性」「p 值」「t 检验」「卡方」「U 检验」「KS」「Fisher」「比例检验」「效应量」「置信区间」「这组数据有没有差异」「是否显著」或等价表述；②需要判断两组/多组数据差异是否显著时；③需要给实验/回测/对比数据出统计裁决卡时；④窑核/红队需要统计口径互证时。覆盖：scripts/stat_test.py 六检验（单/双样本/配对 t、Mann-Whitney U、卡方独立性、Fisher 精确、双样本 KS、单比例 z）+假设前置闸（Shapiro 正态/Levene 方差齐，未过自动改道 Welch 或提示非参复核）+效应量（Cohen's d/rank-biserial/Cramér's V/OR/phat）+CI+裁决卡 json。不覆盖：回归/方差分析多因素（二期候选）、贝叶斯口径、样本量设计（二期）。中文名：统计裁决室。English triggers: statistical significance test, t-test chi-square, p-value verdict card, effect size CI."
metadata:
  version: "0.1.0"
---

# 统计裁决室（stat-verdict-ops）

> v0.1.0（2026-09-09）：创刊。依据=技能正交完备性检查 §3.2-缺口3（D1/D15 有方法论、无通用统计检验落地件，落点长期在临时脚本）+排期表 B8 项（机主令「继续推进相关实施」T3 批）。与内置 auto-stat-test 关系：本件为用户侧主权件，附先证伪裁决卡纪律。

## §0 定位与红线（先证伪后出口铁律落地）
- **假设前置闸**：t 检验先跑 Shapiro 正态+Levene 方差齐——方差未过自动改 Welch 并在裁决卡 notes 明示；正态存疑即注「建议 mwu 复核」；卡方期望频数 <5 即注「fisher 复核」。**禁裸报 p 值**。
- **裁决卡五要素**：检验名+统计量+p 值+效应量+CI（无 CI 者注明口径）；凡「显著/有效」结论必须带效应量，p<0.05 而效应量渺小者须明示「统计显著≠实际显著」。
- **多重比较**：同一批数据跑 ≥2 检验，裁决卡须注「多重比较未校正， exploratory 口径」；确认性结论须预设单一主检验。
- 结论标签「模型能力上限参考」；数据含 PII 先脱敏再入引擎；引擎本地 scipy，零出域。

## §1 六检验速查
| 场景 | 命令 | 前置闸 |
|---|---|---|
| 单组 vs 常数 | ttest --a | Shapiro |
| 两组独立 | ttest --a --b | Shapiro+Levene→Welch 改道 |
| 配对 | ttest --a --b --paired | 差值正态 |
| 非参两组 | mwu --a --b | 无 |
| 列联表 | chi2 --table（;分行） | 期望频数<5→fisher 提示 |
| 2x2 小样本 | fisher --table | 无 |
| 分布比较 | ks --a --b | 无 |
| 比例 vs 常数 | prop --x --n [--p0] | np0≥5，否则以二项精确 CI 为准 |

## §2 协同
- 窑核互证：bidding-ops §6 数值窑核/红队局的统计口径由本件出裁决卡，替代临时脚本（缺口3 原病灶）。
- 与 cognitive-exoskeleton「最小可执行落地」衔接：统计落地即本件，不再散写临时脚本。
- 二期候选册：ANOVA/回归/样本量设计/多重校正族（BH/Bonferroni）。

## §3 留痕与版本纪律
- 每次裁决留 json 卡入 runs；检验选择理由（为何 t 而非 mwu）须随卡留一句话。
- 版本三档同型立法；patch 静默不广播。

## 边界
不做多因素模型；不做因果断言（相关≠因果，裁决卡禁出现「导致」字样）；数据不足（n<3）如实报「检验力不足」不硬算。
