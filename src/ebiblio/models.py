"""Modelos inmutables de datos devueltos por el cliente."""

from typing import NamedTuple


class Medium(NamedTuple):
    """Una edición o medio disponible para un recurso del catálogo."""

    format: str
    quality: str | None = None
    availability: str | None = None
    availability_count: int | None = None
    borrow_url: str | None = None
    streaming: bool = False
    accessible: bool = False


class Contributor(NamedTuple):
    """Colaborador asociado a un recurso y sus nombres."""

    role: str
    names: tuple[str, ...]


class SearchResult(NamedTuple):
    """Un libro, película u otro recurso del catálogo."""

    title: str
    url: str
    resource_type: str | None = None
    resource_id: str | None = None
    cover_url: str | None = None
    description: str | None = None
    contributors: tuple[Contributor, ...] = ()
    media: tuple[Medium, ...] = ()

    @property
    def authors(self) -> tuple[str, ...]:
        """Devuelve los colaboradores etiquetados como autor."""
        return next(
            (
                contributor.names
                for contributor in self.contributors
                if contributor.role == "autor"
            ),
            (),
        )


class SearchResults(NamedTuple):
    """Página de resultados e información para continuar la paginación."""

    items: tuple[SearchResult, ...]
    current_page: int = 1
    page_numbers: tuple[int, ...] = ()
    next_page_url: str | None = None
