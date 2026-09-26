---
name: vision-ocr-pipeline
description: "图像识读管线负责截图与长图的识读及跨平台传输。采用本地OCR双引擎分工架构，由RapidOCR执行全文识别并交由tesseract完成数字核验；支持按字高阈值压图以降低token消耗，对超长图片进行长条切片处理，最终生成跨AI环境可用的自包含HTML文件供Kimi、助手甲或外部模型甲等接收图文与对话上下文。适用于截图转文字、提取账单或记录类截图内容、处理图片太长发不出或发给AI太贵的情况、压缩图片后再发给视觉模型、跨AI传图传对话，以及询问OCR、超分或去马赛克方案等场景。当用户提供手机界面截图且设置选项看不清需要把上面的字都认出来时，管线将直接调用该流程完成识别与交付。"
license: MIT
metadata:
  version: "1.1.2"
---

# 图像识读管线（vision-ocr-pipeline）

<!-- v1.1.2（2026-08-29，修改人：Kimi K3）pix2tex 装机实测：阳性对照符号级误差+手写组纯噪声——未达门槛判定升级为实验级；GitHub 权重镜像（ghfast.top）与沙箱非持久 shell 经验入库 -->
<!-- v1.1.1（2026-08-29，修改人：Kimi K3）手写试卷整页实证补登（RapidOCR 装机成功：镜像源路径+双 site-packages 警示；叙事行可用/公式不可用；分田式双通道规则；交叉核验无推翻项） -->
<!-- v1.1.0（2026-08-29，修改人：Kimi K3）新增 references/model_landscape_hmer.md：GitHub HMER/LaTeX-OCR 模型地形图实测调研（pix2tex/MathSnap-AI/CAN 全未达到手写中文整页门槛，官方 README 证据级）+ 本沙箱背景进程不跨调用存活的环境实证；补登 metadata.version（存量立法） -->


把"截图里的信息"以最低成本、可核验地送进文本世界。结论来自 2026-08-27 双样本阶梯实验 + 6 图一致性阶梯 + 对抗压测（旋转/噪声/对比度/亮度/JPEG 重压下 RapidOCR 仍 19~20/20），数据见 references/thresholds_and_pitfalls.md——**动手前先读它**。

> **不确定度声明**：阈值锚点来自 2 张图、6 个字高点（36/18px 实测锚点 + 线性插值）、实验者自评（非盲测），档位有 **±30% 平移误差**。下表数字是带误差带的工程参考，不是物理常数。

## 三条通路决策表

| 信息去向 | 做法 | 成本 |
|---|---|---|
| 本地结构化（进事实表） | `scripts/ocr_shot.py 图 --mode full`（RapidOCR） | 0 token |
| 数字字段（金额/密码/单号/日期） | `ocr_shot.py 图 --mode digits --box x0,y0,x1,y1`（tesseract白名单，自动） | 0 token；与full冲突→裁小图发视觉模型 |
| 发 Kimi 等视觉模型 | 压到正文字高 ≥9px 直接发（手机图宽≥450px/桌面图宽≥900px，见下方口径） | 像素面积降至 ~13%，token 节省**上限** ~87% |
| 跨 AI 交接（助手甲等） | `scripts/pack_handoff_html.py --out h.html 文件…`（图片base64内联） | 单文件自包含 |

**"省 ~87% token" 口径**：数学来自面积比 (450/1260)²≈13%；Kimi 网关对超面积上限的图会先强制降采样、按缩放后尺寸 ÷14 向上取整成网格块计费（2026-06 官方论坛口径），故实际节省是阶梯状的、87% 是**上界**；旧 moonshot-v1-vision 系列为每图固定 1024 token（2026-08-31 下线）。**以 estimate-token-count 实测为准**。

**digits 的 --box 怎么定**：先 `--mode full` 跑 RapidOCR 拿到字段所在文本行位置（或直接看图目视估计金额区域像素坐标），框住目标字段即可；box 越界会自动裁剪并告警。该分工（digits→tesseract）基于单样本个案（RapidOCR 检测器漏裁片内超大美术字），**遇空输出/误读必须 `--engine rapid` 互验**。白名单含 `,%` 和「万元折」，但 CJK 字符在 eng 引擎下会被静默忽略——需要量纲字符时用 rapid 互验。

## 铁律（实证得出的负结果，勿 reinvent）

1. **神经超分不省 token**（适用范围：**干净降采样截图 + 本 OCR 链路 + 已测通用 SR 模型**）：FSRCNN/LapSRN/ESPCN/Real-ESRGAN 全面 ≤ LANCZOS 回放大；GAN 会幻觉出错误笔画（"3.3折"→"9.909"实锤）。需要放大时用 LANCZOS。**未测边界**：文字专用 SR（TATT/TextZoom 系）、带运动模糊/JPEG 块效应等退化输入——对这两类输入本结论不外推。
2. **单图去马赛克不可用**：马赛克=信息销毁（均值池化），静帧恢复=幻觉；JavPlayer/DeepCreamPy 类视频工具仅靠跨帧信息聚合。注意例外：**Depix 类针对"像素化（盒滤波）文字"的恢复攻击真实存在**（利用字体先验搜索），恢复自己被像素化的密码截图是合法用例，但产物仍属推断、禁入事实表。自有数据被打码 → 优先 PIPL 个人信息副本导出申请；PIPL 不可用（平台无导出入口/跨境服务）时无可靠兜底，只能人工回忆+第二信源。合成/恢复内容永远禁入事实表/证据链。
3. **长宽比 >1:7 先切片**（腾讯系拒收线）：`scripts/img_token_saver.py 图 --mode slice`（按 report 建议的 `--screen-h` 显式传值）。
4. **272px 级压缩长条是一切本地 OCR 的死区**（实测 0/18 密码）——只能裁小图发视觉模型。

## 字高阈值速查（汉字像素高，非总像素）

| 通路 | 稳妥 | 极限 | 死亡 |
|---|---|---|---|
| Kimi 视觉 | ≥9px | ≤5px 低置信 | ≤3.6px |
| RapidOCR | ≥6-7px（9px满分） | ≤5px 衰减 | 复杂图小字失效更早 |
| tesseract 整图 | ≥14px | 10px 靠LANCZOS回放大 | ≤7px |
| tesseract 数字白名单 | ≥12px（裁片+zoom放大） | — | — |

**"正文字高"操作定义**：一行**正文**汉字（非标题/注释）在图中所占像素高度。测量：`img_token_saver.py 图 --mode report --glyph`（RapidOCR 框高中位数，粗测 ±20%），或裁一行文字看裁片高度。450px/900px 宽度换算钉在"字高≈36px@1260w"单样本上，字号更小的 App 需按字高重新换算。

## 模型与依赖

- RapidOCR：`pip install rapidocr-onnxruntime`（自带 PP-OCRv4 ONNX 权重）。`<上传区>/cross-ai-toolkit/rapidocr_models/` 另有离线权重备件（仅供手工分发，脚本不自动引用）。
- tesseract 中文包：脚本按 `scripts/tessdata/` → 脚本同目录 → `<上传区>/cross-ai-toolkit/tessdata` → toolkit 根 的顺序找 chi_sim.traineddata，都找不到则用系统默认（digits 白名单模式本就走系统 eng，不受影响；full 的 tesseract 兜底缺包时会显式告警而非静默空转）。自备语言包 = 把 chi_sim.traineddata 拷进 `scripts/tessdata/`。
- 输出位置：full 默认写 `源文件.ocr.txt`，源目录只读时自动落当前目录并告警，`--out` 可显式指定。
- cv2 超分实验需 opencv-contrib 4.x（5.x 删了 dnn_superres）；basicsr 需打 torchvision 补丁。仅复现实验时需要，正常管线**不需要**。

## 模型选型（手写公式/试卷照片）

先读 [references/model_landscape_hmer.md](references/model_landscape_hmer.md)——当前公开 HMER/LaTeX-OCR 模型对手写中文混合整页照片均未达门槛，勿重装浪费。

## 输出纪律

- 进事实表的数字必须过 digits 核验或与第二信源一致；OCR 文本 conf 最高记 estimated（引擎误差），视觉模型目视另按对应技能规程。
- data_cutoff 必填；报告类产物带 top3_likely_wrong。
