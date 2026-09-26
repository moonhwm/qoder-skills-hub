// 常驻右栏仪表（CHARTS.md P14 简版）：窗口徽章 + 期段条 + 营收/归母迷你走势 + 四项读数
(() => {
  const rail = document.getElementById("dash-rail");
  const canvas = document.getElementById("dash-canvas");
  if (!rail || !canvas || !window.U || !window.RPT) return;
  const { PAL, clamp } = U;
  const MONO = 'Menlo, Consolas, monospace';
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const R = window.RPT;

  const WINS = [
    { id: "exec",   no: "§0", name: "执行摘要" },
    { id: "iter",   no: "§1", name: "自述链" },
    { id: "fund",   no: "§2", name: "基本面" },
    { id: "bear",   no: "§3", name: "空头检验台" },
    { id: "val",    no: "§4", name: "估值锚" },
    { id: "claims", no: "§5", name: "证明链" },
    { id: "sem",    no: "§6", name: "语义链" },
    { id: "hash",   no: "§7", name: "哈希链" },
  ];
  let cur = "exec", shown = false, t0 = performance.now(), raf = 0, running = false;
  const STATS = [
    { k: "K2", lab: "营业收入 · 2026H1", val: "25.35 亿", d: "+4.37%", col: PAL.red },
    { k: "K3", lab: "归母净利润", val: "1.08 亿", d: "+134.49%", col: PAL.red },
    { k: "K4", lab: "经营现金流", val: "0.91 亿", d: "-67.03%", col: PAL.neg },
    { k: "K6", lab: "合同负债", val: "37.13 亿", d: "+2.47%", col: PAL.redHi },
  ];
  const bc = U.bindCanvas(canvas);
  let W = 0, H = 0;
  const hits = [];

  function draw(now) {
    const r = bc.fit(); W = r.w; H = r.h;
    const ctx = bc.ctx;
    ctx.clearRect(0, 0, W, H);
    hits.length = 0;
    if (W < 100) return;
    const t = (now - t0) / 1000;
    const mL = 34, mR = 34, iw = W - mL - mR;
    let y = 92;
    const w = WINS.find(x => x.id === cur) || WINS[0];
    // 窗口徽章 + 标题
    ctx.font = `700 10px ${MONO}`; ctx.textAlign = "left"; ctx.textBaseline = "middle";
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.5;
    ctx.strokeRect(mL, y - 11, 40, 22);
    ctx.fillStyle = PAL.ink; ctx.fillText(w.no, mL + 9, y + 1);
    ctx.font = `700 21px ${'"et-book", Palatino, Georgia, serif'}`;
    ctx.fillText(w.name, mL + 52, y + 2);
    ctx.font = `9px ${MONO}`; ctx.fillStyle = PAL.inkLo;
    ctx.fillText("TOFFLON 300171.SZ · 数据截至 2026-08-28", mL + 52, y + 22);
    y += 52;
    // 期段条（8 段，当前段蓝）
    const segW = iw / WINS.length;
    WINS.forEach((s, i) => {
      ctx.fillStyle = s.id === cur ? PAL.red : PAL.line;
      ctx.fillRect(mL + i * segW, y, segW - 4, s.id === cur ? 5 : 2.5);
      if (s.id === cur && !REDUCE) {
        ctx.globalAlpha = 0.35 + 0.25 * Math.sin(t * 3);
        ctx.fillStyle = PAL.red; ctx.fillRect(mL + i * segW, y - 3, segW - 4, 2);
        ctx.globalAlpha = 1;
      }
    });
    y += 26;
    // 迷你走势：营收（柱）+ 归母（线），5 期
    const data = R.income, ch = 110;
    const gx0 = mL, gw = iw, gy = y + 20;
    const revMax = 60, npMax = 6.5;
    ctx.font = `9px ${MONO}`; ctx.fillStyle = PAL.inkLo;
    ctx.fillText("REVENUE · 柱 = 亿", gx0, y);
    ctx.textAlign = "right"; ctx.fillText("归母 · 线", gx0 + gw, y); ctx.textAlign = "left";
    const step = gw / data.length;
    data.forEach((d, i) => {
      const bx = gx0 + step * i + step * 0.22, bw = step * 0.56;
      const bh = (d.revenue / revMax) * (ch - 24);
      ctx.fillStyle = d.kind === "h1" ? PAL.blueSoft : "rgba(34,81,255,.8)";
      ctx.fillRect(bx, gy + ch - bh, bw, bh);
      ctx.fillStyle = PAL.inkLo; ctx.textAlign = "center";
      ctx.fillText(d.period.replace("20", ""), gx0 + step * i + step / 2, gy + ch + 12);
      hits.push({ x: gx0 + step * i, y: gy, w: step, h: ch, d });
    });
    ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.6; ctx.beginPath();
    data.forEach((d, i) => {
      const px = gx0 + step * i + step / 2, py = gy + ch - (d.np / npMax) * (ch - 24);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    });
    ctx.stroke();
    data.forEach((d, i) => {
      const px = gx0 + step * i + step / 2, py = gy + ch - (d.np / npMax) * (ch - 24);
      ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(px, py, 3, 0, U.TAU); ctx.fill();
      ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.2; ctx.stroke();
    });
    // 末端脉冲
    if (!REDUCE) {
      const px = gx0 + gw - step / 2, py = gy + ch - (data[data.length - 1].np / npMax) * (ch - 24);
      ctx.globalAlpha = 0.5 + 0.4 * Math.sin(t * 3);
      ctx.strokeStyle = PAL.red; ctx.beginPath(); ctx.arc(px, py, 7, 0, U.TAU); ctx.stroke();
      ctx.globalAlpha = 1;
    }
    y += ch + 52;
    // 四项读数
    STATS.forEach(s => {
      ctx.strokeStyle = PAL.lineLo; ctx.beginPath(); ctx.moveTo(mL, y); ctx.lineTo(W - mR, y); ctx.stroke();
      ctx.font = `9.5px ${MONO}`; ctx.fillStyle = PAL.inkLo; ctx.fillText(s.lab, mL, y + 14);
      ctx.font = `700 19px ${MONO}`; ctx.fillStyle = s.col; ctx.fillText(s.val, mL, y + 38);
      ctx.font = `700 11px ${MONO}`;
      ctx.fillStyle = s.d.startsWith("-") ? PAL.neg : PAL.inkMd;
      ctx.textAlign = "right"; ctx.fillText(s.d, W - mR, y + 38); ctx.textAlign = "left";
      hits.push({ x: mL, y, w: iw, h: 56, stat: s });
      y += 56;
    });
    ctx.strokeStyle = PAL.lineLo; ctx.beginPath(); ctx.moveTo(mL, y); ctx.lineTo(W - mR, y); ctx.stroke();
    y += 22;
    ctx.font = `9px ${MONO}`; ctx.fillStyle = PAL.inkLo;
    ctx.fillText("点击读数下钻 K 锚 · L1 原型级", mL, y);
  }

  function loop(now) { if (!running) return; draw(now); raf = requestAnimationFrame(loop); }
  function start() { draw(performance.now()); if (!REDUCE && !running) { running = true; raf = requestAnimationFrame(loop); } }
  function stop() { running = false; cancelAnimationFrame(raf); }

  // 滚动联动：窗口切换 + 封面后显示
  const secIO = new IntersectionObserver(es => es.forEach(en => {
    if (en.isIntersecting) { cur = en.target.dataset.win; if (REDUCE) draw(performance.now()); }
  }), { rootMargin: "-38% 0px -52% 0px", threshold: 0 });
  document.querySelectorAll("[data-win]").forEach(s => secIO.observe(s));
  new IntersectionObserver(es => es.forEach(en => {
    const past = !en.isIntersecting && en.boundingClientRect.bottom < 0;
    if (past && !shown) { shown = true; rail.classList.add("on"); start(); }
    else if (!past && shown && en.isIntersecting) { shown = false; rail.classList.remove("on"); stop(); }
  }), { threshold: 0.12 }).observe(document.getElementById("cover"));
  addEventListener("resize", () => { if (shown) draw(performance.now()); });

  canvas.addEventListener("click", e => {
    const r = canvas.getBoundingClientRect();
    const lx = e.clientX - r.left, ly = e.clientY - r.top;
    const h = hits.find(hh => lx >= hh.x && lx <= hh.x + hh.w && ly >= hh.y && ly <= hh.y + hh.h);
    if (!h || !window.K) return;
    if (h.stat) K.drill(h.stat.k, e.clientX, e.clientY);
    else if (h.d) K.drill(h.d.k, e.clientX, e.clientY);
  });
})();
