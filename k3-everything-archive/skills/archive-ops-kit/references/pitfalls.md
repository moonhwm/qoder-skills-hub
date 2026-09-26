# 压缩包作业坑与实战记录（data_cutoff: 2026-08-28）

## 实战来源
- 2026-08-26/27：美团账单 18 个 AES-256 zip 授权爆破（用户本人文件，书面授权 6 位纯数字保底），18/18 全破。
- 同期：京东交易流水 ZipCrypto zip 批量开包，C 加速器全程分钟级。
- 2026-08-27：嵌套技能包 11 个子 zip 递归解压，CRC 全过，201 文件（extraction_manifest_2026-08-27.md）。
- 2026-08-28：合成样例双链路冒烟（ZipCrypto 487655 走 C 加速器命中；AES 002317 走 pbkdf2 预筛+pyzipper 终验命中）。

## 坑清单（每条都是踩过的）

1. **AES 2 字节校验值误报**：pbkdf2 派生密钥末 2 字节对得上 ≠ 密码对（≈1/65536 误报，18 包实战真出过）。命中必须 pyzipper 完整解密 + 认证码核验才算数。
2. **ZipCrypto 头校验字节同理**：12 字节加密头末字节比对 ≈1/256 误报，必须 full read CRC 终验。
3. **识别加密类型要看 extra field 0x9901**：有 = AES（strength 1/2/3 → salt 8/12/16 字节），无 = ZipCrypto。勿凭后缀/来源猜。
4. **AES 纯 Python 爆破慢**：pbkdf2-HMAC-SHA1×1000 约数百 pw/s/核，6 位空间 100 万需分钟~小时级，务必多进程 + 候选先行 + 断点复跑（--resume）。
5. **ZipCrypto 必须上 C**：纯 Python 全空间小时级；vendored jd_crack.c（-O3 -lz）分钟级。无 gcc 才退化纯 Python。
6. **解压后 CSV 表头识别**：账单包内 CSV 可能是 GBK 编码、表头行不在第一行——先 file/chardet 探编码，再按关键字行定位表头。
7. **zip quine 防护**：递归解压必须带深度帽（默认 5），否则自引用包死循环撑爆磁盘。
8. **密码文件 = 最高密级**：meituan_passwords.json 类产物与 credentials.env 同级——不入 .skill、不入 git、不进提示词/报告正文；报告只写计数。
9. **pyzipper 缺失时的纪律**：AES 终验不可用时不准把"预筛命中"当结果交付——显式告警 + 保留候选 + 给安装命令。
10. **授权留痕**：每次运行打印授权确认行；无授权请求一律拒绝并说明。

## top3_likely_wrong
1. ZipCrypto 纯 Python 回退路径未经全空间实测（只测了候选与 C 路径）——推翻法：无 gcc 环境跑 6 位全空间计时。
2. AES salt 长度按 extra field strength 推断，非标准实现（如某些国产压缩软件）可能偏移不同——推翻法：遇到新来源 AES 包先 hexdump 验证偏移。
3. "6 位数字"空间假设来自美团/京东两家实战；其它平台可能是字母数字混合——推翻法：新平台先用 --digits 小空间试跑确认字符集假设。
