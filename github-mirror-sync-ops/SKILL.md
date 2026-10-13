---
name: github-mirror-sync-ops
description: "[项目技能] GitHub 镜像同步运维——把本地文件树（技能库/文书/静态站点）经 GitHub 通道同步到远端仓库的「推送车道选型 + 逐字节核验 + 失真结案」纪律。触发（满足任一）：①用户说「同步到 GitHub」「推镜像仓」「更新 github 技能库」「同步 openplanlink-mirror」「建仓推送」「GitHub 增量同步」「push 到仓库」或等价表述（含语音变体，不纠正用户、映射意图）；②任何经 GitHub MCP 插件（push_files/create_or_update_file/get_file_contents）、PAT+git、或一次性 Actions 工作流向远端仓库批量写文件时；③推送后需要证明「远端逐字节一致」或处理「推上去的字节和本地不一样」时；④大文件超限需分片发布并端到端还原验证时。覆盖：六条推送车道选型与实证行为、git-blob sha 断言纪律、结尾换行不一致处置、输出层 \\uXXXX 失真结案规程、分片发布、全树终验、台账闭合。不覆盖：外发前审查闸（走 release-gate-audit，未过闸禁推送）、便携件生命周期（走 portable-sync-ops）、跨实例委派函格式本体（走 coordination-letter，本件只在字节级补救时联挂）。中文名：镜像同步运维。English triggers: github mirror sync, byte-exact push verification, git blob sha assert, bulk push via GitHub MCP, shard large file to repo."
metadata:
  version: "1.0.0"
---

# 镜像同步运维（github-mirror-sync-ops）

> 出生案：2026-09-30→10-01 技能库 655 件同步至公开镜像仓马拉松——654 件逐字节核验通过、1 件输出层失真结案（语义等价）、353KB 大文件分片发布端到端还原验证。本件把该役实证的车道行为与核验纪律固化，下次同步直接照做，不再用 14 轮试错换教训。

## §0 定位与边界（先读）

- 本件管**推送执行与核验**：车道选型 → 逐件断言 → 全树终验 → 台账/结案。管「字节到了没有、对不对」。
- 本件**不管**事前审查：任何内容出沙箱前必须先过 release-gate-audit（分级/脱敏扫描/五道漏洞审查），未过闸禁推送——引用不复制。
- 字节级补救需要桌面/网页车道时，委派函格式走 coordination-letter；本件只规定函内必带的三件货（见 §4）。
- 红线：凭据永不入包/不入正文/不入 git 历史；PAT 走文件注入、用后 `unset`，不回显值；探针金丝雀用完即删，树上无残留。

## §1 推送车道决策表（六车道，全部实证过）

| # | 车道 | 实证行为 | 何时用 |
|---|---|---|---|
| 1 | **coder 子代理车道**（首选） | 子代理自行从磁盘读文件、自行调 GitHub MCP，内容不经主代理转录——200+ 件近 100% 成功 | 批量推送默认车道；主代理发射阻塞时的解围车道 |
| 2 | 主代理直推 `create_or_update_file` | 大批量时会出现持续性**发射阻塞**（占位调用百余次、零落盘）——账本可能出现「标已推而远端缺失」的假标记 | 仅零星几件时用；阻塞即换车道 1 |
| 3 | `push_files` + base64 编码 | **探针实证：content 按明文存储、不做 base64 解码**（金丝雀 blob == 明文串哈希）——不能用来绕输出层失真 | 多文件单提交时可用（明文）；不要当编码旁路 |
| 4 | PAT + git 协议 | 最干净的字节级车道（git 对象直传，不经模型输出层）；脚本骨架见 references/push-lanes.md §2 | 有 PAT 且要求严格字节一致时首选 |
| 5 | 一次性 Actions 工作流 | 工作流自删型：payload 走临时文件分享链接 + sha256 校验，运行后 `rm` 自身并 commit | 无 PAT 但仓库可跑 Actions 时的整树替换 |
| 6 | 网页上传 / 桌面端委派 | 唯一能落定字面 `\uXXXX` 转义的车道（不经任何模型输出层） | 字节级补救专用（见 §4） |

车道纪律：**一文件一断言**——推前本地重算 git-blob sha，推后断言远端 `content.sha`+`size` 双等；不符即修复重推（见 §3），禁止「推了就当到了」。

## §2 标准工作流（六步，顺序执行）

1. **暂存树 = 白名单**：推送全集 = 过闸后的暂存树，先跑 `scripts/gh_sync_verify.py manifest <root>` 生成 `{relpath: blob_sha}` 清单；推送前做「暂存树 ↔ 推送文件」逐件对账。
2. **选车道**：按 §1 决策表；批量默认 coder 子代理车道，子代理简报模板见 references/push-lanes.md §1。
3. **逐件推送 + 逐件断言**：`verify-file` 双等（sha+size）才记账；ledger 逐件登记（路径/本地 blob/远端 blob/commit/状态）。
4. **大文件分片**：超通道上限即分片（§5），不硬推。
5. **全树终验**：`verify-tree` 拉 `git/trees/HEAD?recursive=1` 全树 blob 与 manifest 比对——抓得出「账本标已推、远端实际缺件」的假标记（实战抓出 4 件）。
6. **结案闭合**： mismatch 件按 §3/§4 处置；ledger + 报告落盘；远端既有文件（站点基础设施等）一律不动，manifest 注明「未动」。

## §3 字节级核验纪律（三条铁律）

1. **git-blob sha 算法**：`sha1(b"blob %d\0" % len(data) + data)`。`scripts/gh_sync_verify.py blob-sha <file>` 直接出值；远端对应 `GET /repos/{owner}/{repo}/contents/{path}` 返回的 `sha`（base64 解码后复算双保险）。
2. **结尾换行不一致**：MCP 写件对结尾换行行为不稳定——推后 size 差 1 字节先查 `\n`。处置两式：**nl-fix**（无尾换行的文件绝不给加换行，原样重推）；**sha-fix**（以远端错误 blob 的 sha 作 `sha` 参数重推正确内容）。
3. **压缩续接不信口供**：凡压缩/续接后，账本里打印的历史 sha、闸值、计数一律不信——推送前从磁盘重算，以盘为准（实战教训：压缩后口头值与实物漂移）。

## §4 输出层失真结案规程（`\uXXXX` 类）

**病灶**：模型输出层会把常见 CJK 转义（如字面 `\u4e00`）自动展开成汉字——**出站（写入）必失真，入站（读回）反斜杠保真**；三实例×14 轮×三种写法 + base64 车道全部穷尽，属平台层缺陷，别再试。

**结案五拍**（缺一拍不算结案）：
1. 穷尽声明：列明已试车道与轮次，宣布 agent 车道穷尽；
2. **归一化比对**：把已知差异点归一化（如 `一`→`\u4e00`）后与本地源逐字节比对——差异点唯一且语义等价才可结案，其余每个字节必须全等；
3. 台账记 `semantic_equivalent`（本地 blob/size vs 远端 blob/size/commit + 差异点描述），功能等价结论须可复算；
4. 字节级补救**委派桌面/网页车道**：协调函内嵌三件货——文件全文（代码块）+ 验收标准（字节数+blob sha）+ 质询清单；成品函须**反向提取代码块与原文件逐字节比对**通过才准交付（防转录失真）；
5. 如实声明「不补救功能无损」——语义等价版可永久服役，补救属可选项，把裁决权交用户。

## §5 大文件分片发布

超通道上限文件：切成 N 片推至 `<dir>/parts/p0..pN` + 指针文件 `<name>.PARTS.md`（片数/顺序/总 sha）。**端到端还原验证**才算完：从远端拉回全部片拼接，复算字节数与 blob sha 与 manifest 全等。分片与复算用 `scripts/gh_sync_verify.py shard / reassemble`。

## §6 失败模式（if-then）

| 触发 | 一线处置 | 禁止 |
|---|---|---|
| 主代理推 MCP 连续占位调用、零落盘 | 立即换 coder 子代理车道；账本回头核销假标记 | 继续空转刷调用 |
| 推后 sha 不符、size 差 1 | 查结尾换行 → nl-fix / sha-fix | 不重验直接记账 |
| 内容含字面 `\uXXXX` 必须字节级一致 | 直接走 §4，不试 agent 车道 | 逐轮试写法（已穷尽，纯浪费） |
| 探针/金丝雀文件 | 用完即删并复核树上无残留 | 留探针在公开树 |
| 远端有任务前既有文件 | manifest 标「未动」，终验排除 | 顺手「整理」他人/既有文件 |
| 公开仓推送后 | 明示「已推送内容可能被 fork/收录，撤回对已扩散副本无效」 | 承诺可彻底撤回 |

## Resources

- `scripts/gh_sync_verify.py`：纯标准库 CLI——`blob-sha` / `manifest` / `verify-file` / `verify-tree` / `shard` / `reassemble`（`--help` 自查；公开仓免 token，私有仓用 `GH_TOKEN` 环境变量注入）。
- [references/push-lanes.md](references/push-lanes.md)：六车道详细战法（子代理简报模板、PAT 脚本骨架、一次性 Actions 工作流骨架）、2026-10-01 失真结案案卷全文要点。推送前选车道或处置失真时必读。
