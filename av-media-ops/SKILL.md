---
name: av-media-ops
description: "[项目技能] 音视频作战室——音视频材料的摄取、ASR 转写、信源核查与语音化产出一体管线（用户侧主权件）。当您需要查一下视频里提到的这个数据是不是真的，或者需要把视频里的话都整理出来时，系统将调用 ffmpeg 探针与抽取（scripts/av_intake.py）解析素材，经 faster-whisper 本地 ASR 识别后对低置信段标记为【存疑】并禁猜读，随后通过音视频信源核查升级链（转 rumor-chain-verifier，引用不复制）核验声明真伪，最终结合语音变体表容错机制与本地 TTS 末节生成兼容《摄取蒸馏两段式管线契约 v1.0》的摄取包。本管线专注离线处理，不覆盖音视频创作剪辑、实时流处理与任何出域上传，完整覆盖 audio transcription、video speech-to-text、podcast fact-check、voice memo ingest 与 local TTS 等对应场景。"
metadata:
  version: "0.1.0"
---

# 音视频作战室（av-media-ops）

> v0.1.0（2026-09-09）：创刊。机主令「必须全量化建设，拒绝轻量化」——四能力件全建。依据=技能正交完备性检查 §3.2-缺口2（音视频媒介轴用户侧零覆盖，conf=High）+创刊卡 v1.0。在场性实测：ffmpeg 5.1.9 在场；faster-whisper 1.2.1 在场（引擎选型 spike：本地零出域，CPU 可跑 tiny/base/small 三档）。

## §0 定位与红线
- 本件为**编排层作业纪律+本地脚本管线**；音视频原件与转写文本一律**本地化**，零出域（金融数据与个人信息本地化铁律）。
- 凡「转写准确」先证伪后出口：抽段人工勾稽前，准字率断言最高记 conf=estimated。
- PII：转写文本入文书前一律掩码；凭证类音视频（电话录音等）转写后 conf 最高记 estimated。
- 与内置 edge-tts/speech-synthesis 关系：仅作兜底参照；**音频出域先过脱敏闸三判据**，有疑即只用本地通道。

## §1 四能力件
1. **ASR 转写通道**：`scripts/av_intake.py transcribe <音视频路径>`——ffmpeg 抽 16kHz 单声道 → faster-whisper 本地转写 → 带时间戳逐字稿（jsonl+md 双态）。speaker 分段以静音切分近似（v0.1 不承诺说话人归属，归属断言=【存疑】）。低置信段（avg_logprob 低于阈值）逐条标【存疑】**禁猜读**（继承 doc-image-solver 同型纪律）。
2. **语音输入容错层**：`references/voice_variants.md` 变体表（「古吧→股吧」型同音/近音误听映射），转写后先过表再做意图映射；命中即登记「变体命中」留痕。
3. **音视频信源核查**：抽帧（ffmpeg scene 抽帧）+转写 → 声明拆链 → 升级 rumor-chain-verifier / source-tiers 一级信源复核（引用不复制）；未升级标 unverified。
4. **TTS 末节**：`scripts/av_intake.py tts <文本路径>`——本地/内置兜底通道语音化；输出 mp3 落本地；涉实名/金融/PII 文本**先掩码再合成**。

## §2 摄取包产出契约（兼容摄取蒸馏两段式管线契约 v1.0）
一切摄取产出落「摄取包」目录：①原始件（原格式不动）②index.jsonl（每行 source_uri/fetched_ts/title/raw_path/content_hash(md5)/media_type/duration_s）③manifest.md（批次摘要）。蒸馏件消费契约从契约 v1.0，引用带 content_hash 前 8 位溯源。

## §3 引擎档位与成本纪律
- ASR 档位：tiny（快检）/base（常规）/small（凭证级）三档；默认 base；凭证级转写须 small+人工抽段勾稽。
- 模型文件本地缓存，下载一次复用；免费域纪律：不烧 API token。
- 长件（>30 分钟）先切段（30 分钟/段）防内存坍缩，段间重叠 5 秒拼接去重。

## §4 留痕与版本纪律
- 每次转写/核查留 runs 台账（输入 hash/档位/引擎版本/耗时/【存疑】段计数）。
- 版本管理三档（major/minor/patch）继承 bidding-ops §9 同型立法；patch 静默级不广播不催换装。
- 档位变更须附新实测证据件，不得凭记忆升档。

## 边界
不做音视频创作剪辑；不做实时流；一切核查结论标「模型能力上限参考」；音视频原件不出域；转写文本含 PII 掩码后方可入文书。
