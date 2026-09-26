# 套磁信模板库（T1/T2/T3）

填空式骨架。`{...}` 为必填变量，`[可选]` 段按 M1/M2 结果决定取舍。
写完后运行 `scripts/letter_honesty_check.py <file>` 再做人工复核。

## T1 正式套磁信（150-200 词）

适用：M1=relevant 且有具体论文 Hook 素材。required_segments: hook, differentiation, gap, platform, interest, request。

```
Subject: MSc Inquiry — {差异化关键词组合，如 "AI for STEM Defect Detection"}

Dear {称谓} {姓氏},

{Hook：引用导师论文原句或其研究的具体观察，1-2 句}
{数字锚点：你本科科研中可辩护的硬数据 1 条，与导师方向的连接 1 句}

Since graduating in {年份}, I have focused on {gap 宽泛主动表述}. I am now ready to commit
to a focused MSc program at {目标院校}, where I hope to contribute to {导师组方向}.

{导师兴趣段：导师工作的哪个具体方面 informs 你的转向，1-2 句}

I would like to formally express my interest in position {职位编号}, and I would welcome
the opportunity for a brief email exchange to explore potential alignment.

I have attached my CV and thesis. Thank you for your time.

Best regards,
{姓名}
[REPLACE_WITH_EMAIL] | [REPLACE_WITH_PHONE]
```

## T2 探索性询问信（120-150 词）

适用：M1=marginal 或信息不足，试探导师是否有坑位。required_segments: hook, capability, exploration, request。

```
Subject: Inquiry — {方向关键词} at {目标院校}

Dear {称谓} {姓氏},

{轻 Hook：方向层面的观察，不必引用具体论文}

My background is in {核心技能/经历，1 句}. {若有：一个可辩护数字锚点}

I am exploring MSc opportunities in {方向}. Would your group be considering new students
for {入学时间}? If so, I would be glad to share my CV and discuss potential fit.

Best regards,
{姓名}
[REPLACE_WITH_EMAIL]
```

## T3 约束确认信（130-160 词）

适用：M2 检出 fatal 约束（C1 转博/C6 强制条款），先确认再决定正式申请。

```
Subject: MSc {职位编号} — {背景关键词} + Interest in {导师方向}

Dear {称谓} {姓氏},

{背景 1 句 + 可辩护数字锚点 1 句}
{gap 宽泛主动表述 + 平台锚定 1-2 句}
{导师兴趣段：具体连接点 1-2 句}

Given my plan to {你的长期规划}, I would like to clarify whether {约束问题，措辞包装在
积极叙事里}. If {期望的答案条件}, I would be eager to submit a full application.

Best regards,
{姓名}
[REPLACE_WITH_EMAIL] | [REPLACE_WITH_PHONE]
```

## 通用禁忌

- 禁用 "Inquiry about MSc Position" 类平庸标题；禁用 "I believe"（主观冗余）
- 不写不可辩护的技能声称（精通 Python/ML 等，除非证据库直接支撑）
- 不提其他 offer、不提缴费 deadline（负面信号）
- 词数硬上限：T1≤200，T2≤150，T3≤160
