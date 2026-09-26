# Drive Kit 实测 spike 报告 v1.0（2026-08-31）

> 登记式表述。首行锚：本件为内部技术实测记录，不构成采购或开发建议；证据以 practice/drivekit_spike/evidence/ 原始应答为唯一基准。

## 一、任务来源
用户口令「试 Drive Kit」生效，追加指令：「脆弱已知，跑实际的分析：Drive Kit，如果足够脆弱，上传相关库作为相关的实践经验。」

## 二、实测动作（全部无凭证、不触用户数据）
| 探针 | 目标 | 实测 | 判定 |
|---|---|---|---|
| P1 | driveapis.cloud.huawei.com.cn/drive/v1/files | HTTP 401，errorCode 21000401「authorization header not exist.」 | 服务存活，鉴权闸门在轨 |
| P2 | /drive/v1/about | 同上 401 | 存活 |
| P3 | oauth-login.cloud.huawei.com/oauth2/v3/token | HTTP 400，error 1102「missing required parameter: client_id」 | OAuth 端点存活 |
| P4 | /oauth2/v3/authorize?response_type=code | HTTP 200，返回 OAuth 页 HTML | 授权流入口存活 |
两轮复跑结果一致（evidence/probe_run_20260831.json）。

## 三、文档面交叉核验
1. 官方产品页在架，明示「提供 RESTful 服务接口，支持非 Android 设备上的 App 接入」——服务端接入形态官方认可。
2. REST 开发文档（含文件变化通知等）在文档中心正常发布，未见下线公告。
3. 官方论坛技术支持确认：HarmonyOS NEXT 不提供 Drive Kit，仅端云同步类 API；官方战略替代=Cloud Kit（应用自有数据同步，HDC2026 新增 Web 端接入能力陆续开放中）。

## 四、脆弱性裁决：「足够脆弱」成立
- **非死于技术**：四端点全活，第三方 OAuth+REST 服务端实证存在，技术链可打通。
- **死于结构**：① 官方战略已迁往 Cloud Kit，Drive Kit 属存量维护态，无 NEXT 未来；② 新应用开通需 AGC 实名+开通审批（本 spike 未验证，unverified）；③ access_token 3600s 短命+refresh 链自维护，重运维；④ 「应用的用户文件」定位与「agent 仓库」用途擦边，ToS 政策风险；⑤ 配额/限流未文档化。
- **结论**：不为 1.5T 余量建 Drive Kit 生产依赖。维持总裁决（OBS 正道）不变。

## 五、处置
1. spike 实践库入册：`practice/drivekit_spike/`（探针脚本+两轮原始证据+README 经验卡），供未来复跑对照（任一响应变形即触发重估）。
2. 线三挂账中「Drive Kit spike」工单**销号**，转为观察项档案。
3. 保留观察触发器：Cloud Kit Web 端接入正式开放时重估（正规军路线）。
4. <通道库> <跨席通道表> 发 HANDOFF 简报一封（授权仅限此表写读）。
