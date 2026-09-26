// §2 基本面：①营收/归母趋势（柱+点线，FY/H1 混合口径已标注）②先行指标（合同负债/存货/应收）
(() => {
  const R = window.RPT; if (!R || !window.U) return;
  const { PAL, clamp } = U;
  const MONO = 'Menlo, Consolas, monospace';
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ── 图①：营收柱 + 归母点线 ──
  const host = document.getElementById("fund-chart");
  if (host) {
    const body = U.frame(host, {
      title: "收入横盘三年，利润从 2024 谷底爬回",
      sub: "蓝柱=营业收入（亿元·左轴） · 墨线=归母净利润（亿元·右轴） · ⚠ FY 与 H1 为不同口径，并列仅作节奏对照，不可相除 · 点击下钻",
      src: "iFinD 利润表底表 + 2026 中报摘要（2026-08-28）· K10 / K2 / K3",
    });
    const canvas = document.createElement("canvas");
    canvas.style.width = "100%"; canvas.style.display = "block"; canvas.style.height = "380px";
    body.appendChild(canvas);
    const bc = U.bindCanvas(canvas);
    const W0 = 860, H0 = 380, mL = 56, mR = 56, mT = 34, mB = 56;
    let W = 0, H = 0, sc = 1, prog = 0, played = false;
    const fits = () => { const r = bc.fit(); W = r.w; H = r.h; sc = Math.min(W / W0, H / H0); };
    const data = R.income;
    const revMax = 60, npMax = 6.5;
    const hits = [];
    const fmt2 = v => v.toFixed(2);

    function render() {
      fits();
      const ctx = bc.ctx; ctx.clearRect(0, 0, W, H);
      ctx.save();
      ctx.translate((W - W0 * sc) / 2, (H - H0 * sc) / 2); ctx.scale(sc, sc);
      hits.length = 0;
      const iw = W0 - mL - mR, ih = H0 - mT - mB;
      const yR = v => mT + ih - (v / revMax) * ih;
      const yN = v => mT + ih - (v / npMax) * ih;
      const gap = iw / data.length;
      // 双轴网格
      ctx.font = `10px ${MONO}`; ctx.textBaseline = "middle";
      for (const gv of [0, 20, 40, 60]) {
        ctx.strokeStyle = PAL.lineLo; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(mL, yR(gv)); ctx.lineTo(W0 - mR, yR(gv)); ctx.stroke();
        ctx.fillStyle = PAL.inkLo; ctx.textAlign = "right"; ctx.fillText(String(gv), mL - 8, yR(gv));
      }
      for (const gv of [0, 2, 4, 6]) {
        ctx.fillStyle = PAL.inkMd; ctx.textAlign = "left"; ctx.fillText(gv.toFixed(0), W0 - mR + 8, yN(gv));
      }
      ctx.fillStyle = PAL.inkLo; ctx.textAlign = "right"; ctx.font = `9px ${MONO}`;
      ctx.fillText("收入·亿", mL - 8, mT - 12);
      ctx.textAlign = "left"; ctx.fillText("归母·亿", W0 - mR + 8, mT - 12);
      // 柱
      data.forEach((d, i) => {
        const cx0 = mL + gap * i + gap / 2;
        const p = REDUCE ? 1 : clamp(prog * 1.5 - i * 0.12, 0, 1);
        const bw = Math.min(64, gap * 0.5);
        const hgt = ih * (d.revenue / revMax) * p;
        ctx.fillStyle = d.kind === "h1" ? PAL.blueSoft : PAL.red;
        ctx.globalAlpha = d.kind === "h1" ? 0.85 : 0.92;
        ctx.fillRect(cx0 - bw / 2, yR(d.revenue * p), bw, hgt);
        ctx.globalAlpha = 1;
        if (p > 0.6) {
          ctx.font = `700 13px ${MONO}`; ctx.textAlign = "center"; ctx.fillStyle = PAL.ink;
          ctx.strokeStyle = "rgba(255,255,255,.9)"; ctx.lineWidth = 4;
          ctx.strokeText(fmt2(d.revenue), cx0, yR(d.revenue) - 10);
          ctx.fillText(fmt2(d.revenue), cx0, yR(d.revenue) - 10);
          if (d.yoyRev != null) {
            ctx.font = `10px ${MONO}`; ctx.fillStyle = PAL.red;
            ctx.fillText(`+${d.yoyRev}%`, cx0, yR(d.revenue) - 26);
          }
        }
        ctx.font = `11px ${MONO}`; ctx.textAlign = "center"; ctx.fillStyle = PAL.ink;
        ctx.fillText(d.period, cx0, H0 - mB + 20);
        ctx.font = `9px ${MONO}`; ctx.fillStyle = PAL.inkLo;
        ctx.fillText(d.kind === "fy" ? "全年" : "半年", cx0, H0 - mB + 35);
        hits.push({ x: cx0 - gap / 2, y: mT, w: gap, h: ih, d });
      });
      // 归母点线（墨）
      ctx.strokeStyle = PAL.ink; ctx.lineWidth = 2;
      ctx.beginPath();
      data.forEach((d, i) => {
        const cx0 = mL + gap * i + gap / 2;
        const yy = yN(d.np * (REDUCE ? 1 : clamp(prog * 1.5 - i * 0.12, 0, 1)));
        i ? ctx.lineTo(cx0, yy) : ctx.moveTo(cx0, yy);
      });
      ctx.stroke();
      data.forEach((d, i) => {
        const cx0 = mL + gap * i + gap / 2;
        const p = REDUCE ? 1 : clamp(prog * 1.5 - i * 0.12, 0, 1);
        const yy = yN(d.np * p);
        ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(cx0, yy, 4.5, 0, U.TAU); ctx.fill();
        ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.6; ctx.stroke();
        if (p > 0.6) {
          ctx.font = `700 11.5px ${MONO}`;
          ctx.strokeStyle = "rgba(255,255,255,.95)"; ctx.lineWidth = 4;
          if (i === 0) { // 2023FY：点贴近柱顶标签，改为右侧放置避免碰撞
            ctx.textAlign = "left";
            ctx.strokeText(fmt2(d.np), cx0 + 10, yy); ctx.fillStyle = PAL.ink; ctx.fillText(fmt2(d.np), cx0 + 10, yy);
          } else {
            ctx.textAlign = "center";
            const ly = yy + 18;
            ctx.strokeText(fmt2(d.np), cx0, ly); ctx.fillStyle = PAL.ink; ctx.fillText(fmt2(d.np), cx0, ly);
            if (d.yoyNp != null) {
              ctx.font = `10px ${MONO}`; ctx.fillStyle = PAL.red;
              ctx.strokeText(`+${d.yoyNp}%`, cx0, ly + 14); ctx.fillText(`+${d.yoyNp}%`, cx0, ly + 14);
            }
          }
        }
      });
      ctx.restore();
    }
    function play() {
      if (played) return; played = true;
      if (REDUCE) { prog = 1; render(); return; }
      const t0 = performance.now();
      (function tick(now) { prog = clamp((now - t0) / 1400, 0, 1); render(); if (prog < 1) requestAnimationFrame(tick); })(t0);
    }
    canvas.addEventListener("click", e => {
      const r = canvas.getBoundingClientRect();
      const lx = (e.clientX - r.left - (W - W0 * sc) / 2) / sc, ly = (e.clientY - r.top - (H - H0 * sc) / 2) / sc;
      const h = hits.find(hh => lx >= hh.x && lx <= hh.x + hh.w && ly >= hh.y && ly <= hh.y + hh.h);
      if (h && window.K) {
        const c = K.get(h.d.k);
        U.showDrill({ title: `${h.d.period} · ${h.d.kind === "fy" ? "全年" : "半年"} · ${h.d.k}`,
          value: `营收 ${fmt2(h.d.revenue)} 亿 · 归母 ${fmt2(h.d.np)} 亿`,
          sub: `EPS ${h.d.eps} 元。${h.d.note}${c ? "。证伪检验：" + c.test : ""}`,
          source: c ? K.srcLine(c) : "", x: e.clientX, y: e.clientY });
      }
    });
    new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) play(); }), { threshold: 0.2 }).observe(canvas);
    addEventListener("resize", render);
    render();
  }

  // ── 图②：先行指标（合同负债期初/期末成对 + 存货/应收期末与环比）──
  const host2 = document.getElementById("lead-chart");
  if (host2) {
    const body = U.frame(host2, {
      title: "合同负债 +2.47%：订单企稳的弱支撑，触发线未触发",
      sub: "合同负债=期初/期末成对柱（亿元） · 存货与应收为期末值+环比标签 · 预注册触发线：连续 2 季环比降 >10% → 未触发 · 点击下钻",
      src: "2026 中报全文合并资产负债表（2026-08-28）· K6 / K7",
    });
    const canvas = document.createElement("canvas");
    canvas.style.width = "100%"; canvas.style.display = "block"; canvas.style.height = "300px";
    body.appendChild(canvas);
    const bc = U.bindCanvas(canvas);
    const W0 = 760, H0 = 300, mL = 50, mR = 20, mT = 44, mB = 54;
    let W = 0, H = 0, sc = 1, prog = 0, played = false;
    const fits = () => { const r = bc.fit(); W = r.w; H = r.h; sc = Math.min(W / W0, H / H0); };
    const L2 = R.leading;
    const groups = [
      { name: "合同负债", vals: [{ v: L2.contractLiabBegin, lab: "期初" }, { v: L2.contractLiabEnd, lab: "期末" }],
        chg: "+2.47%", chgPos: true, k: "K6",
        basis: "期末 3,712,857,819.00 vs 期初 3,623,204,442.73；期初值与 iFinD 双源一致" },
      { name: "存货", vals: [{ v: L2.inventory, lab: "期末" }], chg: "+3.9% vs 期初", chgPos: true, k: "K6",
        basis: "存货 33.22 亿，较期初 +3.9%（中报全文合并资产负债表）" },
      { name: "应收账款", vals: [{ v: L2.ar, lab: "期末" }], chg: "+0.3% vs 期初", chgPos: true, k: "K7",
        basis: "应收 1,591,477,964.83 元，增速低于收入增速 +4.37%；S2 本期未获支持" },
    ];
    const maxV = 40;
    const hits2 = [];
    function render() {
      fits();
      const ctx = bc.ctx; ctx.clearRect(0, 0, W, H);
      ctx.save();
      ctx.translate((W - W0 * sc) / 2, (H - H0 * sc) / 2); ctx.scale(sc, sc);
      hits2.length = 0;
      const iw = W0 - mL - mR, ih = H0 - mT - mB;
      const y = v => mT + ih - (v / maxV) * ih;
      ctx.font = `10px ${MONO}`;
      for (const gv of [0, 10, 20, 30, 40]) {
        ctx.strokeStyle = PAL.lineLo; ctx.beginPath(); ctx.moveTo(mL, y(gv)); ctx.lineTo(W0 - mR, y(gv)); ctx.stroke();
        ctx.fillStyle = PAL.inkLo; ctx.textAlign = "right"; ctx.textBaseline = "middle";
        ctx.fillText(String(gv), mL - 8, y(gv));
      }
      const gap = iw / groups.length;
      groups.forEach((g, i) => {
        const gx = mL + gap * i;
        const bw = 52;
        const n = g.vals.length;
        g.vals.forEach((v, j) => {
          const p = REDUCE ? 1 : clamp(prog * 1.5 - (i * 0.16 + j * 0.08), 0, 1);
          const bx = gx + gap / 2 - (n * bw + (n - 1) * 10) / 2 + j * (bw + 10);
          const solid = j === n - 1;
          ctx.fillStyle = solid ? PAL.red : "rgba(5,28,44,.75)";
          if (!solid) { ctx.fillStyle = "transparent"; ctx.strokeStyle = PAL.ink; ctx.lineWidth = 1.2; }
          const bh = ih * (v.v / maxV) * p;
          if (solid) ctx.fillRect(bx, y(v.v * p), bw, bh);
          else ctx.strokeRect(bx, y(v.v * p), bw, bh);
          if (p > 0.6) {
            ctx.font = `700 13px ${MONO}`; ctx.textAlign = "center";
            ctx.strokeStyle = "rgba(255,255,255,.9)"; ctx.lineWidth = 4;
            ctx.strokeText(v.v.toFixed(2), bx + bw / 2, y(v.v) - 10);
            ctx.fillStyle = PAL.ink; ctx.fillText(v.v.toFixed(2), bx + bw / 2, y(v.v) - 10);
            ctx.font = `9px ${MONO}`; ctx.fillStyle = PAL.inkLo;
            ctx.fillText(v.lab, bx + bw / 2, H0 - mB + 34);
          }
          hits2.push({ x: bx, y: mT, w: bw, h: ih, g, v });
        });
        ctx.font = `700 11.5px ${MONO}`; ctx.textAlign = "center"; ctx.fillStyle = PAL.ink;
        ctx.fillText(g.name, gx + gap / 2, H0 - mB + 19);
        ctx.font = `700 10px ${MONO}`; ctx.fillStyle = g.chg.startsWith("-") ? PAL.neg : PAL.red;
        ctx.fillText(g.chg, gx + gap / 2, mT - 12);
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
      const h = hits2.find(hh => lx >= hh.x && lx <= hh.x + hh.w && ly >= hh.y && ly <= hh.y + hh.h);
      if (h && window.K) {
        const c = K.get(h.g.k);
        U.showDrill({ title: `${h.g.name} · ${h.v.lab} · ${h.g.k}`,
          value: `${h.v.v.toFixed(2)} 亿 · ${h.g.chg}`,
          sub: h.g.basis + (c ? "。证伪检验：" + c.test : ""),
          source: c ? K.srcLine(c) : "", x: e.clientX, y: e.clientY });
      }
    });
    new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) play(); }), { threshold: 0.2 }).observe(canvas);
    addEventListener("resize", render);
    render();
  }
})();
