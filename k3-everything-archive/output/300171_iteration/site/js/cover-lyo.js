// ═══ 封面引擎 · 医用冻干机（lyophilizer）═══
// COVER.md 四态引擎的 B 态（物理爆炸图）与 C 态（工程蓝图线框），共用同一几何引擎。
// 主题原子：一台冻干机 —— 真空泵组 / 冷阱 / 冻干腔体（搁板）/ 控制压塞系统。
// B/C 两态均为同一台机器的不同视角；点击空白处装配/分解。
(() => {
  const canvas = document.getElementById("cover-canvas");
  const host = document.getElementById("cover");
  if (!canvas || !host || !window.U) return;
  const { PAL, clamp } = U;
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const SERIF = '"et-book", Palatino, Georgia, serif';
  const MONO = 'Menlo, Consolas, monospace';

  // ── 图层定义（自底向上）；col = 该层命题色 ──
  const LAYERS = [
    { name: "真空泵组", en: "VACUUM PUMP SET", w: 22, d: 14, h: 4.2,
      head: "真空泵组 · 出海引擎", sub: "国际收入 10.40 亿 · +29.24% · K8",
      col: PAL.red, kind: "pumps" },
    { name: "冷阱", en: "CONDENSER · COLD TRAP", w: 19, d: 13, h: 5.2,
      head: "冷阱 · 耗材结构改善", sub: "生物工艺毛利率 +18.22pct · K9",
      col: PAL.redHi, kind: "coils" },
    { name: "冻干腔体 · 搁板", en: "DRYING CHAMBER · SHELVES", w: 24, d: 16, h: 8.5,
      head: "冻干腔体 · 制剂基本盘", sub: "制剂装备 11.10 亿 · 占收入 44% · K2",
      col: "#42566a", kind: "chamber" },
    { name: "控制与压塞系统", en: "CONTROL & STOPPERING", w: 15, d: 11, h: 5.0,
      head: "现金流背离 · 置顶关注", sub: "经营现金流 -67.03% vs 归母 +134% · K4",
      col: PAL.neg, kind: "control" },
  ];
  const SEP = 7.2; // 爆炸层间距（z 向）

  let mode = "w"; // 'x' = B 爆炸图 · 'w' = C 蓝图线框（默认 C，见任务指定）
  try {
    const q = new URLSearchParams(location.search).get("cover");
    const saved = localStorage.getItem("lyo-cover-mode");
    if (q === "x" || q === "w") mode = q;
    else if (saved === "x" || saved === "w") mode = saved;
  } catch (e) {}

  let W = 0, H = 0, u = 10, cx = 0, cy = 0, showLabels = true;
  let yaw = Math.PI / 4, mouseYaw = 0;
  let k = 0, kTgt = 1;           // 爆炸主参数 0=装配 1=分解
  let labelAlpha = 0;
  let running = false, raf = 0, t0 = performance.now();

  const bc = U.bindCanvas(canvas);
  function fit() {
    const r = bc.fit(); W = r.w; H = r.h;
    const leftBound = 0.585 * W, right = W - 332;
    u = Math.min((right - leftBound) / 44, H * 0.0132);
    showLabels = u >= 5.6;
    if (!showLabels) { const r2 = W - 40; u = Math.min((r2 - leftBound * 0.8) / 44, H * 0.0135); }
    cx = (leftBound + (showLabels ? right : W - 40)) / 2;
    cy = 0.56 * H;
    if (W < 860) { cx = W * 0.5; cy = 0.62 * H; u = Math.min(W / 60, H * 0.0128); }
  }

  // 轴测投影：z 向上
  function pt(x, y, z) {
    const rx = x * Math.cos(yaw) - y * Math.sin(yaw);
    const ry = x * Math.sin(yaw) + y * Math.cos(yaw);
    return { x: cx + rx * u, y: cy + ry * u * 0.5 - z * u, rx, ry };
  }
  const easeOutBack = t => { const c = 1.70158; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
  function layK(i) { // 逐层错峰
    return easeOutBack(clamp(k * 1.55 - i * 0.17, 0, 1));
  }
  // 第 i 层的 z 底座（含爆炸抬升 + 呼吸浮动）
  function layerZ(i, t) {
    let z = 0;
    for (let j = 0; j < i; j++) z += LAYERS[j].h;
    const lift = SEP * layK(i) * (i + 0.4);
    const breathe = REDUCE ? 0 : Math.sin(t * 1.1 + i * 1.7) * 0.12 * layK(i);
    return z + lift + breathe;
  }

  // 盒子的 8 角
  function boxVerts(L, zb) {
    const hw = L.w / 2, hd = L.d / 2;
    const c = [];
    for (const z of [zb, zb + L.h])
      for (const [x, y] of [[-hw, -hd], [hw, -hd], [hw, hd], [-hw, hd]])
        c.push({ p: pt(x, y, z), depth: x + y, x, y, z });
    return { b: c.slice(0, 4), t: c.slice(4, 8) };
  }

  function poly(ctx, pts, close = true) {
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
    if (close) ctx.closePath();
  }

  // ── B 态：材质化爆炸图 ──
  function drawLayerSolid(ctx, L, i, t) {
    const zb = layerZ(i, t), { b, t: tp } = boxVerts(L, zb);
    // 侧四面（painter：远面先画）
    const faces = [
      [b[0], b[1], tp[1], tp[0]], [b[1], b[2], tp[2], tp[1]],
      [b[2], b[3], tp[3], tp[2]], [b[3], b[0], tp[0], tp[3]],
    ].map(f => ({ f, d: (f[0].depth + f[2].depth) / 2 }));
    faces.sort((a, b2) => b2.d - a.d);
    for (const { f, d } of faces) {
      const g = ctx.createLinearGradient(f[0].p.x, f[0].p.y, f[2].p.x, f[2].p.y);
      const shade = clamp(0.5 + d / 60, 0.18, 0.82);
      g.addColorStop(0, `rgba(255,255,255,${0.30})`);
      g.addColorStop(0.5, `rgba(133,149,166,${0.28 + shade * 0.2})`);
      g.addColorStop(1, `rgba(5,28,44,${0.10 + shade * 0.16})`);
      poly(ctx, f.map(v => v.p));
      ctx.fillStyle = g; ctx.fill();
      ctx.strokeStyle = "rgba(5,28,44,.55)"; ctx.lineWidth = 1; ctx.stroke();
    }
    // 顶面（斜向光照 + 亮棱）
    poly(ctx, tp.map(v => v.p));
    const tg = ctx.createLinearGradient(tp[0].p.x, tp[0].p.y, tp[2].p.x, tp[2].p.y);
    tg.addColorStop(0, "rgba(247,249,252,.96)");
    tg.addColorStop(1, "rgba(219,226,234,.96)");
    ctx.fillStyle = tg; ctx.fill();
    ctx.strokeStyle = "rgba(5,28,44,.7)"; ctx.lineWidth = 1.1; ctx.stroke();
    ctx.strokeStyle = "rgba(255,255,255,.85)"; ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(tp[0].p.x, tp[0].p.y); ctx.lineTo(tp[1].p.x, tp[1].p.y); ctx.stroke();
    drawIdentity(ctx, L, i, zb, false);
  }

  // ── 状态 C：X射线线框（不消隐）──
  function drawLayerWire(ctx, L, i, t) {
    const zb = layerZ(i, t), { b, t: tp } = boxVerts(L, zb);
    const col = L.col;
    // 顶面白纱罩（前后层次）
    poly(ctx, tp.map(v => v.p));
    ctx.fillStyle = "rgba(255,255,255,.62)"; ctx.fill();
    const edges = [
      [b[0], b[1]], [b[1], b[2]], [b[2], b[3]], [b[3], b[0]],       // 底
      [tp[0], tp[1]], [tp[1], tp[2]], [tp[2], tp[3]], [tp[3], tp[0]],// 顶
      [b[0], tp[0]], [b[1], tp[1]], [b[2], tp[2]], [b[3], tp[3]],    // 立柱
    ];
    for (const [a, bb] of edges) {
      const depth = (a.depth + bb.depth) / 2;
      const isTop = a.p === undefined ? false : (a.z === zb + L.h && bb.z === zb + L.h);
      const al = isTop ? 0.85 : clamp(0.5 + depth / 55, 0.22, 0.7);
      ctx.strokeStyle = hexA(col, al);
      ctx.lineWidth = isTop ? 1.2 : 0.9;
      ctx.beginPath(); ctx.moveTo(a.p.x, a.p.y); ctx.lineTo(bb.p.x, bb.p.y); ctx.stroke();
    }
    drawIdentity(ctx, L, i, zb, true);
  }

  function hexA(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }

  // ── 每层识别细节：泵组双泵+管路 / 冷阱盘管 / 腔体搁板+圆形观察窗 / 控制柜仪表 ──
  function drawIdentity(ctx, L, i, zb, wire) {
    const col = wire ? hexA(L.col, 0.8) : "rgba(5,28,44,.62)";
    ctx.strokeStyle = col; ctx.lineWidth = 0.9;
    const hw = L.w / 2, hd = L.d / 2;
    if (L.kind === "pumps") {
      // 两台泵罐（顶面椭圆）+ 上行管路
      for (const px of [-hw * 0.45, hw * 0.45]) {
        const c = pt(px, 0, zb + L.h);
        ctx.beginPath(); ctx.ellipse(c.x, c.y, 2.4 * u, 1.2 * u, 0, 0, U.TAU); ctx.stroke();
        const c2 = pt(px, 0, zb + L.h - 1.2);
        ctx.beginPath(); ctx.ellipse(c2.x, c2.y, 2.4 * u, 1.2 * u, 0, 0, U.TAU); ctx.stroke();
        const e1 = pt(px - 2.4, 0, zb + L.h), e2 = pt(px - 2.4, 0, zb + L.h - 1.2);
        const e3 = pt(px + 2.4, 0, zb + L.h), e4 = pt(px + 2.4, 0, zb + L.h - 1.2);
        ctx.beginPath(); ctx.moveTo(e1.x, e1.y); ctx.lineTo(e2.x, e2.y);
        ctx.moveTo(e3.x, e3.y); ctx.lineTo(e4.x, e4.y); ctx.stroke();
      }
      // 管路：泵组 → 冷阱方向（虚线上引）
      const p0 = pt(hw * 0.45, 0, zb + L.h + 0.4), p1 = pt(hw * 0.45, 0, zb + L.h + 3.2);
      ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.moveTo(p0.x, p0.y); ctx.lineTo(p1.x, p1.y); ctx.stroke();
      ctx.setLineDash([]);
    } else if (L.kind === "coils") {
      // 顶面盘管折线（之字形冷阱盘管）
      ctx.beginPath();
      const n = 7;
      for (let s = 0; s <= n; s++) {
        const x = -hw * 0.8 + (s / n) * hw * 1.6;
        const y = (s % 2 ? -1 : 1) * hd * 0.62;
        const p = pt(x, y, zb + L.h);
        s ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y);
      }
      ctx.stroke();
      // 内壁同心折线第二圈
      ctx.globalAlpha = 0.5; ctx.beginPath();
      for (let s = 0; s <= n; s++) {
        const x = -hw * 0.6 + (s / n) * hw * 1.2;
        const y = (s % 2 ? 1 : -1) * hd * 0.34;
        const p = pt(x, y, zb + L.h * 0.55);
        s ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y);
      }
      ctx.stroke(); ctx.globalAlpha = 1;
    } else if (L.kind === "chamber") {
      // 四层搁板（横贯腔体的层线）
      for (let s = 1; s <= 4; s++) {
        const z = zb + (s / 5) * L.h;
        const a = pt(-hw, -hd, z), b = pt(hw, -hd, z), c = pt(hw, hd, z), d = pt(-hw, hd, z);
        ctx.beginPath();
        ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.lineTo(c.x, c.y); ctx.lineTo(d.x, d.y); ctx.closePath();
        ctx.stroke();
        if (!wire) { ctx.fillStyle = "rgba(125,155,255,.10)"; ctx.fill(); }
      }
      // 前面圆形腔门 + 观察窗（冻干机的标志性圆门）
      const door = pt(0, hd, zb + L.h * 0.52);
      const rD = Math.min(hw, L.h) * 0.42 * u;
      ctx.beginPath(); ctx.ellipse(door.x, door.y, rD, rD, 0, 0, U.TAU); ctx.stroke();
      ctx.lineWidth = 1.3;
      ctx.beginPath(); ctx.ellipse(door.x, door.y, rD * 0.42, rD * 0.42, 0, 0, U.TAU); ctx.stroke();
      ctx.lineWidth = 0.9;
      if (!wire) { ctx.fillStyle = "rgba(125,155,255,.14)"; ctx.fill(); }
      // 门栓十字
      ctx.beginPath();
      ctx.moveTo(door.x - rD * 0.42, door.y); ctx.lineTo(door.x + rD * 0.42, door.y);
      ctx.moveTo(door.x, door.y - rD * 0.42); ctx.lineTo(door.x, door.y + rD * 0.42);
      ctx.stroke();
    } else if (L.kind === "control") {
      // 控制柜：两只表盘 + 一排按钮
      for (const px of [-hw * 0.4, hw * 0.25]) {
        const c = pt(px, 0, zb + L.h);
        ctx.beginPath(); ctx.ellipse(c.x, c.y, 1.3 * u, 0.65 * u, 0, 0, U.TAU); ctx.stroke();
        const nd = pt(px + 0.5, 0, zb + L.h);
        ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.lineTo(nd.x, nd.y - 0.5 * u); ctx.stroke();
      }
      for (let s = 0; s < 4; s++) {
        const c = pt(-hw * 0.6 + s * hw * 0.35, hd * 0.55, zb + L.h);
        ctx.beginPath(); ctx.arc(c.x, c.y, 0.28 * u, 0, U.TAU); ctx.stroke();
      }
    }
  }

  // ── 标注列（leader line → 右列）──
  function drawLabels(ctx, t) {
    if (!showLabels || labelAlpha < 0.02) return;
    const colX = W - 312;
    const rows = [];
    LAYERS.forEach((L, i) => {
      const zb = layerZ(i, t);
      // 锚点：投影后最右侧的顶角
      const { t: tp } = boxVerts(L, zb);
      let best = tp[0];
      for (const v of tp) if (v.p.x > best.p.x) best = v;
      rows.push({ L, ax: best.p.x, ay: best.p.y, y: best.p.y });
    });
    rows.sort((a, b) => a.y - b.y);
    for (let i = 1; i < rows.length; i++)
      if (rows[i].y - rows[i - 1].y < 40) rows[i].y = rows[i - 1].y + 40;
    ctx.save();
    ctx.globalAlpha = labelAlpha;
    for (const r of rows) {
      const { L } = r;
      ctx.strokeStyle = "rgba(5,28,44,.4)"; ctx.lineWidth = 0.8;
      ctx.beginPath(); ctx.moveTo(r.ax, r.ay); ctx.lineTo(colX - 14, r.y); ctx.lineTo(colX - 6, r.y); ctx.stroke();
      // 空心圆端点（制图惯例）
      ctx.beginPath(); ctx.arc(r.ax, r.ay, 2.6, 0, U.TAU);
      ctx.strokeStyle = hexA(L.col, 0.9); ctx.stroke();
      ctx.fillStyle = "#fff"; ctx.fill();
      ctx.font = `700 11.5px ${MONO}`;
      ctx.fillStyle = L.col; ctx.textAlign = "left";
      ctx.fillText(fitStr(ctx, L.head.toUpperCase(), 292), colX, r.y - 3);
      ctx.font = `10px ${MONO}`; ctx.fillStyle = "#8595a6";
      ctx.fillText(fitStr(ctx, L.sub, 292), colX, r.y + 12);
    }
    ctx.restore();
  }
  function fitStr(ctx, s, budget) {
    if (ctx.measureText(s).width <= budget) return s;
    while (s.length && ctx.measureText(s + " …").width > budget) s = s.slice(0, -1);
    return s.replace(/[，、·\s]+$/u, "") + " …";
  }

  // ── C 态制图底稿：十字网格 + 四角对位标记 + 签名条 ──
  function drawDrafting(ctx) {
    ctx.save();
    ctx.strokeStyle = "rgba(133,149,166,.18)"; ctx.lineWidth = 0.6;
    for (let x = 26; x < W; x += 52) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    for (let y = 26; y < H; y += 52) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    // 四角对位标记（电蓝）
    ctx.strokeStyle = "rgba(34,81,255,.75)"; ctx.lineWidth = 1;
    for (const [mx, my] of [[26, 26], [W - 26, 26], [26, H - 26], [W - 26, H - 26]]) {
      ctx.beginPath(); ctx.arc(mx, my, 7, 0, U.TAU); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(mx - 11, my); ctx.lineTo(mx + 11, my);
      ctx.moveTo(mx, my - 11); ctx.lineTo(mx, my + 11); ctx.stroke();
    }
    ctx.restore();
  }

  function drawCaption(ctx) {
    if (W < 860) return;
    const bx = W - 30, by = H - 88;
    ctx.save();
    ctx.font = `700 10.5px ${MONO}`; ctx.textAlign = "right";
    ctx.fillStyle = PAL.red;
    ctx.fillText(mode === "w" ? "FIG. C — PHARMACEUTICAL LYOPHILIZER" : "FIG. B — PHARMACEUTICAL LYOPHILIZER", bx, by);
    ctx.font = `9.5px ${MONO}`; ctx.fillStyle = "#8595a6";
    ctx.fillText(mode === "w" ? "X-RAY WIREFRAME · 4 ASSEMBLIES" : "EXPLODED VIEW · 4 ASSEMBLIES", bx, by + 16);
    ctx.fillText(k > 0.5 ? "SCALE · NTS · CLICK TO ASSEMBLE" : "SCALE · NTS · CLICK TO EXPLODE", bx, by + 31);
    ctx.restore();
  }

  function draw(now) {
    const t = (now - t0) / 1000;
    const ctx = bc.ctx;
    ctx.clearRect(0, 0, W, H);
    if (!REDUCE) {
      yaw = Math.PI / 4 + 0.3 * Math.sin(t * 0.11) + mouseYaw;
      k = U.ease(k, kTgt, 1 / 60, 0.09);
    } else { k = kTgt; yaw = Math.PI / 4; }
    labelAlpha = U.ease(labelAlpha, clamp((k - 0.45) * 2.4, 0, 1), 1 / 60, 0.06);

    if (mode === "w") drawDrafting(ctx);
    // 地面软阴影
    const gs = pt(0, 0, -0.4);
    const gR = 26 * u * (1 - k * 0.12);
    const grd = ctx.createRadialGradient(gs.x, gs.y + 3 * u, 0, gs.x, gs.y + 3 * u, gR);
    grd.addColorStop(0, "rgba(5,28,44,.10)"); grd.addColorStop(1, "rgba(5,28,44,0)");
    ctx.fillStyle = grd;
    ctx.beginPath(); ctx.ellipse(gs.x, gs.y + 3 * u, gR, gR * 0.42, 0, 0, U.TAU); ctx.fill();
    // 层间悬浮影
    LAYERS.forEach((L, i) => {
      if (i === 0 || layK(i) < 0.05) return;
      const zb = layerZ(i, t);
      const c = pt(0, 0, zb);
      const al = clamp(0.20 - (zb - 0) * 0.007, 0, 0.2) * layK(i);
      ctx.fillStyle = `rgba(5,28,44,${al})`;
      ctx.beginPath(); ctx.ellipse(c.x, c.y + 1.2 * u, L.w * 0.62 * u, L.w * 0.3 * u, 0, 0, U.TAU); ctx.fill();
    });
    // 主体（painter：z 序即层序）
    LAYERS.forEach((L, i) => (mode === "w" ? drawLayerWire : drawLayerSolid)(ctx, L, i, t));
    drawLabels(ctx, t);
    // 左侧文本列白纱罩（保持标题可读）
    const wash = ctx.createLinearGradient(0, 0, 0.62 * W, 0);
    wash.addColorStop(0, "rgba(255,255,255,.92)");
    wash.addColorStop(0.7, "rgba(255,255,255,.55)");
    wash.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = wash; ctx.fillRect(0, 0, 0.62 * W, H);
    drawCaption(ctx);
  }

  function loop(now) {
    if (!running) return;
    draw(now);
    raf = requestAnimationFrame(loop);
  }
  function start() {
    fit();
    if (REDUCE) { k = kTgt; labelAlpha = 1; requestAnimationFrame(() => { fit(); draw(performance.now()); }); return; }
    if (!running) { running = true; raf = requestAnimationFrame(loop); }
  }
  function stop() { running = false; cancelAnimationFrame(raf); }

  // 交互：点击空白装配/分解（排除按钮/chips/链接）
  host.addEventListener("click", e => {
    if (e.target.closest("button, a, .chip, .cover-mode")) return;
    kTgt = kTgt > 0.5 ? 0 : 1;
    if (REDUCE) { k = kTgt; labelAlpha = k ? 1 : 0; draw(performance.now()); }
  });
  host.addEventListener("mousemove", e => {
    const r = host.getBoundingClientRect();
    mouseYaw = ((e.clientX - r.left) / r.width - 0.5) * 0.22;
  });
  addEventListener("resize", () => { if (running || REDUCE) { fit(); if (REDUCE) draw(performance.now()); } });

  // 模式切换（B/C 两键，局部存储 + ?cover= 直达）
  function setMode(m) {
    mode = m;
    try { localStorage.setItem("lyo-cover-mode", m); } catch (e) {}
    document.querySelectorAll("#cover-mode button").forEach(b =>
      b.classList.toggle("on", b.dataset.mode === m));
    if (REDUCE) requestAnimationFrame(() => { fit(); draw(performance.now()); });
  }
  document.querySelectorAll("#cover-mode button").forEach(b =>
    b.addEventListener("click", () => setMode(b.dataset.mode)));
  setMode(mode);

  // 封面离屏即停
  new IntersectionObserver(es => es.forEach(en => {
    if (en.isIntersecting) start(); else stop();
  }), { threshold: 0.05 }).observe(host);

  window.COVER_LYO = { setMode };
})();
