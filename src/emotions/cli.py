"""Línea de comandos: ``emotions <comando>``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, site_data
from .config import get_paths
from .text import has_nlp_model


def _cmd_build(args: argparse.Namespace) -> int:
    paths = get_paths(args.root)
    if not paths.raw.exists():
        print(f"No encuentro los datos originales en {paths.raw}", file=sys.stderr)
        print("Lee data/README.md para saber dónde descomprimirlos.", file=sys.stderr)
        return 1
    if not has_nlp_model():
        print(
            "Aviso: spaCy/es_core_news_sm no está instalado; se cuentan palabras sin lematizar.\n"
            '        pip install -e ".[nlp]" && python -m spacy download es_core_news_sm',
            file=sys.stderr,
        )
    for output in site_data.write(paths):
        print(f"✓ {output.relative_to(paths.root)}")
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    paths = get_paths(args.root)
    print(f"emotions {__version__}")
    print(f"raíz:            {paths.root}")
    print(f"datos originales: {paths.raw} ({'ok' if paths.raw.exists() else 'NO ENCONTRADOS'})")
    print(f"modelo spaCy:    {'ok' if has_nlp_model() else 'no instalado'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # consola de Windows
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="emotions", description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="raíz del repositorio")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "build-site-data", help="recalcula docs/data y data/processed desde data/raw"
    ).set_defaults(func=_cmd_build)
    sub.add_parser("info", help="muestra rutas y estado del entorno").set_defaults(func=_cmd_info)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
