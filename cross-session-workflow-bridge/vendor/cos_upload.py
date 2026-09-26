# -*- coding: utf-8 -*-
"""VENDORED 2026-08-26 自 <工作区根>/temp/cos_upload.py（腾讯助手甲产出，用户提供）｜上游: 用户会话｜依赖: pip install cos-python-sdk-v5（非标准库，属"无可奈何降级可选项"——仅COS通道需要）

光伏产业链 K3 交付物 → 腾讯云 COS 上传 + 预签名 URL 生成
=====================================================
填写下方 4 项配置后运行：  python3 cos_upload.py
依赖：pip install cos-python-sdk-v5

【凭证安全】SecretKey 仅存在于你本机，不要贴进任何对话/截图/仓库。
            推荐用「子账号密钥」或 STS 临时密钥（见 授权与上传指南.md）。
"""

# ============ ① 需要你填写的 4 项 ============
SECRET_ID  = "AKIDxxxxxxxxxxxxxxxx"   # TODO: 你的 SecretId
SECRET_KEY = "xxxxxxxxxxxxxxxxxxxx"   # TODO: 你的 SecretKey
REGION     = "ap-guangzhou"           # 截图已选：公有云园区-中国-广州
BUCKET     = "kimi-share-1475054847"  # TODO: 截图里的 [名称]-1475054847，改成完整桶名
#    ↑ 完整桶名 = 你在控制台看到的名称（含后缀 -1475054847），例如 my-pv-1475054847
#      若不确定，控制台「存储桶列表」第一列即是完整名称。
# ==============================================

KEY_DURATION = 24 * 3600   # 预签名 URL 有效期（秒），默认 24 小时，可改短


def main():
    from qcloud_cos import CosConfig, CosS3Client

    client = CosS3Client(CosConfig(
        Region=REGION, SecretId=SECRET_ID, SecretKey=SECRET_KEY))

    # 待上传文件清单（路径相对于本脚本所在目录，或写绝对路径）
    files = [
        "光伏产业链_K3单一文件最终版.html",
        "光伏产业链_K3文本总控台_v4.html",
        "公众号一手出处档案.zip",
        "K3任务交接包_v1.2.zip",
        "股票代码补齐映射表.csv",
        "两份未映射代码核验.json",
    ]

    lines = []
    print(f"{'文件':<45} {'大小(MB)':>9}  状态")
    print("-" * 90)
    for f in files:
        try:
            key = "guangfu/" + f   # COS 中的对象键（前缀 guangfu/ 便于管理）
            client.upload_file(Bucket=BUCKET, Key=key, LocalFilePath=f)
            size = __import__("os").path.getsize(f) / 1e6

            # 生成预签名下载 URL（私有桶靠此分享，无需公开桶）
            url = client.get_presigned_download_url(
                Bucket=BUCKET, Key=key, Expired=KEY_DURATION)
            lines.append(f"{key}\t{url}")

            print(f"{key:<45} {size:>9.2f}  ✓ 上传成功")
        except Exception as e:
            print(f"{f:<45} {'—':>9}  ✗ {type(e).__name__}: {e}")

    # 输出 URL 清单（把这个文件的内容发给 Kimi / 我即可，密钥不用给）
    out = "cos_urls.txt"
    with open(out, "w", encoding="utf-8") as fp:
        fp.write("# 预签名 URL（有效期 %dh，到期需重新运行本脚本刷新）\n" % (KEY_DURATION // 3600))
        fp.write("\n".join(lines))
    print(f"\n已生成 {out}，共 {len(lines)} 条 URL")


if __name__ == "__main__":
    main()
