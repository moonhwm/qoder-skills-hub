---
name: skills-hub-pipeline
description: qoder-skills-hub 仓库的汉化工具链、SHA-3 Merkle 校验、推送网络怪癖与发现性诊断结论
metadata:
  type: project
---

`qoder-skills-hub`（github.com/moonhwm/qoder-skills-hub，公开）维护工具链与已知结论（2026-09-26）：

- 汉化批：workspace 根 `sinicize.cjs`（plan 端点 qwen3.6-flash、并发 2、文件级断点 `.sinicize-progress.json`、台账 `docs/sinicize-ledger.jsonl`）；只替换整行注释，sameShape 校验（标记+缩进逐行比对）拒绝即留原文——首跑 553 译/394 留。
- README 重建：`build-readme-zh.cjs`（简体中文七节模板）。
- 完整性：`tools/merkle.cjs gen|verify` + `MERKLE.json`（SHA3-512 二叉树，2026-09-27 由 SHA3-256 升级；叶子按路径排序；MERKLE.json 自身不入哈希）。**固定次序：git add → gen → verify → add MERKLE → commit**（gen 用 git ls-files 仅见 tracked；此坑踩过两次，第二次靠"根未变"识破）。
- 调度度量（2026-09-27）：嵌入强代理（text-embedding-v4 余弦 argmax，273 触发例）v1=0.656 / v2=0.659（差=噪声）→ 关键词表非召回杠杆，杠杆在描述文本；42 miss 清单=下轮描述手术输入。子串弱代理（0.282/0.238）弃用留痕。embeddings 批上限 10；**plan 端点不开 embeddings**，走赠送键+dashscope 老域。
- 检索索引：`tools/gen-keywords.cjs`（plan 端点 qwen3.6-flash、并发 2）→ `docs/skill-index-zh.json`（91 件中文关键词+摘要，服务搜索/调度）。
- 推送怪癖：github.com:443 间歇性重置/不可达；`git -c http.version=HTTP/1.1 push` + 重试循环可过；浏览器通道不受影响。
- Windows 壳陷阱：curl 经 ACP 传中文请求体会损坏（改用 node 发送，干净客户端已验证）；`head -c` 按字节截断多字节 UTF-8 产生伪乱码误诊（预览须安全解码）。
- 发现性诊断：GitHub 仓库搜索可命中（排第一）；Qoder extension-market 搜索 0 命中＝平台无发布入口（非库缺陷）；本地调度正常。topics 未加（新 UI 设置页无字段），留作用户可选件。
- 既有缺陷留痕：`skill-refresh-ops/scripts/refresh_check.sh` 入库前即 bash -n 失败（`<技能安装位>` 占位伪脚本），未修；k3 归档内同名副本同样既有失败；2026-09-27 门禁实测发现第三件同类：`k3-everything-archive/upload/skill-dist-20260829/一键重装.sh`。三件均入豁免表留痕不修。
- 流水线完整程序（2026-09-27）：桌面 `skills-hub-release/release.cjs`（单文件零依赖 Node≥18），命令 gate/gen/verify/commit/push/remote/release，固化 add→gen→verify→add MERKLE→commit→HTTP/1.1 push 重试→远端 fetch fatal-UTF8 root 比对+抽查哈希；push 需 --push 且交互确认；沙箱与真实仓库（2978 件，root 与远端一致）双向验证通过。
- 自主阶段二批（2026-09-27）：二轮复译 419 块（累计 972 译/356 留，拒绝集收敛按退化门停三轮）；`docs/evals/` 273 例调度评测（tools/evals-gen.cjs）；`docs/skill-graph.json` 57 边（tools/gen-graph.cjs）；tools/ 共七件生成器。Merkle 根随批更新，每批 gen→verify→中文 commit→HTTP/1.1 后台重试推送。
- Qoder 自定义模型写入（#14）自动化证伪证据：customs 存储真加密（QMC\x01）无离线写入器；computer-use 像素路径在三套坐标体制（+12+41 / 恒等 / 设置覆层非线性漂移）与 app 自更新（0.4.3 换句柄）下不可靠；设置页真实路径＝设置→模型→添加自定义模型，四值候用户粘贴。

**Why:** 用户要求库"注释完整简体汉化、去 AI 味、结构化、注入 SHA-3 后量子哈希树"，上述工具链即该立法的落地件。
**How to apply:** 改库内容后严格按固定次序 add→gen→verify→add MERKLE→中文 commit→HTTP/1.1 推送；再跑汉化批时复用断点文件续跑。
