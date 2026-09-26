# 解码器安装矩阵与实测登记

## 安装矩阵（2026-08-30 沙箱实测）

| 解码器 | 安装 | 依赖/坑 |
|---|---|---|
| opencv | 随 cv2 内置 | opencv-python 与 opencv-contrib-python 同名互斥，只能留一个 |
| zxing | `pip install zxing-cpp` | 自带预编译轮，免系统 zbar，零配置，**推荐默认装** |
| wechat | `pip install opencv-contrib-python==4.10.0.84`（先卸 opencv-python/headless） | ①需 4 个模型文件（detect/sr 的 prototxt+caffemodel），源：`github.com/WeChatCV/opencv_3rdparty` 的 wechat_qrcode 分支；②**opencv 5.0 的 wechat_qrcode 构造器不收模型路径（残缺接口），须锁 4.10.x**；③路径经 `WECHAT_QR_MODELS` 环境变量或 `--wechat-models` 传入 |
| qreader | `pip install qreader`（拉 torch+ultralytics，体积大） | ①默认 weights_folder 指向 site-packages 内（无写权限即 PermissionError）——**必须显式传可写目录**；②首次运行下载 24MB YOLO 权重；③解码结果 tuple 可能含 None，需过滤 |

## 实测登记（样本：考研册页照片 image_1788016651006(1).jpg，2026-08-30）

| 样本 | opencv | zxing-cpp | wechat | qreader |
|---|---|---|---|---|
| 整页（含清晰件） | ✗ | ✓ | ✓ | ✓ |
| 重影裁剪（上海化工研究院，运动鬼边） | ✗ | ✗ | ✗ | ✗ |

重影件施加 7 种预处理变体（原图/白边/×2/×4/Otsu/CLAHE/非锐化掩模/自适应阈值）× 4 解码器 = 28 组合全灭；
对照组清晰件三库均命中。**结论：解码器换代不补运动重影的信息物理丢失，重拍 > 超分 > 算法堆叠。**

原始报告：`ghost_report.json`（undecoded）、`full_report.json`（decoded，同目录）。

## 开放项（未收敛，登记待试）

- dnn_superres 超分 + 重影件复测（模型下载大，quota-guard 下未做）；
- 去模糊专用网络（DeblurGAN-v2 等）前置；
- 多帧合成（若用户能提供连拍）。
