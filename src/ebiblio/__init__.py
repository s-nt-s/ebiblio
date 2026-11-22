"""Cliente de búsqueda para catálogos web basados en eBiblio."""

from .client import EbiblioClient, EbiblioError
from .models import Medium, SearchResult, SearchResults

__all__ = [
 "EbiblioClient",
 "EbiblioError",
 "Medium",
 "SearchResult",
 "SearchResults",
]
