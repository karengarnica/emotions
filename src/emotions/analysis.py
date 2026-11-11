"""Medidas que se calculan sobre las respuestas.

Todas las funciones devuelven **agregados**: ninguna salida contiene respuestas
textuales ni permite reconstruirlas.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

import pandas as pd

from .config import EMOTION_KEYS, GENERIC, NO_RESPONSE, OTHER
from .text import content_lemmas, count_words, is_no_response, label_feeling, normalize


def word_frequencies(texts: Iterable[object], top: int | None = None) -> list[dict]:
    """Frecuencia de lemas con significado: ``[{"w": lema, "n": veces, "pos": categoría}]``.

    ``pos`` es la categoría gramatical más frecuente con la que apareció el lema.
    """
    counts: Counter[str] = Counter()
    pos_votes: dict[str, Counter[str]] = defaultdict(Counter)
    for text in texts:
        if is_no_response(text):
            continue
        for lemma, pos in content_lemmas(text):
            counts[lemma] += 1
            pos_votes[lemma][pos] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [
        {"w": lemma, "n": n, "pos": pos_votes[lemma].most_common(1)[0][0]}
        for lemma, n in ranked[:top]
    ]


def response_summary(texts: Iterable[object]) -> dict:
    """Cuántas respuestas hay, cuántas son "No sé" y qué tan largas son las demás."""
    texts = list(texts)
    answered = [t for t in texts if not is_no_response(t)]
    lengths = count_words(answered)
    return {
        "n": len(texts),
        "sin_respuesta": len(texts) - len(answered),
        "pct_sin_respuesta": round(100 * (len(texts) - len(answered)) / len(texts), 1)
        if texts
        else 0.0,
        "palabras_promedio": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
    }


def definitions_by_emotion(df: pd.DataFrame, top: int = 40) -> dict[str, dict]:
    """Resumen y palabras más frecuentes por emoción para un cuestionario "¿Qué es…?"."""
    out = {}
    for key in EMOTION_KEYS:
        texts = df.loc[df["emocion"] == key, "respuesta"].tolist()
        if texts:
            out[key] = {**response_summary(texts), "palabras": word_frequencies(texts, top)}
    return out


def feelings_by_session(df: pd.DataFrame) -> list[dict]:
    """Qué emoción nombran los niños en cada registro de "¿Cómo me siento hoy?"."""
    df = df.assign(etiqueta=df["respuesta"].map(label_feeling))
    sessions = []
    for registro, group in df.groupby("registro", sort=True):
        counts = group["etiqueta"].value_counts().to_dict()
        named = [k for k in counts if k in EMOTION_KEYS]
        sessions.append(
            {
                "registro": int(registro),
                "n": int(len(group)),
                "conteo": {k: int(v) for k, v in counts.items()},
                "emociones_distintas": len(named),
                "pct_nombra_emocion": round(100 * sum(counts[k] for k in named) / len(group), 1),
            }
        )
    return sessions


_SITUATION_ANSWER = (
    ("alegria", ("felic", "feliz", "alegr")),
    ("tristeza", ("trist",)),
    ("enojo", ("enoj", "brav", "ira")),
    ("miedo", ("miedo", "asust")),
    ("calma", ("calma", "tranquil")),
    ("sorpresa", ("sorpr",)),
    ("asco", ("asco",)),
    ("carino", ("carin", "querid", "amor")),
)


def _situation_label(answer: object) -> str:
    if is_no_response(answer):
        return NO_RESPONSE
    norm = normalize(answer)
    for key, stems in _SITUATION_ANSWER:
        if any(norm.startswith(s) or f" {s}" in norm for s in stems):
            return key
    return OTHER


def situations_matrix(df: pd.DataFrame) -> dict:
    """Tabla situación × emoción elegida (conteos)."""
    df = df.assign(etiqueta=df["respuesta"].map(_situation_label))
    table = pd.crosstab(df["pregunta"], df["etiqueta"])
    order = [k for k in (*EMOTION_KEYS, OTHER, NO_RESPONSE) if k in table.columns]
    situations = list(dict.fromkeys(df["pregunta"]))  # orden original del test
    return {
        "situaciones": situations,
        "emociones": order,
        "conteo": [[int(table.loc[s, k]) for k in order] for s in situations],
    }


__all__ = [
    "GENERIC",
    "definitions_by_emotion",
    "feelings_by_session",
    "response_summary",
    "situations_matrix",
    "word_frequencies",
]
