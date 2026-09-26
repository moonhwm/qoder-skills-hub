// §1 自述链：迭代时间线 DOM + 缺陷收敛图（R1→R4 缺陷总量 vs High 级，逐轮归零）
(() => {
  const R = window.RPT; if (!R || !window.U) return;
  const { PAL, clamp } = U;
  const MONO = 'Menlo, Consolas, monospace';
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ── 时间线 DOM ──
  const tl = document.getElementById("iter-timeline");
  if (tl) {
    tl.innerHTML = R.iterations.map(it => `
      <li>
        <span class="it-round">${it.round}</span><span class="it-ver">v${it.version}</span>
        <h4>${it.action}</h4>
        <p>产出：${it.output}<br>结果：${it.result}</p>
      </li>`).join("");
  }
  // ── 缺陷修订清单 ──
  const dl = document.getElementById("defect-list");
  if (dl) {
    dl.innerHTML = R.defectFixes.map(([id, txt]) =>
      `<li><b style="font-family:Menlo,Consolas,monospace;font-size:12px;color:var(--red)">${id}</b>　${txt}</li>`).join("");
  }
  // ── 排期表 ──
  const st = document.getElementById("schedule-table");
  if (st) {
    st.innerHTML = `<table class="dt"><thead><tr>
      <th>优先级</th><th>任务</th><th>验收标准</th><th>状态</th></tr></thead><tbody>
      ${R.schedule.map(s => `<tr>
        <td class="num">${s.p}</td><td>${s.task}</td><td>${s.acceptance}</td>
        <td>${s.status === "done"
          ? '<span class="conf high">DONE</span>'
          : '<span class="conf medium">PENDING</span>'}</td></tr>`).join("")}
      </tbody></table>`;
  }

  // ── 缺陷收敛图 ──
  const host = document.getElementById("iter-chart");
  if (!host) return;
  const body = U.frame(host, {
    title: "缺陷面先被撑大，再被逐轮清零",
    sub: "R1→R4 · 墨柱=当轮缺陷总数 · 红柱=其中 High 级 · R3 残留为 Medium · R4 证据链脚本校验 0 错误 · 点击柱体下钻",
    src: "iteration_log.json + charter_v0.1/v1.0 + 报告 §一（2026-08-28）",
  });
  const canvas = document.createElement("canvas");
  canvas.style.width = "100%"; canvas.style.display = "block"; canvas.style.height = "330px";
  body.appendChild(canvas);
  const bc = U.bindCanvas(canvas);
  const W0 = 760, H0 = 330, mL = 54, mR = 20, mT = 40, mB = 58;
  let W = 0, H = 0, sc = 1, prog = 0, played = false;
  const fits = () => { const r = bc.fit(); W = r.w; H = r.h; sc = Math.min(W / W0, H / H0); };

  const data = R.iterations;
  const maxV = 20;
  const hits = [];
  function render() {
    fits();
    const ctx = bc.ctx; ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.translate((W - W0 * sc) / 2, (H - H0 * sc) / 2); ctx.scale(sc, sc);
    hits.length = 0;
    const iw = W0 - mL - mR, ih = H0 - mT - mB;
    const y = v => mT + ih - (v / maxV) * ih;
    // 网格线
    ctx.strokeStyle = PAL.lineLo; ctx.lineWidth = 1;
    ctx.fillStyle = PAL.inkLo; ctx.font = `10px ${MONO}`; ctx.textAlign = "right";
    for (const gv of [0, 5, 10, 15, 20]) {
      ctx.beginPath(); ctx.moveTo(mL, y(gv)); ctx.lineTo(W0 - mR, y(gv)); ctx.stroke();
      ctx.fillText(String(gv), mL - 8, y(gv) + 3);
    }
    const bw = 34, gap = iw / data.length;
    data.forEach((d, i) => {
      const cx0 = mL + gap * i + gap / 2;
      const p = REDUCE ? 1 : clamp(prog * 1.5 - i * 0.14, 0, 1);
      // 总量柱（墨）
      const h1 = (d.defects / maxV) * ih * p;
      ctx.fillStyle = d.defects === 0 ? "rgba(5,28,44,.16)" : "rgba(5,28,44,.82)";
      if (d.defects > 0) ctx.fillRect(cx0 - bw - 4, y(d.defects * p) + (1 - p) * 0, bw, h1);
      else { // R4：0 基线标记
        ctx.strokeStyle = PAL.line; ctx.setLineDash([3, 3]);
        ctx.strokeRect(cx0 - bw - 4, y(0) - 3, bw, 3); ctx.setLineDash([]);
      }
      // High 柱（语义红）
      if (d.high > 0) {
        const h2 = (d.high / maxV) * ih * p;
        ctx.fillStyle = PAL.neg;
        ctx.fillRect(cx0 + 4, y(d.high * p), bw, h2);
      } else {
        ctx.strokeStyle = "rgba(194,47,78,.4)"; ctx.setLineDash([3, 3]);
        ctx.strokeRect(cx0 + 4, y(0) - 3, bw, 3); ctx.setLineDash([]);
      }
      // 数值标签
      if (p > 0.6) {
        ctx.font = `700 13px ${MONO}`; ctx.textAlign = "center";
        ctx.fillStyle = PAL.ink;
        ctx.fillText(String(d.defects), cx0 - bw / 2 - 4, y(d.defects) - 8);
        ctx.fillStyle = PAL.neg;
        ctx.fillText(String(d.high), cx0 + bw / 2 + 4, y(Math.max(d.high, 0.4)) - 8);
      }
      // x 轴标签
      ctx.font = `700 11.5px ${MONO}`; ctx.fillStyle = PAL.ink; ctx.textAlign = "center";
      ctx.fillText(d.round, cx0, H0 - mB + 20);
      ctx.font = `9.5px ${MONO}`; ctx.fillStyle = PAL.inkLo;
      ctx.fillText("v" + d.version, cx0, H0 - mB + 35);
      ctx.fillText(d.ts.slice(0, 10), cx0, H0 - mB + 49);
      hits.push({ x: cx0 - bw - 4, y: mT, w: bw * 2 + 8, h: ih, d });
    });
    // 收敛注记
    ctx.font = `italic 12px ${'"et-book", Palatino, Georgia, serif'}`;
    ctx.fillStyle = PAL.inkMd; ctx.textAlign = "right";
    ctx.fillText("连续 2 轮无 High 级错点 → 有限收敛达成（R3/R4）", W0 - mR, mT - 14);
    ctx.restore();
  }
  function play() {
    if (played) return; played = true;
    if (REDUCE) { prog = 1; render(); return; }
    const t0 = performance.now();
    (function tick(now) { prog = clamp((now - t0) / 1300, 0, 1); render(); if (prog < 1) requestAnimationFrame(tick); })(t0);
  }
  canvas.addEventListener("click", e => {
    const r = canvas.getBoundingClientRect();
    const lx = (e.clientX - r.left - (W - W0 * sc) / 2) / sc, ly = (e.clientY - r.top - (H - H0 * sc) / 2) / sc;
    const h = hits.find(hh => lx >= hh.x && lx <= hh.x + hh.w && ly >= hh.y && ly <= hh.y + hh.h);
    if (h) U.showDrill({ title: `${h.d.round} · 版本 v${h.d.version}`,
      value: `${h.d.defects} 条缺陷 · High ${h.d.high} 条`,
      sub: `${h.d.action}。产出：${h.d.output}。结果：${h.d.result}`,
      source: "iteration_log.json · " + h.d.ts.slice(0, 10), x: e.clientX, y: e.clientY });
  });
  new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) play(); }), { threshold: 0.2 }).observe(canvas);
  addEventListener("resize", render);
  render();
})();
