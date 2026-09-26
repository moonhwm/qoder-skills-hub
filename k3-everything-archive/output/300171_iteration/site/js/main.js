// main.js · chips 滚动、K 锚行内下钻、IO 入场、阅读进度、页脚 top3_likely_wrong
(() => {
  const R = window.RPT; if (!R || !window.U) return;

  // 封面 chips → 分区滚动
  document.querySelectorAll("[data-goto]").forEach(b =>
    b.addEventListener("click", () => {
      const t = document.querySelector(b.dataset.goto);
      if (t) t.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }));

  // 行内 ◆K 锚按钮
  document.addEventListener("click", e => {
    const b = e.target.closest("button.klink");
    if (b && window.K) K.drill(b.dataset.k, e.clientX, e.clientY);
  });

  // IO 入场（.rev 统一淡入上移）
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revIO = new IntersectionObserver(es => es.forEach(en => {
    if (en.isIntersecting) { en.target.classList.add("in"); revIO.unobserve(en.target); }
  }), { threshold: 0.12 });
  document.querySelectorAll(".rev").forEach(el => {
    if (REDUCE) el.classList.add("in"); else revIO.observe(el);
  });

  // 阅读进度细条
  const bar = document.getElementById("read-progress");
  if (bar) {
    const upd = () => {
      const max = document.documentElement.scrollHeight - innerHeight;
      bar.style.width = (max > 0 ? clamp(scrollY / max, 0, 1) * 100 : 0) + "%";
    };
    const clamp = (v, a, b2) => Math.max(a, Math.min(b2, v));
    addEventListener("scroll", upd, { passive: true }); upd();
  }

  // 页脚 top3_likely_wrong
  const t3 = document.getElementById("top3-list");
  if (t3) {
    t3.innerHTML = `<table class="dt"><thead><tr>
      <th>#</th><th>最可能错的断言</th><th>错因</th><th>推翻方法</th></tr></thead><tbody>
      ${R.top3Wrong.map(x => `<tr>
        <td class="num" style="color:var(--neg);font-weight:700">${x.n}</td>
        <td><b>${x.claim}</b></td>
        <td style="font-size:12.5px;color:var(--ink-md)">${x.why}</td>
        <td style="font-size:12.5px;color:var(--ink-md)">${x.falsify}</td></tr>`).join("")}
      </tbody></table>`;
  }
})();
