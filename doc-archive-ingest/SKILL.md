---
name: doc-archive-ingest
description: 网盘分享链接文档归档管线：解析坚果云公开分享链接与百度网盘分享链接（pan.baidu.com/s/）、枚举目录、带节奏批量下载、生成出处登记册（含字幕组式版权注记与文档摘要）、PDF 水印识别与合规去水印（仅限用户已购/自有文档）。百度网盘支持双通道：本人网盘官方 xpan/PCS API（用户自持 access_token）+分享页逆向枚举（不稳定，如实标注）。用于网盘归档、坚果云、百度网盘、百度云、百度云盘、pan.baidu.com、PCS、xpan、分享链接解析、提取码、批量下载、出处登记、版权注记、水印识别、去水印、文档摘要、PDF处理等场景。中文名：网盘文档归档台
---

# doc-archive-ingest（网盘文档归档台）

<!-- v1.2（2026-08-29）\这是中文解释：新增坚果云预览通道备用取回——pubPreviewLink→WOPI GetFile（≤10MB 办公文档原始字节）+tblv2 图片预览档（.preview.jpg 诚实命名），实战 10 分享 1004 文件 385MB 验证；403 不再是唯一终点，授权后可走 preview 通道并登记 channel=preview；历史：v1.1 百度云双通道、v1.0.1 五件套映射声明、v1.0 首版 -->
<!-- v1.1（2026-08-24）\这是中文解释：新增百度云双通道——官方 xpan API（--token）+分享页逆向枚举（--share，标注不稳定）；限速与 31362/UA 事实入 references；历史：v1.0.1 五件套映射声明、v1.0 首版 -->

## 概述

把用户提供的坚果云公开分享链接归档为本地文件 + 可追溯的出处登记册：
枚举目录 → 批量下载（带节奏、留证据）→ 逐文件登记出处与摘要 → （可选且
需授权）对已购文档做 PDF 水印识别/合规抹除。全链路标准库起步，PDF 处理
依赖 pymupdf。自本版本起同时支持百度网盘：用户本人网盘走官方 xpan API
（token 由用户自行获取），分享链接走分享页逆向枚举（不稳定，如实标注）；
两通道清单与证据 JSON 直接喂同一出处登记册。

## 铁律（不可违反）

1. **不伪造下载成功**：403/失败如实记录，摘要不编造；未获正文只按文件名
   判断并注明"未获取正文"。
2. **不绕过技术保护**：分享者禁止下载即止步留痕（唯一例外：用户显式授权后的
   官方预览通道备用取回，见 references 第 10 节——取回范围以分享者已开放的
   预览权限为限，图片仅预览分辨率且须 `.preview.jpg` 诚实命名）；加密/DRM 的
   PDF 不破解；图像层水印有边界不清风险，只报告不涂抹。
3. **授权范围限定**：去水印仅限用户本人已购/自有文档，且必须取得并记录
   显式授权声明（`--owned`），处理范围以声明为限。

## 路由表

| 用户意图 | 路由 |
|---|---|
| 解析分享链接、看目录里有什么 | `scripts/netdisk_browse.py <链接> --enum-only` |
| 批量下载归档（带节奏与留痕） | `scripts/netdisk_browse.py <链接> --out <目录> --round N --trigger "授权说明"` |
| 403/下载被拒怎么办 | 读 `references/jianguoyun_api.md` 第 4/5/6/9 节（先读 download_is_disabled 标志，不重试不绕过）；用户显式授权后可走预览通道备用取回（第 10 节） |
| 坚果云分享禁止下载但已获用户授权取回 | `scripts/jianguoyun_preview_fetch.py <链接> --out <目录> --trigger "授权说明"`（≤10MB 办公文档取原始字节；图片仅预览分辨率存 `.preview.jpg`；>10MB 如实记 big） |
| 生成出处登记册、版权注记、文档摘要 | `scripts/source_register.py --manifest 清单.json --evidence 证据.json --archive-root 目录 --out 出处登记册.md`（字段规范见 `references/source_register_spec.md`） |
| 扫描 PDF 有哪些水印 | `scripts/pdf_watermark.py scan <路径> [报告.json]` |
| 给已购/自有 PDF 去水印 | `scripts/pdf_watermark.py clean <路径> --owned "用户授权声明原文"`（边界与法律提示见 `references/legal_notes.md`） |
| 百度网盘分享链接（pan.baidu.com/s/，含提取码） | `scripts/baidu_share_browse.py --share <链接> --pwd <提取码>`（逆向通道，接口事实与失效处置见 `references/baidu_netdisk_api.md`） |
| 用户本人百度网盘枚举/取直链 | `scripts/baidu_share_browse.py --token <access_token> --dir <路径>` 或 `--fsids "[...]" --dlink`（官方 xpan 通道，token 由用户自行在开放平台获取） |
| 多轮重跑（用户称已获授权） | 轮次 +1 重跑下载与登记，证据/清单/登记册全部追加不覆盖 |

## 标准工作流

1. **解析链接**：从 `https://www.jianguoyun.com/p/{hash}` 提取分享 ID；
   接口用法与地域分流现象读 `references/jianguoyun_api.md`。
2. **枚举**：运行 `netdisk_browse.py --enum-only` 出清单 JSON；若拿到分享页
   HTML，先读 `download_is_disabled` 标志预判下载可行性。
3. **下载**：去 `--enum-only` 重跑；节奏 0.5~1s，4xx 不重试，证据写入
   `下载尝试证据.json` 的 `round{N}` 节点。全部 403 时如实收工，向用户说明
   出路（索取已开下载权限的链接/访问密码，或在用户显式授权后走第 10 节
   预览通道备用取回），不伪造成功。
4. **登记**：用 `source_register.py` 生成 `出处登记册.md`；已下载文件按类型
   抽取摘要（PDF 前 500 字 / docx 正文 / xlsx 表头），未下载的诚实标注。
5. **水印（可选）**：先 `scan` 出报告给用户看；仅在用户明确声明文档为其
   已购/自有并授权后，带 `--owned "声明原文"` 执行 `clean`。原件保留，
   产出 `_cleaned.pdf` 副本与双 SHA-256 日志。

每个脚本支持 `--smoke` 离线自测（假响应/合成清单/自构带水印 PDF），
交付或改动后先跑冒烟再实跑。

## 五件套立场

本技能的五条为**领域定制等价物**，与标准五件套对应关系：诚实留痕↔收割指针
（落盘可回放）、尊重权限↔conf 纪律（403 是确定性结论）、授权留证↔top3 自我
批判位（授权边界即最可能错处）、最小处理↔L 等级诚实、注记忠实↔data_cutoff
（轮次时间戳即时效锚）。显式声明：标准五件以等价形态齐备，无豁免缺项。

1. **诚实留痕**：成败、轮次、原因全部落盘（证据 JSON + 登记册），追加不
   覆盖，可回放审计。
2. **尊重权限**：403 SandboxAccessDenied 是确定性结论——不重试、不绕过、
   不伪装；把"怎么办"的选择权交还用户。
3. **授权留证**：去水印的授权声明原文记入日志，范围外文档一律不碰；
   无 `--owned` 旗标脚本直接拒绝（退出码 3）。
4. **最小处理**：只动文本/注解层水印对象，原件永远保留，副本双 SHA-256
   可校验。
5. **注记忠实**：字幕组式版权注记逐字使用（"由用户提供的公开分享链接
   获取，仅供个人学习使用，权利归原权利人所有"），不夸大授权、不掩饰
   灰色地带（《著作权法》第四十九条/第五十三条提示见 references）。

## 与其他技能衔接

归档产物（清单 JSON、证据 JSON、出处登记册.md）是干净的面板数据源：
招生/录取类归档的面板数据可喂 unified-decision-suite 的
admission-panel-analytics 做后续分析。

## 资源索引

- `scripts/netdisk_browse.py` — 坚果云枚举+下载一体化（仅标准库，`--smoke` 不联网）
- `scripts/jianguoyun_preview_fetch.py` — 坚果云预览通道备用取回：pubPreviewLink→WOPI GetFile（≤10MB 办公文档原始字节+size_match 校验）+ tblv2 图片预览档（`.preview.jpg` 诚实命名）；`--trigger` 授权必填，`--smoke` 离线自测
- `scripts/baidu_share_browse.py` — 百度网盘双通道：官方 xpan 枚举/取直链（--token）+ 分享页逆向枚举（--share，不稳定）（仅标准库，`--smoke` 全离线 FakeFetcher）
- `scripts/source_register.py` — 清单+证据→出处登记册.md（摘要抽取按需惰性加载 pymupdf/python-docx/openpyxl）
- `scripts/pdf_watermark.py` — PDF 水印识别与合规抹除（需 pymupdf，缺失时优雅降级）
- `references/jianguoyun_api.md` — 已逆向接口文档与两轮 403 实战教训
- `references/baidu_netdisk_api.md` — 百度网盘双通道接口事实（data_cutoff=2026-08-24，conf=estimated）：官方 xpan 接口表、dlink UA/31362/600s 时效、限速事实、分享页逆向警示、实测 errno 登记表模板、退出码语义
- `references/legal_notes.md` — 版权注记范本、去水印授权边界、灰色地带提示、公开工具索引登记规则
- `references/source_register_spec.md` — 出处登记册字段/摘要/诚实标注规范
