# 轮铸调度细则 v1.0（能跑门六检 · 名册 schema · 排期算法 · 管线接口）

## 1. 能跑门六检明细（全部静态，零执行）

| # | 检 | 过 | 不过 |
|---|---|---|---|
| 1 | src-exists | 源路径在（目录/.skill/.zip） | 源不存在 |
| 2 | skill-md | SKILL.md 在（目录：根或一层子目录；包：包内 ≤1 层）且 zip 完整性过（testzip） | 缺失/坏 zip |
| 3 | frontmatter | `---` 围栏完整；name 为 kebab-case；description 在位且 ≤1024 字符 | 解析失败/name 非法/desc 缺或超长 |
| 4 | links | SKILL.md 正文相对链接（非 http(s)/mailto/#锚）全部可解（目录=文件在；包=namelist 命中） | 悬空链接列出 |
| 5 | py-compile | 全部 .py 过 `compile(src, path, "exec")` | SyntaxError 列出 文件:行号 |
| 6 | scripts-ref | 正文提及的 `scripts/xxx` 全部在位 | 缺件列出 |

判 runnable = 六检全过。检 5 是**编译级**：`compile()` 只产字节码对象，不运行模块顶层任何语句——这是「外来脚本永不执行」铁律与「能跑」验证的唯一合法交集（smoke 内有用模块顶层 `raise SystemExit` 的夹具自证：过门且未执行）。

## 2. roster.json schema（单一事实源）

```json
{
  "schema": "forge-roster/1",
  "engine": "1.0.0",
  "doctrine": "先能跑，再完善",
  "created": "ts",
  "skills": [
    {
      "name": "kebab-case",
      "src": "目录或包路径",
      "src_kind": "dir | pkg",
      "version": "自由文本",
      "md5": "源指纹（目录=相对路径+字节滚 hash）",
      "note": "登记注记",
      "phase": "A-pending | A-passed | A-failed | B-rounds | alumni",
      "registered_ts": "ts",
      "gate": {"runnable": true, "checks": [{"check","ok","detail"}], "ts": "ts"},
      "gate_ts": "ts",
      "rounds": [{"ts", "verdict": "KEEP|REVISE|FAIL", "note"}],
      "last_round_ts": "ts"
    }
  ]
}
```

相位迁移：`A-pending --gate--> A-passed/A-failed`；`A-passed/B-rounds --advance KEEP--> alumni`；`--advance REVISE/FAIL--> B-rounds`；`A-failed --register 换源--> A-pending`（回炉重门）。`A-pending/A-failed --advance--> 硬闸 exit 3`。

## 3. 排期算法（--next）

1. 候选 = 全部非 alumni 件；空 → 如实报「全定案」。
2. **先能跑**：候选中有 A-pending/A-failed → 取（gate_ts 升序，空串最前；registered_ts 次序决胜）。含义：从未过门者最先，门失败者按失败先后回炉。
3. **再完善**：全部过门 → 取（last_round_ts 升序，空串最前；registered_ts 决胜）。含义：从未锻过最先，其后最久未锻先轮——一轮一技，不并行赶工。
4. 输出附 `action`：门未过 →「过能跑门 --gate」；已过 →「进完善轮」。

## 4. 与 skill-forge-pipeline 的接口

`--next` 指向 Phase B 件后，锻造动作按 skill-forge-pipeline 执行：
- 新件首锻：N-C-D 主链一次成形 + N⇄D 短链收敛（判官三视角、paired 奇数多数决、MAX_ROUNDS=3 触顶熔断）。
- 既有件大修：D + 短链（判官先行）。
- 收敛/触顶后，把终局裁定回录：KEEP=定案出队；REVISE=残余留队；FAIL=触顶未收敛留队并在 note 写明回滚基线。
- 回录 note 建议格式：`R<轮数> <裁定>（均分/票数一句，残余一句）`。

## 5. 退出码

0=全过/正常输出；1=门有失败件/名册无此名/源不存在；2=用法错误/撞名拒写；3=名册缺失损坏/A 未过强进 B（硬闸）。

## 6. 红线

- 外来脚本永不执行——能跑门全静态；
- roster.json 单一事实源，原子写（tmp+replace）；
- 一轮一技；裁定未回录，指针不推进；
- KEEP 出队不反复重锻；重开须换源再登记（md5 变即新证）。
