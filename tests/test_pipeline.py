"""Prueba el recorrido Excel -> agregados con un libro pequeño inventado."""

import pandas as pd
import pytest

from emotions import analysis, io
from emotions.datasets import emotion_of


@pytest.fixture
def workbook(tmp_path):
    path = tmp_path / "registro.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame(
            {
                "ID": [1, 2, 3, 4],
                "CUESTIONARIO": ["X"] * 4,
                "NUM": [1, 1, 2, 2],
                "Preg": ["¿Qué es la alegria?"] * 2 + ["¿Qué es el miedo?"] * 2,
                "Res": ["Jugar en el parque.", "No sabe", "La oscuridad.", "Las arañas."],
            }
        ).to_excel(writer, sheet_name="larga", index=False)
        pd.DataFrame(
            [
                ["RESULTADOS", None, None],
                ["RESPUESTA", "¿Qué es la alegria?", "¿Qué es el enojo?"],
                ["1", "Mi mamá.", "Que me peguen."],
                ["2", "No se.", None],
            ]
        ).to_excel(writer, sheet_name="ancha", index=False, header=False)
        pd.DataFrame(
            [
                ["COMO ME SIENTO HOY…", None, None],
                ["RESPUESTA 1", "Feliz, porque sí.", None],
                [" ", "RESPUESTA 2", "Bien."],
            ]
        ).to_excel(writer, sheet_name="lista", index=False, header=False)
    return path


def test_read_long(workbook):
    df = io.read_long(workbook, "larga")
    assert list(df.columns) == ["pregunta", "respuesta"]
    assert len(df) == 4


def test_read_wide_omite_celdas_vacias(workbook):
    df = io.read_wide(workbook, "ancha")
    assert len(df) == 3
    assert set(df["pregunta"]) == {"¿Qué es la alegria?", "¿Qué es el enojo?"}


def test_read_list_tolera_columnas_corridas(workbook):
    df = io.read_list(workbook, "lista", "¿Cómo me siento hoy?")
    assert df["respuesta"].tolist() == ["Feliz, porque sí.", "Bien."]


def test_emotion_of():
    assert emotion_of("¿Qué es la felicidad?") == "alegria"
    assert emotion_of("¿Qué es el enojo?") == "enojo"
    assert emotion_of("¿Cuántos años tienes?") is None


def test_definitions_by_emotion(workbook):
    df = io.read_long(workbook, "larga")
    df = df.assign(emocion=df["pregunta"].map(emotion_of))
    out = analysis.definitions_by_emotion(df)
    assert out["alegria"]["n"] == 2
    assert out["alegria"]["sin_respuesta"] == 1
    assert out["alegria"]["pct_sin_respuesta"] == 50.0
    assert {w["w"] for w in out["miedo"]["palabras"]} >= {"oscuridad"}
    assert "enojo" not in out  # sin respuestas -> no se reporta


def test_feelings_by_session():
    df = pd.DataFrame(
        {
            "registro": [1, 1, 2, 2],
            "respuesta": ["Bien.", "Bien, porque sí.", "Feliz.", "Calmado, porque juego."],
        }
    )
    first, second = analysis.feelings_by_session(df)
    assert first["pct_nombra_emocion"] == 0.0
    assert second["pct_nombra_emocion"] == 100.0
    assert second["emociones_distintas"] == 2


def test_situations_matrix_conserva_el_orden_del_test():
    df = pd.DataFrame(
        {
            "pregunta": ["Veo una araña.", "Juego en el parque", "Veo una araña."],
            "respuesta": ["Miedo", "Felicidad", "No responde"],
        }
    )
    out = analysis.situations_matrix(df)
    assert out["situaciones"] == ["Veo una araña.", "Juego en el parque"]
    assert out["emociones"] == ["alegria", "miedo", "sin_respuesta"]
    assert out["conteo"] == [[0, 1, 1], [1, 0, 0]]
