---
name: archive-ops-kit
description: "压缩包作业箱：自有加密 zip（AES-256/ZipCrypto）授权爆破、两级校验防误报、批量递归解压（嵌套包+CRC校验+防zip quine）、MD5 差异比对与封存归档。当用户要处理加密压缩包/解压密码忘了/账单类 zip（美团/京东等）批量开包、嵌套 zip 递归解压、批量文件归档封存时触发。中文名：压缩包作业箱"
license: MIT
---

# 压缩包作业箱（archive-ops-kit）

加密包授权破解 + 批量解压验真 + 封存归档。全部脚本经 2026-08-27/28 实战与合成样例冒烟（references/pitfalls.md）。

## 红线（先于一切操作）

1. **授权铁律**：爆破仅限用户本人文件 + 明确书面授权；无授权不启动。
2. **保密铁律**：产出的密码文件（`_passwords.json` 等）与 credentials.env 同级保密——绝不打包进 .skill、绝不提交 git、绝不写进任何文档/提示词。
3. **两级校验铁律**：任何"快速校验命中"都必须 full_verify（完整解密+CRC/认证码）终验后才可信——AES 2 字节校验值误报率 ≈1/65536、ZipCrypto 头校验字节误报率 ≈1/256，实战中误报真实发生过。

## 前置依赖（动手前先查）

```bash
which gcc && echo 'zlib.h' | gcc -E - >/dev/null 2>&1   # ZipCrypto C 加速器需要（缺则退化纯 Python）
python3 -c "import pyzipper"                            # AES 终验需要（缺则预筛命中也无法定案）
```
缺 pyzipper：`pip install pyzipper`；缺 gcc：ZipCrypto 链路仍可用但慢一个量级。

## 决策表

| 场景 | 命令 | 说明 |
|---|---|---|
| 加密 zip 密码忘了（定长数字） | `scripts/zip_crack.py "包.zip或通配"` | 自动识别 AES/ZipCrypto 走对应链路；ZipCrypto 有 gcc 时分钟级，**AES 纯 Python 预筛最坏小时级**——先用候选+小空间确认字符集假设再全空间 |
| 批量/嵌套 zip 解压+验真 | `scripts/skill_batch_archive.py 源包.zip --reference 参照目录 --workdir 工作目录 --seal 封存包路径` | 递归下钻、CRC 校验、MD5 新旧比对、封存 |
| 只要递归解压验真 | 同上，去掉 --seal | 产出解压清单（markdown） |

## 交付规程

1. 脚本产出 `_passwords.json`（保密级）；若任务要求特定格式（如 result.json），从它转换生成，**转换件同样保密**。
2. **独立复核铁律**：写最终交付文件前，用 zipfile/pyzipper 以所得密码独立解密一遍确认（工具内两级校验之外的第三道保险）。
3. 报告只写"已破解 N/M"与链路说明，**不写密码本体**。

## zip_crack.py 链路（自包含三级兜底）

- **ZipCrypto**：先常见候选秒试 → vendored `scripts/jd_crack.c` 有 gcc 自动编译加速（全程分钟级）→ 无编译器退化纯 Python 头校验预筛（慢但可用）。
- **AES-256**：常见候选 → 纯标准库 pbkdf2 预筛多进程并行 → 命中必须 pyzipper 完整解密终验；缺 pyzipper 时**显式告警并保留候选**（`pip install pyzipper` 后 `--resume` 复跑），绝不静默。
- 支持 `--digits N`、`--out`、`--resume`（复跑自动跳过已破解包）。
- 进度实时打印；密码逐包落盘 `--out`（默认包同目录 `_passwords.json`，**注意保密**）。

## skill_batch_archive.py 要点

- 递归解压嵌套 zip，深度帽 5 层防 zip quine；每包 `testzip()` CRC 验真。
- 与 `--reference` 目录逐文件 MD5 比对出新旧差异表；`--seal` 把原始子包打成带日期封存 zip + README。
- `--smoke` 合成样例自检（纯标准库，零依赖）。

## 输出纪律

- 破解/解压结果落盘带日期；密码文件单独存放、报告里只写"已破解 N/M"不写密码本体。
- data_cutoff 必填；报告类产物带 top3_likely_wrong；conf 分 empirical/estimated/assumed。
