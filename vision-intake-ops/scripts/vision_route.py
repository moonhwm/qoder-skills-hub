#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vision_route.py v0.1.0 — 视觉输入路由+共享识读底座（2026-09-09 创刊）
纪律：路由层只做「分给谁」，识读逻辑一律调三件本体脚本（引用不复制）。
用法：
  vision_route.py route <图片路径> [--mode auto|qr|doc|problem]   # 判路由+给调用建议
  vision_route.py prep <图片路径> [--out 路径]                     # 共享预处理（正方向/压图/长图切片建议）
  vision_route.py --self-test                                     # 五夹具自检
"""
import json, os, sys, subprocess

def has_cv2():
    try:
        import cv2  # noqa
        return True
    except Exception:
        return False

def qr_present(path):
    """opencv 探测是否含可定位 QR（不解码，解码归 qr-visual-rescue）"""
    if not has_cv2():
        return None
    import cv2
    img = cv2.imread(path)
    if img is None:
        return None
    det = cv2.QRCodeDetector()
    ok, _ = det.detectMulti(img)
    return bool(ok)

def aspect_ratio(path):
    if not has_cv2():
        return None
    import cv2
    img = cv2.imread(path)
    if img is None:
        return None
    h, w = img.shape[:2]
    return round(max(h, w) / max(1, min(h, w)), 3)

def doc_like(path):
    """文档页画像启发式：长宽比近 A4(1.414) 或长图，且边缘密度高→倾向 OCR/转写"""
    if not has_cv2():
        return None
    import cv2
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    edges = cv2.Canny(img, 80, 200)
    density = float((edges > 0).mean())
    return density

def route(path, mode='auto'):
    if mode != 'auto':
        return {'path': path, 'mode': mode, 'target': target_of(mode),
                'note': '人工指定模式（auto 判定跳过）'}
    if not os.path.exists(path):
        return {'error': 'file_not_found', 'path': path}
    qr = qr_present(path)
    if qr:
        return {'path': path, 'mode': 'qr', 'target': target_of('qr'),
                'note': 'QR 定位命中→qr-visual-rescue（解码归其本体）'}
    ar = aspect_ratio(path)
    ed = doc_like(path)
    if ar and ar > 1.7:
        return {'path': path, 'mode': 'doc', 'target': target_of('doc'),
                'note': '长图（长宽比 %.2f）→vision-ocr-pipeline（>1:7 先切片，继承其纪律）' % ar}
    if ed is not None and ed > 0.02:
        return {'path': path, 'mode': 'doc', 'target': target_of('doc'),
                'note': '边缘密度 %.3f 文档页画像→vision-ocr-pipeline' % ed}
    return {'path': path, 'mode': 'problem', 'target': target_of('problem'),
            'note': '无 QR/非文档页→doc-image-solver（拍题/图示转写）'}

def target_of(mode):
    return {'qr': {'skill': 'qr-visual-rescue', 'script': 'scripts/qr_multi_decode.py'},
            'doc': {'skill': 'vision-ocr-pipeline', 'script': 'scripts/ocr_shot.py'},
            'problem': {'skill': 'doc-image-solver', 'script': 'scripts/transcription_qa.py'}}[mode]

def prep(path, out=None):
    """共享预处理：EXIF 方向校正+长边压 2000px+超长图切片建议；只产预处理件，原件不动"""
    if not has_cv2():
        return {'error': 'cv2_missing'}
    import cv2
    img = cv2.imread(path)
    if img is None:
        return {'error': 'unreadable', 'path': path}
    h, w = img.shape[:2]
    notes = []
    scale = 1.0
    if max(h, w) > 2000:
        scale = 2000.0 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        notes.append('长边压至 2000px（scale=%.3f）' % scale)
    ar = max(h, w) / max(1, min(h, w))
    if ar > 7:
        notes.append('长宽比 %.1f > 7：建议先切片再识读（继承 vision-ocr-pipeline 纪律）' % ar)
    out = out or (os.path.splitext(path)[0] + '.prepped.jpg')
    cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return {'prepped': out, 'src': path, 'scale': round(scale, 3), 'notes': notes}

def self_test():
    import tempfile
    ok = []
    td = tempfile.mkdtemp()
    p1 = os.path.join(td, 'a.jpg')
    if has_cv2():
        import cv2, numpy as np
        cv2.imwrite(p1, np.full((800, 600, 3), 255, dtype=np.uint8))
        r = route(p1)
        ok.append(('F1 route_runs', 'target' in r))
        r2 = route(p1, mode='qr')
        ok.append(('F2 manual_override', r2['mode'] == 'qr'
                   and r2['target']['skill'] == 'qr-visual-rescue'))
        pr = prep(p1, os.path.join(td, 'p.jpg'))
        ok.append(('F3 prep_out', os.path.exists(pr.get('prepped', ''))))
        long_p = os.path.join(td, 'long.jpg')
        cv2.imwrite(long_p, np.full((7000, 500, 3), 255, dtype=np.uint8))
        r3 = route(long_p)
        ok.append(('F4 longimg_doc', r3['mode'] == 'doc'))
        r4 = route(os.path.join(td, 'nope.jpg'))
        ok.append(('F5 missing_file', r4.get('error') == 'file_not_found'))
    else:
        ok = [('F1-F5', False)]
    for name, v in ok:
        print('%s %s' % ('PASS' if v else 'FAIL', name))
    allpass = all(v for _, v in ok)
    print('SELF-TEST', 'PASS' if allpass else 'FAIL')
    return 0 if allpass else 1

def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 2
    if argv[0] == '--self-test':
        return self_test()
    if argv[0] == 'route' and len(argv) >= 2:
        mode = 'auto'
        if '--mode' in argv:
            mode = argv[argv.index('--mode') + 1]
        print(json.dumps(route(argv[1], mode), ensure_ascii=False, indent=1)); return 0
    if argv[0] == 'prep' and len(argv) >= 2:
        out = argv[argv.index('--out') + 1] if '--out' in argv else None
        print(json.dumps(prep(argv[1], out), ensure_ascii=False, indent=1)); return 0
    print('bad args'); print(__doc__); return 2

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
