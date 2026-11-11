# Datos

| Carpeta | ¿Se versiona? | Contenido |
|---|---|---|
| `raw/` | **No** (ignorada por git) | Material original del proyecto: Excel de registro, dibujos escaneados, documentos, video. Contiene datos personales de menores de edad. |
| `interim/` | **No** | Tablas intermedias con respuestas textuales (útiles para análisis local). |
| `processed/` | Sí | Solo **agregados anónimos**: frecuencias de palabras, conteos por emoción, etc. |

## Cómo obtener `raw/`

Descomprime la carpeta `PROYECTO EMOCIONES` (Drive de la investigadora) en:

```
data/raw/proyecto_emociones/
├── 2019/
├── 2024/
└── 2025/
```

## Regla de oro

Nada que permita identificar a un niño o niña (nombre, foto, voz, dibujo firmado,
relato textual de su vida familiar) sale de `raw/`. El sitio web se alimenta únicamente
de `docs/data/*.json`, generados por `emotions build-site-data` a partir de agregados.
