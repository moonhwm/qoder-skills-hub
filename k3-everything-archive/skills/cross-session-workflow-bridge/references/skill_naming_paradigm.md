# 技能中文命名范式（skill naming paradigm）

技术名（目录名 / frontmatter `name`）是系统身份，**永不变更**；中文名是人类可读别名，
供索引、对话、交接场景快速理解技能用途。本文件是中文名的唯一权威规范。

## 五条范式规则

1. **长度**：2–6 个汉字为主（如「套磁信教练」4 字、「证据链核查员」6 字）。
2. **结构**：场景/对象 + 角色/工具。前半说干什么事（套磁信、证据链、通勤择校），
   后半说以什么身份/形态出现（教练、核查员、参谋、管家、指南、引擎、手册）。
3. **望文知义**：非技术人员看到名字能猜对用途，不依赖英文或行话；避免生造词。
4. **description 固定格式**：中文名写在 SKILL.md frontmatter description 字符串
   **尾部**，格式 `中文名：XX`（引号内末尾，不破坏 YAML；description 其余内容不动）。
   H1 标题行同步为 `# 中文名（技术名）`。
5. **索引列**：`scripts/build_skill_index.py` 用正则 `中文名[：:]\s*([^，。,"\']+)`
   从 description 提取中文名写入 MASTER_SKILL_INDEX.md「中文名」列；提取不到时
   回退查 `<注册处>/skill_aliases.json`，
   仍无则显示 `—`。

## 新技能创建流程（先取中文名）

1. 起技术名（kebab-case 英文，目录即身份，起好后不改）。
2. **立刻按五条范式取中文名**，并登记进
   `<注册处>/skill_aliases.json` 的 `aliases` 表。
3. 写 SKILL.md 时：H1 用 `# 中文名（技术名）`；description 尾部追加 `中文名：XX`。
4. 跑 `scripts/build_skill_index.py` 刷新索引，确认「中文名」列出现新名。
5. 改名（仅中文名可改）：同步改 H1、description 尾部、aliases 表三处，再刷索引。

## 现有别名表（19 项，以 skill_aliases.json 为准）

| 技术名 | 中文名 |
|---|---|
| evidence-chain-verifier | 证据链核查员 |
| iteration-convergence-ops | 迭代收敛管家 |
| cross-session-workflow-bridge | 项目接力桥 |
| commute-school-optimizer | 通勤择校参谋 |
| fusion-program-audit | 聚变择校核查员 |
| claims-deep-audit | 宣传打假核查员 |
| multi-dimensional-option-scoring | 多维打分参谋 |
| diffusion-dynamics-extension | 演化推演器 |
| medical-malpractice-criminal-review | 医疗事故刑事评估员 |
| grad-advisor-outreach | 套磁信教练 |
| sandbox-project-ops | 沙箱运维管家 |
| data-viz-gen | 数据图解生成器 |
| seo-copywriting-guide | SEO文案指南 |
| software-testing-guide | 软件测试指南 |
| k8s-cluster-ops | K8s集群运维手册 |
| rust-browser-pilot | 浏览器自动化引擎 |
| web-security-audit | 网站安全体检 |
| gitlab-cli-guide | GitLab命令手册 |
| medical-career-transition | 医学转行指南针（新建中） |
