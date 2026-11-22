"""Interfaz de línea de comandos para ebiblio-client."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
from typing import Sequence

from .client import EbiblioClient, EbiblioError
from .models import SearchResult


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ebiblio",
        description=(
            "Busca libros, películas y otros recursos "
            "en un catálogo eBiblio."
        ),
    )
    parser.add_argument(
        "url",
        help="URL del catálogo (p. ej. https://madrid.ebiblio.es/)",
    )
    parser.add_argument(
        "keywords",
        nargs="?",
        default="",
        help="Palabras clave",
    )
    parser.add_argument(
        "--page", type=int, default=1, help="Página que se consultará"
    )
    parser.add_argument(
        "--all",
        dest="all_pages",
        action="store_true",
        help="Recorrer todas las páginas",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Límite de páginas para --all",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Tiempo máximo de espera en segundos",
    )

    parser.add_argument("--isbn")
    parser.add_argument("--author")
    parser.add_argument("--narrator")
    parser.add_argument("--director")
    parser.add_argument("--actor")
    parser.add_argument("--publisher")
    parser.add_argument("--collection-title")
    parser.add_argument("--issued-on-range")
    parser.add_argument("--language")
    parser.add_argument("--audience")
    parser.add_argument("--category")
    parser.add_argument("--category-standard")
    parser.add_argument("--nature")
    parser.add_argument("--medium")
    parser.add_argument("--sort-by")
    parser.add_argument(
        "--available",
        action="store_true",
        help="Limitar a títulos disponibles",
    )
    parser.add_argument(
        "--json", action="store_true", help="Imprimir resultados como JSON"
    )
    return parser


def _filters_from_args(args: argparse.Namespace) -> dict[str, object]:
    filters = {
        "isbn": args.isbn,
        "author": args.author,
        "narrator": args.narrator,
        "director": args.director,
        "actor": args.actor,
        "publisher": args.publisher,
        "collection_title": args.collection_title,
        "issued_on_range": args.issued_on_range,
        "language": args.language,
        "audience": args.audience,
        "category": args.category,
        "category_standard": args.category_standard,
        "nature": args.nature,
        "medium": args.medium,
        "sort_by": args.sort_by,
    }
    selected = {
        name: value
        for name, value in filters.items()
        if value is not None
    }
    if args.available:
        selected["availability"] = True
    return selected


def _print_result(item: SearchResult, index: int) -> None:
    kind = item.resource_type or "Recurso"
    print(f"{index}. {item.title} [{kind}]")
    print(f"   {item.url}")
    for role, names in item.contributors.items():
        print(f"   {role.capitalize()}: {', '.join(names)}")
    if item.description:
        print(f"   {item.description}")
    for medium in item.media:
        details = [medium.format or "Medio"]
        if medium.quality:
            details.append(medium.quality)
        if medium.availability:
            details.append(medium.availability)
        print(f"   Medio: {' — '.join(details)}")


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada del comando `ebiblio`."""
    args = _build_parser().parse_args(argv)
    filters = _filters_from_args(args)
    try:
        client = EbiblioClient(args.url, timeout=args.timeout)
        if args.all_pages:
            items = client.search_all(
                args.keywords,
                max_pages=args.max_pages,
                **filters,
            )
            page_result = None
        else:
            page_result = client.search(
                args.keywords,
                page=args.page,
                **filters,
            )
            items = page_result.items
    except (EbiblioError, TypeError, ValueError) as exc:
        print(f"ebiblio: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload: dict[str, object] = {
            "items": [asdict(item) for item in items]
        }
        if page_result is not None:
            payload.update(
                current_page=page_result.current_page,
                page_numbers=page_result.page_numbers,
                next_page_url=page_result.next_page_url,
            )
        else:
            payload["all_pages"] = True
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not items:
        print("No se encontraron recursos.")
    else:
        for index, item in enumerate(items, start=1):
            _print_result(item, index)
    if page_result and page_result.next_page_url:
        print(f"Página siguiente: {page_result.next_page_url}")
    if args.all_pages:
        print(f"Total de recursos recuperados: {len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
