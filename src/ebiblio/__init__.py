"""Cliente de búsqueda para catálogos web basados en eBiblio."""

from .client import EbiblioClient, EbiblioError
from .models import Contributor, Medium, SearchQuery, SearchResult
from .models import SearchResults

__all__ = [
 "EbiblioClient",
 "EbiblioError",
 "Contributor",
 "SearchQuery",
 "Medium",
 "SearchResult",
 "SearchResults",
]
