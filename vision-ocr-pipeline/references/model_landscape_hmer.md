# HMER/LaTeX-OCR 模型地形图（2026-08-29 GitHub 实测调研）

> 触发场景：手写试卷/公式照片的 LaTeX 化求助。结论先行：**当前公开模型对手写中文+公式混合整页照片全部未达到门槛**；本技能的"视觉直读+数值核验"链路维持为唯一可用路径。

## 候选清单与门槛判定

| 项目 | 星标/维护 | 训练域 | 对本任务（手写中文+公式整页照） | 判定 |
|---|---|---|---|---|
| lukas-blecher/LaTeX-OCR（pix2tex） | 高星、持续 | im2latex-100k 印刷体渲染公式 | 官方 README 自述手写支持在 TODO 未勾；汉字全盲；torch 重依赖 | **未达到**（官方证据级） |
| Reriiii/MathSnap-AI（Mini-CoMER） | 6 星 | CROHME 2013/16/19 | CROHME=干净白底手写数学符号，无 CJK；项目极小 | **未达到** |
| fisherman611/手写数学表达式识别（CAN） | 2 星 | CROHME | 同上 | **未达到** |

## 环境实证（2026-08-29 本沙箱）

- RapidOCR（rapidocr-onnxruntime）安装尝试：后台模式死于 shell 非持久（nohup 不跨调用），前台模式超工具 deadline——**本沙箱调用时限内不可装**；登记为环境限制（非模型否定），长时限环境可再试。
- 教训入库：**本环境背景进程不跨 shell 调用存活**——长安装只能单次前台完成，超限即弃。

## 正确使用姿势（若未来达到门槛）

1. 手写公式→CROHME 系模型只覆盖"干净白底纯公式裁片"子域——须先裁片（本技能 img_token_saver），且仍不读汉字；
2. 任何模型输出 conf≤estimated，进事实表前须第二通道核验（数值复算或视觉模型对照）；
3. 挑模型先看训练域与字集，不看 demo 图。

## 手写试卷整页实证（2026-08-29，RapidOCR 装机成功补记）

**装机路径（镜像源决胜）**：默认 PyPI 超时 → `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple rapidocr-onnxruntime` 一次成（根因=默认源慢，非包重）。注意 shell(root) 与 ipython(uid999) 双 site-packages，装哪边跑哪边。

**能力域实测**（2024 大工手写真题 4 图，输出存 dlut_2024_exam/rapidocr_raw.json）：
- 手写汉字叙事行：可用（约八字准）；试卷结构行（题号/边界条件）：可用；
- 公式/矩阵/上下标/帽符：不可用（矩阵塌成数字行、细笔画 i/σ 丢失）；
- **分工规则修订**：手写试卷 = RapidOCR 跑叙事骨架 + 视觉模型读公式区（按内容类型分田，非全文兜底）。
- 交叉核验价值实证：OCR 作第二信源抽查转写稿，无推翻项、两处互证（见 dlut_2024_exam/ocr_crosscheck_20260829.md）。

## pix2tex 装机实测（2026-08-29，判定升级为实验级）

阳性对照（印刷体，真值已知）：3/3 结构骨架正确，但 2/3 有符号级误差（ħ→r̄、cos→c o S）——v0.0.1 权重在训练域内亦非生产级。
实测组（手写真题裁片）：2/2 输出为 array 括号噪声汤——**域外失效实证**。
装机路径：清华 pip 镜像 + ghfast.top 预下载双权重（GitHub 直连超时）；权重落 model/checkpoints/ 即离线。
**最终判定：未达到门槛（conf=empirical，实验级）**。详细报告：dlut_2024_exam/ocr_lab/pix2tex_lab_report.md。
