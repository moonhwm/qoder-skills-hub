---
name: cross-session-workflow-bridge
description: "继续项目/加载项目环境时首先触发的跨会话工作流衔接伞形技能：任何新对话中说「继续项目」「加载项目环境」「继续上次进度」即命中本技能，规程=读双索引（upload 下的 MASTER_INDEX 与 MASTER_SKILL_INDEX）→ 列项目卡 → 确认首任务，把「每次手动点 N 个技能插件按钮」降为「一句话 + 至多一次确认」。覆盖跨对话、跨会话、跨项目的上下文衔接、长会话/模式切换交接（handoff，Kimi 2.6 快速 ↔ K3 长对话集群）、技能全量导入（加载技能/导入技能/维护技能索引 MASTER_SKILL_INDEX）、工作流衔接与技能间管线（pipeline）数据契约、多项目并行上下文切换、持久层地图（「技能安装位」/ 跨会话持久，「上传区」/ 用户文件区、唯一实证跨 lineage 共享层，「输出区」/ 仅同 lineage 保留、跨 lineage 不可见、运行环境不保留）。当用户说跨对话、跨会话、跨项目、交接、handoff、继续项目、加载技能、导入技能、技能索引、工作流衔接、管线、上次进度、MASTER_INDEX、接着上次、恢复上下文、换会话继续、项目交接、把成果带给下个会话时触发；也覆盖**跨 AI/跨模型交接**（Kimi↔腾讯助手甲/ChatGPT/外部模型甲 等）：握手文档、任务委托单、互传通道选型、助手甲侧任务名单、批判权责划分。触发词补充：「交给助手甲」「助手甲交接」「跨AI协同」「握手文档」「给另一个AI的指令」「连接 kimi claw」「本地桌面 agent 接管」。中文名：项目接力桥"
---
<!-- v1.8（2026-09-02，修改人：skill-evaluation/Orchestrator）\这是中文解释：持久层地图修订——output 降级为「同 lineage 保留，跨 lineage 不可见」、upload 升为「唯一实证跨 lineage 共享层」，新增跨 lineage 接力纪律；实证=2026-08-27 双树全量比对（两会话 output 各存 8/23 历史文件但互不同套；他 lineage 的 rumor-verify 报告 19,986B 本 lineage 零命中），用户 2026-08-29 选项 B 拍板；pipeline_contracts.md §4 同步。注意：A 线工作副本（<输出区>/skills/，v1.9.3）已先行同义修订，两线编号分叉未合并，安装位口径以本件为准；委派函 correspondence/CL-SKILL-20260829-DT-02 -->
<!-- v1.7（2026-08-29，修改人：skill-evaluation/Orchestrator）\这是中文解释：cross_ai_coordination.md 新增 §12 本地桌面 agent 接管规程（Kimi Claw 完整握手闭环实证：文件摆渡硬约束/质询四问/判定权保留云端/回执验收两件套/双通道冗余期/cron 表达式偏差登记）；description 触发词补「本地桌面 agent 接管」「Kimi Claw」 -->
<!-- v1.6（2026-08-28，修改人：skill-evaluation/Orchestrator）\这是中文解释：落地 2026-08-27 会话未装上的 handoff_protocol v2.0（交接五件套+可选第六件 SKILL 生成规格 skill_gen 块）；持久层地图补充「<技能安装位> 运行期常只读」实测口径与技能写回规程（2026-08-24~28 至少 6 个会话 touch 预检返回 Read-only file system） -->
<!-- v1.5（2026-08-26，修改人：Orchestrator/Kimi K3）\这是中文解释：新增线程拓扑§9（平台版本甲/K3/集群甲×助手甲四引擎+专家模式）、一致性行为人协议§10、自主提问补全清单§11 -->
<!-- v1.4（2026-08-26，修改人：Orchestrator/Kimi K3）\这是中文解释：新增跨AI协调模块（cross_ai_coordination.md+握手模板+HTML打包器+COS通道vendor）；含依赖内置化纪律（vendoring置顶）与质询机制 -->
<!-- v1.3（2026-08-24）\这是中文解释：本轮新增递归回灌胶囊协议 -->

# 项目接力桥（cross-session-workflow-bridge）

在任何新对话中用户说「继续项目」「加载项目环境」时，**先执行本技能的「新会话开场规程」再动手**。本技能管跨会话衔接、交接与技能导入；沙箱内单项目运维（权限/pytest/git/504）由 `sandbox-project-ops` 负责，见文末分工节。

## 持久层地图（第一关键知识，写文件前先查这张表）

| 路径 | 持久性 | 用途 |
|---|---|---|
| `<技能安装位>/` | **跨会话持久，但运行期常只读**（2026-08-24~28 多会话实测 `touch` 预检返回 `Read-only file system`，条目 root-owned） | 用户技能安装位，自建技能以此为准；写入前先预检，只读时走下方「技能写回规程」 |
| `<上传区>/` | **用户文件区，唯一实证跨 lineage 共享层**（2026-08-27 实证：K3 会话写入的执行单在诊断会话 lineage 可见） | MASTER_INDEX、交接包、可信数据集、correspondence 函件归档 |
| `<输出区>/` | **同 lineage 保留，跨 lineage 不可见**（2026-08-27 双树全量比对实证：两会话 output 各存 8/23 历史文件但互不同套；他 lineage 的 rumor-verify 报告 19,986B 本 lineage 零命中——此前「实测跨会话保留」判据系同 lineage 残留误读） | 当前会话工作区兼同 lineage 产物区；**运行环境不保留**（pip 安装的包、.git、/tmp 均随沙箱重置） |
| `/app/.agents/skills/` | 内置库，**用户写入不持久** | 禁止把自建技能装这里（真实事故：amap-travel-skill 装此处两次，随沙箱销毁全丢） |

技能持久化仍以 `<技能安装位>/` + `.skill` 包备份为准（双保险）。本表口径已与 sandbox-project-ops 统一。

**跨 lineage 接力纪律（2026-08-29 用户拍板）**：交接五件套、回灌胶囊、协调函等凡需跨 lineage 接力的产物，一律落 `<上传区>/` 或 `.skill` 包；output 仅作同 lineage 周转。引用任何「既往会话产出」前先 `ls` 核验本 lineage 可见性，不可见即按缺失处理、从 upload/.skill 重建，禁止凭索引记忆假设 output 文件仍在。

**技能写回规程（改/装用户技能前必做）**：先 `touch <技能安装位>/.wtest` 预检可写性。可写则直接改；**只读则禁止反复重试**，改走：① 在 `<输出区>/` 搭建补丁后的完整技能树 → ② `package_skill.py` 打成 `.skill` 包 → ③ 镜像到 `<上传区>/skill-dist-<YYYYMMDD>/` → ④ 登记写回队列（待写回清单，含目标路径与 diff 摘要），交由可写会话/集群通道执行或请用户手动安装；交付时向用户明示「未装入安装位，包在何处」。真实事故：2026-08-27 会话 handoff_protocol v2.0 编辑在只读位上连续失败、只在 output 留了副本，会话结束后险些全丢——只读环境下**先打包再迭代**，不要攒到收尾。

**每次产生重要成果，三选一立即落盘**：① 制成/更新 `<技能安装位>/` 下的用户技能；② 拷贝进 `<上传区>/`；③ 用 package_skill.py 打成 `.skill` 包并同时放 upload。禁止「迭代 20 版全在聊天里、零文件落盘」（真实事故：AAPP 协议单会话 v5.0→v3.13 纯聊天空转）。

## 新会话开场规程（说「继续项目」时按序执行）

0. **优先收胶囊而非全量对话**：先找项目目录下的回灌胶囊（`capsule*.md`，由
   `scripts/build_reentry_capsule.py` 生成），按胶囊【核验锚点】先 `ls` 核验再动手；
   只回灌完成任务所需的最小记忆层，禁止整篇旧对话回灌——协议见
   [references/reentry_capsule.md](references/reentry_capsule.md)。胶囊缺失再降级走下方全流程。
1. **读双索引**：两级查找——先 `ls <上传区>/`，找不到再查 `<输出区>/` 根，找到并读取项目主索引（`MASTER_INDEX*` / `总纲-00-归档索引*.md` 类文件，含【必读】硬结论、文档快捷码、版本日志、场景入口；**注意：output 根的索引文件仅同 lineage 可见**——2026-08-27 前观察到的「总纲-00-归档索引与版本说明.md 现存于 <输出区>/ 根」系同 lineage 残留，其他 lineage 会话不可见，跨 lineage 场景一律以 upload 副本为准，upload 缺失即视为缺失并重建）；技能索引同理按 upload → output 根顺序查找 `MASTER_SKILL_INDEX.md`，两级都不存在则跑 `scripts/build_skill_index.py` 现场生成。引用索引中的任何文件前先 `ls` 核验存在性——跨会话记忆可能引用从未落盘的东西（真实事故：用户记得有估值报告但盘上根本没有），核验失败就如实报告并从索引能找到的最新版本重建，**不要凭记忆编数据**。
   - **索引自检**：若索引生成日期与 `ls <技能安装位> | wc -l` 数量不符（索引条目数 ≠ 盘上技能数），即视为过期，重跑 `scripts/build_skill_index.py` 刷新。
2. **读【必读】硬结论**：索引中标注【必读】的文件全部读完再产出，后续产出不得与其矛盾；发现矛盾就改旧文件，不并存两套结论。
3. **列项目卡**：对每个活跃项目输出一行卡片——`项目名 | 目标 | 当前状态 | 下一动作 | 关键文件路径`。多项目并行时逐条确认本次推进哪个，防止张冠李戴。
4. **确认首任务**：把排序第一、可在本会话内完成的动作作为首任务，向用户报一句「本对话首任务：X」后**直接开始执行**，开场不是纯规划。
5. **按需加载技能**：对照 MASTER_SKILL_INDEX 列出与本任务相关的技能名请用户勾选（一次确认），见 [references/skill_import_mechanisms.md](references/skill_import_mechanisms.md)。

## 会话收尾规程（会话将尽/用户说「交接」「交接给下个会话」时执行）

1. **回写索引**：本会话产出的新文档全部登记进 MASTER_INDEX（快捷码、路径、一句话摘要），版本号诚实递增；产出不回写索引等于没交付。
2. **更新技能索引**：重跑 `python3 scripts/build_skill_index.py`，让新装/新改的技能进入 MASTER_SKILL_INDEX。
3. **做交接五件套**（长会话或模式切换如 Kimi 2.6 快速 ↔ K3 长对话集群时强制）：交接文档（现状/硬结论/未决项）、可信数据集、可运行引擎/脚本、状态看板 JSON、下会话首任务卡；**若本会话沉淀出可复用工作流，追加可选第六件——SKILL 生成块（skill_gen YAML）**，供 集群甲自动汇总生成 `.skill` 包。模板、状态看板 JSON schema 与 skill_gen 块规格见 [references/handoff_protocol.md](references/handoff_protocol.md)。真实案例：CSCI 城市舒适度项目已用此模式交接 集群甲。
4. **落盘核验**：`ls` 确认五件套都在 `<上传区>/`（或 .skill 包内），输出清单给用户。
5. **生成/更新回灌胶囊**：跑 `python3 scripts/build_reentry_capsule.py --project-dir <项目目录> --level L2 --out <项目目录>/capsule.md`，
   让下个会话能按最小层回灌而非搬整篇对话。

## 技能全量导入机制（用户核心诉求：换对话不想逐个点技能按钮）

平台按各技能 description 匹配自动触发，agent **无法编程强制平台勾选 UI 按钮**。三条机制把「每次点 N 个按钮」降为「一句话 + 至多一次确认」，诚实边界与操作细节见 [references/skill_import_mechanisms.md](references/skill_import_mechanisms.md)：

- **机制 A（伞形触发）**：本技能即伞——宽触发词命中后按开场规程读技能索引、列出相关技能、按任务加载。
- **机制 B（索引脚本）**：`python3 scripts/build_skill_index.py [--user-only]` 扫描 `<技能安装位>/` 与 `/app/.agents/skills/` 全部 SKILL.md frontmatter，生成 MASTER_SKILL_INDEX.md（技能名/触发词摘要/路径/一句话用途/是否用户技能）。
- **机制 C（元引用常驻）**：用户自创技能的 description 统一加「[项目技能]」前缀标签，便于一眼识别、批量勾选。

**禁止承诺做不到的全自动**（如「我帮你自动勾上所有技能」）。

## 管线数据契约（技能间对接）

一个技能的产出给另一个技能消费时，走统一 JSON 契约（两级字段要求）：`data_cutoff`（数据截止日）为唯一硬必填；`conf` 允许字符串等级 empirical/estimated/assumed（与 scoring_engine.parse_conf 对齐）；`top3_likely_wrong`（最可能错的三处）报告类产物必填、数据流 JSON 可选。已知链路：`claims-deep-audit` 命题评分卡 → `multi-dimensional-option-scoring` 的 dimensions；`commute-school-optimizer` 通勤维度 → 同上。完整生产者→消费者→schema 对照表见 [references/pipeline_contracts.md](references/pipeline_contracts.md)。新链路建立时先更新该表再对接。

## 跨项目交流（多项目并行）

- 每个项目维持一张**项目卡**（目标/状态/下一动作/关键文件路径），集中登记在 MASTER_INDEX 或各项目状态看板 JSON 中。
- 切换项目时：先读目标项目卡与【必读】文件，再动手；禁止把 A 项目的结论凭记忆带进 B 项目。
- 项目卡中的「下一动作」必须具体到「本对话可执行的一步」，不允许写「继续推进」这类空词。

## 跨 AI 协调（用户说"交给助手甲/跨AI协同/握手文档/连接 kimi claw/本地桌面 agent 接管"时触发）

规程见 [references/cross_ai_coordination.md](references/cross_ai_coordination.md)。要点：
1. **每次跨模型交接必须产出握手文档**（模板 [assets/handshake_template.md](assets/handshake_template.md)）：TL;DR/证据三态/输出骨架/硬约束/执行指令/**质询清单+致谢**——无质询的握手无效。
2. **分工矩阵**（证据状态见原文）：微信生态获取可试助手甲（P+推断级，待基准题证伪）；犀利批判/沥干/最终判定**保留在本侧不委托**。
3. **互传首选单文件自包含 HTML**：`python3 scripts/pack_handoff_html.py --out handoff.html <文件…>`（任何模型可读、绕开压缩包兼容问题）；>100MB 才降级 COS 预签名（vendor/cos_upload.py，24h 有效期须明示）。
4. **停止规则**：内容不是预期类型→停解析即告知；三次握手不收敛→升级用户做选择题，禁止模型间无限往返。
5. **依赖内置化（vendoring）纪律置顶**：外部依赖第一时间克隆进技能 vendor/（GitHub 404 失效先例），体积不设限——此为用户明确要求的顶格条款，优先级高于精简原则。
6. **本地桌面 agent 接管**（Kimi Claw 类）：云端路径本地不可达→用户摆渡文件；判定权保留云端；回执须过理解复述抽验；冗余期云端 cron 不先撤——完整规程见原文 §12。

## 与 sandbox-project-ops 的分工（引用不复制）

- **sandbox-project-ops**（<技能安装位>/）：管沙箱**内部**运维——双 uid 权限冲突、pytest/git 环境重建、长测试后台轮询、<输出区> 根目录归档细节、【自主推进排期】执行细则。遇到 Permission denied / 504 / git 丢失时去加载它。
- **本技能**：管**跨会话边界**——持久层选址、开场/收尾规程、交接五件套、技能导入、管线契约、多项目切换。两者互补，MASTER_INDEX 归档约定以其原文为准，此处不重复。

## Resources

- `scripts/build_skill_index.py`：生成/刷新 MASTER_SKILL_INDEX.md（纯标准库，`--user-only` 只扫用户技能）。
- `scripts/build_reentry_capsule.py`：装配递归回灌胶囊（纯标准库，读 status_board.json /
  iteration_log.json，`--level L0/L1/L2` 三档上限 50/200/800 字，超限自动截断并警告）。
- `references/reentry_capsule.md`：递归回灌创新方案——分层记忆架构（L0-L3）、胶囊固定槽位、
  自指式执行指令、差异回灌、质量自检三问、诚实边界。
- `references/handoff_protocol.md`：交接五件套模板 + 状态看板 JSON schema + 可选第六件 SKILL 生成规格（skill_gen 块）。
- `references/skill_import_mechanisms.md`：机制 A/B/C 详述 + 诚实边界。
- `references/pipeline_contracts.md`：技能间数据契约表。
- `references/skill_naming_paradigm.md`：技能中文命名范式（技术名不变、中文名为别名）+ 19 项别名表。**何时读**：创建新技能、改技能中文名、批量维护技能命名/索引时必读；新技能必须先按此范式取中文名并登记进 `skill_aliases.json`。
- `references/cross_ai_coordination.md`：跨 AI 协调规程（分工矩阵/互传通道限制表/握手模板/基准题/vendoring 纪律/线程拓扑§9-11/本地桌面 agent 接管规程§12）。
- `assets/handshake_template.md`：跨 AI 握手文档模板（六节+质询清单）。
- `scripts/pack_handoff_html.py`：交接包单文件 HTML 打包器（纯标准库，实测通过）。
- `vendor/cos_upload.py`：腾讯云 COS 预签名上传通道（vendored 2026-08-26；依赖 cos-python-sdk-v5 属无可奈何降级可选项）。
