# Nuestras Emociones 2.0

Investigación sobre cómo niños y niñas de preescolar (5 y 6 años) **reconocen, nombran y
expresan sus emociones**, y cómo el arte, la literatura infantil y la inteligencia
artificial pueden acompañarlos.

- **Investigadora principal:** Karen Garnica Torres — <karen.garnica.211@secundinamarca.edu.co>
- **Contexto:** grado Transición, Jardín Infantil Mickey (IED Alfonso López Pumarejo), Nemocón, Cundinamarca, Colombia
- **Sitio web:** <https://karengarnica.github.io/emotions/>

Este repositorio contiene el código que convierte los registros de aula en resultados
y el sitio que los publica.

## Cómo fluye la información

```
data/raw/  ──►  emotions build-site-data  ──►  docs/data/resultados.json  ──►  sitio (D3.js)
(Excel de aula,                            └►  data/processed/*.csv
 no se versiona)
```

Para publicar un avance nuevo: se actualizan los Excel en `data/raw/`, se ejecuta el
comando y se hace *commit* de `docs/data/` y `data/processed/`.

## Estructura

```
emotions/
├── src/emotions/          Paquete Python
│   ├── config.py          Rutas y catálogo de emociones (nombres y colores)
│   ├── io.py              Lectores de los tres formatos de Excel de registro
│   ├── datasets.py        Conjuntos de datos del proyecto (2024, 2025…)
│   ├── text.py            Limpieza, lematización y léxico de emociones
│   ├── analysis.py        Medidas: frecuencias, "no sé", emoción nombrada, situaciones
│   ├── site_data.py       Arma el JSON que consume el sitio
│   └── cli.py             Comando `emotions`
├── notebooks/             Cuaderno de análisis de texto (Colab) sin salidas
├── data/
│   ├── raw/               Material original — ignorado por git
│   └── processed/         Agregados anónimos
├── docs/                  Sitio para GitHub Pages (HTML + CSS + D3, sin compilación)
├── tests/                 Pruebas (pytest)
└── .github/workflows/     Integración continua
```

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -e ".[nlp,dev]"
python -m spacy download es_core_news_sm
```

Coloca el material original en `data/raw/proyecto_emociones/` (ver [`data/README.md`](data/README.md)) y luego:

```bash
emotions info                 # revisa rutas y entorno
emotions build-site-data      # regenera docs/data y data/processed
pytest                        # pruebas
ruff check src tests          # estilo
```

Para ver el sitio en local:

```bash
python -m http.server 8000 --directory docs
```

## Publicar en GitHub Pages

En GitHub: **Settings → Pages → Build and deployment → Deploy from a branch**, rama
`main`, carpeta `/docs`. No hay paso de compilación.

## Agregar un resultado nuevo

1. **Datos:** escribe una función en `src/emotions/datasets.py` que lea el nuevo registro.
2. **Medida:** si hace falta, agrega la función de agregación en `analysis.py` (con su prueba).
3. **JSON:** añade la clave en `site_data.build()`.
4. **Gráfico:** dibújalo en `docs/assets/js/charts.js` y llámalo desde `main.js`.

## Privacidad y ética

Los participantes son menores de edad. Por eso:

- `data/raw/` **nunca** se versiona: contiene nombres, dibujos firmados y relatos familiares.
- El sitio y `data/processed/` publican **solo conteos**; no hay respuestas textuales.
- Los nombres propios se descartan del análisis de palabras.
- La participación cuenta con consentimiento informado de las familias.

## Cómo citar

Ver [`CITATION.cff`](CITATION.cff).

## Licencia

Código bajo licencia [MIT](LICENSE). Los materiales pedagógicos y las producciones de
los niños no están cubiertos por esta licencia.
