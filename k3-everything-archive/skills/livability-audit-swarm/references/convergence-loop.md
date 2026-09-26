# 迭代收敛协议（对接 iteration-convergence-ops）

> 目标：审计 → 修复 → 复验 循环，直到 `convergence_check.py` 判 CONVERGED。
> 不考虑预算：允许足量子代理与迭代轮次；但**禁止**为省轮次合并审计角色或跳过复验。

## 循环定义

```
Round N:
  1. 扫描登记    livability_doc_scanner.py  → registry.json
  2. 切包派发    audit_pack_builder.py      → ≥5 角色任务包
  3. 并行审计    ≥5 审计子代理（只读）       → 六份审计报告 + findings.json
  4. 汇总判敛    convergence_check.py       → CONVERGED / NOT CONVERGED
  5. 若未收敛:   主代理据审计**直接修改文档**，每处修改跑 notice_stamp.py 留痕
  6. 复验轮      verifier 子代理核实修复落盘与无新矛盾 → 更新 findings.json → 回到 4
```

## 收敛判定（硬规则）

- `CONVERGED` ⇔ findings.json 中无 open 的 blocker/high，且 open 的 medium 全部带 `accept_reason` 或 `scheduled`。
- 复验轮必须抽查「声称已修」的条目：打开原文件核实（防止 edit 未落盘——本项目有 edit_file 静默未生效前科，修复后必须 grep 验证）。
- 复验新增**可用性检查**：被改的 .py 必须 `py_compile` 通过、.json 必须 `json.load` 通过；不通过 = 未修复。
- 复验新增**三方一致性检查**：文头块 change_id == CHANGELOG 末行 == 实际修复内容，三者一致才算关闭。
- 连续两轮 verdict 相同且 minimal_fix_list 不变 → 判定停滞，主代理须改变修复策略而非重发同一指令（v2 起由 `--prev` 自动判 STAGNATED，见下表）。

## verdict 三值表（convergence_check.py v2）

| verdict | 语义 | exit code | 后续动作 |
|---|---|---|---|
| CONVERGED | 无 open 的 blocker/high，且 open medium 全部带 accept_reason/scheduled | 0 | 跳修复轮，直接交付 |
| NOT CONVERGED | 仍有 open blocker/high，或有无理由的 open medium | 1 | 进入修复轮：按严重度排序修复 + 三件套留痕 → 复验 |
| STAGNATED | 两轮均未收敛且 open 的 blocker/high id 集合完全相同且非空（`--prev` 比对命中） | 3 | **禁止重发同一修复指令**；主代理必须更换修复策略（换角度复审证据、拆细修复粒度、升级人工裁决等）后再进修复轮 |

- 用法/IO/**数据错误** exit code=2：findings 缺失、JSON 解析失败、--prev 文件不可读、--consistency-dir 非目录，以及数据形态错误（findings 含非对象条目、open 的 blocker/high 缺 id、--prev 的 minimal_fix_list 含非对象或缺 id 的 blocker/high）。数据错误路径仍输出 JSON 契约字段并附 `errors` 列表（不 traceback）；用法/IO 错误只走 stderr。
- severity/status 规范化：统一 lower() 后映射；未知 severity → WARNING 并按 blocker（最严重）处理；未知/缺失 status → WARNING 并视为 open，绝不静默放行。
- v2 自动核验开关：`--usability-checks`（失败自动追加 USE- blocker，id 碰撞自动顺延；点名的文件不存在按失败处理，目录/其他扩展名列入 `usability_skipped`）、`--consistency-dir`（三方不一致自动追加 CONS- blocker；缺留痕文件只记 WARNING）；两者追加的 finding 参与本轮判定。
- v2.1 证据复核开关：`--verify-evidence` 对 status=closed 且携带 `verify` 规范（`{"type":"grep","pattern","file","expect":"present|absent"}`）的条目实跑核验；失败（含文件缺失/规范非法）自动改回 open 并写 `reopen_reason`。**纪律：closed 条目必须携带 verify 规范**（复核 grep 模式或等效机器可验证据），防止虚假关闭骗出 CONVERGED。

## 收敛指标（主代理在轮次日志中累计）

- `rounds_to_converge`：从首轮判敛到首次 CONVERGED 的轮次数；脚本输出的 `rounds_metrics.rounds_to_converge` 仅为占位（null），真实值由主代理跨轮累计。
- 轮均关闭率 = 当轮关闭数 / 上轮 open 数（当轮关闭数 = 上轮 open 且本轮变为 closed 的条目数；上轮 open 数可取上轮输出的 `rounds_metrics.open_count_this_round`）。
- 轮均关闭率连续两轮为 0 时，即使未触发 STAGNATED，主代理也应按停滞对待并更换策略。

## 实战校准

> 数据来源：`livability-audit-swarm-workspace/battle/`（案例1：case-1/；案例2：case-2/ + grader_notes.md 独立复验；案例3：case-3-cities/ 三城检索+比对，含 grader_notes.md/reviewer_notes.md；案例4：case-4-cities/ 六城整合比对，含 grader_notes.md/reviewer_notes.md/convergence_round2.json）。案例1/2 为六角色内联降级执行、技能 v1.1（checker v2）跑出，案例2 第 3 轮起用 v1.2（checker v2.1）；案例3 为 v1.3 检索组件全链实战（广州/深圳/长沙 × 8 参数，24 条登记），修复轮后升 v1.4；案例4 为 v1.5 全链实战（历史三城 §9 口径重算 + 西安/合肥/南昌新城检索，49 条登记 --merge），对抗审查（F1–F9）后升 v1.6。

### 五案例实测指标

| 指标 | 案例1（md+tex，2026-08-23） | 案例2（两个 .py，2026-08-24） | 案例3（三城检索+比对，2026-08-24） | 案例4（六城整合比对，2026-08-24） | 案例5（九城整合比对，2026-08-24） |
|---|---|---|---|---|---|
| findings 总数（b/h/m/l） | 17（0/6/6/5） | 15（0/3/6/6） | 4（0/0/1/3） | 6（0/1/3/2） | 11（0/0/6/5） |
| rounds_to_converge | **2** | **3**（R2 的 CONVERGED 因 P4 虚假关闭被 grader 抓获作废；首次真 CONVERGED = R3） | **2**（R1 NOT CONVERGED open 4 → 修复轮 → R2 CONVERGED exit 0） | **2**（R1 NOT CONVERGED exit 1 open high E1 → 修复轮 → R2 CONVERGED exit 0） | **2**（R1 NOT CONVERGED exit 1 open 11 → 修复轮 → R2 CONVERGED exit 0） |
| 轮均关闭率 | 100%（17/17，单一修复轮） | R2：88.9%（8/9）；R3：严格口径 0/1（仅剩 open low P3），含 grader 重开口径 1/2 | 75%（3/4，单一修复轮） | 83.3%（5/6，单一修复轮；medium P2 按设计留 open，accept_reason+scheduled 齐全） | 90.9%（10/11，单一修复轮；medium P2 按设计留 open，accept_reason+scheduled 齐全） |
| 终态 | 17/17 closed；grader 抽查全过，**收敛声明成立** | closed 14（`--verify-evidence` 实跑 **14/14 ok**）/ open 1（low P3 带 accept_reason）；R3 CONVERGED exit 0 | closed 3（`--verify-evidence` 实跑 **3/3 ok**）/ open 1（low E2 带 accept_reason+scheduled）；grader 六项复验全过判**收敛声明成立**；检索登记 24 条 exit 0（0 错误/7 警告），检索质量评级 **A-** | closed 5（`--verify-evidence` 实跑 **5/5 ok**）/ open 1（medium P2 带 accept_reason+scheduled）；grader 7 项复验全过判**收敛声明成立**；检索登记 49 条 `--merge` 六城 **exit 0**（0 错误/16 警告全预期），检索质量评级 **A**（较案例3 上调） | closed 10（`--verify-evidence` 实跑 **10/10 ok**）/ open 1（medium P2 带 accept_reason+scheduled）；grader 六项复验 6/6 全过判**收敛声明成立**；检索登记 74 条 `--merge` 九城 **exit 0**（0 错误/29 警告全预期，含 v1.7 口径剪切 ×3），检索质量评级 **A**（与案例4 持平） |
| STAGNATED | 未触发（identical=false） | 未触发（R2/R3 open blocker/high 集合均为空，空集恒等不判停滞） | 未触发（R1/R2 空集恒等，不判停滞） | 未触发（R1 open high={E1}、R2 空集，集合有变化 identical=false） | 未触发（R1/R2 open blocker/high 均空集，空集恒等不判停滞） |
| 三方一致性 | consistent=true（三方=CHG-20260824-B1-002） | consistent=true（三方=CHG-20260824-B2-005） | consistent=true（三方=CHG-20260824-B3-003，warnings=[]） | consistent=true（三方=CHG-20260824-B4-002，warnings=[]，内嵌日期与 date 均 2026-08-24） | consistent=true（三方=CHG-20260824-B5-002，warnings=[]，内嵌日期与 date 均 2026-08-24；case-5 工作区目录另取 B5-004 亦 consistent） |
| 行为保持 | 纯文档修复 | 冒烟 14/14 全等（smoke_replay.py 可复现，SMOKE IDENTICAL），零行为改变 | 纯注释级修复（行注/注释块，数值零改动），冒烟 19/19 全等（SMOKE IDENTICAL，exit 0），零行为改变 | 纯注释级修复（行注/注释块，数值零改动），冒烟 **26/26** 全等（SMOKE IDENTICAL，exit 0，before/after/replay 三方互等），零行为改变 | 纯注释级修复（行注/注释块，数值零改动），冒烟 **33/33** 全等（SMOKE IDENTICAL，exit 0，before/after/replay 三方互等），零行为改变 |
| 主要事故 | 首批并行 edit 同文件写竞态，4 处报成功未落盘，grep 抓获后串行重放 | P4 虚假关闭（见定律①）；edit 未落盘 3 次（见定律④） | B3-002 reason 编号不符协议，B3-003 规范化重盖（CHANGELOG append-only 双侧留痕）；登记校验结论 TZ 依赖（见定律⑤） | E1 质性评分排序倒挂裁决（见定律⑥）；housing 覆盖口径更正（简报「六城仅广州有」→ 实测四城有/南昌半缺口）；12 条参数名超建议取值表 WARNING（预期内） | notice_stamp strip_legacy P0 灾难性回溯：livability.py（49 行 `#` 注释）盖章挂起 >12min（O(2^N) 永不返回，见定律⑦）；B5-002 改**手工盖章绕过 + 字节级 parity 验证**（协议允许的降级路径），grader 独立复算 parity 逐字节成立；E9 WARNING 分类计数 22→21 勘误（B5-004） |

### 实战定律（按风险排序）

1. **closed 必须携带 verify 规范——虚假关闭是实测发生过的最大风险。** 案例2 P4（medium）在 evidence 与 B2-002 留痕 reason/summary 中写下「三字典字段级 conf 已补、grep『conf=』命中 4 处」，实测仅 DESIRABILITY 一处落盘（grep 实际 1 处），直接骗出 CONVERGED；grader 将 P4 重开后正确 verdict 应为 NOT CONVERGED。教训：finding 的 evidence 与留痕文本都可能记录未发生的修改；v2.1 起 `--verify-evidence` 对 closed 条目实跑核验、失败自动改回 open，**凡 closed 必带 verify 规范，无规范不关闭**。
2. **同日多文件盖章的 change_id 排序规则。** 一轮修 ≥2 个文件时各文头块 date 必然相同，「文头块最新」tie-break 若按文件名字典序取最大，约 50% 概率误报 CONS-1（对抗审查 H1，端到端复现确认）。v2.1 已改为同 date 平手按 change_id 取最大；主代理侧配套做法：不参与文头扫描的文件类型先盖章、被扫描类型后盖章（案例1 即按 .tex→.md 顺序盖 001→002 保证三方一致）。
3. **行为保持类修复，冒烟脚本与入参强制落盘。** 案例2 初版只落盘 smoke_before/after 两个结果 JSON，未落盘脚本与入参，第三方复现需反推（grader 问题4）；勘误轮补齐 `smoke_replay.py + smoke_inputs.json` 后可一键重放 14/14 全等。凡声明「零行为改变」的修复轮，必须把可执行冒烟脚本、入参文件、前后基线一并落盘工作区。
4. **edit 报成功 ≠ 落盘；grep 复验是最后防线，且须逐条复核而非抽样。** 「编辑未落盘」前科本轮实战复现 4 次：案例1 首批并行 edit 同文件写竞态（4 处未落盘，改串行重放后落盘）；案例2 B2-003 的 P2（被 grep 抓获，以 B2-004 补落）、B2-002 的 P4（漏过 grep 复核，被 grader 抓获，以 B2-005 勘误补落）、勘误轮 docstring/LIVABILITY 头注首写（再被 grep 抓获重写）。P4 证明「抽查式 grep」会漏——每处声称的修改都要 grep 验证（建议直接写入 verify 规范由 `--verify-evidence` 机器执行），同文件多处编辑串行执行。
5. **检索登记的日期判定必须时区钉死（UTC 基准 + UTC 今日 +1 天容差），跨机复跑须同 verdict。** 案例3 M1 教训：同一份 entries.json（24 条，check_date 2026-08-24）在 `TZ=Asia/Shanghai` 下 `retrieval_registry_check.py` exit 0（0 错误/7 警告），换 UTC 复跑变 **exit 1 / 16 条未来日期错误**——UTC↔Asia/Shanghai 每天有 8 小时窗口判决相反，「exit 1 须先修正再派审」门槛变成机器相关（reviewer M1，v1.4 前脚本用本地时区 `date.today()`）。v1.4 已修复：未来日期判定钉死 UTC 基准，超 UTC 今日 +1 天才报错、容差内仅 WARNING。主代理侧纪律：登记校验结论必须声明运行 TZ；蜂群多机/跨时区环境下，登记校验与收敛判定的复跑必须同 verdict，不一致先查 TZ/UTC 口径再议修复。
6. **质性评分冲突裁决须先读字典语义头注再定性，禁止按数值大小直接判「谁虚高」。** 案例4 E1：合肥 INDUSTRY=0.75 vs 深圳 0.92，相对排序与 fusion 证据方向冲突（合肥 EAST 在运/CRAFT 集成调试/BEST 总装 + 聚变新能 145 亿链主 + 200+ 企业，深圳仅初创公司+联合实验室、无大科学装置）。若跳过语义层，极易按「低证据方分高」误判为「深圳虚高」；实查 `city_livability.py:32` 头注「INDUSTRY = 与物理/材料/核/计算相关的就业出口密度」四维度后，「计算」轴（深圳 ICT/华为/腾讯）可独立解释深圳绝对高值，故正确定性为「**合肥低估**」而非「深圳虚高」（grader 复核三重支撑成立：计算轴独立依据 / E2 西安 0.72 反向佐证 / 杭州 0.90 自注偏 IT 仍高于合肥）。处置保持行为优先：**数值不动**、行注标冲突+证据指针，候选建议值（合肥 ≥0.90）入 candidate_entries 排期、数值变更走独立 change_id 评审。教训：质性字典参数的跨城排序冲突，第一步永远是读头注拆维度，把「哪一轴能解释哪一城」分开证伪，再决定定性方向。案例5 起该裁决有 §10 阶梯表作可复现标尺（retrieval-paths.md），九城按带判定：上海 0.95 带内相容、成都 0.70 带内下沿、深圳 0.92 聚变轴出带、绵阳缺席低估。
7. **留痕工具自身须过对抗压测——指数回溯在 49 行注释文件上永不返回；手工盖章 + parity 验证是合规降级路径。** 案例5 实战遗留 L1：notice_stamp.py `strip_legacy` 的 HASH/PCT 分支 `(?:#.*\n)*?`（re.S）对连续独立注释行为 O(2^N) 灾难性回溯——city_livability.py（27 行 `#`）0.49s 完成，livability.py（**49 行 `#`**）挂起 >12min 被 kill（对抗审查 F-B1 实测 ≥~25 行连续 `#` 注释即挂起，外推 49 行 ≈445 天，**永不返回**；首次盖章与幂等重盖双路径均触发）。教训两条：①**盖章前先用小样本计时自验**（30/50/100 行合成文件应 <1s），凡进入强制流程的工具（本协议步骤 3.2 每处修改必跑）须先过对抗压测，否则蜂群会在留痕环节被卡死；②**大文件首盖失败时的合规降级路径**：按 change-notice-protocol.md §1「手写时须严格对齐」手工盖章（三件套齐全、六字段+notice_to 固定句、插入位置合规），并用脚本自身 build_block/py_insert_pos 逻辑对产物做**字节级 parity 验证** + py_compile——案例5 B5-002 即按此执行，grader 用脚本自身函数独立复算逐字节相等，合规性成立。v1.8 已修复（逐行形态 `(?:#[^\n]*\n)*?` / `(?:%[^\n]*\n)*?` 且去掉 re.S：5000 行进程内 ~0.01ms、CLI 30/50/100/5000 行 ~40ms，正常文件删除结果与旧正则逐字节一致），修复前手工+parity 流程为唯一可用路径。

## 并发纪律

1. 同一目标目录同一时刻只允许一个修复实例（用 `.audit-lock` 占位文件或独立工作副本）。
2. change_id 由主代理集中分配或加实例后缀（如 CHG-20260824-eval1-001），禁止并发各自编号。
3. 扫描产物（registry/packs）同轮共享一份，禁止重复扫描。

## 修复轮纪律

1. 修复清单按 blocker → high → medium → low 排序；每轮至少关闭全部 blocker。
2. 每处文档修改**必须** `notice_stamp.py` 留痕（无留痕的修改视为未修复）。
3. 修复不得超出审计结论范围（禁止顺手重构未审计的代码路径）。
4. 每轮结束更新 findings.json 状态，并附 `evidence`（文件:行号 或 grep 命中计数）。
