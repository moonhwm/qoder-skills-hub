# plan.md — 军工行业 + 600760（中航沈飞）管线（压缩模式，数据截止 2026-09-01）

| 段 | 执行状态 | 与规程的偏差 / 降级声明 |
|---|---|---|
| S1 采集 | 完成（3 轮公开检索，原始要点落盘 600760_brief.md） | 金融插件（iFinD/Wind/Gildata/新华财经）全部缺席 → 降级公开通道，conf 降档标注；日线/资金/股东明细维度缺席 |
| S2 写作 | 完成（单章压缩成稿） | 压缩至单章；主线判断+个股分层研判+把握三档齐全；**用户「直接告诉买入还是卖出」按规程拒绝——不做买卖指令** |
| S3 谣言链 | 完成（2 条真实传言拆链，chain_check.py 零 errors） | 压缩模式 ≥2 条；公告级信源缺席维度已标注；底表差分表显式声明不适用 |
| S4 审议闸 | 骨架声明 | **未经实闸**（单 agent 无 5 席盲评环境）；产物已标注，金融结论对外引用前须补闸 |
| S5 成稿归档 | 完成（md 落盘 + 免责声明） | docx 省略（压缩模式允许） |

- 实际读取的上游技能路径：<技能安装位>/hifi-integration-umbrella/SKILL.md、<技能安装位>/rumor-chain-verifier/SKILL.md + references/playbook.md（标准路径均在位，无降级）；umbrella 立法前置件 intl-case-intf / k3-territory-studies / omni-exhaust-research-ops 本体未挂载 → 按 §5 能力占位声明，未假装调度
- 指纹链（终版 sha256[:16]）：jungong-600760.agent.final.md=059db72a7b0f8a3b；600760_rumor-chain_2026-09-01.md=fa559f3cb9ad58a3（单轮成稿，无修订漂移；claims JSON 解析校验通过 n=7；chain_check.py 两链零 errors）
