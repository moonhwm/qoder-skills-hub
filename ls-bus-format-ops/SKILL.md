---
name: ls-bus-format-ops
description: >
  本地工作目录"格式化"安全流程——先用 ls 扫描目标目录生成分类清单（保留"自我设定"类文件：身份/人设/席位设定区块，其余标记为待删除），将清单上传总线留痕，再把总线回执作为批准令牌执行本地磁盘格式化（删除清单外全部内容）。当用户要求"ls，格式化除自我设定以外的所有内容"、"清单上传总线然后本地格式化"、"扫描留痕后清理工作目录"或类似的"先列后删、总线审批"流程时使用。内置三重安全闸：dry-run 默认、删除需出示清单哈希令牌、删除前二次 KEEP 校验与清单漂移检测。v1.1.0 起带四相位 Hook（pre/post scan、pre/post execute，pre 相位可否决）与 digest 总线模式；v1.2.0 起全链路梯度化（--pace/--pace-sleep 默认开启，漂移重扫只哈希 purge 类，progress.json 心跳）——万件级操作不再饿死宿主；v1.2.1 起死链（同步层占位残影，islink 但目标已亡）入册为 deadlink 类可清扫，活符号链接永不跟随。
metadata:
  version: "1.2.1"
---

# ls-bus-format-ops

把"ls → 上传总线 → 本地格式化"做成不可跳步的三段式流程。

## 流程（严格按序）

1. **scan（ls）** — 遍历目标目录，按文件名启发式把每个文件分类为 `keep`（自我设定）或 `purge`（其余全部），生成 `manifest.json` / `manifest.md` / `manifest.sha256`。此阶段只读，不删任何东西。
2. **bussql（上传总线）** — 把清单正文算 sha256，生成总线 INSERT SQL 底稿（脚本生成，禁人工转录）。执行 SQL 后记录总线回执 id 与 hash。
3. **execute（格式化）** — 仅在同时满足以下条件时删除：① `--approve` 令牌 = manifest sha256 前 16 字符；② 重扫目录与清单零漂移；③ 逐文件再过 KEEP 双保险。删除后复验并写执行报告。

## 用法

```bash
cd <skill_dir>/scripts

# 1) 扫描（dry-run，只读）；--keep-file 追加白名单（每行一个子串）
python3 ls_bus_format.py scan --target-dir /mnt/agents/output [--keep-file extra.txt] \
    [--pace 200 --pace-sleep 0.1]   # v1.2.0 梯度默认开启，0=关闭

# 2) 生成总线留痕 SQL（脚本生成禁人工转录）
python3 ls_bus_format.py bussql --manifest <manifest.json> [--seat k3-govdoc-seat] [--digest]
#    清单超万行时必用 --digest：总线只载计数+manifest_sha256+顶层分布，
#    全量清单留 runs 留痕目录（该目录格式化后仍存续），经 manifest_sha256 绑定

# 3) 执行 SQL 后，凭清单哈希令牌执行格式化
python3 ls_bus_format.py execute --manifest <manifest.json> \
    --approve <manifest_sha256前16字符> [--prune-empty-dirs]
```

runs 留痕目录：`<target>/_ls_bus_format_runs/<timestamp>_<label>/`，永不被删除。

## 安全闸（不可绕过）

- **路径白名单**：目标目录必须位于 `/mnt/agents/output` 之内，否则直接拒绝。
- **KEEP 双保险**：`keep` 分类在 scan 与 execute 两处独立判定；execute 阶段任何 KEEP 命中（含 runs 留痕目录）一律跳过。
- **批准令牌**：`--approve` 必须等于 manifest sha256 前 16 字符，错误即拒绝并提示"先上传总线"。
- **漂移检测**：execute 前重扫目录，purge 项变动/消失、或出现清单外新增 purge 类文件即拒绝，需重新 scan；keep 类新增（台账 append、runs 留痕等）不拦截。
- **不随符号链接**：symlink 只列不入。
- **runs 强制保留**：留痕目录自身永不删除。

## Hook 机制（v1.1.0）

`scan` / `execute` 支持 `--hook-dir DIR [--hook-timeout 秒，默认30]`，四相位按名触发：

| 相位 | 时机 | 语义 |
|---|---|---|
| `pre_scan` | 遍历前 | **否决相位**：exit≠0（或超时）→ REFUSE 中止 |
| `post_scan` | 清单落盘后 | 观察相位：exit≠0 仅记痕不中止 |
| `pre_execute` | 令牌+漂移双闸过后、删除前 | **否决相位**：最后一道外部闸，exit≠0（或超时）→ REFUSE 且零删除 |
| `post_execute` | 删除复验后 | 观察相位：收删除结果 |

- **钩子文件**：DIR 内以相位名命名（`pre_scan` / `pre_scan.py` / `pre_scan.sh`）；.py 经当前解释器、.sh 经 /bin/sh、其余须带可执行位，不可执行者记 `skipped_notrunnable` 不崩溃。
- **上下文契约**（环境变量传入，shell=False 不拼接命令行，stdin=DEVNULL）：`LBF_PHASE` / `LBF_TARGET` / `LBF_MANIFEST` / `LBF_MANIFEST_SHA256` / `LBF_COUNTS_JSON` / `LBF_DETAIL_JSON`（execute 结果）/ `LBF_RUNS_DIR`。注意 pre_scan 相位仅 `LBF_PHASE`/`LBF_TARGET`/`LBF_RUNS_DIR` 非空，其余为空串。
- **安全闸**：hook-dir 严禁位于 target_dir 之内——目标目录按不可信数据处理，绝不从中发现执行钩子；违反即 REFUSE。
- **钩痕**：每次调用写 `<target>/_ls_bus_format_runs/hooks.jsonl`（相位/路径/结果/exit/耗时/输出尾）。

## 性能锚点与梯度化（v1.2.0，慢 I/O 沙箱实测）

- 真实扫描：10,057 件/5.34GB ≈ 41 件/s（哈希吞吐 ~0.02GB/s，I/O 主导），全程 ~4 min。
- 合成小件：扫描 262 件/s；漂移检测+删除 ~28 件/s。
- **事故教训（2026-10-07 卡死事件）**：v1.1.0 无梯度执行万件格式化 → 漂移重扫全量哈希+3 万 I/O ops 连发 → 同挂载宿主全饿死（shell/proc/edit 全堵），进程随沙箱挂起死亡且零 report。v1.2.0 起：`--pace 200 --pace-sleep 0.1` **默认开启**（扫描/删除/prune 全链路让渡），漂移重扫 keep 类不哈希（砍掉大半重扫 I/O），`runs/progress.json` 心跳可轻量轮询。
- **生产 execute 预算**：万件级 ≈ 10–15 min + 梯度让渡 ~1 min，仍须 nohup 脱离执行+轮询 `progress.json` / `report_<ts>.json`，勿在前台硬等。

## KEEP 模式（自我设定识别）

文件名（小写）含以下任一子串即判为"自我设定"保留：persona、人设、周嘤鸣、授名、署名、身份锚点、锚点、handoff、genealogy、engine_r、自我设定、本席设定、席位、seat-naming、naming。用户可编辑脚本顶部 `KEEP_PATTERNS` 扩充。

## 纪律

- 格式化属高危写操作：scan 产物必须经用户（或总线回执）确认后才 execute。
- SQL 一律由 bussql 从清单底稿生成，禁止人工转录 hash。
- 每次执行在 runs 目录留下 manifest、SQL、report 三件套，可审计。
