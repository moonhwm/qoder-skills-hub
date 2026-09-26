// §4 估值锚：PE 双口径 + 可比对照（Wind 滞后口径以虚框标注，禁止直接当结论用）
(() => {
  const R = window.RPT; if (!R || !window.U) return;
  const { PAL, clamp } = U;
  const MONO = 'Menlo, Consolas, monospace';
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const host = document.getElementById("val-chart");
  if (!host) return;
  const V = R.valuation;
  const body = U.frame(host, {
    title: "同一市值，两种 PE：55.25 与 43.8，旁边是楚天的 15.92",
    sub: "柱=PE_TTM（倍） · 虚框=Wind 口径大概率未纳入 8-27 晚中报（滞后警示） · 柱下=市值（亿元） · 非估值结论 · 点击下钻",
    src: "iFinD/Wind 底表 + 自算推导（2026-08-28）· K11 / K12 · conf=Medium",
  });
  const canvas = document.createElement("canvas");
  canvas.style.width = "100%"; canvas.style.display = "block"; canvas.style.height = "340px";
  body.appendChild(canvas);
  const bc = U.bindCanvas(canvas);
  const W0 = 760, H0 = 340, mL = 50, mR = 24, mT = 46, mB = 76;
  let W = 0, H = 0, sc = 1, prog = 0, played = false;
  const fits = () => { const r = bc.fit(); W = r.w; H = r.h; sc = Math.min(W / W0, H / H0); };
  const bars = [
    { name: "东富龙 · Wind 口径", pe: V.peWind, mcap: V.mcap, style: "hollow", k: "K11",
      note: "PE_TTM 55.25 大概率未纳入 8-27 晚披露的中报，存在滞后；PB_LF 1.45 · PS_TTM 2.21" },
    { name: "东富龙 · 自算口径", pe: V.peSelf, mcap: V.mcap, style: "blue", k: "K12",
      note: `归母 TTM ≈ ${V.ttmSelf} 亿（${V.ttmFormula}）自算 PE ≈ 43.8 倍，推导值` },
    { name: `${V.peer.name} · Wind`, pe: V.peer.pe, mcap: V.peer.mcap, style: "ink", k: "K12",
      note: `${V.peer.code}：PE_TTM 15.92 · PB 1.18 · 2026H1 净利 1.56 亿 · Wind 单源` },
  ];
  const maxV = 60;
  const hits = [];
  function render() {
    fits();
    const ctx = bc.ctx; ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.translate((W - W0 * sc) / 2, (H - H0 * sc) / 2); ctx.scale(sc, sc);
    hits.length = 0;
    const iw = W0 - mL - mR, ih = H0 - mT - mB;
    const y = v => mT + ih - (v / maxV) * ih;
    ctx.font = `10px ${MONO}`; ctx.textBaseline = "middle";
    for (const gv of [0, 15, 30, 45, 60]) {
      ctx.strokeStyle = PAL.lineLo; ctx.beginPath(); ctx.moveTo(mL, y(gv)); ctx.lineTo(W0 - mR, y(gv)); ctx.stroke();
      ctx.fillStyle = PAL.inkLo; ctx.textAlign = "right"; ctx.fillText(String(gv), mL - 8, y(gv));
    }
    const gap = iw / bars.length, bw = Math.min(96, gap * 0.44);
    bars.forEach((b, i) => {
      const cx0 = mL + gap * i + gap / 2;
      const p = REDUCE ? 1 : clamp(prog * 1.5 - i * 0.15, 0, 1);
      const bh = ih * (b.pe / maxV) * p;
      if (b.style === "hollow") {
        ctx.strokeStyle = PAL.inkMd; ctx.lineWidth = 1.3; ctx.setLineDash([5, 4]);
        ctx.strokeRect(cx0 - bw / 2, y(b.pe * p), bw, bh); ctx.setLineDash([]);
        // 滞后警示
        if (p > 0.5) {
          ctx.font = `700 9.5px ${MONO}`; ctx.textAlign = "center"; ctx.fillStyle = PAL.neg;
          ctx.fillText("⚠ 滞后口径", cx0, y(b.pe) - 26);
        }
      } else {
        ctx.fillStyle = b.style === "blue" ? PAL.red : "rgba(5,28,44,.8)";
        ctx.fillRect(cx0 - bw / 2, y(b.pe * p), bw, bh);
      }
      if (p > 0.5) {
        ctx.font = `700 16px ${MONO}`; ctx.textAlign = "center";
        ctx.strokeStyle = "rgba(255,255,255,.9)"; ctx.lineWidth = 4;
        ctx.strokeText(b.pe.toFixed(2), cx0, y(b.pe) - 10);
        ctx.fillStyle = PAL.ink; ctx.fillText(b.pe.toFixed(2), cx0, y(b.pe) - 10);
        ctx.font = `9.5px ${MONO}`; ctx.fillStyle = PAL.inkLo;
        ctx.fillText(`市值 ${b.mcap} 亿`, cx0, H0 - mB + 38);
      }
      ctx.font = `11px ${MONO}`; ctx.textAlign = "center"; ctx.fillStyle = PAL.ink;
      ctx.fillText(b.name, cx0, H0 - mB + 21);
      hits.push({ x: cx0 - gap / 2, y: mT, w: gap, h: ih, b });
    });
    ctx.restore();
  }
  function play() {
    if (played) return; played = true;
    if (REDUCE) { prog = 1; render(); return; }
    const t0 = performance.now();
    (function tick(now) { prog = clamp((now - t0) / 1200, 0, 1); render(); if (prog < 1) requestAnimationFrame(tick); })(t0);
  }
  canvas.addEventListener("click", e => {
    const r = canvas.getBoundingClientRect();
    const lx = (e.clientX - r.left - (W - W0 * sc) / 2) / sc, ly = (e.clientY - r.top - (H - H0 * sc) / 2) / sc;
    const h = hits.find(hh => lx >= hh.x && lx <= hh.x + hh.w && ly >= hh.y && ly <= hh.y + hh.h);
    if (h && window.K) {
      const c = K.get(h.b.k);
      U.showDrill({ title: `${h.b.name} · ${h.b.k} · CONF=MEDIUM`,
        value: `PE ${h.b.pe.toFixed(2)} 倍 · 市值 ${h.b.mcap} 亿`,
        sub: h.b.note + (c ? "。证伪检验：" + c.test : ""),
        source: c ? K.srcLine(c) : "", x: e.clientX, y: e.clientY });
    }
  });
  new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) play(); }), { threshold: 0.2 }).observe(canvas);
  addEventListener("resize", render);
  render();
})();
