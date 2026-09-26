// §2 分部与出海：分产品横条（收入×同比×毛利率三维）+ 分地区对照 + 分部表
(() => {
  const R = window.RPT; if (!R || !window.U) return;
  const { PAL, clamp } = U;
  const MONO = 'Menlo, Consolas, monospace';
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ── 分部表（DOM）──
  const tb = document.getElementById("seg-table");
  if (tb) {
    const row = (s, hl) => `<tr${hl ? ' class="hl"' : ""}>
      <td>${s.name}</td><td class="num">${s.rev.toFixed(2)}</td>
      <td class="num" style="color:${s.yoy < 0 ? "var(--neg)" : "var(--red)"}">${s.yoy > 0 ? "+" : ""}${s.yoy.toFixed(2)}%</td>
      <td class="num">${s.gm.toFixed(2)}%</td>
      <td class="num" style="color:${s.gmChg < 0 ? "var(--neg)" : "var(--red)"}">${s.gmChg > 0 ? "+" : ""}${s.gmChg.toFixed(2)}pct</td>
      <td><button class="klink" data-k="${s.k}" data-drill-keep>${s.k}</button></td></tr>`;
    tb.innerHTML = `<table class="dt"><thead><tr>
      <th>分部（2026H1）</th><th>收入·亿</th><th>YOY</th><th>毛利率</th><th>毛利率变动</th><th>锚</th></tr></thead>
      <tbody>${R.segments.map(s => row(s)).join("")}
      ${R.regions.map(s => row({ ...s, gmChg: s.gmChg }, s.name === "国际")).join("")}
      </tbody></table>
      <p class="muted" style="margin-top:8px">国际/国内为分地区口径；五个事业部为分产品口径，两套口径并列展示（中报全文）。</p>`;
  }

  // ── 分部图 ──
  const host = document.getElementById("seg-chart");
  if (!host) return;
  const body = U.frame(host, {
    title: "耗材没放量但毛利率跳了 18 个点；出海量升价降",
    sub: "横条=2026H1 分部收入（亿元） · 行右=毛利率与变动（pct） · 底部=分地区对照 · 点击行下钻",
    src: "2026 中报全文分产品表 / 分地区表（2026-08-28）· K8 / K9",
  });
  const canvas = document.createElement("canvas");
  canvas.style.width = "100%"; canvas.style.display = "block"; canvas.style.height = "430px";
  body.appendChild(canvas);
  const bc = U.bindCanvas(canvas);
  const W0 = 860, H0 = 430, mL = 150, mR = 200, mT = 30, rowH = 52;
  let W = 0, H = 0, sc = 1, prog = 0, played = false;
  const fits = () => { const r = bc.fit(); W = r.w; H = r.h; sc = Math.min(W / W0, H / H0); };
  const segs = R.segments, regs = R.regions;
  const maxRev = 16; // 分产品与分地区共用同一标尺（国内 14.95 也必须落在尺内）
  const hits = [];
  function barX(v) { return mL + (v / maxRev) * (W0 - mL - mR); }

  function render() {
    fits();
    const ctx = bc.ctx; ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.translate((W - W0 * sc) / 2, (H - H0 * sc) / 2); ctx.scale(sc, sc);
    hits.length = 0;
    // 刻度
    ctx.font = `9.5px ${MONO}`; ctx.fillStyle = PAL.inkLo; ctx.textAlign = "center";
    for (const gv of [0, 3, 6, 9, 12]) {
      ctx.strokeStyle = PAL.lineLo; ctx.beginPath();
      ctx.moveTo(barX(gv), mT - 6); ctx.lineTo(barX(gv), mT + segs.length * rowH + 8); ctx.stroke();
      ctx.fillText(String(gv), barX(gv), mT - 12);
    }
    segs.forEach((s, i) => {
      const y0 = mT + i * rowH, cy = y0 + rowH / 2 - 4;
      const p = REDUCE ? 1 : clamp(prog * 1.5 - i * 0.13, 0, 1);
      // 名称
      ctx.font = `12px ${'"et-book", Palatino, Georgia, serif'}`; ctx.textAlign = "right";
      ctx.fillStyle = PAL.ink; ctx.fillText(s.name, mL - 12, cy);
      // 收入条
      const bw = (barX(s.rev) - mL) * p;
      ctx.fillStyle = s.name.includes("生物工艺") ? PAL.red : "rgba(5,28,44,.78)";
      ctx.fillRect(mL, cy - 10, bw, 20);
      if (p > 0.5) {
        ctx.font = `700 12px ${MONO}`; ctx.textAlign = "left";
        ctx.strokeStyle = "rgba(255,255,255,.9)"; ctx.lineWidth = 4;
        ctx.strokeText(s.rev.toFixed(2), mL + bw + 8, cy);
        ctx.fillStyle = PAL.ink; ctx.fillText(s.rev.toFixed(2), mL + bw + 8, cy);
        ctx.font = `10px ${MONO}`;
        ctx.fillStyle = s.yoy < 0 ? PAL.neg : PAL.red;
        ctx.fillText(`${s.yoy > 0 ? "+" : ""}${s.yoy.toFixed(2)}%`, mL + bw + 52, cy);
      }
      // 毛利率（行右）
      if (p > 0.5) {
        ctx.font = `700 11.5px ${MONO}`; ctx.textAlign = "left"; ctx.fillStyle = PAL.inkMd;
        ctx.fillText(`GM ${s.gm.toFixed(1)}%`, W0 - mR + 16, cy - 7);
        ctx.font = `700 10.5px ${MONO}`;
        ctx.fillStyle = s.gmChg < 0 ? PAL.neg : PAL.red;
        ctx.fillText(`${s.gmChg > 0 ? "+" : ""}${s.gmChg.toFixed(2)}pct`, W0 - mR + 16, cy + 9);
      }
      hits.push({ x: mL, y: y0, w: W0 - mL, h: rowH - 8, s });
    });
    // 分地区对照（底部双条）
    const ry = mT + segs.length * rowH + 34;
    ctx.strokeStyle = PAL.line; ctx.beginPath(); ctx.moveTo(mL, ry - 16); ctx.lineTo(W0 - mR, ry - 16); ctx.stroke();
    ctx.font = `10px ${MONO}`; ctx.fillStyle = PAL.inkLo; ctx.textAlign = "left";
    ctx.fillText("分地区 · REV / SHARE / GM", mL, ry - 24);
    regs.forEach((g, i) => {
      const y0 = ry + i * 44;
      const p = REDUCE ? 1 : clamp(prog * 1.5 - (segs.length * 0.13 + i * 0.14), 0, 1);
      ctx.font = `12px ${'"et-book", Palatino, Georgia, serif'}`; ctx.textAlign = "right"; ctx.fillStyle = PAL.ink;
      ctx.fillText(`${g.name}（占比 ${g.share}%）`, mL - 12, y0 + 12);
      const bw = (barX(g.rev) - mL) * p;
      ctx.fillStyle = g.name === "国际" ? PAL.red : PAL.inkMd;
      ctx.fillRect(mL, y0, bw, 24);
      if (p > 0.5) {
        ctx.font = `700 12px ${MONO}`; ctx.textAlign = "left";
        ctx.strokeStyle = "rgba(255,255,255,.9)"; ctx.lineWidth = 4;
        const s1 = `${g.rev.toFixed(2)}  ${g.yoy > 0 ? "+" : ""}${g.yoy.toFixed(2)}%`;
        ctx.strokeText(s1, mL + bw + 8, y0 + 12); ctx.fillStyle = PAL.ink; ctx.fillText(s1, mL + bw + 8, y0 + 12);
        ctx.font = `10.5px ${MONO}`;
        ctx.fillStyle = g.gmChg < 0 ? PAL.neg : PAL.red;
        ctx.fillText(`GM ${g.gm.toFixed(1)}% ${g.gmChg > 0 ? "+" : ""}${g.gmChg.toFixed(2)}pct`, W0 - 104, y0 + 12);
      }
      hits.push({ x: mL, y: y0 - 4, w: W0 - mL, h: 32, s: g });
    });
    ctx.restore();
  }
  function play() {
    if (played) return; played = true;
    if (REDUCE) { prog = 1; render(); return; }
    const t0 = performance.now();
    (function tick(now) { prog = clamp((now - t0) / 1500, 0, 1); render(); if (prog < 1) requestAnimationFrame(tick); })(t0);
  }
  canvas.addEventListener("click", e => {
    const r = canvas.getBoundingClientRect();
    const lx = (e.clientX - r.left - (W - W0 * sc) / 2) / sc, ly = (e.clientY - r.top - (H - H0 * sc) / 2) / sc;
    const h = hits.find(hh => lx >= hh.x && lx <= hh.x + hh.w && ly >= hh.y && ly <= hh.y + hh.h);
    if (h && window.K) {
      const c = K.get(h.s.k);
      U.showDrill({ title: `${h.s.name} · 2026H1 · ${h.s.k}`,
        value: `收入 ${h.s.rev.toFixed(2)} 亿 · GM ${h.s.gm.toFixed(2)}%`,
        sub: `同比 ${h.s.yoy > 0 ? "+" : ""}${h.s.yoy.toFixed(2)}%；毛利率变动 ${h.s.gmChg > 0 ? "+" : ""}${h.s.gmChg.toFixed(2)}pct${c ? "。证伪检验：" + c.test : ""}`,
        source: c ? K.srcLine(c) : "", x: e.clientX, y: e.clientY });
    }
  });
  new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) play(); }), { threshold: 0.15 }).observe(canvas);
  addEventListener("resize", render);
  render();
})();
