import pytest

from emotions.text import (
    content_lemmas,
    is_no_response,
    label_feeling,
    normalize,
    tokenize,
)


def test_normalize_quita_tildes_y_conserva_la_enie():
    assert normalize("  ¿Qué  es la ALEGRÍA, niño? ") == "¿que es la alegria, niño?"


def test_tokenize_solo_palabras():
    assert tokenize("Me pegan, por no estar en la casa.") == [
        "me", "pegan", "por", "no", "estar", "en", "la", "casa",
    ]  # fmt: skip


@pytest.mark.parametrize("text", ["No sabe", "No sé.", "no se", "No responde", "", None, "MMMMM"])
def test_is_no_response(text):
    assert is_no_response(text)


@pytest.mark.parametrize("text", ["No me dejan jugar", "Nada me da miedo", "Mi familia."])
def test_respuestas_validas_no_son_sin_respuesta(text):
    assert not is_no_response(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Feliz, porque estoy en la escuela.", "alegria"),
        ("Querida, porque mi mamá me quiere.", "carino"),
        ("Camlado porque vengo al colegio.", "calma"),
        ("Tranquilo, mamá me deja dormir.", "calma"),
        ("Asustado, porque él me empujó.", "miedo"),
        ("Bravo, porque no me dejaron jugar.", "enojo"),
        ("Sorprendida, porque ya sé montar bicicleta.", "sorpresa"),
        ("Bien, porque sí.", "bien"),
        ("Bien, querida, porque me gusta estar aquí.", "carino"),
        ("No sé.", "sin_respuesta"),
        ("Con sueño.", "otro"),
    ],
)
def test_label_feeling(text, expected):
    assert label_feeling(text) == expected


def test_label_feeling_prioriza_lo_que_va_antes_del_porque():
    # La emoción nombrada es la calma; "pega" está en la explicación.
    assert label_feeling("Calmado, porque nadie me pega y no estoy triste.") == "calma"


def test_content_lemmas_descarta_vacias_y_eco():
    lemmas = [lemma for lemma, _ in content_lemmas("Me siento feliz cuando como pastel.")]
    assert "pastel" in lemmas
    assert not {"me", "siento", "feliz", "cuando"} & set(lemmas)
