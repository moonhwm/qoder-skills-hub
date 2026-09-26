# 四技能职责矩阵（引用不复制）

| 管线位置 | 技能 | 管辖内容 | 边界（不做什么） |
|---|---|---|---|
| S1 识读 | vision-ocr-pipeline | 通路决策（直读/双引擎/切片）、字高阈值、token 经济、神经超分负结果 | 不管作答正确性 |
| S2 转写 | doc-image-solver（本技能） | 精读文档模板、QA 机检、存疑登记 | 不替 vision-ocr-pipeline 定 OCR 参数 |
| S3 作答 | doc-image-solver + quant-frontier-lab（涉及算法选型时） | 三级核验标签、数值复算 | 不给"伪精确"（未核验不标 ✅） |
| S4 收敛 | autonomous-advance-protocol | 四拍循环、top3 生命周期、边际递减硬停止 | 不管单题正误 |
| 横向·委派 | coordination-letter | 子代理派单六段式、回执五段式、逃逸防线 | 单会话内普通指令不用函 |
| 横向·健康 | k3-interaction-ops | L0–L4 退化光谱、复杂度阶梯、quota 止损 | 不替代交付核验 |

## 冲突裁决
k3-interaction-ops 的 quota 止损 > 一切推进义务；隐私铁律（网盘/个人来源不公开）> 一切交付完整性诉求；coordination-letter 的「越界即停」> 子代理任务完成冲动。
