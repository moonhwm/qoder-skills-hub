# 300171 东富龙分析宪章 v0.1（R1 产出，未经三角色审查）
<!-- 模式:完整 | 毕业等级:L1原型 | 未验证项:三角色审查未做、数据接口未连通 -->

## 0. 迭代机制缺陷修正（对原始提示词）
- D1 未来 skill 扫描 → 改为每轮迭代前 `ls` 技能库巡检（本轮已扫：user 39 个 / builtin 全量）
- D2 "信息霸权" → 重定义为：公开信息(C1通道及以上)的结构化处理优势，禁止任何非公开信息暗示
- D3 Swarm 规模 → 按 source-semantics-sentinel 最小作用量路由：R-高命题走高通道多源，R-低命题单源即停
- D4 cron 无人值守 → 自动化三角色由子代理扮演，产物标注 L1，用户复盘后才升级
- D5 用途假设 → 默认"研究观察"，显式标注，不作买卖建议

## 1. 标的与研究边界
- 标的：300171.SZ 东富龙（制药装备，创业板）
- 研究问题：基于公开信息的基本面-估值-风险三维审视，输出 conf 分级结论
- 边界：不使用任何非公开信息；不构成投资建议；数据截止以接口返回为准并标注 data_cutoff

## 2. 数据接口路由（A股 → iFinD 优先，Wind 兜底交叉）
- 公司概况/股东：iFinD profile + holders
- 财务三表（近3年+最新季报）：iFinD financial statements
- 行情与估值：iFinD price + Wind get_stock_price_indicators 交叉
- 公告与舆情：Wind financial_docs / xhcj-news / Gildata sentiment
- 行业地位：公开研报摘要（Gildata）+ 官网/年报

## 3. 三角色审查编制（R2 执行）
- 角色A 多头研究员：找增长逻辑与催化剂
- 角色B 空头质疑者：攻击每个因果节（rumor-chain-verifier 拆链法）
- 角色C 风控合规官：审查合规红线、数据口径、conf 分级是否诚实

## 4. 收敛标准（iteration-convergence-ops 第④拍）
- 连续2轮无 High 级错点
- 所有关键断言有证据链（evidence-chain-verifier 五步登记）
- 扰动测试通过（空头反例攻击后结论仍成立）

## 5. 交付纪律
- conf 三级标注；top3_likely_wrong 必附；落盘于 <输出区>/300171_iteration/
- 版本号诚实递增；每轮 ls 核验
