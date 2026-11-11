/* Arranque de la página: caritas, portada animada y carga de resultados. */

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ── Portada: las emociones flotan y se pueden arrastrar ───────────── */
function heroPlayground() {
  const svg = d3.select("#hero-play");
  const node = svg.node();
  let width = node.clientWidth;
  let height = node.clientHeight;
  const wide = () => width >= 860;

  const big = Object.keys(Emotions).map((key, i) => ({ key, r: [58, 46, 50, 42, 44, 40, 48, 34][i] }));
  const confetti = d3.range(14).map((i) => ({ r: 5 + (i % 4) * 3, color: Object.values(Emotions)[i % 8].color }));
  const nodes = [...big, ...confetti];
  const scale = () => (wide() ? 1 : 0.62);
  // Zona de juego: a la derecha del texto en pantallas anchas, debajo en las angostas.
  const text = document.querySelector(".hero__text");
  const zone = () => {
    const hero = node.getBoundingClientRect();
    const box = text.getBoundingClientRect();
    return wide()
      ? { x0: box.right - hero.left + 24, y0: 0 }
      : { x0: 0, y0: box.bottom - hero.top + 12 };
  };
  let area = zone();
  const home = () => [(area.x0 + width) / 2, (area.y0 + height) / 2];
  nodes.forEach((d, i) => {
    const [hx, hy] = home();
    d.x = hx + Math.cos(i) * 160;
    d.y = hy + Math.sin(i * 1.7) * 120;
  });

  svg.append("style").text(FACE_STYLE);
  const blob = svg.selectAll("g.blob").data(nodes).join("g").attr("class", "blob");
  blob.filter((d) => d.key).append("g").attr("class", "blob__face").html((d) => faceMarkup(d.key));
  blob.filter((d) => !d.key).append("circle").attr("r", (d) => d.r).attr("fill", (d) => d.color).attr("opacity", 0.75);
  blob.filter((d) => d.key).append("title").text((d) => Emotions[d.key].name);

  const simulation = d3.forceSimulation(nodes)
    .velocityDecay(0.18)
    .force("collide", d3.forceCollide((d) => d.r * (d.key ? scale() : 1) + 5).strength(0.9))
    .force("x", d3.forceX(() => home()[0]).strength(0.035))
    .force("y", d3.forceY(() => home()[1]).strength(0.05))
    .on("tick", () => {
      nodes.forEach((d) => {
        const r = d.r * (d.key ? scale() : 1);
        d.x = Math.max(area.x0 + r, Math.min(width - r, d.x));
        d.y = Math.max(area.y0 + r, Math.min(height - r, d.y));
      });
      blob.attr("transform", (d) => `translate(${d.x},${d.y})`);
      blob.select(".blob__face").attr("transform", `scale(${scale()})`);
    });

  blob.call(d3.drag()
    .on("start", (event, d) => { simulation.alphaTarget(0.25).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
    .on("end", (event, d) => { simulation.alphaTarget(0); d.fx = d.fy = null; }));

  if (reducedMotion) {
    simulation.tick(200);
    simulation.stop();
    blob.attr("transform", (d) => `translate(${d.x},${d.y})`);
    blob.select(".blob__face").attr("transform", `scale(${scale()})`);
  } else {
    // Un empujoncito cada tanto para que nunca se queden quietas.
    d3.interval(() => {
      if (document.hidden) return;
      nodes.forEach((d) => { d.vx += (Math.random() - 0.5) * 2.4; d.vy += (Math.random() - 0.5) * 2.4; });
      simulation.alpha(0.25).restart();
    }, 2200);
  }

  new ResizeObserver(() => {
    width = node.clientWidth;
    height = node.clientHeight;
    area = zone();
    simulation.force("x").initialize(nodes);
    simulation.force("y").initialize(nodes);
    simulation.force("collide").initialize(nodes);
    if (!reducedMotion) simulation.alpha(0.5).restart();
  }).observe(node);
}

/* ── Resultados ────────────────────────────────────────────────────── */
function renderResults(data) {
  const el = (id) => document.getElementById(id);
  const sessions = data.como_me_siento_2025;
  const fmt = new Intl.NumberFormat("es-CO");

  const totalAnswers = d3.sum(data.definiciones, (c) => c.total.n) + d3.sum(sessions, (s) => s.n)
    + d3.sum(data.situaciones_2025.conteo.flat());
  el("fig-respuestas").textContent = fmt.format(totalAnswers);
  el("fig-registros").textContent = sessions.length;
  el("data-stamp").textContent = `Datos generados el ${new Date(`${data.generado}T12:00:00`).toLocaleDateString("es-CO", { dateStyle: "long" })}.`;

  feelingsCallouts(el("feelings-callouts"), sessions);
  drawSunburst(el("chart-sunburst"), data.definiciones, (path, count) => {
    el("sunburst-path").textContent = path;
    el("sunburst-count").textContent = `${fmt.format(count)} menciones de palabras`;
  });

  const responsive = () => {
    drawLegend(el("legend-feelings"), drawFeelings(el("chart-feelings"), sessions));
    drawNoSe(el("chart-nose"), data.definiciones);
    drawSituations(el("chart-situations"), data.situaciones_2025);
  };
  responsive();
  let lastWidth = window.innerWidth;
  window.addEventListener("resize", () => {
    if (window.innerWidth === lastWidth) return;
    lastWidth = window.innerWidth;
    responsive();
  });
}

mountFaces();
heroPlayground();
d3.json("data/resultados.json").then(renderResults).catch((error) => {
  console.error(error);
  document.querySelectorAll("#resultados .chart").forEach((chart) => {
    chart.innerHTML = '<p class="note">No se pudieron cargar los datos. Ejecuta <code>emotions build-site-data</code>.</p>';
  });
});
