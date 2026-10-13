# Rodin MCP 工具清单（实测 7 件，含 schema 定谳）

来源：2026-09-23 对 `https://api.hyper3d.com/api/mcp` 实测 tools/list 全量 schema。
状态参数一律是 `generation_id`（不是 task_id）。

## rodin_create_uploads（必填 `files`）
为 1–5 张参考图开 1 小时有效的预签 PUT 上传位，返回 upload IDs。
PUT 被网络拦时，按其支持的环境授权流程放行上传域名后重试；实在无法上传，
如实告诉用户"当前模型环境无法上传图片，可到 https://hyper3d.ai 网页上传生成"。

## rodin_import_images（必填 `images`）——仅 ChatGPT Chat 场景
导入 1–5 张会话附件（用 ChatGPT 给的 file_id/download_url；file_name 可带本地路径，
Hyper3D 只保留末尾文件名，≤128 字符）。成功后把 uploads[].upload_id 按序传给
rodin_generate 的 reference_upload_ids。**非 ChatGPT 环境不要用此工具**，走
create_uploads + PUT 链路。

## rodin_generate（prompt / reference_upload_ids 至少其一）
Rodin Gen-2.5 生成，文生、图生或图文混合。消耗 credits。
- `prompt`：无图时必填。
- `reference_upload_ids`：1–5 个 upload ID，按图序传入。
- `mesh_mode` / `tier` / `geometry_file_format`：按需。
- `quality_override`：目标面数；Raw 500–1,000,000，Quad 1,000–50,000。
调用**超时不要自动重试**——让用户去 Hyper3D Mine 检查任务是否已在跑。

## rodin_generate_bang（必填 `asset_id`）——后置拆件，非生成入口
把**已完成的** Rodin 生成按语义拆成部件：传 rodin_generate 返回的 generation_id
作 asset_id。消耗 credits。可选 `instruction`（点名要拆的部件）、`strength`
（目标件数软上限）、`explode_strength`、`escore`（贴图复杂度）、`reference_scale`、
`seed`、`resolution`、`geometry_file_format`。超时同样不自动重试。

## rodin_get_status（必填 `generation_id`）
读当前状态与阶段。stage 含用户可读名 + 1-based 当前进度 + 固定总数；
首个阶段开始前 current 为 0。

## rodin_wait（必填 `generation_id`，可选 `timeout_seconds`）
单次最长等 45 秒到终态。**超时返回的是最新状态，不代表失败**；进度按
stage 名/current/total 报，不是百分比。未竟则再次调用。

## rodin_get_result（必填 `generation_id`）
返回**永久**结果页 display_url + 各产物文件的**临时**签名 URL（files[].url）。
对用户只展示 display_url，**永不暴露 files[].url**；仅当用户明确要下载文件时
才用 files[].url 去取。

## 典型调用链

- 文生：`rodin_generate(prompt)` → `rodin_wait`（循环至终态）→ `rodin_get_result`
- 图生（1–5 图，通用环境）：`rodin_create_uploads` → 逐个 HTTP PUT 上传 →
  `rodin_generate(reference_upload_ids=[...])` → `rodin_wait` → `rodin_get_result`
- 图生（ChatGPT Chat 附件）：`rodin_import_images` → 同上后半段
- 拆件（后置）：`rodin_generate_bang(asset_id=<generation_id>)` →
  `rodin_wait` → `rodin_get_result`

## 纪律

- 生成/拆件消耗 credits，批量前先确认余量；失败如实回传原因。
- `rodin_wait` 返回 ≠ 产物；终态 success 后再 `rodin_get_result`。
- 只给用户 display_url；签名文件 URL 短时效、不缓存、不展示。
