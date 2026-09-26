# plan.md — 光伏研报 + 300274 个股 + 谣言链（简版口径，2026-09-01）

| 步骤 | 状态 | 偏差/降级 |
|---|---|---|
| 读技能本体+references/pipeline.md+example-filled.md | 完成 | 无 |
| §1 首动作：读上游两技能 | 完成 | 实际读取路径 `<技能安装位>/hifi-integration-umbrella/SKILL.md`（v1.7.6）与 `<技能安装位>/rumor-chain-verifier/SKILL.md`（v1.1.0）+ playbook.md + scripts/chain_check.py；标准路径在场，未降级 |
| 伞 §0.1 前置链（intl-case-intf/k3/omni） | 声明降级 | 本任务为金融管线，前置链件与本任务无管辖交集；按「最小够用」仅采纳伞 §2 仲裁序（红线→验收闸→执行件），未逐件调度 |
| S1 数据采集 | 完成 | 金融插件（iFinD/Wind）不在场→降级公开检索通道（2 轮 web 检索），conf 照实标注；原始简报落盘 <输出区>/research/pv-300274/ |
| S2 研报写作 | 完成 | 压缩模式：单章成稿，免 docx/图表；含行业主线+个股分层研判（确认/破坏信号+把握三档） |
| S3 谣言链 | 完成 | 压缩模式：2 条真实传言（空方禁令链/多方千亿营收链），各 ≥3 节含因果节；chain_check.py 校验零 errors |
| S4 审议闸 | 骨架声明 | 时间受限按压缩表执行：未跑控辩/盲评/监管门，产物标注「未经实闸」 |
| S5 成稿归档 | 完成 | 压缩模式：md 落盘+免责声明，docx 与卷宗从简（仅 verdict-gate 骨架声明文件） |
