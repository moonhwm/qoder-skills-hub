#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qr_multi_decode.py — 多解码器并集 QR 挽救梯子

对一张图（可带裁剪框）按「解码器 × 预处理变体」全组合尝试解码，
输出 JSON 报告；任何解码器命中即记录，绝不覆盖其它结果。

用法:
  python3 qr_multi_decode.py <图...> [--box x1,y1,x2,y2] [--report out.json] [--self-test]

解码器（可用即用，缺席跳过）:
  opencv   - cv2.QRCodeDetector（内置）
  zxing    - zxing-cpp（pip install zxing-cpp）
  wechat   - cv2.wechat_qrcode_WeChatQRCode（opencv-contrib 4.10 + 模型文件）
  qreader  - qreader（YOLO 检测+解码，pip install qreader，需 torch）

纪律（与 autonomous-advance-ops/qr-decode-rescue 一致）:
  - 全变体 0 命中且目视见斜向拖影/鬼边 = 运动重影，结论=请重拍，勿堆算法。
  - 禁止把 None/空结果写成「无 QR」——只能写「未解出」。
"""
import argparse, json, os, sys

def _variants(bgr):
    import cv2, numpy as np
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr
    out = {'orig': bgr}
    out['pad40'] = cv2.copyMakeBorder(g, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
    out['up2'] = cv2.resize(g, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    out['up4pad'] = cv2.copyMakeBorder(cv2.resize(g, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC),
                                       80, 80, 80, 80, cv2.BORDER_CONSTANT, value=255)
    out['otsu'] = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    sharp = cv2.addWeighted(g, 1.8, cv2.GaussianBlur(g, (0, 0), 3), -0.8, 0)
    out['sharp-up2'] = cv2.resize(sharp, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    out['ath-up2'] = cv2.resize(cv2.adaptiveThreshold(
        g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5),
        None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return out

def _decoders(wechat_models=None, qreader_weights=None):
    decs = {}
    import cv2
    det = cv2.QRCodeDetector()
    def opencv(im):
        ok, infos, _, _ = det.detectAndDecodeMulti(im)
        return [t for t in (infos if ok else []) if t]
    decs['opencv'] = opencv
    try:
        import zxingcpp
        def zxing(im):
            return [r.text for r in zxingcpp.read_barcodes(im) if r.text]
        decs['zxing'] = zxing
    except ImportError:
        pass
    if wechat_models and hasattr(cv2, 'wechat_qrcode_WeChatQRCode'):
        try:
            w = cv2.wechat_qrcode_WeChatQRCode(
                os.path.join(wechat_models, 'detect.prototxt'),
                os.path.join(wechat_models, 'detect.caffemodel'),
                os.path.join(wechat_models, 'sr.prototxt'),
                os.path.join(wechat_models, 'sr.caffemodel'))
            def wechat(im):
                ts, _ = w.detectAndDecode(im)
                return [t for t in ts if t]
            decs['wechat'] = wechat
        except Exception:
            pass
    try:
        from qreader import QReader
        kw = {'weights_folder': qreader_weights} if qreader_weights else {}
        qr = QReader(**kw)
        def qreader(im):
            if im.ndim == 2:
                im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
            elif im.shape[2] == 3:
                im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            return [t for t in qr.detect_and_decode(image=im) if t]
        decs['qreader'] = qreader
    except Exception:
        pass
    return decs

def run(image_path, box=None, wechat_models=None, qreader_weights=None):
    import cv2
    img = cv2.imread(image_path)
    if img is None:
        return {'image': image_path, 'error': 'imread failed'}
    if box:
        x1, y1, x2, y2 = box
        img = img[y1:y2, x1:x2]
    report = {'image': image_path, 'box': box, 'hits': [], 'decoders': {}}
    decs = _decoders(wechat_models, qreader_weights)
    for name, fn in decs.items():
        dhits = []
        for vtag, vim in _variants(img).items():
            try:
                for t in fn(vim):
                    dhits.append({'variant': vtag, 'text': t})
            except Exception as e:
                report['decoders'].setdefault(name, {}).setdefault('errors', []).append(f'{vtag}: {e}'[:120])
        # 去重文本
        seen = {}
        for h in dhits:
            seen.setdefault(h['text'], h['variant'])
        report['decoders'][name] = {'unique_hits': seen}
        for t, v in seen.items():
            report['hits'].append({'decoder': name, 'variant': v, 'text': t})
    report['verdict'] = 'decoded' if report['hits'] else 'undecoded'
    return report

SELFTEST_QR = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='

def self_test(wechat_models=None, qreader_weights=None):
    """生成一个确定内容的 QR 图，要求至少一个解码器命中。"""
    import cv2, numpy as np, tempfile
    payload = 'qr-visual-rescue-selftest-2026-08-30'
    enc = cv2.QRCodeEncoder_create()
    mat = enc.encode(payload)
    mat = cv2.copyMakeBorder(mat, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    p = os.path.join(tempfile.gettempdir(), 'qvr_selftest.png')
    cv2.imwrite(p, mat)
    rep = run(p, None, wechat_models, qreader_weights)
    ok = any(h['text'] == payload for h in rep['hits'])
    print(json.dumps({'self_test': 'PASS' if ok else 'FAIL', 'decoders_seen': list(rep['decoders'])}, ensure_ascii=False))
    return 0 if ok else 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('images', nargs='*')
    ap.add_argument('--box', help='x1,y1,x2,y2')
    ap.add_argument('--wechat-models', default=os.environ.get('WECHAT_QR_MODELS'))
    ap.add_argument('--qreader-weights', default=os.environ.get('QREADER_WEIGHTS'))
    ap.add_argument('--report')
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test(a.wechat_models, a.qreader_weights))
    if not a.images:
        ap.error('need images or --self-test')
    box = [int(x) for x in a.box.split(',')] if a.box else None
    reps = [run(p, box, a.wechat_models, a.qreader_weights) for p in a.images]
    out = json.dumps(reps, ensure_ascii=False, indent=1)
    if a.report:
        open(a.report, 'w').write(out)
    print(out)
    sys.exit(0 if all(r.get('verdict') == 'decoded' for r in reps) else 2)

if __name__ == '__main__':
    main()
