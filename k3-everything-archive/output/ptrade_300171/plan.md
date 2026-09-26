# Plan: PTrade 量化策略 300171（东富龙）自主迭代至收敛

## 目标
基于 ptrade-guide 插件（ptrade-strategy-writer 技能），为 A 股 300171（东富龙）
生成符合恒生 PTrade 平台规范的可回测策略代码，并通过"生成 → 静态校验 → 评审 → 修复"
循环自主迭代，直至收敛（静态校验零错误 + 连续评审轮无新增问题）。

## 阶段设计

### Stage 0 — 准备
- 读取技能文件：/app/.agents/plugins/ptrade-guide/skills/ptrade-strategy-writer/SKILL.md
- 建立 verifier/ 目录与验收标准（verifier/v1/）
- 可选：用 ifind 插件取 300171 基本信息与近期行情特征，为策略参数提供依据

### Stage 1 — 初版生成（v1）
- 按技能规范生成 PTrade 策略 v1（必选事件函数 initialize/handle_data 等、Python 3.5 兼容、API 拼写规范）
- 运行静态校验（技能内置校验脚本，若有）

### Stage 2 — 迭代循环（v2…vn）
- 每轮：静态校验 + 独立评审子代理（reviewer）检查逻辑/规范/风控
- 发现问题 → 修复生成新版本 → 重新校验
- 校验记录全部追加到 verifier/runs/

### Stage 3 — 收敛判定与交付
- 收敛标准：静态校验 exit 0 且连续 1 轮评审无新增实质问题
- 更新 verifier/README.md 索引
- 交付最终策略 .py 至 <输出区>/ptrade_300171/

## 子代理分工
- coder/评审：策略生成与修复由主代理按技能执行；独立 reviewer 子代理做交叉评审

## 追加阶段 — 散户解读文档（第二轮目标）

### Stage 4 — 文档 verifier 建立
- verifier/v2/criteria.md：面向散户的通俗性、与策略代码的事实一致性、风险揭示完整性、合规措辞（禁承诺收益）
- verifier/v2/lint_doc.py：自动检查（禁用词、必备章节、长度）

### Stage 5 — 文档起草与迭代
- 起草 doc_v1.md（大白话 + 计算实例 + 风险提示）
- 独立 reviewer 子代理由散户视角评审 → 修复 → 复审至 PASS

### Stage 6 — 交付
- 加载 docx 技能，将终稿转 .docx
- 运行记录追加 verifier/runs/
