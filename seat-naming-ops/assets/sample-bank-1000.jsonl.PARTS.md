# sample-bank-1000.jsonl — 分片发布说明

原文件 353374B / 1000 行 JSONL，超出单次推送上限，按行切分为 7 片发布于 `parts/` 目录。
拼接还原（逐字节一致）：

```bash
cat parts/p0.jsonl parts/p1.jsonl parts/p2.jsonl parts/p3.jsonl parts/p4.jsonl parts/p5.jsonl parts/p6.jsonl > sample-bank-1000.jsonl
```

校验：还原后文件 353374B，git-blob sha1 = `2be7f5e28fd831f86b29fe1271b0ac17f9486f45`
（`git hash-object sample-bank-1000.jsonl` 应输出该值）。

| 分片 | 行数 | 字节 | git-blob sha1 |
|---|---|---|---|
| p0.jsonl | 143 | 50454 | 1b1baf37da691847ab6b544727452c0af62965aa |
| p1.jsonl | 143 | 50315 | 59aebd9984081e66fb93aae709b213ac240d1022 |
| p2.jsonl | 143 | 50681 | 47088c3dd39e3d93ea1bd7f1b37a0530f04ff793 |
| p3.jsonl | 143 | 51007 | 86169a4a7797a3ed8cb801b91a3b76ab4ab82efa |
| p4.jsonl | 143 | 50355 | ba5d0ba7a9806faa555bc01ad229e8dc86f4fd7f |
| p5.jsonl | 143 | 50273 | 0bc774e481345eeba86542935874881c39e0c965 |
| p6.jsonl | 142 | 50289 | abd80fd5acd9a5c8a828d84a77df46cd556d2992 |

> 原件本地保留；如需整文件直推（git 协议/PAT）可日后补推并删除本说明与 parts/。
