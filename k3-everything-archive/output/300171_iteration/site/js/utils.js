// 共享工具
window.U = (() => {
  const TAU = Math.PI * 2;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smooth = t => t * t * (3 - 2 * t);
  const ease = (cur, tgt, dt, dur) => cur + (tgt - cur) * (1 - Math.exp(-dt / dur));

  function makeRng(seed) {
    let s = seed >>> 0;
    return () => {
      s += 0x6d2b79f5; let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // 专业配色方案——白色底色，深海军蓝文字，电光蓝强调色。
  // 注意关键语义：`red` 为旧版强调色槽位（现已替换为电光蓝），故现有
  // 强调色用法会自动重新着色；真正的负向状态（拒绝/崩溃/缺失）
  // 必须使用 PAL.neg —— 按图表逐一审计。
  const PAL = {
    paper: "#ffffff", hi: "#f7f9fc", ink: "#051c2c", inkMd: "#42566a", inkLo: "#8595a6",
    line: "#dbe2ea", lineLo: "#eef1f6", red: "#2251ff", redHi: "#1233b8",
    blue: "#7a45c9", copper: "#b07a10", green: "#008a6d", gold: "#b07a10",
    neg: "#c22f4e", accent: "#2251ff", navy: "#051c2c",
  };
  const SERIES = [PAL.red, PAL.blue, PAL.copper, PAL.green];

  // HiDPI canvas 尺寸绑定
  function bindCanvas(canvas) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const fit = () => {
      const r = canvas.getBoundingClientRect();
      canvas.width = Math.round(r.width * dpr);
      canvas.height = Math.round(r.height * dpr);
      const ctx = canvas.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return { w: r.width, h: r.height, cx: r.width / 2, cy: r.height / 2 };
    };
    return { fit, ctx: canvas.getContext("2d") };
  }

  // 3D 投影
  function project(pt, view, cam = {}) {
    const yaw = cam.yaw ?? 0, pitch = cam.pitch ?? 0;
    const scale = cam.scale ?? Math.min(view.w, view.h) * 0.24;
    const dist = cam.distance ?? 3.8;
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    let x = pt.x * cy - pt.z * sy;
    let z = pt.x * sy + pt.z * cy;
    let y = pt.y * cp - z * sp;
    z = pt.y * sp + z * cp;
    const p = dist / (dist + z);
    return { x: (cam.ox ?? view.cx) + x * scale * p, y: (cam.oy ?? view.cy) + y * scale * p, z, p };
  }

  // 网点字段（颜色可调）
  function dotField(ctx, x0, y0, w, h, opt = {}) {
    const gap = opt.gap ?? 12;
    const color = opt.color ?? PAL.red;
    const density = opt.density ?? ((x, y) => 1 - y); // 0..1
    ctx.save(); ctx.fillStyle = color;
    for (let y = y0; y < y0 + h; y += gap) {
      const off = (Math.round((y - y0) / gap) % 2) ? gap / 2 : 0;
      for (let x = x0; x < x0 + w; x += gap) {
        const u = (x - x0 + off) / w, v = (y - y0) / h;
        const d = clamp(density(u, v), 0, 1);
        if (d < 0.03) continue;
        ctx.globalAlpha = clamp(0.05 + d * 0.5, 0, 0.62);
        const r = 0.6 + d * gap * 0.26;
        ctx.beginPath(); ctx.arc(x + off, y, r, 0, TAU); ctx.fill();
      }
    }
    ctx.restore();
  }

  // ── 数字递增（三次缓出；当 html:true 时通过 innerHTML 写入）──
  function countUp(el, { from = 0, to = 1, dur = 1100, html = false, fmt = v => Math.round(v).toLocaleString("en-US") } = {}) {
    let raf = 0, t0 = null;
    const tick = ts => {
      if (t0 == null) t0 = ts;
      const t = clamp((ts - t0) / dur, 0, 1);
      const e = 1 - Math.pow(1 - t, 3);
      if (html) el.innerHTML = fmt(lerp(from, to, e));
      else el.textContent = fmt(lerp(from, to, e));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }

  const fmt = {
    b: v => v == null ? "—" : "$" + (v >= 100 ? v.toFixed(0) : v.toFixed(1)) + "B",
    pct: v => (v > 0 ? "+" : "") + v.toFixed(v % 1 ? 1 : 0) + "%",
    n: v => v.toLocaleString("en-US"),
  };

  // ── 下钻数据卡片 ──
  const drill = document.getElementById("drill-card");
  let drillOpen = false;
  function showDrill({ title, value, delta, sub, source, x, y }) {
    drill.innerHTML = `<button class="d-close">✕</button>
      <div class="d-title">${title}</div>
      <div class="d-val">${value}${delta != null ? ` <span class="${delta >= 0 ? "pos" : "neg"}" style="font-size:15px">${fmt.pct(delta)}</span>` : ""}</div>
      ${sub ? `<div class="d-sub">${sub}</div>` : ""}
      ${source ? `<div class="d-src">Source · ${source}</div>` : ""}`;
    drill.hidden = false; drillOpen = true;
    const r = drill.getBoundingClientRect();
    let left = clamp(x + 14, 8, window.innerWidth - r.width - 8);
    let top = clamp(y - r.height - 14, 8, window.innerHeight - r.height - 8);
    if (y - r.height - 14 < 8) top = clamp(y + 18, 8, window.innerHeight - r.height - 8);
    drill.style.left = left + "px"; drill.style.top = top + "px";
    drill.querySelector(".d-close").onclick = hideDrill;
  }
  function hideDrill() { drill.hidden = true; drillOpen = false; }
  document.addEventListener("click", e => {
    if (drillOpen && !drill.contains(e.target)) {
      // let the triggering element handle it itself
      if (!e.target.closest("[data-drill-keep]")) hideDrill();
    }
  }, true);

  // ── 悬停提示 ──
  const tip = document.createElement("div");
  tip.className = "tip"; document.body.appendChild(tip);
  function showTip(html, x, y) {
    tip.innerHTML = html; tip.style.opacity = 1;
    tip.style.left = clamp(x + 12, 4, window.innerWidth - 220) + "px";
    tip.style.top = (y - 34) + "px";
  }
  function hideTip() { tip.style.opacity = 0; }

  // ── 图表框架 ──
  function frame(el, { title, sub, src }) {
    const head = document.createElement("div");
    if (title) head.innerHTML = `<p class="chart-title">${title}</p>${sub ? `<p class="chart-sub">${sub}</p>` : ""}`;
    el.appendChild(head);
    const body = document.createElement("div");
    el.appendChild(body);
    if (src) {
      const s = document.createElement("p");
      s.className = "chart-src"; s.textContent = "Source · " + src;
      el.appendChild(s);
    }
    return body;
  }

  return { TAU, clamp, lerp, smooth, ease, makeRng, PAL, SERIES, bindCanvas, project, dotField, countUp, fmt, showDrill, hideDrill, showTip, hideTip, frame };
})();
