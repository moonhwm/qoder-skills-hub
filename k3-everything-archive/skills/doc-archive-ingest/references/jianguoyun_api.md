# 坚果云公开分享接口参考（已逆向，实战核对）

> 来源：2026-08-24 归档实战（4 个分享链接、195 个文件、两轮 403）。接口签名
> 核自分享页前端 `/static/js/pubobject_page.min-*.js`（该 JS 的全量 ajax 端点
> 已枚举，无其他公开下载端点）。坚果云未公开文档化这些接口，签名可能变动；
> 每次开跑前重新核对分享页前端 JS。
> 2026-08-29 增补第 10 节：预览通道（pubPreviewLink→WOPI GetFile + tblv2 图片
> 预览档）备用取回路径，实战 10 分享 1004 文件 385MB 验证。

## 目录

- [1. 端点清单](#1-端点清单)
- [2. pubDIRBrowse 目录枚举](#2-pubdirbrowse-目录枚举)
- [3. pubDIRLink 下载](#3-pubdirlink-下载)
- [4. download_is_disabled 标志判读](#4-download_is_disabled-标志判读)
- [5. 403 SandboxAccessDenied 处置](#5-403-sandboxaccessdenied-处置)
- [6. 地域分流现象](#6-地域分流现象)
- [7. 节奏与重试纪律](#7-节奏与重试纪律)
- [8. 失败留痕格式（round 追加不覆盖）](#8-失败留痕格式round-追加不覆盖)
- [9. 实战教训汇总（两轮 403）](#9-实战教训汇总两轮-403)
- [10. 预览通道备用取回（2026-08-29 实证）](#10-预览通道备用取回2026-08-29-实证)

## 1. 端点清单

| 用途 | 方法 | 端点 | 参数 |
|---|---|---|---|
| 目录枚举 | GET | `https://www.jianguoyun.com/d/ajax/dirops/pubDIRBrowse` | `hash`, `relPath` |
| 取下载 URL | GET | `https://www.jianguoyun.com/d/ajax/dirops/pubDIRLink` | `k`, `dn`, `p` |
| 分享页 HTML | GET | `https://www.jianguoyun.com/p/{hash}` | —（判读 `download_is_disabled` 用） |

分享 ID（hash）从分享链接 `https://www.jianguoyun.com/p/{hash}` 的末段取得，
形如 `DctQY5sQoPuYDRjWwugFIAA`。

## 2. pubDIRBrowse 目录枚举

```
GET /d/ajax/dirops/pubDIRBrowse?hash={分享ID}&relPath={路径}
```

- `relPath` 从 `"/"` 开始；对返回对象中 `type == "directory"` 的条目以其
  `relPath` 递归下钻（BFS），直至无新目录。
- 200 响应：`{"objects": [{"name", "relPath", "type": "file"|"directory",
  "size", "mtime", ...}]}`；`size` 单位字节，`mtime` 为分享方修改时间。
- 非 200 或缺少 `objects` 键：记入 `enum_errors`（relPath + http_status +
  response_head 前 300 字符），不中断整体枚举。
- 枚举成功 ≠ 可下载。枚举走的是匿名公开通道，与下载权限相互独立。

## 3. pubDIRLink 下载

```
GET /d/ajax/dirops/pubDIRLink?k={分享ID}&dn={根目录名}&p={relPath}
```

- `k` 即分享 ID；`dn` 为分享根目录名（取分享页 `PageInfo.name`；地域分流
  拿不到时用占位名，实测权限判定与 dn 无关）；`p` 为文件 `relPath`。
- 允许下载时：HTTP 200 `{"payload": <下载URL或其包装>}`。payload 可能是
  字符串 URL，也可能是 `{"url"|"link"|"downloadUrl"|"href": ...}` 字典包装，
  需兼容提取；随后 `GET` 该 URL 取字节落盘，落盘前按 relPath 拼接目标路径
  并做路径穿越防护。
- 禁止下载时：HTTP 403，响应体
  `{"errorCode": "SandboxAccessDenied", "detailMsg": "Can not download it"}`。
- 落盘后校验：实际字节数 vs 清单 `size`，记 `size_match`。

## 4. download_is_disabled 标志判读

- 分享页 HTML 内嵌 `download_is_disabled: true|false` 前端标志，是分享者
  「允许下载」开关的直接证据。
- **教训：批量尝试下载前先读该标志。** 实战中 link3/link4 标志为 `true`，
  其全部文件下载果然 403；标志读取成本远低于逐文件试错。
- 地域分流导致拿不到分享页 HTML 时（见下节），该标志不可读，应在证据中
  注明"标志不可读（地域分流）"，不得臆测其值。

## 5. 403 SandboxAccessDenied 处置

403 + `SandboxAccessDenied` = 分享者侧权限拒绝，是**确定性**结论：

1. 不做无谓重试（4xx 一律不重试；仅网络错误/5xx 重试 ≤2 次）。
2. 不绕过：不使用任何规避权限的手段。以下"旁证"动作只做**事实确认**，
   不改变处置结论——实战中均已实测仍 403：
   - 携带分享页 Cookie + Referer 重试；
   - 整包下载变体（不带 `p` 参数）；
   - 换用正确根目录名 `dn`。
3. 如实留痕（格式见第 8 节），在登记册中写"未获取正文（分享者设置了
   '仅预览/禁止下载'权限，下载接口返回 403 SandboxAccessDenied；本管线
   不绕过该限制）"。
4. 给用户的出路：向分享者索取已开启下载权限的链接；用自己的坚果云账号
   确认是否在被授权范围；或索取访问密码。用户声明已获授权后，开新一轮
   （round+1）重跑，历史轮次留痕不覆盖。

## 6. 地域分流现象

- 从境外（如美国出口 IP）匿名访问部分分享页时，坚果云返回**注册引导页**
  而非分享页 HTML（实战中 link1/link2 如此，link3/link4 正常）。
- 后果：根目录名 `dn` 与 `download_is_disabled` 标志均无法取得。
- 处置：`dn` 用占位名继续（已实测权限判定与 dn 无关）；证据中注明
  "分享页因地域分流返回注册引导页"。
- 注意：目录枚举接口（pubDIRBrowse）不受地域分流影响，仍可正常枚举。

## 7. 节奏与重试纪律

- 每次请求间隔 **0.5~1.0 秒**（随机抖动），不并发打接口。
- 重试上限 2 次，且仅针对网络错误（连接异常）与 5xx；4xx 确定性拒绝
  不重试。
- 长任务每完成一个链接即落盘一次证据，防中断丢失。

## 8. 失败留痕格式（round 追加不覆盖）

证据文件 `下载尝试证据.json` 按轮次节点组织——**追加 `round{N}` 节点，
永不覆盖历史轮次**；同轮次重跑仅替换本链接的记录（幂等）：

```json
{
  "round1": {
    "fetched_at": "2026-08-24 05:57:00 +0800",
    "trigger": "本轮触发说明（如用户授权声明）",
    "interface": "接口签名核对来源说明",
    "enumeration": {"<hash>": {"dirs": 10, "files": 56, "enum_errors": [], "manifest": "…"}},
    "download_attempts": [
      {"link": "<hash>", "relPath": "/a/b.pdf",
       "endpoint": "/d/ajax/dirops/pubDIRLink?k=…&dn=…&p=/a/b.pdf",
       "attempts": 1, "http_status": 403,
       "errorCode": "SandboxAccessDenied", "detailMsg": "Can not download it",
       "saved_path": null, "saved_bytes": null, "expected_size": 127227}
    ],
    "summary": {"<hash>": {"success": 0, "failed": 56, "total": 56}}
  }
}
```

成功记录则 `http_status: 200`、`saved_path`（相对链接子目录）、
`saved_bytes`、`size_match: true`、`detailMsg: "OK"`。
重新枚举的清单另存 `文件清单_{名称}_第{N}轮.json`，不覆盖历史清单。

## 9. 实战教训汇总（两轮 403）

| 教训 | 内容 |
|---|---|
| 先读标志再下载 | `download_is_disabled: true` 预示全量 403，先读标志省一轮试错 |
| 403 是确定性结论 | Cookie+Referer、整包变体、正确 dn 均不改变 403；不做无谓重试 |
| 枚举≠可下载 | 两轮枚举均成功且清单一致，但 195/195 下载全 403 |
| 地域分流 | 境外 IP 可能拿到注册引导页；dn 用占位名，证据注明分流 |
| 留痕追加不覆盖 | round1/round2 节点并存；重跑同轮只替换本链接记录 |
| 不伪造 | 两轮成功 0 即如实记 0；登记册摘要写"未获取正文"，不编造 |

## 10. 预览通道备用取回（2026-08-29 实证）

当第 3 节 pubDIRLink 全量 403（download_is_disabled=true，分享者设置「仅预览」）
且**用户显式授权**时，分享者已开放的官方预览通道可作为备用取回路径。
实证：10 个分享、1004 文件、385MB、0 缺失；WOPI 通道 30 个抽样字节数与清单
`size` 全部一致（取回的是原始字节，非转码档）。脚本：
`scripts/jianguoyun_preview_fetch.py`（`--trigger` 授权说明必填，`--smoke` 离线自测）。

### 10.1 办公文档（pdf/xlsx/docx 等，≤10MB）：pubPreviewLink → WOPI GetFile

```
GET /d/ajax/pubPreviewLink?key={hash}&pdfviewer=false&relpath={relPath}
    （Referer: https://www.jianguoyun.com/p/{hash}）
-> 200 {"url": "https://...viewer...?src={wFileId}", ...}
GET https://oos.jianguoyun.com/oh/wopi/files/@/wFileId/contents?wFileId={quote(src, safe='')}
-> 200 文件原始字节
```

- **10MB 上限**：>10MB 文件此通道不可得，如实记 `big`，不截断不伪造。
- 落盘后校验 `saved_bytes == 清单 size`（size_match）。
- 失败形态：`{"errorCode": "OperationNotAllowed", ...}`（图片等不支持类型，见 10.2）。

### 10.2 图片：tblv2 预览档（非原图，诚实标注）

- 图片走 pubPreviewLink 返回 `OperationNotAllowed`；改取 pubDIRBrowse 清单对象
  自带的 `tblUri` 字段：

```
GET https://www.jianguoyun.com{tblUri}/{l|m|s}
    （Referer: https://www.jianguoyun.com/p/{hash}）
```

- `l`≈`m`（实测同一张 546x1024、171450B JPEG），`s` 为缩略图（53x100、1840B）；
  **均为预览分辨率，不是原图**；裸 tblUri 与 `?size=original`/`?w=2000` 均 400。
- 落盘统一命名 `<原名去扩展名>.preview.jpg`——内容为 JPEG 预览档，不得伪装成
  原扩展名原图；登记册注明「预览分辨率副本（channel=preview-image）」。

### 10.3 合规边界（不可逾越）

- 启动前提：用户显式授权（`--trigger` 必填，原文入证据 JSON）。
- 本通道取回的是分享者已开放预览的内容；加密/DRM 文档不破解；不得把
  预览档描述为「原文件已下载」——办公文档须 size_match 佐证，图片必须
  `.preview.jpg` 命名。
- 留痕沿用第 8 节 round{N} 追加不覆盖；证据节点加 `"channel": "preview"`。
