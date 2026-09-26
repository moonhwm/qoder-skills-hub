#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""av_intake.py v0.1.0 — 音视频作战室管线脚本（2026-09-09 创刊）
本地化铁律：一切处理在本机，零出域。低置信段【存疑】禁猜读。
用法：
  av_intake.py probe <音视频路径>                     # ffprobe 探针（时长/流信息）
  av_intake.py transcribe <音视频路径> [--model base] [--out 目录]   # ASR 逐字稿（jsonl+md）
  av_intake.py ingest <音视频路径>... --out <摄取包目录>               # 摄取包（契约 v1.0）
  av_intake.py frames <视频路径> [--interval 60] [--out 目录]          # 抽帧（信源核查用）
  av_intake.py tts <文本路径> --out <mp3路径>          # 语音化末节（本地 espeak/ffmpeg 兜底）
  av_intake.py --self-test                            # 五夹具自检
"""
import json, subprocess, sys, os, hashlib, datetime, re

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout, r.stderr

def md5file(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def probe(path):
    code, out, err = sh(['ffprobe', '-v', 'quiet', '-print_format', 'json',
                         '-show_format', '-show_streams', path])
    if code != 0:
        return {'error': 'ffprobe_failed', 'stderr': err[:300]}
    d = json.loads(out)
    fmt = d.get('format', {})
    return {'path': path,
            'duration_s': float(fmt.get('duration', 0) or 0),
            'size': int(fmt.get('size', 0) or 0),
            'streams': [{'codec_type': s.get('codec_type'), 'codec_name': s.get('codec_name')}
                        for s in d.get('streams', [])]}

def extract_wav(src, dst):
    code, _, err = sh(['ffmpeg', '-y', '-i', src, '-ac', '1', '-ar', '16000',
                       '-vn', '-f', 'wav', dst])
    if code != 0:
        raise RuntimeError('ffmpeg_extract_failed: ' + err[:300])
    return dst

LOW_LOGPROB = -1.0  # 低于此 avg_logprob 的段标【存疑】

def transcribe(path, model_size='base', out_dir=None):
    out_dir = out_dir or os.path.dirname(os.path.abspath(path)) or '.'
    os.makedirs(out_dir, exist_ok=True)
    info = probe(path)
    if 'error' in info:
        print(json.dumps(info, ensure_ascii=False)); return 1
    tmpwav = os.path.join(out_dir, '._av_tmp.wav')
    extract_wav(path, tmpwav)
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device='cpu', compute_type='int8')
    segments, meta = model.transcribe(tmpwav, vad_filter=True)
    base = os.path.splitext(os.path.basename(path))[0]
    jpath = os.path.join(out_dir, base + '.transcript.jsonl')
    mpath = os.path.join(out_dir, base + '.transcript.md')
    n_seg = n_low = 0
    lines = ['# 逐字稿：%s' % base,
             '> 引擎=faster-whisper 本地 / 档位=%s / 语言=%s / 时长=%.1fs' % (
                 model_size, getattr(meta, 'language', '?'), info['duration_s']),
             '> 低置信段标【存疑】禁猜读；speaker 归属 v0.1 不承诺（静音切分近似）。', '']
    with open(jpath, 'w', encoding='utf-8') as jf:
        for seg in segments:
            n_seg += 1
            low = seg.avg_logprob < LOW_LOGPROB
            n_low += low
            rec = {'start': round(seg.start, 2), 'end': round(seg.end, 2),
                   'text': seg.text.strip(), 'avg_logprob': round(seg.avg_logprob, 3),
                   'flag': 'LOW_CONF' if low else 'ok'}
            jf.write(json.dumps(rec, ensure_ascii=False) + '\n')
            t = '[%7.2f→%7.2f] %s%s' % (seg.start, seg.end,
                                        '【存疑】' if low else '', seg.text.strip())
            lines.append(t)
    lines += ['', '---', '段数=%d，其中【存疑】段=%d。凡引用先抽段人工勾稽，准字率断言最高 conf=estimated。'
              % (n_seg, n_low)]
    open(mpath, 'w', encoding='utf-8').write('\n'.join(lines))
    try:
        os.remove(tmpwav)
    except OSError:
        pass
    print(json.dumps({'jsonl': jpath, 'md': mpath, 'segments': n_seg,
                      'low_conf': n_low, 'duration_s': info['duration_s']},
                     ensure_ascii=False))
    return 0

def ingest(paths, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for p in paths:
        info = probe(p)
        dst = os.path.join(out_dir, os.path.basename(p))
        if os.path.abspath(p) != os.path.abspath(dst):
            with open(p, 'rb') as fi, open(dst, 'wb') as fo:
                fo.write(fi.read())
        rows.append({'source_uri': os.path.abspath(p),
                     'fetched_ts': datetime.datetime.now().isoformat(timespec='seconds'),
                     'title': os.path.basename(p), 'raw_path': dst,
                     'content_hash': md5file(dst), 'media_type': 'av',
                     'duration_s': info.get('duration_s')})
    with open(os.path.join(out_dir, 'index.jsonl'), 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    man = ['# 摄取包 manifest（av-media-ops）', '',
           '> 契约=摄取蒸馏两段式管线契约 v1.0；原始件原格式不动。', '',
           '| # | 文件 | 时长(s) | content_hash |', '|---|---|---|---|']
    for i, r in enumerate(rows, 1):
        man.append('| %d | %s | %s | %s |' % (i, r['title'], r['duration_s'], r['content_hash']))
    open(os.path.join(out_dir, 'manifest.md'), 'w', encoding='utf-8').write('\n'.join(man))
    print(json.dumps({'ingest_pack': out_dir, 'items': len(rows)}, ensure_ascii=False))
    return 0

def frames(path, interval=60, out_dir=None):
    out_dir = out_dir or (os.path.splitext(path)[0] + '_frames')
    os.makedirs(out_dir, exist_ok=True)
    pat = os.path.join(out_dir, 'frame_%05d.jpg')
    code, _, err = sh(['ffmpeg', '-y', '-i', path, '-vf',
                       'fps=1/%d' % interval, '-q:v', '3', pat])
    if code != 0:
        print(json.dumps({'error': 'ffmpeg_frames_failed', 'stderr': err[:300]})); return 1
    n = len([f for f in os.listdir(out_dir) if f.startswith('frame_')])
    print(json.dumps({'frames_dir': out_dir, 'frames': n, 'interval_s': interval},
                     ensure_ascii=False))
    return 0

def tts(text_path, out_mp3):
    txt = open(text_path, encoding='utf-8').read()
    # 掩码闸：手机/身份证/银行卡长数字串先掩码再合成
    txt2 = re.sub(r'\d{7,}', '〔长数字已掩码〕', txt)
    # 本地通道：espeak-ng 直出 wav 再转 mp3
    tmp = out_mp3 + '.tmp.wav'
    with open('/tmp/._tts_in.txt', 'w', encoding='utf-8') as f:
        f.write(txt2)
    exe = 'espeak-ng' if subprocess.run(['which', 'espeak-ng'],
                                        capture_output=True).returncode == 0 else 'espeak'
    if subprocess.run(['which', exe], capture_output=True).returncode != 0:
        print(json.dumps({'error': 'no_local_tts_engine',
                          'note': 'espeak-ng/espeak 不在场；请装 espeak-ng 或改用内置兜底通道（出域先过脱敏闸）'},
                         ensure_ascii=False)); return 1
    code, _, err = sh([exe, '-v', 'cmn', '-f', '/tmp/._tts_in.txt', '-w', tmp])
    if code != 0:
        print(json.dumps({'error': 'tts_failed', 'stderr': (err or '')[:300]})); return 1
    code, _, err = sh(['ffmpeg', '-y', '-i', tmp, '-codec:a', 'libmp3lame',
                       '-q:a', '4', out_mp3])
    try:
        os.remove(tmp)
    except OSError:
        pass
    if code != 0:
        print(json.dumps({'error': 'mp3_conv_failed', 'stderr': err[:300]})); return 1
    print(json.dumps({'mp3': out_mp3, 'masked': txt2 != txt}, ensure_ascii=False))
    return 0

FIXTURE_TRANSCRIPT = [
    {'start': 0.0, 'end': 1.2, 'text': '测试一句。', 'avg_logprob': -0.2, 'flag': 'ok'},
    {'start': 1.2, 'end': 2.5, 'text': '含糊不清的一段', 'avg_logprob': -1.4, 'flag': 'LOW_CONF'},
]

def self_test():
    ok = []
    # F1 probe 夹具：对生成的 1s 正弦 wav 探针
    sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1', '/tmp/._f1.wav'])
    info = probe('/tmp/._f1.wav')
    ok.append(('F1 probe', abs(info.get('duration_s', 0) - 1.0) < 0.2))
    # F2 ingest 夹具
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        ingest(['/tmp/._f1.wav'], td)
        ok.append(('F2 ingest_pack', os.path.exists(os.path.join(td, 'index.jsonl'))
                   and os.path.exists(os.path.join(td, 'manifest.md'))))
    # F3 低置信判级夹具
    lows = [r for r in FIXTURE_TRANSCRIPT if r['avg_logprob'] < LOW_LOGPROB]
    ok.append(('F3 low_conf_triage', len(lows) == 1 and lows[0]['flag'] == 'LOW_CONF'))
    # F4 掩码闸夹具
    t = '联系电话 13800138000 请回电'
    masked = re.sub(r'\d{7,}', '〔长数字已掩码〕', t)
    ok.append(('F4 pii_mask', '13800138000' not in masked))
    # F5 frames 夹具
    with tempfile.TemporaryDirectory() as td:
        sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'testsrc=duration=3:size=320x240:rate=10',
            '/tmp/._f5.mp4'])
        frames('/tmp/._f5.mp4', interval=1, out_dir=td)
        ok.append(('F5 frames', len([f for f in os.listdir(td) if f.startswith('frame_')]) >= 2))
    allpass = all(v for _, v in ok)
    for name, v in ok:
        print('%s %s' % ('PASS' if v else 'FAIL', name))
    print('SELF-TEST', 'PASS' if allpass else 'FAIL')
    return 0 if allpass else 1

def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 2
    cmd = argv[0]
    if cmd == '--self-test':
        return self_test()
    if cmd == 'probe' and len(argv) == 2:
        print(json.dumps(probe(argv[1]), ensure_ascii=False, indent=1)); return 0
    if cmd == 'transcribe' and len(argv) >= 2:
        model = 'base'; out = None
        if '--model' in argv:
            model = argv[argv.index('--model') + 1]
        if '--out' in argv:
            out = argv[argv.index('--out') + 1]
        return transcribe(argv[1], model, out)
    if cmd == 'ingest' and '--out' in argv:
        out = argv[argv.index('--out') + 1]
        paths = [a for a in argv[1:] if not a.startswith('-') and a != out]
        return ingest(paths, out)
    if cmd == 'frames' and len(argv) >= 2:
        interval = 60; out = None
        if '--interval' in argv:
            interval = int(argv[argv.index('--interval') + 1])
        if '--out' in argv:
            out = argv[argv.index('--out') + 1]
        return frames(argv[1], interval, out)
    if cmd == 'tts' and len(argv) >= 2 and '--out' in argv:
        return tts(argv[1], argv[argv.index('--out') + 1])
    print('bad args'); print(__doc__); return 2

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
