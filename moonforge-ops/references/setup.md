# setup.md — 从零起步模板（moongate-craft 段 1–6 的落地骨架）

> 所有外链资源须下载为**本地 vendor**（单文件自足纪律：无外部 CDN 依赖，防追踪、防掉线）。

## 1. three.js 钉版骨架（importmap，本地 vendor）

```html
<script type="importmap">
{ "imports": { "three": "./assets/vendor/three.module.js" } }
</script>
<script type="module">
import * as THREE from 'three';
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, innerWidth / innerHeight, 0.1, 200);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));   /* 高分屏钳 2，保帧率 */
document.body.appendChild(renderer.domElement);
</script>
```

- three.module.js 钉版：r160+（实证 r16x 系 API 稳定）；从 unpkg/jsdelivr 下载一次后本地vendor化。
- 月球纹理：NASA SVS CGI Moon Kit（LROC 彩色 + LOLA 位移，公有领域）。

## 2. SunCalc 引入（授时引擎）

```html
<script src="./assets/vendor/suncalc.js"></script>
<script>
  var mt = SunCalc.getMoonTimes(new Date(), lat, lon);   /* 月出月落 */
  var st = SunCalc.getTimes(new Date(), lat, lon);       /* 日出日落（回退级） */
  /* 三级回退：月出月落 → 日出日落 → 兜底 [6,18) 本地时段 */
</script>
```

- 源：github.com/mourner/suncalc（BSD-2）；单文件 suncalc.js 直接 vendor。
- 徽章纪律：判决结果 + 依据 + 定位源 + 下次重算时刻，四件同屏。

## 3. 序章视频切取（ffmpeg 三件套）

```bash
ffmpeg -ss <起> -t 65 -headers "Referer: https://www.bilibili.com/\r\nUser-Agent: <UA>\r\n" \
  -i <video_url> -ss <起> -t 65 -i <audio_url> \
  -map 0:v -map 1:a -c:v libx264 -crf 27 -preset veryfast -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart out.mp4
```

- 验收：抽帧验亮度均值 < 5 即判黑片，换时间点重切。
- B 站取流：view API（无 cookie）拿 cid → playurl `?bvid=&cid=&qn=80&fnval=4048` 拿 durl/dash。

## 4. Playwright 断言模板（段 6）

```python
# 六项硬断言：门可达 / 拖拽改 orbit / 滚轮改 cam / 远端 nebula>0 /
# 徽章含判决依据 / 序章池 ≥2 且反重复 / 零 console error
await pg.goto(BASE); await skip_prologue(pg)
o0 = await pg.evaluate("__gate.orbit")
await drag(pg, 1150, 300, 850, 500)          # 空白处拖拽
o1 = await pg.evaluate("__gate.orbit")
assert o0 != o1                              # 全域可转
await wheel(pg, 3200, 55)                    # 缩小
assert await pg.evaluate("__gate.cam") > 20
assert await pg.evaluate("__gate.nebula") > 0   # 远端星云显影
badge = await pg.text_content('#mgDnStat')
assert '月出' in badge and '月落' in badge      # 判决依据在屏
```

- 安装：`pip install playwright && python3 -m playwright install chromium-headless-shell`
  （无浏览器缓存时可用系统 chromium：`launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])`）。

## 5. 真实钢琴音源（去塑料感）

- Salamander Grand Piano（CC-BY 3.0，github.com/sr229/salamander 镜像）：
  每音 16 个 velocity 层太多——取 C2–C6 每纯八度 3 个力度层即可，ogg 单音 ~100KB。
- 退而求其次：Web Audio 物理建模（弦振动的 Karplus-Strong + 踏板共鸣卷积）远优于裸正弦波。

## 6. FUSE 写盘五连（/mnt 挂载点纪律）

```python
def fuse_write(dst, content: bytes):
    import os, time, shutil, hashlib
    tmp = '/tmp/.fuse_tmp'
    open(tmp, 'wb').write(content)
    try: os.remove(dst)
    except FileNotFoundError: pass
    time.sleep(0.3)
    shutil.copyfile(tmp, dst)
    back = open(dst, 'rb').read()
    assert hashlib.sha256(back).hexdigest() == hashlib.sha256(content).hexdigest()
```
