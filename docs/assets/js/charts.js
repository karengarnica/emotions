/* Gráficos D3 de la sección de resultados.
   Cada función recibe el contenedor y los datos de docs/data/resultados.json. */

const EXTRA = {
  bien: { name: "“Bien” (genérico)", color: "#B9B2A3" },
  otro: { name: "Otra respuesta", color: "#D9D3C5" },
  sin_respuesta: { name: "Sin respuesta", color: "#EFEAE0" },
};
const category = (key) => Emotions[key] || EXTRA[key];

const tooltip = {
  el: null,
  show(event, html) {
    this.el ??= document.getElementById("tooltip");
    this.el.innerHTML = html;
    this.el.style.opacity = 1;
    const pad = 14;
    const { width, height } = this.el.getBoundingClientRect();
    const x = Math.min(window.innerWidth - width - 8, event.clientX + pad);
    const y = event.clientY - height - pad < 8 ? event.clientY + pad : event.clientY - height - pad;
    this.el.style.left = `${Math.max(8, x)}px`;
    this.el.style.top = `${y}px`;
  },
  hide() {
    if (this.el) this.el.style.opacity = 0;
  },
};

/** Texto oscuro o claro según el color de fondo. */
function inkOn(color) {
  const { r, g, b } = d3.rgb(color);
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6 ? INK : "#fff";
}

function svgIn(container, width, height) {
  const root = d3.select(container);
  root.selectAll("*").remove();
  return root.append("svg").attr("viewBox", [0, 0, width, height]).attr("width", width).attr("height", height);
}

/* ── 1 · ¿Cómo me siento hoy? — barras apiladas al 100 % ───────────── */
const FEELING_ORDER = ["alegria", "carino", "calma", "sorpresa", "tristeza", "miedo", "enojo", "asco", "bien", "otro", "sin_respuesta"];

function drawFeelings(container, sessions) {
  const width = container.clientWidth;
  const height = Math.max(260, Math.min(380, width * 0.5));
  const m = { top: 8, right: 4, bottom: 40, left: 38 };
  const svg = svgIn(container, width, height);

  const keys = FEELING_ORDER.filter((k) => sessions.some((s) => s.conteo[k]));
  const x = d3.scaleBand(sessions.map((s) => s.registro), [m.left, width - m.right]).padding(width < 520 ? 0.12 : 0.2);
  const y = d3.scaleLinear([0, 1], [height - m.bottom, m.top]);
  const stack = d3.stack().keys(keys).value((s, k) => (s.conteo[k] || 0) / s.n);

  svg.append("g").attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(4, "%").tickSize(-(width - m.left - m.right)))
    .call((g) => g.select(".domain").remove());

  const every = Math.ceil(sessions.length / Math.max(4, Math.floor((width - m.left) / 30)));
  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8).tickValues(x.domain().filter((_, i) => i % every === 0)))
    .call((g) => g.select(".domain").remove());
  svg.append("text").attr("class", "axis-label").attr("x", (m.left + width) / 2).attr("y", height - 4)
    .attr("text-anchor", "middle").text("Registro (día de taller) →");

  svg.append("g").selectAll("g").data(stack(sessions)).join("g")
    .attr("fill", (layer) => category(layer.key).color)
    .selectAll("rect").data((layer) => layer.map((d) => ({ ...d, key: layer.key }))).join("rect")
    .attr("x", (d) => x(d.data.registro))
    .attr("width", x.bandwidth())
    .attr("y", (d) => y(d[1]) + 1)
    .attr("height", (d) => Math.max(0, y(d[0]) - y(d[1]) - 1))
    .attr("rx", 2)
    .on("pointermove", (event, d) => {
      const n = d.data.conteo[d.key];
      tooltip.show(event, `<b>${category(d.key).name}</b><br>Registro ${d.data.registro}: ${n} de ${d.data.n} niños (${Math.round((100 * n) / d.data.n)} %)`);
    })
    .on("pointerleave", () => tooltip.hide());

  return keys;
}

function drawLegend(container, keys) {
  container.innerHTML = keys.map((k) =>
    `<span class="legend__item"><span class="legend__swatch" style="background:${category(k).color};${k === "sin_respuesta" ? "border:1px solid #cfc8b8" : ""}"></span>${category(k).name}</span>`
  ).join("");
}

function feelingsCallouts(container, sessions) {
  const first = sessions[0];
  const reached = sessions.find((s) => s.pct_nombra_emocion >= 95);
  const rest = sessions.slice(1);
  const mean = d3.mean(rest, (s) => s.pct_nombra_emocion);
  const fmt = (v) => `${Math.round(v)} %`;
  const items = [
    [fmt(first.pct_nombra_emocion), "nombró una emoción el primer día; el resto dijo “bien”", "var(--ink-2)"],
    [fmt(reached ? reached.pct_nombra_emocion : mean), reached ? `lo hizo en el registro ${reached.registro}` : "en promedio después", "var(--calma)"],
    [fmt(mean), `en promedio en los ${rest.length} registros siguientes`, "var(--tristeza)"],
  ];
  container.innerHTML = items.map(([value, text, color]) =>
    `<div class="callout"><b style="color:${color}">${value}</b><span>${text}</span></div>`).join("");
}

/* ── 2 · Gráfico solar navegable (zoomable sunburst) ───────────────── */
const POS_GROUPS = { VERB: "Acciones", NOUN: "Seres y cosas", ADJ: "Cualidades", X: "Palabras" };
const COHORT_SHORT = { "2024_antes": "2024 antes", "2024_despues": "2024 después", "2025_inicio": "2025 inicio" };
const COHORT_COLORS = ["#1F2544", "#4B5273", "#7A80A0"];
const WORDS_PER_GROUP = 10;

function sunburstHierarchy(definiciones) {
  return {
    name: "Todas las respuestas",
    children: definiciones.map((cohort, i) => ({
      name: COHORT_SHORT[cohort.clave] || cohort.nombre,
      long: cohort.nombre,
      color: COHORT_COLORS[i % COHORT_COLORS.length],
      children: Object.entries(cohort.emociones).map(([key, info]) => ({
        name: Emotions[key].name,
        emotion: key,
        children: d3.groups(info.palabras, (w) => (POS_GROUPS[w.pos] ? w.pos : "X")).map(([pos, words]) => ({
          name: POS_GROUPS[pos],
          children: words.slice(0, WORDS_PER_GROUP).map((w) => ({ name: w.w, value: w.n })),
        })),
      })),
    })),
  };
}

function drawSunburst(container, definiciones, onFocus) {
  const size = 640;
  const RINGS = 3; // anillos visibles a la vez alrededor del centro
  const radius = size / (2 * (RINGS + 1));
  const hierarchy = d3.hierarchy(sunburstHierarchy(definiciones)).sum((d) => d.value || 0).sort((a, b) => b.value - a.value);
  const root = d3.partition().size([2 * Math.PI, hierarchy.height + 1])(hierarchy);
  root.each((d) => (d.current = d));

  const fill = (d) => {
    if (d.depth === 1) return d.data.color;
    const emotion = d.ancestors().find((a) => a.data.emotion);
    const base = Emotions[emotion.data.emotion].color;
    return d3.interpolateRgb(base, "#fff")([0, 0, 0, 0.38, 0.68][d.depth]);
  };

  const arc = d3.arc()
    .startAngle((d) => d.x0).endAngle((d) => d.x1)
    .padAngle((d) => Math.min((d.x1 - d.x0) / 2, 0.006)).padRadius(radius * 1.5)
    .innerRadius((d) => d.y0 * radius).outerRadius((d) => Math.max(d.y0 * radius, d.y1 * radius - 2));

  const arcVisible = (d) => d.y1 <= RINGS + 1 && d.y0 >= 1 && d.x1 > d.x0;
  const labelVisible = (d) => arcVisible(d) && (d.x1 - d.x0) * ((d.y0 + d.y1) / 2) * radius > 15;
  const labelTransform = (d) => {
    const angle = (((d.x0 + d.x1) / 2) * 180) / Math.PI;
    const r = ((d.y0 + d.y1) / 2) * radius;
    return `rotate(${angle - 90}) translate(${r},0) rotate(${angle < 180 ? 0 : 180})`;
  };
  const trail = (d) => d.ancestors().reverse().slice(1).map((a) => a.data.name).join(" › ") || root.data.name;

  d3.select(container).selectAll("*").remove();
  const svg = d3.select(container).append("svg").attr("viewBox", [-size / 2, -size / 2, size, size]);

  const path = svg.append("g").selectAll("path").data(root.descendants().slice(1)).join("path")
    .attr("fill", fill)
    .attr("fill-opacity", (d) => (arcVisible(d.current) ? 1 : 0))
    .attr("pointer-events", (d) => (arcVisible(d.current) ? "auto" : "none"))
    .attr("d", (d) => arc(d.current))
    .style("cursor", (d) => (d.children ? "pointer" : "default"))
    .on("click", (event, d) => d.children && zoom(d))
    .on("pointermove", (event, d) => tooltip.show(event, `<b>${d.data.name}</b><br>${trail(d)}<br>${d.value} ${d.value === 1 ? "mención" : "menciones"}`))
    .on("pointerleave", () => tooltip.hide());

  const label = svg.append("g").attr("text-anchor", "middle").selectAll("text")
    .data(root.descendants().slice(1)).join("text")
    .attr("dy", "0.35em")
    .attr("font-size", 12)
    .attr("fill-opacity", (d) => +labelVisible(d.current))
    .attr("transform", (d) => labelTransform(d.current))
    .style("fill", (d) => inkOn(fill(d)))
    .text((d) => (d.data.name.length > 13 ? `${d.data.name.slice(0, 12)}…` : d.data.name));

  const center = svg.append("g").style("cursor", "pointer").on("click", () => zoom(focus.parent || root));
  center.append("circle").attr("r", radius - 4).attr("fill", "#FFF9EF").attr("stroke", INK).attr("stroke-width", 2.5);
  const centerTitle = center.append("text").attr("text-anchor", "middle").attr("dy", "-0.1em")
    .attr("font-size", 15).attr("font-weight", 800).style("font-family", "var(--display)");
  const centerHint = center.append("text").attr("text-anchor", "middle").attr("dy", "1.5em")
    .attr("font-size", 12).style("fill", "#4B5273");

  let focus = root;
  function describe(d) {
    centerTitle.text(d === root ? "Explora" : d.data.name.length > 13 ? `${d.data.name.slice(0, 12)}…` : d.data.name);
    centerHint.text(d === root ? "toca un anillo" : "← volver");
    onFocus(d === root ? root.data.name : trail(d), d.value);
  }

  function zoom(target) {
    focus = target;
    describe(target);
    root.each((d) => {
      d.target = {
        x0: Math.max(0, Math.min(1, (d.x0 - target.x0) / (target.x1 - target.x0))) * 2 * Math.PI,
        x1: Math.max(0, Math.min(1, (d.x1 - target.x0) / (target.x1 - target.x0))) * 2 * Math.PI,
        y0: Math.max(0, d.y0 - target.depth),
        y1: Math.max(0, d.y1 - target.depth),
      };
    });
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const t = svg.transition().duration(still ? 0 : 650);
    path.transition(t)
      .tween("data", (d) => { const i = d3.interpolate(d.current, d.target); return (k) => (d.current = i(k)); })
      .filter(function (d) { return +this.getAttribute("fill-opacity") || arcVisible(d.target); })
      .attr("fill-opacity", (d) => (arcVisible(d.target) ? 1 : 0))
      .attr("pointer-events", (d) => (arcVisible(d.target) ? "auto" : "none"))
      .attrTween("d", (d) => () => arc(d.current));
    label.filter(function (d) { return +this.getAttribute("fill-opacity") || labelVisible(d.target); })
      .transition(t)
      .attr("fill-opacity", (d) => +labelVisible(d.target))
      .attrTween("transform", (d) => () => labelTransform(d.current));
  }

  describe(root);
}

/* ── 3 · “No sé” por emoción y momento ─────────────────────────────── */
const MOMENTS = [
  { key: "2024_antes", name: "2024 antes", color: "#1F2544" },
  { key: "2024_despues", name: "2024 después", color: "#2FA36B" },
  { key: "2025_inicio", name: "2025 inicio", color: "#F2811D" },
];

function drawNoSe(container, definiciones) {
  const byKey = Object.fromEntries(definiciones.map((c) => [c.clave, c.emociones]));
  const emotions = Object.keys(byKey["2024_antes"]);
  const rows = emotions.map((e) => ({
    emotion: e,
    values: MOMENTS.filter((mo) => byKey[mo.key]?.[e]).map((mo) => ({ ...mo, pct: byKey[mo.key][e].pct_sin_respuesta, info: byKey[mo.key][e] })),
  }));

  const width = container.clientWidth;
  const rowH = 54;
  const m = { top: 34, right: 26, bottom: 30, left: 84 };
  const height = m.top + rows.length * rowH + m.bottom;
  const svg = svgIn(container, width, height);
  const max = Math.max(25, d3.max(rows, (r) => d3.max(r.values, (v) => v.pct)) + 3);
  const x = d3.scaleLinear([0, max], [m.left, width - m.right]);
  const y = (i) => m.top + i * rowH + rowH / 2;

  svg.append("g").attr("transform", `translate(0,${height - m.bottom})`)
    .call(d3.axisBottom(x).ticks(5).tickFormat((d) => `${d} %`).tickSize(-(height - m.top - m.bottom)))
    .call((g) => g.select(".domain").remove());

  const legend = svg.append("g").attr("transform", `translate(${m.left},12)`);
  let offset = 0;
  MOMENTS.forEach((mo) => {
    const g = legend.append("g").attr("transform", `translate(${offset},0)`);
    g.append("circle").attr("r", 6).attr("fill", mo.color);
    const text = g.append("text").attr("x", 11).attr("dy", "0.35em").attr("font-size", 12.5).text(mo.name);
    offset += 11 + text.node().getComputedTextLength() + 16;
  });

  const row = svg.append("g").selectAll("g").data(rows).join("g").attr("transform", (d, i) => `translate(0,${y(i)})`);
  row.append("text").attr("x", m.left - 14).attr("dy", "0.35em").attr("text-anchor", "end")
    .attr("font-weight", 700).attr("font-size", 14).text((d) => Emotions[d.emotion].name);
  row.append("line")
    .attr("x1", (d) => x(d3.min(d.values, (v) => v.pct))).attr("x2", (d) => x(d3.max(d.values, (v) => v.pct)))
    .attr("stroke", "#CFC8B8").attr("stroke-width", 3).attr("stroke-linecap", "round");
  row.selectAll("circle").data((d) => d.values).join("circle")
    .attr("cx", (v) => x(v.pct)).attr("r", 9).attr("fill", (v) => v.color).attr("stroke", "#fff").attr("stroke-width", 2)
    .on("pointermove", (event, v) => tooltip.show(event, `<b>${v.name}</b><br>${v.info.sin_respuesta} de ${v.info.n} respuestas fueron “no sé” (${v.pct} %)`))
    .on("pointerleave", () => tooltip.hide());
  row.selectAll(".value").data((d) => d.values).join("text").attr("class", "value")
    .attr("x", (v) => x(v.pct)).attr("y", (v) => (v.key === "2025_inicio" ? 23 : -15)).attr("text-anchor", "middle").attr("font-size", 11.5).attr("font-weight", 700)
    .style("fill", (v) => v.color).text((v) => `${Math.round(v.pct)} %`);
}

/* ── 4 · Situaciones × emoción ─────────────────────────────────────── */
function wrapWords(text, maxChars) {
  const lines = [""];
  text.replace(/\.$/, "").split(/\s+/).forEach((word) => {
    const last = lines.length - 1;
    if ((lines[last] + " " + word).trim().length > maxChars && lines[last]) lines.push(word);
    else lines[last] = (lines[last] + " " + word).trim();
  });
  return lines;
}

function drawSituations(container, data) {
  const width = container.clientWidth;
  const labelW = Math.min(190, width * 0.42);
  const narrow = width < 420;
  const m = { top: narrow ? 66 : 44, right: narrow ? 16 : 6, bottom: 6, left: labelW };
  const rowH = 50;
  const height = m.top + data.situaciones.length * rowH + m.bottom;
  const svg = svgIn(container, width, height);

  const x = d3.scalePoint(data.emociones, [m.left, width - m.right]).padding(0.6);
  const maxCount = d3.max(data.conteo.flat());
  const r = d3.scaleSqrt([0, maxCount], [0, Math.min(22, x.step() / 2 - 2)]);
  const short = { sin_respuesta: "Sin resp.", otro: "Otra" };

  svg.append("g").selectAll("text").data(data.emociones).join("text")
    .attr("transform", (k) => `translate(${x(k)},${m.top - 22})${narrow ? " rotate(-40)" : ""}`)
    .attr("text-anchor", narrow ? "start" : "middle")
    .attr("font-size", narrow ? 11.5 : 13).attr("font-weight", 700)
    .text((k) => short[k] || category(k).name);

  const row = svg.append("g").selectAll("g").data(data.situaciones).join("g")
    .attr("transform", (d, i) => `translate(0,${m.top + i * rowH + rowH / 2})`);
  row.append("line").attr("x1", m.left - 6).attr("x2", width - m.right).attr("stroke", "#ECDFC6");
  row.append("text").attr("x", 0).attr("font-size", 13.5)
    .each(function (situation) {
      const lines = wrapWords(situation, Math.floor(labelW / 7.2));
      d3.select(this).selectAll("tspan").data(lines).join("tspan")
        .attr("x", 0).attr("dy", (_, i) => (i === 0 ? `${0.35 - (lines.length - 1) * 0.6}em` : "1.2em")).text((l) => l);
    });

  const cell = row.selectAll(".cell").data((situation, i) =>
    data.emociones.map((k, j) => ({ situation, key: k, n: data.conteo[i][j], total: d3.sum(data.conteo[i]) }))
  ).join("g").attr("class", "cell").attr("transform", (d) => `translate(${x(d.key)},0)`);

  cell.filter((d) => d.n > 0).append("circle").attr("r", (d) => r(d.n))
    .attr("fill", (d) => category(d.key).color)
    .attr("stroke", (d) => (d.key === "sin_respuesta" ? "#CFC8B8" : "none"))
    .on("pointermove", (event, d) => tooltip.show(event, `<b>${d.situation}</b><br>${category(d.key).name}: ${d.n} de ${d.total} niños`))
    .on("pointerleave", () => tooltip.hide());
  cell.filter((d) => r(d.n) >= 10).append("text").attr("text-anchor", "middle").attr("dy", "0.35em")
    .attr("font-size", 12).attr("font-weight", 700).attr("pointer-events", "none")
    .style("fill", (d) => inkOn(category(d.key).color)).text((d) => d.n);
}
