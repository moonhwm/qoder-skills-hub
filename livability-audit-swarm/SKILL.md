---
name: livability-audit-swarm
description: 城市宜居度/舒适度文档的蜂群审计与直接修复编排。当用户要求审计、核查、修复或治理「城市宜居度/住房压力/宿舍舒适度/就读舒适度」有关文档（评分系统文档、报告、配置、数据文件）时使用；也用于把宿舍舒适度等暂缓项纳入远景排期管理。核心流程：扫描登记 → 不少于五个审计助手并行分角色审计（参数/语义/证据/一致性/重复计量/留痕）→ 收敛判定 → 直接修改文档并三件套留痕（文头 AI_READER_NOTICE + CHANGELOG + k3_notices.jsonl，通知后续读取文件的 k3/k3集群 AI agent）→ 复验迭代至完全收敛。典型触发语："审计宜居度文档""宿舍舒适度排期""宜居/舒适度文档治理""按范式迭代到收敛""改完留痕通知 k3"。中文名：宜居文档审计蜂群。
---

# 宜居文档审计蜂群（livability-audit-swarm）

> v1.8：notice_stamp.py strip_legacy 灾难性回溯 P0 修复（对抗审查 F-B1/F-B2/F-B3，实战 L1「挂起 >12min」根因）——HASH/PCT 分支 `(?:#.*\n)*?` 改逐行形态 `(?:#[^\n]*\n)*?` / `(?:%[^\n]*\n)*?` 且去掉 re.S（消除 O(2^N) 回溯：合法块后 ≥~25 行连续 `#`/`%` 注释即挂起；修复后 5000 行进程内 ~0.01ms、CLI 盖章+幂等重盖 30/50/100/5000 行均 ~40ms；正常文件删除结果与旧正则逐字节一致）；HTML 分支保留 re.S 但 `.*?` 改有界 `.{0,4000}?`（未闭合块不再吞掉远处正文）；strip_legacy 按扩展名优先匹配对应注释样式（.py 不跑 HTML 分支——除非 HASH 未命中且文件确含 HTML 块起始标记才迁移）；未闭合旧块（BEGIN 在、END 缺失）不删除任何内容，stderr WARNING「未闭合留痕块，未迁移，请人工核查」，新块照常前插（change-notice-protocol.md §1 已补该语义）。retrieval_registry_check.py：evidence_band 正则 `\d` → `[0-9]`（F-A1，拒全角/数学 Unicode 数字）。文档同步：retrieval-paths.md §8 警告计数 16→17（v1.7 起 +1 缺 comparability 补登提示，存档 16 警告快照不再逐字节复现）、§9.4 口径剪切措辞改「comparability 取值 ≥2 种（full/proxy/stale 任意混杂）」与实现一致。测试：retrieval 套件口径厘清为 125 = R49+C16+M13+V18+W29（v1.6 注的 78 → v1.7 的 96 为同一套件逐版累加口径），v1.8 新增 W30–W33 Unicode 数字拒收 → **129 用例**；新增 tests/test_notice_stamp.py **17 用例**（计时/删除一致性/HTML 4KB 界/未闭合块/扩展名优先）；两套件双 TZ（UTC / Asia/Shanghai）全过；实战回归：评分系统 livability.py（曾挂起的真身）B5-002 幂等重盖产物与手工盖章逐字节一致、py_compile 通过。
>
> v1.7：检索组件口径与证据链登记（承接 case-4 grader 遗留）——retrieval-paths.md §4 schema 新增可选 comparability（full/proxy/stale，非法值报错）与 source_chain（direct/indirect；indirect 转引 conf 上限 C，标 A/B 报错，缺省视为 direct）字段，§5 补转引 conf 上限硬规则，§9.4 --merge 新增口径混杂检测（同 param 跨城 comparability 混杂→WARNING「口径剪切：该参数跨城横比须先对齐」并列城市分组；缺字段条目不参与、仅一次性 WARNING 建议补登），新增 §10「fusion 证据阶梯表」（E1 型质性评分裁决可复现标尺，对接 convergence-loop.md 定律⑥；fusion_* 可选 evidence_band 区间字符串，脚本仅校验格式；现值落在证据带外 → 偏差 finding medium 起）；retrieval_registry_check.py 同步（--help/docstring 已更）；测试 96→125 用例双 TZ 全过，case-4 六城 --merge 回归 exit 0。
>
> v1.6：检索组件对抗审查修复（F1–F9）——retrieval_registry_check.py：--merge 质性比较前先 float() 数值化（"10" 与 10.0 同值走数值分支）、calc_meta ±2% 判定加 1e-9 epsilon 容差且错误文案打印偏差到 4 位小数、calc_meta 偏离 §9 钉死值（hpi 90/2.8、rir 45）出 WARNING「偏离统一口径」、缺 calc_meta 且 unit 含 % 或 rir value>3 出「疑似百分数形态」WARNING、带 calc_meta 但 value 为 string 改判错误、merge/coverage 键与质性 value 比较前 strip 空白归一化；retrieval-paths.md §9.2/§9.3/§9.4 补脚本校验范围声明、rir area_sqm 不入回算说明、空白归一化与「--merge 检测含同文件内部重复」说明。
>
> v1.5：自建比值口径钉死——retrieval-paths.md 新增第 9 节「自建比值口径（硬规范）」（hpi = P×90÷(I×2.8)、rir = rent_1br×12÷I，户均人口统一 2.8 消解三城 2.62/2/3 口径分叉，calc_meta 强制随条目；第三方 hpi 须登记口径并与自建值分列）；retrieval_registry_check.py 新增 calc_meta 回算校验（偏差 >2% 错误、缺失 WARNING、字段须正的有限数）与 --merge 多文件模式（跨文件同 (city,param) 偏差 >5% 值冲突错误、≤5% 重复登记取新 WARNING、合并覆盖矩阵）；§4 schema 表补 calc_meta 行；单文件用法与 v1.4 行为零变化。
>
> v1.4：检索组件对抗审查修复——retrieval_registry_check.py 未来日期判定钉死 UTC（超 UTC 今日 +1 天才报错，容差内仅 WARNING）、URL 改整串匹配并拒纯 IP/userinfo、value 拒 NaN/Infinity 与空白串、coverage 只统计无错误条目且空 city 不计入；retrieval-paths.md 写死 183/365 天近似、声明未知字段容忍、偏差阈值表补 fusion_density/fusion_access/aspiration_proxy 三行（质性核查，无数值阈值）；步骤 1.2 补 exit 2 编排约定。
>
> v1.3：新增「检索路径」组件——references/retrieval-paths.md（L0–L4 分层信源、入口映射、检索纪律、entries.json schema、conf↔source_type 一致性、偏差阈值表）+ scripts/retrieval_registry_check.py（登记校验，exit 0/1/2）；evidence 角色新增按偏差阈值表复核检索参数值职责。
>
> v1.2（convergence_check.py v2.1 / notice_stamp.py 支持 .tex）：对抗复验后修复——同日多文件盖章的「文头块最新」tie-break 改按 change_id 取最大；空集不判停滞；severity/status 规范化（未知值 WARNING+保守处理，不静默放行）；数据错误（非对象条目/缺 id）统一 exit 2 + JSON errors 不 traceback；新增 `--verify-evidence` 防虚假关闭；.tex 用 `%` 行块留痕并纳入三方一致性；change_id 内嵌日期与 date 错位记 WARNING；行为保持类修复强制落盘冒烟脚本与入参。

对「城市宜居度/舒适度」有关文档执行：登记 → ≥5 助手并行审计 → 收敛判定 → 直接修复 + 留痕通知 → 复验迭代至完全收敛。不考虑预算（允许足量子代理与迭代轮次），但不允许跳过角色或复验。

## 触发后固定流程

### 步骤 0：盘点与排期检查

1. 跑 `scripts/livability_doc_scanner.py --root <项目根目录> --out <工作区>/registry.json` 全量扫描。
2. 对照 `references/livability-doc-registry.md` 核心层清单，**优先聚焦城市宜居度有关文档**；扫描新发现的文档补入扩展层。
3. 读 `references/dorm-comfort-roadmap.md`：检查宿舍舒适度等远景项的激活条件是否满足；满足则提出激活建议，否则维持 staged 并在报告中说明。

### 步骤 1：切包派发（不少于五个审计助手）

1. 跑 `scripts/audit_pack_builder.py --registry <工作区>/registry.json --out <工作区>/packs.json`（默认六角色）。
2. **外部检索登记（条件触发）**：若本轮审计需复核文档引用的外部参数值（hpi/rir/收入/榜单/分级等），先按 `references/retrieval-paths.md` 选信源并登记 `workspace/retrieval/entries.json`，跑 `scripts/retrieval_registry_check.py workspace/retrieval/entries.json`；exit 1（schema/越级/未来日期错误）须先修正再派审，WARNING（超期/隔离层/C 级进总分）随任务包下发给 evidence 角色；exit 2（用法/IO/JSON 解析错误，stdout 无 JSON）视为登记文件本身数据错误，先修复 entries.json/命令用法并重新校验，通过后再派审——自动化消费方不得对 exit 2 的 stdout 做 json.loads。
3. 按 `references/audit-roles.md` 派发 **≥5 个**审计子代理（默认六角色全派：parameter/semantic/evidence/consistency/double_count/trace），并行、只读、各自落盘审计报告。
   **降级路径**：若当前执行体无子代理派发权限，则由同一执行体按角色顺序完成六份独立报告，并在交付摘要显式声明「角色内联降级」；角色数不得减到五以下。
4. 上位判定基准文档清单由 `references/audit-roles.md` 规则 6 单源维护，派审时随任务包下发。

### 步骤 2：汇总与收敛判定

1. 汇总六份报告为 `findings.json`（格式见 `scripts/convergence_check.py` docstring）。
2. 跑 `scripts/convergence_check.py --findings findings.json`。
3. CONVERGED → 跳步骤 4 直接交付；NOT CONVERGED → 进步骤 3。

### 步骤 3：直接修复 + 留痕（按 references/convergence-loop.md 纪律）

1. 按 blocker→high→medium→low 顺序修复；修复权限由主代理执行或授权 coder 子代理。
2. **每处文档修改**后立即跑：
   `scripts/notice_stamp.py --file <被改文档> --change-id <CHG-YYYYMMDD-###> --reason "<审计问题编号+原因>" --audit-ref <审计报告路径> --agent <执行者>`
   三件套（文头块/CHANGELOG/k3_notices.jsonl）缺一不可，协议细节见 `references/change-notice-protocol.md`。
3. 更新 findings.json 状态，附修复证据（文件:行号 或 grep 命中数）。

### 步骤 4：复验迭代

1. 派 verifier 子代理复验：核实「已修」条目真实落盘（grep 验证，本项目有编辑未落盘前科）、未引入新矛盾、留痕完备。
2. 复验判敛使用 `convergence_check.py` v2.1 开关自动核验：
   - `--prev <上轮输出JSON>`：两轮 open blocker/high id 集合相同且非空 → STAGNATED（exit 3），须换修复策略；
   - `--usability-checks <被改的 .py/.json ...>`：py_compile / json.load 失败自动追加 USE- blocker；
   - `--consistency-dir <被改文档目录>`：文头块/CHANGELOG/k3_notices 三方 change_id 不一致自动追加 CONS- blocker；
   - `--verify-evidence`：对 closed 且带 `verify` 规范（grep 模式）的条目实跑证据复核，失败自动改回 open（防虚假关闭；closed 条目必须携带 verify 规范，见 references/convergence-loop.md）。
3. 复验发现问题 → 回到步骤 2；连续两轮停滞（含 STAGNATED）→ 换修复策略。
4. 直到 CONVERGED；主代理在轮次日志中累计 rounds_to_converge 与轮均关闭率（口径见 references/convergence-loop.md「收敛指标」）。

### 步骤 5：交付

- 交付摘要必须含：审计报告清单、findings 统计、全部 change_id 清单（会话级通知）、远景排期表当前状态。
- 所有产物落盘工作区，命名 `{主题}_{类型}_{日期}`。

## 实战验证摘要（v1.0 → v1.8，五真实案例）

- 版本演进：v1.0 基础闭环（扫描→六角色审计→两值判敛→修复留痕→复验）；v1.1 升级 checker v2（--prev 停滞比对/STAGNATED、--usability-checks、--consistency-dir 三方一致性、收敛指标口径）；v1.2 升级 checker v2.1，修复对抗审查（H1/H2/M1-M4）与 grader 实战 4 问：同日期 tie-break 改按 change_id、空集不判停滞、数据错误统一 exit 2、severity/status 规范化、新增 --verify-evidence、.tex `%` 块留痕、日期错位 WARNING、冒烟脚本强制落盘。
- 案例1（md+tex）：17 findings，rounds_to_converge=2，轮均关闭率 100%；grader 独立复验判**收敛声明成立**。
- 案例2（两个 .py）：15 findings；R2 曾因 P4 虚假关闭骗出 CONVERGED 被 grader 抓获作废，R3 勘误后真 **CONVERGED**（rounds=3），终态 closed 14（--verify-evidence 14/14）/open 1（low 带 accept_reason），冒烟 14/14 零行为改变。
- 已知局限：`--verify-evidence` 仅支持 type=grep（数值复跑/结构比对仍需 verifier 复核）；change_id 内嵌日期与 date 错位为历史存量（两案例 6/6 条），仅 WARNING 不阻断，新盖章起应一致。
- v1.3 新增「检索路径」组件（references/retrieval-paths.md 分层信源+登记规范 + scripts/retrieval_registry_check.py 校验）；v1.4 为三城实战后对抗审查修复——检索登记未来日期判定钉死 UTC+1 天容差（M1 时区翻车）、URL 整串匹配拒纯 IP/userinfo、value 拒 NaN/空白串、coverage 口径对齐。
- 案例3（三城检索+比对，v1.3 全链）：广州/深圳/长沙 × 8 参数共 24 条检索登记（exit 0，0 错误/7 警告），4 findings（0b/0h/1m/3l），rounds_to_converge=2，轮均关闭率 75%，`--verify-evidence` 3/3，纯注释级修复冒烟 19/19 零行为改变；grader 六项复验全过判**收敛声明成立**，检索质量 A-。
- 三城实战新教训（convergence-loop.md 定律⑤）：登记校验与收敛判定的跨机复跑必须同 verdict——同一份 entries.json 在 Asia/Shanghai exit 0、UTC exit 1（16 条未来日期错误）；校验结论须声明运行 TZ。
- v1.5 自建比值口径硬规范（retrieval-paths.md §9：hpi=P×90÷(I×2.8)、rir=rent_1br×12÷I，户均人口统一 2.8 消解三城 2.62/2/3 分叉，calc_meta 强制随条目 + 回算偏差 >2% 判错误）与 `--merge` 多文件校验（同 (city,param) 偏差 >5% 值冲突错误 / ≤5% 重复登记取新 / 合并覆盖矩阵）；v1.6 对抗审查 F1–F9 修复（质性比较先 float() 数值化、±2% 判定加 1e-9 epsilon、偏离钉死值 WARNING、空白归一化等，78 用例双 TZ 全过）。
- 案例4（六城整合比对，v1.5 全链 + v1.6 修复后复核）：广州/深圳/长沙 §9 重算 + 西安/合肥/南昌新城检索共 **49 条登记**（`--merge` 六城 exit 0，0 错误/16 警告全预期），6 findings（0b/1h/3m/2l），rounds_to_converge=2，轮均关闭率 83.3%，`--verify-evidence` 5/5，冒烟 26/26 零行为改变；grader 7/7 判**收敛声明成立**，检索质量评级 **A**。
- 案例4 新教训（convergence-loop.md 定律⑥）：质性评分冲突裁决须先读字典语义头注再定性——E1 合肥 INDUSTRY 0.75 vs 深圳 0.92 排序倒挂，经四维度头注（物理/材料/核/计算）定位为「合肥低估」而非「深圳虚高」（深圳高值由「计算」轴独立解释），数值不动、候选建议值 ≥0.90 排期独立评审。
- v1.7 检索组件三字段+阶梯表：comparability（full/proxy/stale）/source_chain（indirect 转引 conf 上限 C）/evidence_band 登记与校验、`--merge` 口径混杂检测（口径剪切 WARNING 列城市分组）、retrieval-paths.md §10「fusion 证据阶梯表」（E1 型裁决可复现标尺）；125 用例双 TZ 全过。
- v1.8 notice_stamp strip_legacy P0 回溯修复（案例5 L1 + 对抗审查 F-B1–F-B3）：HASH/PCT 分支 `(?:#.*\n)*?`（re.S）为 O(2^N) 灾难性回溯——49 行 `#` 注释文件盖章挂起 >12min（永不返回），修复改逐行形态 `[^\n]*` 并去 re.S 后 5000 行 ~0.01ms、CLI 30–5000 行 ~40ms；evidence_band `\d`→`[0-9]` 拒 Unicode 数字；检索 129 + notice_stamp 17 用例双 TZ 全过（convergence-loop.md 定律⑦）。
- 案例5（九城整合比对，v1.7 全链 + v1.8 修复后复核）：case-4 六城 + 成都/绵阳/上海共 **74 条登记**（`--merge` 九城 exit 0，0 错误/29 警告全预期，口径剪切 WARNING 捕获 3 组跨城混杂、indirect 转引全部压 C），11 findings（0b/0h/6m/5l），rounds_to_converge=2，轮均关闭率 90.9%，`--verify-evidence` 10/10，冒烟 33/33 零行为改变；grader 6/6 判**收敛声明成立**，检索质量评级 **A**；B5-002 手工盖章 + 字节级 parity 降级路径经 grader 逐字节复算成立。

## 硬条款

1. 审计助手**不少于五个**；角色可增不可减到五以下。
2. 审计轮只读；修复轮必须有对应审计结论支撑，禁止顺手重构。
3. 宿舍舒适度等远景项**不进总分**，只许筛选/标注层（详见 dorm-comfort-roadmap.md）。
4. 留痕即修复：无 notice_stamp 三件套的修改视为未修复。
5. 风评/社媒类证据永不进总分（v48 判定延续）。
