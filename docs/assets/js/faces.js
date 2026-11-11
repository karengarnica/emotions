/* Caritas de las emociones: un círculo de color con ojos y boca dibujados en SVG.
   Se usan en la portada (burbujas), en la navegación y en la ruta de formación. */

const Emotions = {
  alegria: { name: "Alegría", color: "#F5B700" },
  tristeza: { name: "Tristeza", color: "#3B82C4" },
  enojo: { name: "Enojo", color: "#E5484D" },
  miedo: { name: "Miedo", color: "#7C5CBF" },
  calma: { name: "Calma", color: "#2FA36B" },
  sorpresa: { name: "Sorpresa", color: "#F2811D" },
  carino: { name: "Cariño", color: "#E36BA8" },
  asco: { name: "Asco", color: "#8A9A2B" },
};

const INK = "#1F2544";

/* Rasgos en un lienzo de -50…50. Cada emoción: cejas, ojos y boca. */
const FACE_PARTS = {
  alegria: `
    <circle cx="-17" cy="-8" r="5.5"/><circle cx="17" cy="-8" r="5.5"/>
    <path d="M-22 12 Q0 36 22 12" class="stroke"/>`,
  tristeza: `
    <path d="M-25 -20 L-11 -16 M25 -20 L11 -16" class="stroke thin"/>
    <circle cx="-17" cy="-6" r="5"/><circle cx="17" cy="-6" r="5"/>
    <path d="M-18 24 Q0 8 18 24" class="stroke"/>
    <path d="M27 2 q5 9 0 12 q-5 -3 0 -12" fill="#CFE6FA" stroke="none"/>`,
  enojo: `
    <path d="M-27 -22 L-9 -13 M27 -22 L9 -13" class="stroke"/>
    <circle cx="-17" cy="-5" r="5"/><circle cx="17" cy="-5" r="5"/>
    <path d="M-16 21 Q0 12 16 21" class="stroke"/>`,
  miedo: `
    <path d="M-25 -19 Q-17 -27 -9 -19 M9 -19 Q17 -27 25 -19" class="stroke thin"/>
    <circle cx="-17" cy="-5" r="7" fill="#fff"/><circle cx="17" cy="-5" r="7" fill="#fff"/>
    <circle cx="-17" cy="-4" r="3"/><circle cx="17" cy="-4" r="3"/>
    <path d="M-15 21 q5 -7 10 0 q5 7 10 0 q5 -7 10 0" class="stroke thin" transform="translate(-10 0)"/>`,
  calma: `
    <path d="M-25 -6 Q-17 2 -9 -6 M9 -6 Q17 2 25 -6" class="stroke"/>
    <path d="M-13 16 Q0 26 13 16" class="stroke"/>`,
  sorpresa: `
    <path d="M-25 -24 Q-17 -31 -9 -24 M9 -24 Q17 -31 25 -24" class="stroke thin"/>
    <circle cx="-17" cy="-8" r="6.5"/><circle cx="17" cy="-8" r="6.5"/>
    <ellipse cx="0" cy="20" rx="8" ry="10"/>`,
  carino: `
    <path d="M-25 -8 Q-17 -17 -9 -8 M9 -8 Q17 -17 25 -8" class="stroke"/>
    <path d="M-18 12 Q0 32 18 12" class="stroke"/>
    <circle cx="-30" cy="8" r="6" fill="#fff" opacity=".45" stroke="none"/>
    <circle cx="30" cy="8" r="6" fill="#fff" opacity=".45" stroke="none"/>`,
  asco: `
    <path d="M-26 -17 L-10 -14 M26 -20 L10 -13" class="stroke thin"/>
    <circle cx="-17" cy="-5" r="4.5"/><circle cx="17" cy="-5" r="4.5"/>
    <path d="M-16 18 Q-6 10 2 18 T18 16" class="stroke"/>
    <path d="M4 20 q6 12 12 0 z" fill="#fff" opacity=".8" stroke="none"/>`,
};

/** Devuelve el contenido SVG de una carita, centrada en 0,0 y de radio 50. */
function faceMarkup(key) {
  const emotion = Emotions[key];
  return `
    <circle r="48" fill="${emotion.color}" stroke="${INK}" stroke-width="3.5"/>
    <g fill="${INK}" stroke="${INK}" class="face-parts">${FACE_PARTS[key]}</g>`;
}

const FACE_STYLE = `
  .face-parts .stroke{fill:none;stroke-width:5;stroke-linecap:round;stroke-linejoin:round}
  .face-parts .thin{stroke-width:4}
  .face-parts circle,.face-parts ellipse{stroke:none}`;

/** Rellena cada <span data-face="alegria"> con su carita. */
function mountFaces() {
  document.querySelectorAll("[data-face]").forEach((el) => {
    el.innerHTML = `<svg viewBox="-52 -52 104 104" role="img" aria-label="${Emotions[el.dataset.face].name}">
      <style>${FACE_STYLE}</style>${faceMarkup(el.dataset.face)}</svg>`;
  });
}
