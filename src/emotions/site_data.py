"""Genera los datos que consume el sitio web (``docs/data/resultados.json``).

Este es el punto de encuentro entre la investigación y la página: para publicar
un resultado nuevo se agrega aquí una clave y en ``docs/assets/js`` su gráfico.
"""

from __future__ import annotations

import json
from datetime import date

import pandas as pd

from . import analysis, datasets
from .config import EMOTIONS, GENERIC, NO_RESPONSE, OTHER, Paths
from .text import has_nlp_model

COHORTS = (
    ("2024_antes", "2024 · Antes de los talleres", datasets.definiciones_2024_antes),
    ("2024_despues", "2024 · Después de los talleres", datasets.definiciones_2024_despues),
    ("2025_inicio", "2025 · Inicio de Emociones 2.0", datasets.definiciones_2025_inicio),
)


def build(paths: Paths) -> dict:
    """Calcula todos los agregados que publica el sitio."""
    definiciones = []
    for key, label, loader in COHORTS:
        df = loader(paths)
        definiciones.append(
            {
                "clave": key,
                "nombre": label,
                "total": analysis.response_summary(df["respuesta"]),
                "emociones": analysis.definitions_by_emotion(df),
            }
        )

    return {
        "generado": date.today().isoformat(),
        "lematizado": has_nlp_model(),
        "emociones": [
            {"clave": e.key, "nombre": e.label, "color": e.color} for e in EMOTIONS
        ],
        "categorias_extra": {
            GENERIC: 'Genérico ("Bien")',
            NO_RESPONSE: "Sin respuesta",
            OTHER: "Otra respuesta",
        },
        "definiciones": definiciones,
        "como_me_siento_2025": analysis.feelings_by_session(datasets.como_me_siento_2025(paths)),
        "situaciones_2025": analysis.situations_matrix(datasets.situaciones_2025(paths)),
    }


def write(paths: Paths) -> list:
    """Escribe el JSON del sitio y las tablas de ``data/processed``. Devuelve las rutas."""
    data = build(paths)
    paths.site_data.mkdir(parents=True, exist_ok=True)
    paths.processed.mkdir(parents=True, exist_ok=True)

    site_json = paths.site_data / "resultados.json"
    site_json.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    words = pd.DataFrame(
        [
            {"cohorte": c["clave"], "emocion": emo, "lema": w["w"], "pos": w["pos"], "n": w["n"]}
            for c in data["definiciones"]
            for emo, info in c["emociones"].items()
            for w in info["palabras"]
        ]
    )
    feelings = pd.DataFrame(
        [
            {"registro": s["registro"], "etiqueta": k, "n": v}
            for s in data["como_me_siento_2025"]
            for k, v in s["conteo"].items()
        ]
    )
    sit = data["situaciones_2025"]
    situations = pd.DataFrame(sit["conteo"], index=sit["situaciones"], columns=sit["emociones"])

    outputs = [site_json]
    for name, table, index in (
        ("frecuencia_palabras.csv", words, False),
        ("como_me_siento_2025.csv", feelings, False),
        ("situaciones_2025.csv", situations.rename_axis("situacion"), True),
    ):
        target = paths.processed / name
        table.to_csv(target, index=index, encoding="utf-8", lineterminator="\n")
        outputs.append(target)
    return outputs
