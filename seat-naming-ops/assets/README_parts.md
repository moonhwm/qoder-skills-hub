# 分片接收说明（sample-bank-1000.jsonl）

本目录的 `parts/p0..p6.jsonl` 是 `sample-bank-1000.jsonl`（353374 字节 / 1000 行）的分片发布形态——原文件超出推送通道上限，按行连续切成 7 片。本说明给您**零门槛还原**路径：装不装 Python 都能拼，拼完可用同目录 `verify_parts.py` 一键验真。

## 方法一：纯命令行（无需 Python）
```bash
cat parts/p0.jsonl parts/p1.jsonl parts/p2.jsonl parts/p3.jsonl parts/p4.jsonl parts/p5.jsonl parts/p6.jsonl > sample-bank-1000.jsonl
```

还原后用 Git 验真：`git hash-object sample-bank-1000.jsonl` 应输出 `2be7f5e28fd831f86b29fe1271b0ac17f9486f45`；没有 Git 时用方法二脚本验真。


## 方法二：脚本校验+还原（推荐）

同目录 `verify_parts.py` 会逐片核对（字节数/行数/git-blob sha1/尾换行），再整体验收（353374B、1000 行、blob `2be7f5e28fd831f86b29fe1271b0ac17f9486f45`）：

```bash
python3 verify_parts.py parts/                 # 只校验，不写文件
python3 verify_parts.py parts/ --write         # 校验并还原出 sample-bank-1000.jsonl
```

输出 `ALL CHECKS PASS` 即还原成功；任何不符会以退出码 2 报出具体差异。

## 真值表

| 分片 | 行数 | 字节 | git-blob sha1 |
|---|---|---|---|
| p0.jsonl | 143 | 50454 | 1b1baf37da691847ab6b544727452c0af62965aa |
| p1.jsonl | 143 | 50315 | 59aebd9984081e66fb93aae709b213ac240d1022 |
| p2.jsonl | 143 | 50681 | 47088c3dd39e3d93ea1bd7f1b37a0530f04ff793 |
| p3.jsonl | 143 | 51007 | 86169a4a7797a3ed8cb801b91a3b76ab4ab82efa |
| p4.jsonl | 143 | 50355 | ba5d0ba7a9806faa555bc01ad229e8dc86f4fd7f |
| p5.jsonl | 143 | 50273 | 0bc774e481345eeba86542935874881c39e0c965 |
| p6.jsonl | 142 | 50289 | abd80fd5acd9a5c8a828d84a77df46cd556d2992 |
| **还原件** | **1000** | **353374** | **2be7f5e28fd831f86b29fe1271b0ac17f9486f45** |

> 本说明与 verify_parts.py 为 2026-10-01 由同步主线（K3 Orchestrator）补发的接收端便利件；`sample-bank-1000.jsonl.PARTS.md` 是首版指针文件，两者互补，均保留。
