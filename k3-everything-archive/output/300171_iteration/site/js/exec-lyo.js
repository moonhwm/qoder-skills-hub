// §0 证据对象（CHARTS.md P17）：一台冻干机，六个硬数字挂在真正执行测量功能的部位
// 铭牌=营收 · 观察窗=归母 · 控制柜表盘=扣非 · 真空表=经营现金流 · 排污阀=减值 · 吊牌=合同负债
(() => {
  const host = document.getElementById("exec-lyo-chart");
  if (!host || !window.U || !window.RPT) return;
  const { PAL, clamp } = U;
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const MONO = 'Menlo, Consolas, monospace';
  const SERIF = '"et-book", Palatino, Georgia, serif';

  const body = U.frame(host, {
    title: "一台冻干机身上，挂着本期报告最硬的六个数字",
    sub: "EVIDENCE LYOPHILIZER · 铭牌=营收 · 观察窗=归母 · 表盘=扣非 · 真空表=现金流 · 排污阀=减值 · 吊牌=合同负债 · 全部可点击下钻",
    src: "公司中报原文与 iFinD/Wind 底表（2026-08-28 核查）· K2–K6",
  });

  const canvas = document.createElement("canvas");
  canvas.style.width = "100%"; canvas.style.display = "block";
  canvas.style.height = "560px";
  body.appendChild(canvas);
  const bc = U.bindCanvas(canvas);
  let W = 0, H = 0, sc = 1;
  const W0 = 880, H0 = 560;
  function fit() { const r = bc.fit(); W = r.w; H = r.h; sc = Math.min(W / W0, H / H0); }

  // 数字挂载点定义（逻辑坐标 880×560）
  const D = window.RPT.h1_2026, L = window.RPT.leading;
  const ITEMS = [
    { id: "plate", k: "K2", x: 250, y: 108, val: "25.35 亿", lab: "营业收入 · 2026H1", delta: "+4.37%", col: PAL.red,
      anchor: [330, 168], title: "铭牌 · 营业收入", basis: "中报摘要 2,534,573,184.09 元；与 Wind 25.3457 亿交叉一致" },
    { id: "door", k: "K3", x: 460, y: 306, val: "1.08 亿", lab: "归母净利润", delta: "+134.49%", col: PAL.red,
      title: "观察窗 · 归母净利润", basis: "中报摘要 107,678,132.77 元；EPS 0.1415 元" },
    { id: "gauge", k: "K3", x: 718, y: 160, val: "+270.73%", lab: "扣非归母 0.94 亿", delta: null, col: PAL.red,
      anchor: [700, 226], title: "控制柜表盘 · 扣非归母", basis: "中报摘要 94,443,548.36 元；低基数外推价值弱（top3 #2）" },
    { id: "vac", k: "K4", x: 176, y: 200, val: "0.91 亿", lab: "经营现金流净额", delta: "-67.03%", col: PAL.neg,
      anchor: [232, 268], title: "真空表 · 经营现金流", basis: "中报摘要 91,104,156.17 元；与利润 +134% 显著背离（S9 确认）" },
    { id: "drain", k: "K5", x: 176, y: 524, val: "0.72 亿", lab: "资产减值损失", delta: "占利润总额 47.81%", col: PAL.neg,
      anchor: [196, 462], title: "排污阀 · 减值侵蚀", basis: "中报全文非主营业务分析表 -72,433,460.68 元；2024FY 同项 1.51 亿，持续性侵蚀" },
    { id: "tag", k: "K6", x: 560, y: 524, val: "37.13 亿", lab: "合同负债 · 先行指标", delta: "+2.47%", col: PAL.redHi,
      anchor: [600, 452], title: "吊牌 · 合同负债", basis: "期末 3,712,857,819.00 vs 期初 3,623,204,442.73；期初值与 iFinD 双源一致" },
  ];
  const hits = [];

  function txt(ctx, s, x, y, font, col, align = "center", halo = true) {
    ctx.font = font; ctx.textAlign = align; ctx.textBaseline = "middle";
    if (halo) { ctx.strokeStyle = "rgba(255,255,255,.95)"; ctx.lineWidth = 4; ctx.lineJoin = "round"; ctx.strokeText(s, x, y); }
    ctx.fillStyle = col; ctx.fillText(s, x, y);
  }

  function drawMachine(ctx) {
    ctx.save();
    ctx.translate((W - W0 * sc) / 2, (H - H0 * sc) / 2); ctx.scale(sc, sc);
    // 地面线
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(60, 480); ctx.lineTo(830, 480); ctx.stroke();
    ctx.lineWidth = 1;

    // ── 冷阱（左侧圆筒 + 盘管）──
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(140, 300); ctx.lineTo(140, 452);
    ctx.moveTo(236, 300); ctx.lineTo(236, 452); ctx.stroke();
    ctx.beginPath(); ctx.ellipse(188, 300, 48, 16, 0, Math.PI, 0); ctx.stroke(); // 顶盖弧
    ctx.beginPath(); ctx.ellipse(188, 452, 48, 16, 0, 0, Math.PI); ctx.stroke(); // 底弧
    ctx.save(); ctx.beginPath(); ctx.rect(140, 284, 96, 184); ctx.clip();
    ctx.strokeStyle = PAL.inkMd; ctx.lineWidth = 0.9;
    ctx.beginPath(); // 盘管之字
    for (let s = 0; s <= 6; s++) {
      const yy = 316 + s * 21;
      s ? ctx.lineTo(s % 2 ? 226 : 150, yy) : ctx.moveTo(150, yy);
    }
    ctx.stroke(); ctx.restore();
    // 排污阀（底部小阀）
    ctx.strokeStyle = PAL.neg; ctx.lineWidth = 1.3;
    ctx.beginPath(); ctx.moveTo(188, 468); ctx.lineTo(188, 480); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(178, 474); ctx.lineTo(198, 474); ctx.stroke();

    // ── 冻干腔体（主箱体 + 搁板 + 圆门）──
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.8;
    roundRect(ctx, 320, 168, 300, 290, 10); ctx.stroke();
    // 支腿
    ctx.lineWidth = 1.4;
    for (const lx of [356, 584]) {
      ctx.beginPath(); ctx.moveTo(lx, 458); ctx.lineTo(lx, 480); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(lx - 8, 480); ctx.lineTo(lx + 8, 480); ctx.stroke();
    }
    // 搁板四层
    ctx.strokeStyle = PAL.inkMd; ctx.lineWidth = 1;
    for (const sy of [212, 252, 292, 332]) {
      ctx.beginPath(); ctx.moveTo(334, sy); ctx.lineTo(606, sy); ctx.stroke();
      ctx.fillStyle = "rgba(125,155,255,.10)";
      ctx.fillRect(334, sy, 272, 5);
    }
    // 圆形腔门 + 观察窗
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 2.2;
    ctx.beginPath(); ctx.arc(460, 306, 74, 0, U.TAU); ctx.stroke();
    ctx.fillStyle = "rgba(125,155,255,.10)";
    ctx.beginPath(); ctx.arc(460, 306, 44, 0, U.TAU); ctx.fill();
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.arc(460, 306, 44, 0, U.TAU); ctx.stroke();
    // 门把手
    ctx.beginPath(); ctx.moveTo(460, 232); ctx.lineTo(460, 246); ctx.stroke();

    // ── 控制柜（右侧）──
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.6;
    roundRect(ctx, 640, 200, 120, 176, 6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(640, 262); ctx.lineTo(760, 262); ctx.stroke();
    // 表盘两只
    for (const gx of [672, 728]) {
      ctx.beginPath(); ctx.arc(gx, 232, 16, 0, U.TAU); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(gx, 232); ctx.lineTo(gx + 8, 222); ctx.stroke();
    }
    // 按钮一排
    ctx.fillStyle = PAL.inkMd;
    for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(660 + i * 26, 290, 4, 0, U.TAU); ctx.fill(); }
    ctx.strokeStyle = PAL.inkMd; ctx.lineWidth = 0.9;
    ctx.strokeRect(656, 316, 88, 44); // 屏幕
    // 柜腿
    ctx.beginPath(); ctx.moveTo(656, 376); ctx.lineTo(656, 480); ctx.moveTo(744, 376); ctx.lineTo(744, 480); ctx.stroke();

    // ── 真空泵组（右下，两台小泵 + 虚线管路）──
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.3;
    for (const px of [700, 780]) {
      ctx.beginPath(); ctx.ellipse(px, 458, 26, 14, 0, 0, U.TAU); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(px, 446, 26, 14, 0, Math.PI, 0); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(px - 26, 446); ctx.lineTo(px - 26, 458);
      ctx.moveTo(px + 26, 446); ctx.lineTo(px + 26, 458); ctx.stroke();
    }
    // 管路：泵组 → 冷阱 / 腔体（虚线）
    ctx.setLineDash([4, 4]); ctx.strokeStyle = PAL.inkMd; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(700, 432); ctx.lineTo(700, 400); ctx.lineTo(620, 400); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(236, 380); ctx.lineTo(300, 380); ctx.lineTo(320, 380); ctx.stroke();
    // 真空表（管路中部小表盘）
    ctx.setLineDash([]);
    ctx.strokeStyle = PAL.neg; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(268, 380, 12, 0, U.TAU); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(268, 380); ctx.lineTo(276, 372); ctx.stroke();
    ctx.restore();
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  // 每个挂载物：吊牌/标签 + 引线，随入场动画逐个挂上
  function drawItems(ctx, prog) {
    ctx.save();
    ctx.translate((W - W0 * sc) / 2, (H - H0 * sc) / 2); ctx.scale(sc, sc);
    hits.length = 0;
    ITEMS.forEach((it, i) => {
      const p = REDUCE ? 1 : clamp(prog * 1.6 - i * 0.13, 0, 1);
      if (p <= 0) return;
      const dy = (1 - p) * -14;
      ctx.globalAlpha = p;
      if (it.id === "door") {
        // 观察窗内大数字
        txt(ctx, it.val, 460, 296, `700 26px ${MONO}`, it.col);
        txt(ctx, it.delta, 460, 324, `700 13px ${MONO}`, it.col);
        txt(ctx, it.lab, 460, 396, `11px ${MONO}`, PAL.inkMd);
        hits.push({ x: 416, y: 262, w: 88, h: 88, it });
      } else if (it.id === "vac" || it.id === "drain") {
        // 红色语义标签（左列）
        const bw = 168, bh = 46, bx = it.x - bw / 2, by = it.y - bh / 2 + dy;
        ctx.strokeStyle = it.col; ctx.lineWidth = 1.4;
        ctx.strokeRect(bx, by, bw, bh);
        ctx.fillStyle = "rgba(255,255,255,.92)"; ctx.fillRect(bx, by, bw, bh);
        txt(ctx, it.val + "  " + (it.delta || ""), it.x, by + 15, `700 12.5px ${MONO}`, it.col, "center", false);
        txt(ctx, it.lab, it.x, by + 33, `10px ${MONO}`, PAL.inkMd, "center", false);
        // 引线到锚点
        ctx.strokeStyle = hexA(it.col, 0.65); ctx.setLineDash([3, 3]); ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(it.x + bw / 2, it.y + dy); ctx.lineTo(it.anchor[0], it.anchor[1]); ctx.stroke();
        ctx.setLineDash([]);
        ctx.beginPath(); ctx.arc(it.anchor[0], it.anchor[1], 3, 0, U.TAU);
        ctx.strokeStyle = it.col; ctx.stroke(); ctx.fillStyle = "#fff"; ctx.fill();
        hits.push({ x: bx, y: by, w: bw, h: bh, it });
      } else {
        // 吊牌（plate/gauge/tag）：挂牌 + 短线
        const bw = it.id === "tag" ? 196 : 176, bh = 46;
        const bx = it.x - bw / 2, by = it.y - bh / 2 + dy;
        ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.2;
        ctx.fillStyle = "#fff";
        ctx.strokeRect(bx, by, bw, bh); ctx.fillRect(bx, by, bw, bh);
        ctx.fillStyle = it.col; ctx.fillRect(bx, by, 3, bh);
        txt(ctx, it.val, bx + 12, by + 15, `700 14px ${MONO}`, it.col, "left", false);
        if (it.delta) txt(ctx, it.delta, bx + bw - 10, by + 15, `700 11px ${MONO}`, it.delta.startsWith("-") ? PAL.neg : PAL.inkMd, "right", false);
        txt(ctx, it.lab, bx + 12, by + 33, `9.5px ${MONO}`, PAL.inkMd, "left", false);
        if (it.anchor) {
          ctx.strokeStyle = "rgba(5,28,44,.45)"; ctx.setLineDash([3, 3]); ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(it.x, by + bh); ctx.lineTo(it.anchor[0], it.anchor[1]); ctx.stroke();
          ctx.setLineDash([]);
          ctx.beginPath(); ctx.arc(it.anchor[0], it.anchor[1], 3, 0, U.TAU);
          ctx.strokeStyle = it.col; ctx.stroke(); ctx.fillStyle = "#fff"; ctx.fill();
        }
        hits.push({ x: bx, y: by, w: bw, h: bh, it });
      }
      ctx.globalAlpha = 1;
    });
    ctx.restore();
  }

  function hexA(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }

  let prog = REDUCE ? 1 : 0, played = false, raf = 0;
  function render() {
    fit();
    const ctx = bc.ctx;
    ctx.clearRect(0, 0, W, H);
    drawMachine(ctx);
    drawItems(ctx, prog);
  }
  function play() {
    if (played) return; played = true;
    if (REDUCE) { prog = 1; render(); return; }
    const t0 = performance.now();
    (function tick(now) {
      prog = clamp((now - t0) / 1500, 0, 1);
      render();
      if (prog < 1) raf = requestAnimationFrame(tick);
    })(t0);
  }

  // 点击下钻 + hover 提示
  canvas.addEventListener("click", e => {
    const r = canvas.getBoundingClientRect();
    const lx = (e.clientX - r.left - (W - W0 * sc) / 2) / sc;
    const ly = (e.clientY - r.top - (H - H0 * sc) / 2) / sc;
    const h = hits.find(hh => lx >= hh.x && lx <= hh.x + hh.w && ly >= hh.y && ly <= hh.y + hh.h);
    if (h && window.K) {
      const c = K.get(h.it.k);
      U.showDrill({ title: `${h.it.title} · ${h.it.k} · CONF=${c ? c.conf.toUpperCase() : ""}`,
        value: h.it.val + (h.it.delta ? ` ${h.it.delta}` : ""),
        sub: h.it.basis + (c ? `。证伪检验：${c.test}` : ""),
        source: c ? K.srcLine(c) : "", x: e.clientX, y: e.clientY });
    }
  });
  canvas.addEventListener("mousemove", e => {
    const r = canvas.getBoundingClientRect();
    const lx = (e.clientX - r.left - (W - W0 * sc) / 2) / sc;
    const ly = (e.clientY - r.top - (H - H0 * sc) / 2) / sc;
    const h = hits.find(hh => lx >= hh.x && lx <= hh.x + hh.w && ly >= hh.y && ly <= hh.y + hh.h);
    canvas.style.cursor = h ? "pointer" : "default";
    if (h) U.showTip(`${h.it.title} · 点击下钻 ${h.it.k}`, e.clientX, e.clientY); else U.hideTip();
  });
  canvas.addEventListener("mouseleave", () => U.hideTip());

  new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) play(); }), { threshold: 0.18 }).observe(canvas);
  addEventListener("resize", () => render());
  render();
})();
