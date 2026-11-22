"""Modelos de datos devueltos por el cliente."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Medium:
    """Una edición o medio disponible para un recurso del catálogo."""

    format: str
    quality: str | None = None
    availability: str | None = None
    availability_count: int | None = None
    borrow_url: str | None = None
    streaming: bool = False
    accessible: bool = False


@dataclass(frozen=True)
class SearchResult:
    """Un libro, película u otro recurso del catálogo."""

    title: str
    url: str
    resource_type: str | None = None
    resource_id: str | None = None
    cover_url: str | None = None
    description: str | None = None
    contributors: dict[str, list[str]] = field(default_factory=dict)
    media: list[Medium] = field(default_factory=list)

    @property
    def authors(self) -> list[str]:
        """Devuelve los colaboradores etiquetados como autor."""
        return self.contributors.get("autor", [])


@dataclass(frozen=True)
class SearchResults:
    """Página de resultados e información para continuar la paginación."""

    items: list[SearchResult]
    current_page: int = 1
    page_numbers: list[int] = field(default_factory=list)
    next_page_url: str | None = None
