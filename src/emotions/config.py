"""Rutas del proyecto y catálogo de emociones.

Todo lo que el resto del paquete necesita saber sobre *dónde* están las cosas
y *cuáles* emociones se estudian vive aquí.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def find_root(start: Path | None = None) -> Path:
    """Devuelve la raíz del repositorio (la carpeta que contiene ``pyproject.toml``).

    Se puede forzar con la variable de entorno ``EMOTIONS_ROOT``.
    """
    env = os.environ.get("EMOTIONS_ROOT")
    if env:
        return Path(env).resolve()
    here = (start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        if (folder / "pyproject.toml").exists():
            return folder
    return here


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw" / "proyecto_emociones"

    @property
    def interim(self) -> Path:
        return self.root / "data" / "interim"

    @property
    def processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def site_data(self) -> Path:
        return self.root / "docs" / "data"

    # --- Fuentes concretas -------------------------------------------------
    @property
    def analisis_2024(self) -> Path:
        return self.raw / "2024" / "DATOS ANALISIS"

    @property
    def registro_2025(self) -> Path:
        return (
            self.raw
            / "2025"
            / "DATOS_2025_REGISTRO DE EXPRESIONES EMOCIONALES"
            / "REGISTRO DE EMOCIONES 2025_V1.xlsx"
        )


def get_paths(root: Path | None = None) -> Paths:
    return Paths(root or find_root())


@dataclass(frozen=True)
class Emotion:
    key: str
    label: str
    color: str  # color de relleno para gráficos (ver docs/assets/css/styles.css)


# El orden define el orden en leyendas y gráficos.
EMOTIONS: tuple[Emotion, ...] = (
    Emotion("alegria", "Alegría", "#F5B700"),
    Emotion("tristeza", "Tristeza", "#3B82C4"),
    Emotion("enojo", "Enojo", "#E5484D"),
    Emotion("miedo", "Miedo", "#7C5CBF"),
    Emotion("calma", "Calma", "#2FA36B"),
    Emotion("sorpresa", "Sorpresa", "#F2811D"),
    Emotion("carino", "Cariño", "#E36BA8"),
    Emotion("asco", "Asco", "#8A9A2B"),
)

EMOTION_KEYS = tuple(e.key for e in EMOTIONS)

# Categorías que no son emociones pero aparecen al clasificar respuestas.
GENERIC = "bien"  # "Bien", "normal": respuesta genérica, sin nombrar una emoción
NO_RESPONSE = "sin_respuesta"  # "No sé", "No responde"
OTHER = "otro"
