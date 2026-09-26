# verifier v1 验收标准（2026-09-02 创建）

| # | 标准 | 机检方式 |
|---|---|---|
| V1 | 保皇党报告枚举 ≥15 批准条款（A1-A15 全覆盖），每条有 死守/可改造/可委托 三分类之一 | grep 报告含 A1..A15 全编号 + 三分类词 |
| V2 | 隔离报告覆盖 8 个重名交集 + humanizer 三变体，每个有处置（留用/隔离/改名/废弃建议） | 8 名字逐个 grep + humanizer×3 |
| V3 | Loop 蓝图含六组件映射（Automations/Worktrees/Skills/MCP/Sub-agents/Memory-State）+ Maker/Checker + 硬门禁 + 防空转条款 | grep 关键词 |
| V4 | scholar 实查 ≥5 篇 loop 论文（arXiv id 在录），固化件落 skill-dist（不碰安装位） | grep arXiv 号 + 文件存在 |
| V5 | 用量参数变更三件套齐（事由+备份+报告），新旧闸值并录 | grep 报告字段 |
| V6 | 转录件处置：含密登记完成，待办吸收入册，**零明文秘密** | V8 联合 |
| V7 | 固定次序全链：锚 --verify PASS + 广播 id 在录 + msg_hash 先算 | chain_anchor --verify |
| V8 | 交付物无明文凭证：grep 两个密码串/ZAI key/两手机号/邮箱 在 registry 新文书与 output 交付中零命中（掩码形态豁免） | grep -c 各秘密模式 == 0 |
