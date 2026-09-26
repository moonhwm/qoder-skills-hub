# Drive Kit spike 实践经验库（v1.0 / 2026-08-31）

> 入册事由：用户口令「试 Drive Kit」→「脆弱已知，跑实际的分析：如果足够脆弱，上传相关库作为相关的实践经验」。本库即该 spike 的全套实践留痕。

## 目录
- `scripts/drivekit_probe.py` — 无凭证四端点存活探针（可复跑，exit 0=全活被闸）
- `evidence/` — 2026-08-31 两轮实测原始应答（401/400 JSON + 汇总报告）

## 实测结论一句话
**技术全活，战略已迁：四个端点全部存活且闸门正常（401/400 符合预期），但 Drive Kit 不进 HarmonyOS NEXT、官方替代 Cloud Kit 语义不同——「足够脆弱」成立，不建生产依赖，本库仅作实践经验存档。**

## 脆弱性矩阵（实测+文档交叉）
| 环节 | 证据 | 评级 |
|---|---|---|
| REST 服务端点 | 实测 401 `errorCode 21000401 authorization header not exist`（两次复跑一致） | 活 |
| OAuth token 端点 | 实测 400 `error 1102 missing client_id` | 活 |
| authorize 页 | 实测 HTTP 200 返回登录页 HTML | 活 |
| 官方产品页 | 仍在架，明示「RESTful 接口，支持非 Android 设备接入」 | 在架 |
| NEXT 支持 | 官方论坛技术支持：NEXT 无 Drive Kit，仅端云同步 API | **弃用迁移中** |
| 新应用开通 | 需 AGC 登录+开发者实名认证，本 spike 未验证 | unverified |
| token 运维 | access_token 3600s（第三方实证），refresh 链需自维护 | 重运维 |
| 用途合规 | 定位「应用的用户文件」场景，当 agent 仓库=ToS 擦边 | 政策风险 |

## 复跑方法
```bash
python3 scripts/drivekit_probe.py evidence/probe_run_<日期>.json
```
预期：四端点全 `ALIVE_GATED`。任一变形（2xx 无闸/5xx/域名失效）即重估裁决。
