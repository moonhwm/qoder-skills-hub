// §6 语义链：对冲密度仪表（0.35‰ vs 阈值 15‰）+ 三类发现计数 + 发现清单
(() => {
  const R = window.RPT; if (!R || !window.U) return;
  const { PAL, clamp } = U;
  const MONO = 'Menlo, Consolas, monospace';
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const S = R.semantic;

  // ── 发现清单 DOM ──
  const list = document.getElementById("sem-list");
  if (list) {
    const T = { undefined_term: "未定义术语", ambiguous_term: "歧义", dangling_reference: "指称悬空" };
    list.innerHTML = S.findings.map(f => `
      <li><span class="sem-tag">${T[f.type] || f.type}</span>
        <span class="sem-text">「${f.text}」</span>
        <span class="sem-detail">${f.detail} · 句 #${f.si}</span></li>`).join("");
  }

  // ── 仪表图 ──
  const host = document.getElementById("sem-chart");
  if (!host) return;
  const body = U.frame(host, {
    title: "对冲密度 0.35‰，距 15‰ 阈值还很远；14 条启发式候选待人工裁决",
    sub: "左=对冲密度（‰，阈值 15） · 右=三类发现计数 · 全部候选 conf=方法论档 · 点击下钻",
    src: "data/semantic_audit.json（2026-08-28 生成）· 方法论类比",
  });
  const canvas = document.createElement("canvas");
  canvas.style.width = "100%"; canvas.style.display = "block"; canvas.style.height = "260px";
  body.appendChild(canvas);
  const bc = U.bindCanvas(canvas);
  const W0 = 760, H0 = 260, mL = 70, mR = 40;
  let W = 0, H = 0, sc = 1, prog = 0, played = false;
  const fits = () => { const r = bc.fit(); W = r.w; H = r.h; sc = Math.min(W / W0, H / H0); };
  const hits = [];
  const cats = [
    { name: "未定义术语", n: S.stats.counts.undefinedTerm, eg: "L1 / D4 / D5 / Q1 / YoY / 制药工程 / 食品工程" },
    { name: "歧义", n: S.stats.counts.ambiguousTerm, eg: "表现 / 窗口 / 平台×3（含 1 处语境冲突）" },
    { name: "指称悬空", n: S.stats.counts.danglingReference, eg: "「此句为」「该值为调整」无先行词" },
  ];
  function render() {
    fits();
    const ctx = bc.ctx; ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.translate((W - W0 * sc) / 2, (H - H0 * sc) / 2); ctx.scale(sc, sc);
    hits.length = 0;
    // ── 仪表（上）：0→15‰ 线性尺，阈值红刻线，实测蓝标 ──
    const gy = 44, gw = W0 - mL - mR - 60;
    ctx.font = `10px ${MONO}`; ctx.fillStyle = PAL.inkLo; ctx.textAlign = "left";
    ctx.fillText("HEDGING DENSITY · ‰", mL, gy - 24);
    ctx.strokeStyle = PAL.line; ctx.lineWidth = 1;
    ctx.strokeRect(mL, gy, gw, 16);
    for (const tv of [0, 5, 10, 15]) {
      const x = mL + (tv / 15) * gw;
      ctx.beginPath(); ctx.moveTo(x, gy + 16); ctx.lineTo(x, gy + 22); ctx.stroke();
      ctx.textAlign = "center"; ctx.fillText(String(tv), x, gy + 34);
    }
    // 阈值线
    const thX = mL + gw;
    ctx.strokeStyle = PAL.neg; ctx.setLineDash([4, 3]); ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(thX, gy - 8); ctx.lineTo(thX, gy + 22); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = PAL.neg; ctx.textAlign = "right"; ctx.font = `9.5px ${MONO}`;
    ctx.fillText("阈值 15‰", thX + 4, gy - 14);
    // 实测标记（0.35/15 ≈ 2.3% 处）
    const pv = REDUCE ? S.stats.hedgingDensity : S.stats.hedgingDensity * clamp(prog, 0, 1);
    const px = mL + (pv / 15) * gw;
    if (prog > 0.3 || REDUCE) {
      ctx.fillStyle = PAL.red;
      ctx.fillRect(mL, gy, Math.max(2, px - mL), 16);
      ctx.beginPath(); ctx.moveTo(px, gy - 6); ctx.lineTo(px - 5, gy - 16); ctx.lineTo(px + 5, gy - 16); ctx.closePath(); ctx.fill();
      ctx.font = `700 13px ${MONO}`; ctx.textAlign = "left";
      ctx.strokeStyle = "rgba(255,255,255,.9)"; ctx.lineWidth = 4;
      ctx.strokeText(`0.35‰ · 命中 ${S.stats.hedgingHits} 处`, px + 10, gy - 12);
      ctx.fillStyle = PAL.red; ctx.fillText(`0.35‰ · 命中 ${S.stats.hedgingHits} 处`, px + 10, gy - 12);
    }
    hits.push({ x: mL, y: gy - 20, w: gw, h: 56, kind: "gauge" });
    // ── 三类发现计数（下）──
    const cy0 = 130, cgap = (W0 - mL - mR) / 3;
    cats.forEach((c, i) => {
      const cx0 = mL + cgap * i;
      const p = REDUCE ? 1 : clamp(prog * 1.4 - i * 0.15, 0, 1);
      ctx.font = `700 30px ${MONO}`; ctx.textAlign = "left"; ctx.fillStyle = PAL.ink;
      ctx.globalAlpha = p;
      ctx.fillText(String(Math.round(c.n * p)), cx0, cy0 + 22);
      ctx.font = `700 11.5px ${'"et-book", Palatino, Georgia, serif'}`; ctx.fillStyle = PAL.red;
      ctx.fillText(c.name, cx0 + 34, cy0 + 18);
      // 计数小方格
      for (let d = 0; d < c.n; d++) {
        const dp = clamp(p * c.n - d, 0, 1);
        ctx.globalAlpha = dp;
        ctx.fillStyle = "rgba(5,28,44,.75)";
        ctx.fillRect(cx0 + d * 13, cy0 + 36, 9, 9);
      }
      ctx.globalAlpha = p;
      ctx.font = `9.5px ${MONO}`; ctx.fillStyle = PAL.inkLo;
      ctx.fillText(c.eg.length > 19 ? c.eg.slice(0, 19) + "…" : c.eg, cx0, cy0 + 64);
      ctx.globalAlpha = 1;
      hits.push({ x: cx0, y: cy0 - 12, w: cgap - 20, h: 92, kind: "cat", c });
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
    if (!h) return;
    if (h.kind === "gauge") {
      U.showDrill({ title: "对冲密度 · CONF=方法论档",
        value: `${S.stats.hedgingDensity}‰ / 阈值 ${S.stats.hedgingThreshold}‰`,
        sub: `全文 ${S.stats.charCount} 字、${S.stats.sentenceCount} 句，对冲词命中 ${S.stats.hedgingHits} 处。${S.notes}`,
        source: "data/semantic_audit.json · 2026-08-28", x: e.clientX, y: e.clientY });
    } else {
      U.showDrill({ title: `${h.c.name} · ${h.c.n} 条候选`,
        value: `${h.c.n} 条`, sub: `示例：${h.c.eg}。全部为启发式候选，须人工裁决。`,
        source: "data/semantic_audit.json · 2026-08-28", x: e.clientX, y: e.clientY });
    }
  });
  new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) play(); }), { threshold: 0.2 }).observe(canvas);
  addEventListener("resize", render);
  render();
})();
