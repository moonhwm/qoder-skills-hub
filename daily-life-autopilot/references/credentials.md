# 凭证隔离规范（集群甲铁律）

## 唯一真源

全部私有凭证只存 `<上传区>/credentials.env`（项目私有持久卷）。

## 五条铁律

1. 绝不打包进任何 .skill 技能包（打包前 grep 检查：`.env`、token、key 字样不得出现在包内）。
2. 绝不提交 git / 公开仓库；绝不写进提示词、SKILL.md、前端代码。
3. 技能与脚本只引用环境变量名（AMAP_KEY / AMAP_JSCODE / BAIDU_MAP_AK / MEITUAN_DEV_TOKEN / MEITUAN_USER_TOKEN / MEITUAN_DEVICE_TOKEN）。
4. 好友/同学要用 → 各自免费注册：高德 lbs.amap.com（Web服务 key + 安全密钥）、百度 lbsyun.baidu.com（服务端 AK + IP白名单）、美团 developer.meituan.com（个人开发者 Token，实名即开通）。
5. 疑似泄露 → 立即去对应控制台重置，并检查调用量。

## 哈希链

- 账本：`<上传区>/credential_chain.jsonl`，每个凭证登记为区块，`hash = sha256(canonical_json(block) + prev_hash)`，链上只存 sha256 指纹前 16 位（不可逆，外泄安全）。
- 校验：`python3 scripts/verify_chain.py`（输出 ✅ INTACT / ❌ BROKEN 及断链区块）。
- 追加：新凭证登记、作废声明均为 append-only 新区块；历史区块永不修改。

## 凭证登记处（注册渠道备忘）

| 凭证 | 渠道 | 校验方式 |
|---|---|---|
| 高德 AMAP_KEY + AMAP_JSCODE | lbs.amap.com 控制台→我的应用 | 签名：参数名排序、value 原始拼接（不编码）+ jscode → MD5 = sig |
| 百度 BAIDU_MAP_AK | lbsyun.baidu.com 控制台 | IP 白名单（0.0.0.0/0 开发用）；SK 仅在启用 SN 校验时生成，日常不启用 |
| 美团 MEITUAN_DEV_TOKEN | developer.meituan.com 控制台→Token管理 | 仅创建时可见可复制 |
| 美团用户态 USER/DEVICE_TOKEN | 领券技能 auth.py 短信登录 | 60 秒验证码硬窗口；详见 pitfalls.md |
