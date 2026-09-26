# 任务卡七段式模板与标本

## 模板（填槽即得合格卡）

```
【项目·任务名】<一句话使命>。请按序执行并核验：
1. ls 核验核心台账存在：<绝对路径清单，逐个可 ls>。
2. cd <项目根> && git status（应干净或仅有已说明改动）；VERSION 应为 <版本号>。
3. 快速测试门禁：<最小测试命令>（<关键断言摘要>）。沙箱重置丢依赖时先重建（<重建命令>）。
4. 检查挂账是否到期可推进：①<条件/日期+动作> ②…
5. 新增成果确认落库 <路径A> 与 <路径B> 双保险，并更新 <状态板/胶囊>；
   防AI幻觉：只汇报磁盘核验为真的事实，缺测即标缺测。
发现异常（文件缺失/测试红/git丢失）→ 如实报告并给出修复路径，不假装正常。
```

填槽纪律：① 全部绝对路径；④ 每条挂账带日期或触发条件；⑥⑦ 为强制条款（lint C5/C6 硬判）；纯检索类任务可省 ②③。

## 标本一：花未眠·凌晨四点自检（2026-08-29 用户提供的完整原文，lint PASS）

> 【花未眠·凌晨四点自检】物理硕士择校评分系统每日自检（呼应川端康成《花未眠》）。请按序执行并核验：
> 1. ls 核验核心台账存在：<输出区>/评分系统_优化版/data/ 下 schools.json(113校)、panel_pdf_ledger.json(53校)、panel_critique.json、panel_code_scan.json(59代码)、pv_lithium_chain.json；网站 <输出区>/app/(index.html+fusion.html+narrative.html+charts.js+style.css+data.js+sources.js+assets/)；交接文档 <上传区>/集群甲交接_花未眠研究站_完善任务.md。
> 2. cd <输出区>/评分系统_优化版 && git status（应干净或仅有已说明改动）；VERSION 应为 v68.69。
> 3. pytest 快速门禁：python3 -m pytest tests/test_engine.py -q -k "v67_0_param_registry or facade"（param=220 缺解释=0、__version__=68.69、__all__=124）。沙箱重置丢 pytest/git 时先重建（pip install -q pytest；git init+safe.directory+pre-commit hook）。
> 4. 检查挂账是否到期可推进：①9月简章季（花名册7校/北科大0-74/南昌639/坍缩校报名重估）②agent-gw视频接口是否恢复（补封面动态视频）③光伏/锂电/LED ETF 季度复拉（2026-11）。
> 5. 若有新增成果或证据链文件，确认落库 <输出区> 与 <上传区> 双保险，并更新 capsule.md 与 status_board.json；防AI幻觉：只汇报磁盘核验为真的事实，缺测即标缺测。
> 发现异常（文件缺失/测试红/git丢失）→ 如实报告并给出修复路径，不假装正常。

为什么它是好卡：七段齐全；路径全绝对且可 ls；测试门禁带断言摘要（param=220/缺解释=0）；挂账全部带触发条件（9月/接口恢复/2026-11）；反幻觉与异常条款 verbatim 命中。

## 标本二：收敛版周检（grad-path-scorer 项目，lint PASS）

> 【grad-path-scorer 周一自检】仅执行：python3 <输出区>/grad-path-scorer-workspace/scripts/daily_check.py。all_pass=true → 结果追加 cron_check.log 后一行回复收工，禁加载技能、禁读其他文件；FAIL → 按 <输出区>/skill-dist-20260829/HANDOFF.md 与 WRITEBACK_QUEUE.md 处置并向用户报告失效项。附：touch 预检 <技能安装位> 与 <上传区> 可写性，转可写则按队列执行 U1 装包三步。

范式差异：把检查细节沉进独立脚本，卡正文只剩「跑脚本+分流」——**细节进脚本、卡里只留调度**，是携带重检查逻辑任务的推荐形态（卡正文省 token、脚本可版本化）。
