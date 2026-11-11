"""Limpieza de texto, lematización y léxico de emociones.

El cuaderno original usaba NLTK + spaCy. Aquí la tokenización y las palabras vacías
no dependen de descargas externas; spaCy es opcional y solo aporta lema y
categoría gramatical. Sin spaCy, el análisis corre con las palabras tal cual.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache

from .config import GENERIC, NO_RESPONSE, OTHER

_WORD = re.compile(r"[a-záéíóúüñ]+", re.IGNORECASE)

# Palabras vacías del español (lista de NLTK) + muletillas del habla infantil.
STOPWORDS: frozenset[str] = frozenset(
    """
    a al algo algunas algunos ante antes como con contra cual cuando de del desde donde
    durante e el ella ellas ellos en entre era erais eran eras eres es esa esas ese eso esos
    esta estaba estabais estaban estabas estad estada estadas estado estados estamos estando
    estar estaremos estará estarán estarás estaré estaréis estaría estaríais estaríamos
    estarían estarías estas este estemos esto estos estoy estuve estuviera estuvierais
    estuvieran estuvieras estuvieron estuviese estuvieseis estuviesen estuvieses estuvimos
    estuviste estuvisteis estuvo está estábamos estáis están estás esté estéis estén estés
    fue fuera fuerais fueran fueras fueron fuese fueseis fuesen fueses fui fuimos fuiste
    fuisteis ha habida habidas habido habidos habiendo habremos habrá habrán habrás habré
    habréis habría habríais habríamos habrían habrías habéis había habíais habíamos habían
    habías han has hasta hay haya hayamos hayan hayas hayáis he hemos hube hubiera hubierais
    hubieran hubieras hubieron hubiese hubieseis hubiesen hubieses hubimos hubiste hubisteis
    hubo la las le les lo los me mi mis mucho muchos muy más mí mía mías mío míos nada ni no
    nos nosotras nosotros nuestra nuestras nuestro nuestros o os otra otras otro otros para
    pero poco por porque que quien quienes qué se sea seamos sean seas seremos será serán
    serás seré seréis sería seríais seríamos serían serías seáis sido siendo sin sobre sois
    somos son soy su sus suya suyas suyo suyos sí también tanto te tendremos tendrá tendrán
    tendrás tendré tendréis tendría tendríais tendríamos tendrían tendrías tened tenemos
    tenga tengamos tengan tengas tengo tengáis tenida tenidas tenido tenidos teniendo tenéis
    tenía teníais teníamos tenían tenías ti tiene tienen tienes todo todos tu tus tuve
    tuviera tuvierais tuvieran tuvieras tuvieron tuviese tuvieseis tuviesen tuvieses tuvimos
    tuviste tuvisteis tuvo tuya tuyas tuyo tuyos tú un una uno unos vosotras vosotros
    vuestra vuestras vuestro vuestros y ya yo él éramos
    ser haber tener si ahí así hoy vez cosa cosas conmigo algún algun ningún ningun alguien
    """.split()
)

# Palabras que solo repiten la pregunta ("Me siento feliz cuando…", "Me da miedo…").
# Se excluyen de las frecuencias para que aparezca lo que el niño aporta.
ECHO_WORDS: frozenset[str] = frozenset(
    """
    sentir siento siente poner pone dar da cuando
    feliz felicidad alegre alegría alegria triste tristeza enojado enojada enojo enojar
    enoja miedo asustar asusta calma emoción emocion
    """.split()
)

# Correcciones a lemas que el modelo pequeño de spaCy resuelve mal en habla infantil.
LEMMA_FIXES: dict[str, str] = {
    "comar": "comer",
    "comiar": "comer",
    "peleir": "pelear",
    "peguir": "pegar",
    "compartar": "compartir",
    "olvidir": "olvidar",
    "gutar": "gustar",
    "guta": "gustar",
    "mandaar": "mandar",
    "hecer": "hacer",
    "papas": "papá",
    "papa": "papá",
    "papás": "papá",
    "papi": "papá",
    "mama": "mamá",
    "mami": "mamá",
    "profe": "profesora",
    "amiguita": "amiga",
    "amigüita": "amiga",
    "amiguito": "amigo",
    "juego": "jugar",
    "compran": "comprar",
    "regaño": "regañar",
    "regaña": "regañar",
    "regañir": "regañar",
    "comprir": "comprar",
    "prestir": "prestar",
    "lastimir": "lastimar",
    "rasguñir": "rasguñar",
    "abracir": "abrazar",
    "asuatar": "asustar",
    "serpient": "serpiente",
    "juguet": "juguete",
    "juget": "juguete",
    "tenebrós": "tenebroso",
    "venenós": "venenoso",
    "peleen": "pelear",
    "deje": "dejar",
    "monstuo": "monstruo",
    "regaalo": "regalo",
    "caritar": "carita",
    "afuero": "afuera",
    "cumpleaño": "cumpleaños",
    "zombies": "zombi",
    "pelicula": "película",
    "peliculas": "película",
    "monto": "montar",
    "etudie": "estudiar",
    "almorzary": "almorzar",
    "canasado": "cansado",
    "soñe": "soñar",
    "ayudo": "ayudar",
    "bici": "bicicleta",
    "tele": "televisión",
    "hermanito": "hermano",
    "solito": "solo",
    "brava": "bravo",
    "fantasmaviene": "fantasma",
    "halo": "halar",
    "dia": "día",
    "calzoncil": "calzoncillo",
    "trist": "triste",
}

# Categoría gramatical corregida para lemas frecuentes que el modelo confunde.
POS_FIXES: dict[str, str] = {
    **dict.fromkeys(
        """mamá papá helado momia culebra serpiente cometa muñeca bebé dulce zapato
        soñar bravo""".split(),
        "NOUN",
    ),
    **dict.fromkeys("jugar temblar quieto".split(), "VERB"),
    "bravo": "ADJ",
    "quieto": "ADJ",
    "soñar": "VERB",
}

# Formas habituales de no responder.
_NO_RESPONSE = re.compile(
    r"^\s*(no\s+(se|sabe|responde|contesta|reconoce|quiso|dice|respondio)\b|nada\s*$|m+\s*$)"
)

# Léxico para reconocer qué emoción nombra un niño al decir cómo se siente.
# Se compara contra el texto sin tildes y en minúscula; gana la primera coincidencia.
_EMOTION_LEXICON: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("carino", re.compile(r"\b(querid|carin|cario|amad|consentid)")),
    ("calma", re.compile(r"\b(calm|caml|tranquil|relajad)")),
    ("sorpresa", re.compile(r"\b(sorpr|asombr)")),
    ("miedo", re.compile(r"\b(miedo|asust|temor|nervios)")),
    ("enojo", re.compile(r"\b(enoj|brav|furios|rabia|molest|mal\s*genio)")),
    ("tristeza", re.compile(r"\b(trist|llor|aburrid|solit)")),
    ("alegria", re.compile(r"\b(feliz|felic|alegr|content|emocionad|dichos)")),
    ("asco", re.compile(r"\b(asco|asquer|asquead)")),
    (GENERIC, re.compile(r"\b(bien|normal|rico|super|chevere)\b")),
)


def strip_accents(text: str) -> str:
    """Quita tildes y diéresis conservando la ñ."""
    text = text.replace("ñ", "\0").replace("Ñ", "\1")
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return text.replace("\0", "ñ").replace("\1", "Ñ")


def normalize(text: object) -> str:
    """Texto en minúscula, sin tildes y con espacios simples."""
    return re.sub(r"\s+", " ", strip_accents(str(text or "")).lower()).strip()


def tokenize(text: object) -> list[str]:
    """Palabras alfabéticas en minúscula (conserva tildes)."""
    return [w.lower() for w in _WORD.findall(str(text or ""))]


def is_no_response(text: object) -> bool:
    """¿La respuesta es un "No sé / No responde" o está vacía?"""
    norm = normalize(text)
    return not norm or bool(_NO_RESPONSE.match(norm))


def label_feeling(text: object) -> str:
    """Clasifica una respuesta a "¿Cómo me siento hoy?" según la emoción que nombra.

    Solo se mira lo que va antes de la explicación ("porque…"), que es donde el
    niño nombra cómo se siente.

    >>> label_feeling("Querida, porque mi mamá me quiere.")
    'carino'
    >>> label_feeling("Bien, porque sí.")
    'bien'
    """
    if is_no_response(text):
        return NO_RESPONSE
    norm = normalize(text)
    head = re.split(r"\bporque\b|\bpor que\b|\bcuando\b", norm, maxsplit=1)[0] or norm
    for scope in (head, norm):
        for key, pattern in _EMOTION_LEXICON:
            if pattern.search(scope):
                return key
    return OTHER


def _lower_sentence_starts(text: str) -> str:
    """Pone en minúscula la primera letra de cada oración.

    Así "Jugar con mi mamá" no se etiqueta como nombre propio, mientras que los
    nombres a mitad de frase siguen en mayúscula y se descartan (anonimato).
    """
    return re.sub(r"(^|[.!?¡¿]\s*)([A-ZÁÉÍÓÚÑ])", lambda m: m.group(1) + m.group(2).lower(), text)


@dataclass(frozen=True)
class Token:
    text: str
    lemma: str
    pos: str  # NOUN, VERB, ADJ… o "X" si no hay modelo


@lru_cache(maxsize=1)
def _load_spacy():
    try:
        import spacy

        return spacy.load("es_core_news_sm", disable=["ner", "parser"])
    except Exception:  # spaCy o el modelo no están instalados
        return None


def has_nlp_model() -> bool:
    return _load_spacy() is not None


def analyze(text: object) -> list[Token]:
    """Tokeniza y, si spaCy está disponible, lematiza y etiqueta."""
    nlp = _load_spacy()
    if nlp is None:
        return [Token(w, LEMMA_FIXES.get(w, w), "X") for w in tokenize(text)]
    tokens = []
    for tok in nlp(_lower_sentence_starts(str(text or ""))):
        if not tok.is_alpha:
            continue
        lemma = tok.lemma_.lower().split()[0]  # "dar él" -> "dar"
        lemma = LEMMA_FIXES.get(lemma, LEMMA_FIXES.get(tok.text.lower(), lemma))
        tokens.append(Token(tok.text, lemma, POS_FIXES.get(lemma, tok.pos_)))
    return tokens


CONTENT_POS = frozenset({"NOUN", "VERB", "ADJ", "X"})


def content_lemmas(text: object, *, drop_echo: bool = True) -> list[tuple[str, str]]:
    """Lemas con significado de una respuesta, como pares ``(lema, categoría)``.

    Se descartan palabras vacías, nombres propios (anonimato) y, por defecto,
    las palabras eco de la pregunta.
    """
    out = []
    for tok in analyze(text):
        lemma = tok.lemma
        if tok.pos not in CONTENT_POS or len(lemma) < 3:
            continue
        if lemma in STOPWORDS or tok.text.lower() in STOPWORDS:
            continue
        if drop_echo and (lemma in ECHO_WORDS or tok.text.lower() in ECHO_WORDS):
            continue
        out.append((lemma, tok.pos))
    return out


def count_words(texts: Iterable[object]) -> list[int]:
    """Número de palabras de cada respuesta."""
    return [len(tokenize(t)) for t in texts]
