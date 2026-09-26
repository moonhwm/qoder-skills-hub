---
name: doc-image-solver
description: "[项目技能] 拍图解题全管线：试卷/文档照片 → 高精度转写文档 → 逐题解读作答 → 迭代收敛。当用户上传试卷/讲义/文档照片要求转写为可读文档、解读题目、给出答案或解题时使用；覆盖手写体存疑标注、可计算答案的数值核验、收敛判定。触发词：拍题、真题转写、试卷识读、看图解题、照片转文字并作答、OCR 转写（语音变体：转写/转述）。整合四技能职责：识读层=vision-ocr-pipeline、委派层=coordination-letter、健康层=k3-interaction-ops、迭代层=autonomous-advance-protocol（引用不复制，各技能规程不变）。中文名：图像解题官"
metadata:
  version: "1.0.0"
---

# 图像解题官（doc-image-solver）

拍图 → 高精度转写 → 解读作答 → 收敛。四段管线，每段挂接既有技能（**引用不复制**）。

## 管线四段

### S1 识读（归 vision-ocr-pipeline 管辖）
读其 SKILL.md 决策表：图像已在对话内且字高 ≥9px → 视觉直读；需本地结构化/数字字段 → RapidOCR/tesseract 双引擎；长宽比 >1:7 先切片。转写文本 conf 最高 estimated；**手写符号歧义逐条标【存疑】**，禁止猜读充数。

### S2 转写文档（本技能模板）
产出 Markdown 精读文档：题面 LaTeX 化 + 结构还原（题型/分值）+ 存疑清单 + 来源与 conf 口径声明置顶。交付前过 `scripts/transcription_qa.py`（七项机检：LaTeX 配对/题号连续/存疑计数/答案标签覆盖/top3 存在/字数/铁律声明）。

### S3 解读作答（核验纪律置顶）
- **可计算的必须数值核验**（矩阵/积分/概率用 numpy/mpmath 复算），答案标 ✅；纯解析推导标 📝；题干存疑给条件作答标 ⚠。
- 符号约定分歧（如平移算符方向）双约定并列并声明，禁止暗选一个。
- 大题允许"路线图级"作答（骨架+关键公式），但须明示收敛层级。

### S4 收敛（归 autonomous-advance-protocol 管辖 + 本技能机检）
初步收敛判据（可测量）：① QA 脚本全绿 ② 可计算项 100% 数值核验通过 ③ 存疑项全部显式登记 ④ top3_likely_wrong 落文。连续 2 轮无新增 Medium+ 发现即停机（边际递减硬停止）。

## 横向职责（恒常在线）

- **委派子代理/跨实例**（归 coordination-letter）：一函一事、边界否定约束、回执五段式、函与回执落盘可审计。
- **长任务健康**（归 k3-interaction-ops）：多图/长文档任务按复杂度阶梯升载；出现碎片先兆按 L1 接地恢复；交付前必做落盘核验。
- **隐私**：用户图像内容默认 P2 永不公开；涉及网盘来源的转写文档置顶铁律声明。

## Resources

- `scripts/transcription_qa.py`：精读文档七项机检（`--self-test` 内置夹具）。
- [references/answer_verification.md](references/answer_verification.md)：答案核验三级标签规程 + 可计算核验清单 + 常见陷阱题型表（如 [X(0),X(t)]≠0）。
- [references/integration_map.md](references/integration_map.md)：四技能职责矩阵（谁管什么、边界条款）。

## 实战标本

`<输出区>/dlut_2024_exam/大工2024考研真题精读_量子与数理方法.md`（2026-08-29，双科四图，QA 全绿）。
