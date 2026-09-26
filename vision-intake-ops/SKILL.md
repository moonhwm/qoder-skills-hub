---
name: vision-intake-ops
description: "[项目技能·强制入口] 视觉输入总门——图像输入统一路由+共享识读底座（伞件，三件本体不复制）。【强制】凡消息含图片/截图/照片（含静默上传、图文混排）必先经本件路由，禁绕过直读/凭印象猜。触发（任一）：①上传图片不知走哪件（拍题/文档/二维码/截图混杂）；②说「看图」「识别这张图」「扫一下」「读图」「图像输入」或等价表述，含需将合同照片转成文字、把这几张发票和带二维码的海报都扫一遍等指令；③批量图像先分类再分发，处理多源图片时自动归类且不遗漏。覆盖：输入路由（scripts/vision_route.py：QR→qr-visual-rescue，文档/长图→vision-ocr-pipeline，拍题图示→doc-image-solver）、共享预处理（EXIF/压图/切片）、人工--mode直指定。不覆盖：三件本体识读（引用不复制）、视频（归 av-media-ops）、金融凭证勾稽（归 bidding-ops §10.5）。中文名：视觉输入总门。English: image input routing, ocr dispatch, qr scan entry, any image must route here first."
metadata:
  version: "0.1.2"
---

# 视觉输入总门（vision-intake-ops）

> v0.1.2（2026-09-16）：patch——触发层强化（机主令「稍微加强一下强制调用的可能性」）：description 改强制入口制（含静默上传/图文混排必先路由+禁绕过+英文强制钩），值 977B 仍守 ≤1024 盲评约束；§0 增强制调用契约。功能零改动（结构/路由判据/脚本本体三不动）。安装位只读未写回，已入写回队列。
>
> v0.1.1（2026-09-10）：达尔文九维盲评整改——补建 references/routing_misses.md（原悬空引用，空表+填写规范）、§1 补 vision_route.py 真实调用命令与 needs_review 失败分支、新增路由门 🔴CHECKPOINT 与 STOP 显性标记×4、description 裁至 1024 字符内（原 1082 超限）、「切片建议」软化措辞硬化。
>
> v0.1.0（2026-09-09）：创刊。依据=技能正交完备性检查 §3.1-#5（视觉输入三件同格未整合）+排期表 B6 项（机主令「继续推进相关实施」T3 批）。构型=**伞件路由+共享底座**（归一为 vision-intake 伞：输入路由+共享识读底座，三件本体不动——消三套压图/引擎选型重复的入口侧）。

## §0 定位与红线
- 🔴 **强制调用契约**：本件为一切视觉输入的强制入口——凡消息含图像输入（含静默上传、图文混排），先跑 §1 执行式定路由再调目标件本体；禁绕过本件直接识读，禁凭文件名/印象猜路由。
- 🔴 本件是**伞件**：只做「分给谁」与共享预处理；识读逻辑一律调三件本体脚本（引用不复制——防 fusion-map 已验证的吞并式失败）。
- 路由判据为启发式（QR 定位/长宽比/边缘密度），**误判可人工 `--mode` 直指定**；路由结论标 conf=estimated，识读可信度以目标件自身档位为准（vision-ocr-pipeline 高保证/doc-image-solver QA 自检/qr-visual-rescue 降级在场——三档现状继承，不凭记忆升档）。
- 凭证级图片转写后勾稽纪律不归本件——bidding 场景走 bidding-ops §10.5，金融场景走持仓观察纪律章程。

## §1 路由表

🔴 CHECKPOINT（路由门）：未定路由不得进入识读环节；conf=estimated 的 auto 结论不得当作高保证转述。
| 输入画像 | 判据 | 目标件 | 备注 |
|---|---|---|---|
| 二维码/条码 | opencv QR 定位命中 | qr-visual-rescue | 解码归其本体；疑难件登记「未解出」不硬闯 |
| 文档页/扫描件/长图 | 长宽比>1.7 或边缘密度>0.02 | vision-ocr-pipeline | 超 1:7 先切片（继承其纪律） |
| 拍题/图示/手写字 | 前两者不命中 | doc-image-solver | 手写/歧义【存疑】禁猜读 |
| 人工指定 | --mode qr/doc/problem | 对应件 | auto 判定跳过 |

执行式（判据由脚本实测特征驱动，不凭肉眼）：

```bash
python3 scripts/vision_route.py route <图片路径> [--mode auto|qr|doc|problem]
python3 scripts/vision_route.py prep <图片路径> [--out <输出路径>]
python3 scripts/vision_route.py --self-test
```

输出 JSON 含 suggested_route / features / reason / preprocessing。🔴 STOP：返回 `needs_review=true`、脚本执行失败、或 auto 结论与人工预期冲突时，禁自行猜路由——转人工 `--mode` 直指定，并将案例登记 references/routing_misses.md。

## §2 共享预处理底座（prep）
EXIF 方向校正→长边 2000px 压图（保留原件，产 .prepped.jpg）→长宽比>7 🔴STOP 输出切片方案待确认，禁自动切。批量输入先 prep 再 route，防三件各自重复压图。

## §3 留痕与版本纪律
- 路由误判案例（人工 override 与 auto 不一致）登记 references/routing_misses.md，攒 ≥5 例修订判据阈值（证据驱动，禁拍脑袋调参）。
- 版本三档同型立法；patch 静默不广播。

## 边界
不做视频（归 av-media-ops）；不做识读本身；不替代三件各自的环境在场性实测纪律（新环境逐件复测后方得依赖）。
