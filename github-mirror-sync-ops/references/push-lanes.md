# 推送车道战法详录（push-lanes.md）

> 全部结论来自 2026-09-30→10-01 技能库 655 件同步实战（目标：公开镜像仓 main 分支）。目录：§1 coder 子代理车道 / §2 PAT+git 车道 / §3 一次性 Actions 工作流车道 / §4 网页·桌面委派车道 / §5 输出层失真案卷 / §6 探针纪律。

## §1 coder 子代理车道（批量首选）

**为什么需要**：主代理大批量直推 `create_or_update_file` 会出现持续性发射阻塞——占位调用百余次、内容零落盘，且账本可能留下「标已推而远端缺失」的假标记（实战抓出 4 件，全靠全树终验兜底）。

**要点**：子代理**自行从磁盘读文件、自行调 MCP**——文件内容不经主代理转录，主代理只发简报。实证 200+ 件近 100% 成功。

**简报模板**（派给每个子代理）：

```
任务：推送批次 <批次号>，共 <N> 件。
1. 逐件读 /path/to/manifest.json 中本批文件清单（路径 + 目标 blob sha + size）。
2. 逐件：从磁盘读原文（禁止凭简报转录内容）→ 调 GitHub MCP 推送（owner/repo/branch 固定）→
   立即 get_file_contents 断言远端 sha 与 size 双等。
3. 不符处置：size 差 1 先查结尾换行（nl-fix：原样重推，不添加换行）；
   仍不符以远端错误 blob 的 sha 作 sha 参数重推正确内容（sha-fix）。
4. 回报 JSONL：每件一行 {path, local_sha, remote_sha, size, commit, status}；失败件如实报，不凑数。
红线：凭据值不回显；不碰清单外任何远端文件；探针文件用完即删。
```

**额度纪律**：批次串行、逐件断言；不要为省调用合并断言——一件一证。

## §2 PAT + git 协议车道（字节级最干净）

git 对象直传，不经模型输出层——含 `\uXXXX` 字面转义的文件也只有这条车道（与 §4）能字节级落定。

脚本骨架（实证版要点）：

```sh
#!/bin/sh
set -eu
PAT_FILE=/path/to/github-pat.txt          # PAT 走文件注入，永不进命令行回显
[ -f "$PAT_FILE" ] || { echo "缺 PAT 文件"; exit 2; }
GH_PAT=$(tr -d ' \r\n\t' < "$PAT_FILE")   # 去空白，防空格/换行污染
cd "$REPO_DIR"
git -c credential.helper= \
    -c credential.helper='!f() { echo username=x-access-token; echo "password=$GH_PAT"; }; f' \
    push origin HEAD:main
unset GH_PAT                               # 用后即焚
# 随即全树校验：git/trees/<HEAD>?recursive=1 比对 manifest
```

要点：credential.helper 用进程内函数注入，不落 `.git-credentials`；推送后**必须**立刻全树校验再结台账。

## §3 一次性 Actions 工作流车道（无 PAT 的整树替换）

形态：工作流文件自带自删除——运行一次后从树上消失。

骨架（实证版）：

```yaml
name: sync-skills-mirror
on:
  push:
    paths: ['.github/workflows/sync-skills-mirror.yml']
permissions:
  contents: write
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Download and verify payload
        run: |
          curl -fSL "<临时文件分享链接>/payload.tar.gz" -o /tmp/payload.tar.gz
          echo "<payload 的 sha256>  /tmp/payload.tar.gz" | sha256sum -c -
      - name: Install tree and remove this one-shot workflow
        run: |
          rm -rf skills && mkdir skills
          tar xzf /tmp/payload.tar.gz -C skills
          rm -f .github/workflows/sync-skills-mirror.yml
      - name: Commit and push
        run: |
          git config user.name "<bot 名>"; git config user.email "<bot>@users.noreply.github.com"
          git add -A && git commit -m "sync: <说明>" && git push
```

要点：payload 链接需短时效（临时文件分享服务）；sha256 硬校验不过即失败；工作流自删保持树干净。

## §4 网页上传 / 桌面端委派车道（字节级补救专用）

适用：必须落定字面 `\uXXXX` 转义等输出层必失真内容。委派函（格式走 coordination-letter）内嵌三件货：

1. **文件全文**：代码块包裹，从磁盘读入函件（零转录）；
2. **验收标准**：目标字节数 + git-blob sha + 操作路径（网页编辑覆盖远端同路径，勿编辑内容）；
3. **质询清单**：收件方答不上来即停手回报的场景（本地校验不过 / 远端 sha 不符 / 输出层同样失真）。

**交付前自检**：从成品函反向提取代码块，与原文件逐字节比对通过才准发——防函件本身成为新的失真源。

## §5 输出层失真案卷（2026-10-01，img_token_saver.py）

- 病灶文件第 48 行含字面 `\u4e00`/`\u9fff`（CJK 区间判断）。目标：7279B / blob `ee70dc05…`。
- 穷尽证据：三个独立实例 × 共 14 轮修复（直接写法、拼接写法），测得三种互不相同的失真行为；主代理发射阻塞；`push_files`+base64 探针证实 content 按明文存储（金丝雀 blob == 明文串哈希）。agent 车道确凿穷尽。
- 结案：远端停留 7273B 汉字直写版（blob `b6b7e12c…`）。归一化比对——本地源经唯一差异点归一化后与远端 7273B 全等，Python 语义完全等价 → 台账记 `semantic_equivalent`，功能无损结案。
- 补救：字节级补齐委派桌面端（§4 三件货齐备）；并如实声明「不补救不影响任何使用」。
- 教训：**入站读回反斜杠保真、出站写入必然失真**——判断失真时区分方向；别再为这类内容试 agent 车道。

## §5b 第二案卷：吞词失真 × 自身 bug 的区分（2026-10-01，verify_parts.py）

同日给分片区补发接收脚本，5 轮才成，**失真与自身 bug 必须分开归因**：

- **第 1 轮（车道失真）**：纯 ASCII 脚本远端比本地少 5 字节——docstring 里某一行 `bytes  blob <sha>` 的 `blob ` 一词被输出层吞掉（仅一处，非规律性）。定性：输出层除「`\uXXXX` 展开」外，还存在**低概率吞词/丢词**。对策同 §5：ASCII 也不能豁免推后 blob 断言。
- **第 2~4 轮（主代理自身 bug，非车道问题）**：错哈希头 `b"git-object"`、bytes/str 拼接 TypeError、`b[:4]` 把文件头字节当 magic 用——全是「边推边手写、没本地跑通」引入的。**三连败根因是违反「先本地跑通再推」铁律**。
- **第 5 轮（纠正后一次过）**：参数化生成脚本 → 本地对真实数据预跑出 `ALL CHECKS PASS` → 锁定该份**一字不改直发** → 远端 blob 与本地逐字节一致。

**新增铁律**：(a) 推任何脚本前，先在本地对真实数据跑出成功退出码，再原样推送，禁止「推送中现场改写」；(b) 多轮连败时先区分「车道失真 vs 自身 bug」——把远端件拉回本地跑一遍，若报的是你自己代码的异常（TypeError/哈希对不上自己写的常量），那是你的 bug，别赖车道；(c) 吞词失真的定谳法与 §6 相同：复算候选内容 blob sha 对号入座。

## §6 探针纪律

- 探针文件命名醒目（如 `_sync_probe_*.txt`），内容用无意义金丝雀串；
- 探针结论以远端 blob sha 定谳（复算两种候选内容的 sha 对号入座），不凭 get_file_contents 的表象；
- **用完即删**，删后全树终验复核无残留；探针 commit 与删除 commit 都留档在报告「被取代提交全录」——git 历史不可改写，留痕即合规。
