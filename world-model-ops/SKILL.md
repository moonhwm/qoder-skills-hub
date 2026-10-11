---
name: world-model-ops
description: 开放式世界模型之作入口径（建世界/进房/保活/发令/取产物/定量判读）；由 A2A新席_石敢当Cairn 依实测血证整理
---

# 世界模型作业（世界探索 · 实时导演 · 角色演绎）

## 何时用
须创建/进入一个开放式世界、令其保持、或对其输出做定量判读时。

## 硬口径（十四条，皆实测）
1. 建世界**必须**带 `firstFrameImage`（不带 ⇒ HTTP 200 而业务码 `400000`）；**须横版且比例合规**（16:9 可行；5:4 被拒）。
2. **HTTP 200 ≠ 成功** —— 一律看 `output.code`：`400000` 参数错｜`404000` 尚无产物｜`409000` 拒令。
3. `maxExperienceTimeSec` ＝ **枚举 {60, 90, 120}**（45／300 皆拒）。
4. `noStreamAutoEndTimeoutSec = 30` ⇒ **无人接入流即 30 秒自动收束**（短片之真因）。
5. **★保活（每 3 s 轮询 `status`）⇒ `rtcStatus` 由 `INIT` 转 `STREAMING` ⇒ 会话由 30 s 延至 ≥110 s ⇒ 录像由 ~0.8 MB 增至 ~9 MB**。
6. `instruct` 之可受令次数**与会话流态相关**：未保活时第 2 次起 `409000`；`STREAMING` 时第 2 令亦受。
7. `userInstructions[].status` 有显式值（含 `UNEXECUTED`）；令常**登记而不执行**。
8. `characterActions` 由世界自带（本 app：`dash`/`jump`/`crouch`/`attack`），与输入无关。
9. `encryptedTravelId` **与世界绑定**（同世界多次进房尾号相同）。
10. 产物：`artifacts` ⇒ `{composeStatus, video{original, withWatermark, withInstruction, withInstructionAndWatermark}}`；`composeStatus` 可能先 `processing`，**须重取**。
11. RTC 常为**私有实现**：`appId` 公网查不到（`invalid vendor key`）、`token` 为不透明令牌 ⇒ 公网 SDK 不可接；`playUrl` 常为 `None`。
12. **★标记色＋质心追踪法**：首帧置专属标记色 ⇒ 抽帧按容差检测其像素数与质心 ⇒ 同答"存在性／轨迹／几何一致性"。
13. `firstFrame` 回传 CDN 地址 ⇒ 可核"我的首帧是否被采纳"。
14. **★判读须先减"会话抖动底噪"**：均值 0.2409 均差／84.572% 相同；区间 0.1733–0.3339／80.27–88.10% ⇒ 小于此即底噪，大于此方须另寻原因。

## 标准作业五步
① 备 16:9 带标记首帧 → ② 建世界（看业务码）→ ③ 进房（枚举值）→ ④ **保活轮询＋发令** → ⑤ 取产物（重试至非 `processing`）＋抽帧／标记追踪／底噪对照。

## 验收标准
六步皆业务码 0；`rtcStatus` 见 `STREAMING`；录像显著大于未保活者；标记可检出且质心可算；判读有底噪对照。
