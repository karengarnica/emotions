"""Lectura de los Excel de registro.

La investigadora registra las respuestas en tres formas; cada una tiene su lector
y todos devuelven la misma tabla larga: ``pregunta | respuesta``.

- **larga**:  columnas ``ID, CUESTIONARIO, NUM, Preg, Res``
- **ancha**:  una columna por pregunta, una fila por niño
- **lista**:  ``RESPUESTA n | texto`` bajo un título
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .text import normalize

COLUMNS = ["pregunta", "respuesta"]


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df[COLUMNS].copy()
    df["respuesta"] = df["respuesta"].astype("string").str.strip()
    df["pregunta"] = df["pregunta"].astype("string").str.strip()
    df = df[df["respuesta"].notna() & (df["respuesta"] != "")]
    return df.reset_index(drop=True)


def _raw(path: Path, sheet: str | int) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet, header=None, dtype="string")


def sheet_names(path: Path) -> list[str]:
    return pd.ExcelFile(path).sheet_names


def read_long(path: Path, sheet: str | int = 0) -> pd.DataFrame:
    """Hoja con encabezado ``ID, CUESTIONARIO, NUM, Preg, Res``."""
    df = pd.read_excel(path, sheet_name=sheet, dtype="string")
    df.columns = [normalize(c) for c in df.columns]
    missing = {"preg", "res"} - set(df.columns)
    if missing:
        raise ValueError(f"{path.name} [{sheet}] no tiene las columnas {sorted(missing)}")
    return _clean(df.rename(columns={"preg": "pregunta", "res": "respuesta"}))


def _header_row(raw: pd.DataFrame, marker: str) -> int:
    """Índice de la primera fila cuya primera celda con texto empieza por ``marker``."""
    for i, row in raw.iterrows():
        cells = [normalize(c) for c in row.dropna()]
        if cells and cells[0].startswith(marker):
            return int(i)
    raise ValueError(f"No se encontró una fila que empiece por {marker!r}")


def read_wide(path: Path, sheet: str | int = 0, marker: str = "respuesta") -> pd.DataFrame:
    """Hoja con una columna por pregunta (o situación) y una fila por niño."""
    raw = _raw(path, sheet)
    head = _header_row(raw, marker)
    header = raw.iloc[head]
    question_cols = [c for c in raw.columns if pd.notna(header[c])][1:]
    body = raw.iloc[head + 1 :]
    parts = [
        pd.DataFrame({"pregunta": str(header[c]).strip(), "respuesta": body[c]})
        for c in question_cols
    ]
    return _clean(pd.concat(parts, ignore_index=True))


def read_list(path: Path, sheet: str | int = 0, question: str = "") -> pd.DataFrame:
    """Hoja con filas ``RESPUESTA n | texto``. El texto puede estar corrido una columna."""
    raw = _raw(path, sheet)
    answers = []
    for _, row in raw.iterrows():
        cells = [str(c).strip() for c in row.dropna() if str(c).strip()]
        for i, cell in enumerate(cells[:-1]):
            if re.match(r"respuesta\s*\d+", normalize(cell)):
                answers.append(cells[i + 1])
                break
    return _clean(pd.DataFrame({"pregunta": question, "respuesta": answers}))
