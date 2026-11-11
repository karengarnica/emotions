"""Conjuntos de datos del proyecto, ya armados a partir de los Excel originales.

Cada función devuelve una tabla larga lista para analizar. Agregar un nuevo
registro (otro año, otro grupo) consiste en escribir aquí una función más.
"""

from __future__ import annotations

import re

import pandas as pd

from . import io
from .config import Paths
from .text import normalize

# Cómo reconocer la emoción por la que pregunta un "¿Qué es…?".
_QUESTION_EMOTION = (
    ("alegria", r"alegr|felic|feliz"),
    ("tristeza", r"trist"),
    ("miedo", r"miedo|asust"),
    ("enojo", r"enoj"),
    ("calma", r"calma"),
    ("sorpresa", r"sorpres"),
    ("asco", r"asco"),
)


def emotion_of(question: object) -> str | None:
    norm = normalize(question)
    for key, pattern in _QUESTION_EMOTION:
        if re.search(pattern, norm):
            return key
    return None


def _with_emotion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(emocion=df["pregunta"].map(emotion_of))
    return df[df["emocion"].notna()].reset_index(drop=True)


# --- 2024 · Tesis de maestría: literatura infantil y emociones básicas --------


def definiciones_2024_antes(paths: Paths) -> pd.DataFrame:
    """Cuestionario diagnóstico "Represento las emociones": ¿Qué es la alegría…?"""
    path = paths.analisis_2024 / "0 REPRESENTO LAS EMOCIONES.xlsx"
    return _with_emotion(io.read_long(path, "Hoja2"))


def definiciones_2024_despues(paths: Paths) -> pd.DataFrame:
    """Las mismas preguntas después de los talleres literarios (archivos ``… POS``)."""
    frames = [
        io.read_long(path, 0) for path in sorted(paths.analisis_2024.glob("* POS.xlsx"))
    ]
    return _with_emotion(pd.concat(frames, ignore_index=True))


# --- 2025 · Nuestras Emociones 2.0 ------------------------------------------


def definiciones_2025_inicio(paths: Paths) -> pd.DataFrame:
    """Cuestionario "Represento las emociones" aplicado al grupo 2025."""
    return _with_emotion(io.read_wide(paths.registro_2025, "SESION 3 REPRESENTO EMOCIONES"))


_FEELING_SHEET = re.compile(r"como (te sientes|me siento) (\d+)")


def como_me_siento_2025(paths: Paths) -> pd.DataFrame:
    """Registros periódicos de "¿Cómo me siento hoy?" con columna ``registro`` (1…n)."""
    frames = []
    for sheet in io.sheet_names(paths.registro_2025):
        match = _FEELING_SHEET.match(normalize(sheet))
        if not match:
            continue
        df = io.read_list(paths.registro_2025, sheet, "¿Cómo me siento hoy?")
        frames.append(df.assign(registro=int(match.group(2))))
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values("registro", kind="stable").reset_index(drop=True)


def situaciones_2025(paths: Paths) -> pd.DataFrame:
    """Test de situaciones: qué emoción asocia cada niño a una situación cotidiana.

    Aquí ``pregunta`` es la situación y ``respuesta`` la emoción elegida.
    """
    return io.read_wide(paths.registro_2025, "SESION 3 CUESTIONARIO", marker="situacion")
