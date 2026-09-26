---
name: qr-visual-rescue
description: >
  多解码器并集 QR/条码可视觉识别挽救管线。当用户需要扫描/识别/解码照片、截图、
  扫描件中的二维码（尤其拍糊、倾斜、低清的实体册页/海报/屏幕拍照），或常规
  解码失败需要换更先进的识别库（zxing-cpp / wechat_qrcode / qreader / 超分）
  实装实测时使用。触发词：扫码、解码二维码、QR 识别、二维码扫不出、条码识别、
  拍照识别码、视觉识别码。不用于：生成二维码（用 cv2.QRCodeEncoder 即可）；
  与 autonomous-advance-ops 的 qr-decode-rescue 关系=本件为多解码器武器库，
  彼件为单库梯子+坚果云取证链，可互补调用。
metadata:
  version: "1.0.0"
---

# qr-visual-rescue（多解码器 QR 挽救）

> v1.0.0（2026-08-30）创刊：wechat_qrcode/qreader 开放项实测收口（重影件 28 组合全灭，证伪「换库可破」），四解码器并集梯子固化。

## 工作流

1. **先跑脚本**，勿手写一次性解码代码：
   ```bash
   WECHAT_QR_MODELS=<模型目录> QREADER_WEIGHTS=<可写目录> \
   python3 scripts/qr_multi_decode.py <图...> [--box x1,y1,x2,y2] [--report r.json]
   ```
   新环境首跑必做 `--self-test`（应见 `PASS` 且 decoders_seen 尽量全）。
2. **读报告**：`verdict=decoded` → 取 hits 文本（多解码器同文本交叉验证更稳）；
   `verdict=undecoded` → 进入归因，**禁止**写成「图中无 QR」，只能写「未解出」。
3. **归因纪律**（单向有效）：Laplacian 方差 <80 必糊；高值须放大目视查斜向拖影/鬼边。
   见重影 = 拍摄运动模糊 → 结论「请重拍」，勿堆算法（28 组合实证，见 references/decoders.md）。
4. 模型/权重文件缺失时按 references/decoders.md 安装矩阵补齐；装不上的解码器脚本自动跳过，不算失败。

## 资源

- `scripts/qr_multi_decode.py` — 4 解码器 × 7 预处理变体并集扫描，JSON 报告，`--self-test` 确定性自检（已实测 PASS）。
- `references/decoders.md` — 安装矩阵（含 opencv 5.0 wechat 接口残缺等坑）、实测登记表、开放项（超分/去模糊网络/多帧合成）。
- `references/ghost_report.json` / `full_report.json` — 创刊实测原始报告（重影件全灭 / 清晰件三库命中）。

## 诚实边界

1. 重影件未解出 ≠ 无解——超分/多帧/重拍通道仍开放（references 开放项），只是算法梯子本级封顶。
2. qreader 首次运行需下载 24MB 权重且依赖 torch——quota 敏感场景可只用 opencv+zxing+wechat 三库。
3. 解码文本若指向外部链接，跟进前按项目红线走（禁外发/写类例外逐次批准）。

## top3_likely_wrong

1. 样本仅 1 页 1 个重影码——「换库同败」结论的泛化性有限（conf=Medium）；
2. wechat 模型取自 GitHub 第三方仓库，版本漂移可能失效；
3. opencv 5.0 wechat 接口残缺为实测现象，未来版本可能修复，锁 4.10 的建议会过时。
