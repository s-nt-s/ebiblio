"""Cliente HTTP de solo lectura para búsquedas en catálogos eBiblio."""

from __future__ import annotations

from http.cookiejar import CookieJar
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener

from .models import SearchResult, SearchResults
from .parser import parse_search_results


class EbiblioError(Exception):
    """Error de red o de respuesta del catálogo."""


class EbiblioClient:
    """Busca recursos en un sitio compatible con el catálogo eBiblio.

    Ejemplo::

        client = EbiblioClient("https://madrid.ebiblio.es/")
        results = client.search("Mabuse", language="spa", nature="ebook")
        for item in results.items:
            print(item.title, item.authors, item.url)
    """

    _search_fields = {
        "isbn",
        "author",
        "narrator",
        "director",
        "actor",
        "publisher",
        "collection_title",
        "issued_on_range",
        "language",
        "audience",
        "category",
        "nature",
        "medium",
        "availability",
        "category_standard",
        "sort_by",
    }

    def __init__(
        self,
        url: str,
        *,
        timeout: float = 20.0,
        user_agent: str = "ebiblio-client/0.1 (+https://www.python.org/)",
    ) -> None:
        parsed = urlsplit(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("La URL debe ser absoluta y usar http o https.")
        if timeout <= 0:
            raise ValueError("timeout debe ser mayor que cero.")
        self.base_url = urlunsplit((parsed.scheme, parsed.netloc, "/", "", ""))
        self.timeout = timeout
        self.user_agent = user_agent
        self._cookies = CookieJar()
        self._opener = build_opener(HTTPCookieProcessor(self._cookies))

    def _fetch(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (HTTPError, URLError, OSError) as exc:
            raise EbiblioError(f"No se pudo consultar {url}: {exc}") from exc

    def search(
        self,
        keywords: str = "",
        *,
        page: int = 1,
        **filters: Any,
    ) -> SearchResults:
        """Ejecuta una búsqueda y devuelve los recursos de la página indicada.

        Los filtros aceptan los nombres del formulario web (por ejemplo,
        ``author``, ``language``, ``category``, ``nature``, ``medium`` y
        ``availability``). También se admite ``q`` como alias de ``keywords``.
        """
        if page < 1:
            raise ValueError("page debe ser un entero positivo.")
        if "q" in filters:
            if keywords:
                raise TypeError("Usa keywords o q, pero no ambos.")
            keywords = filters.pop("q")

        unknown = set(filters) - self._search_fields
        if unknown:
            fields = ", ".join(sorted(unknown))
            raise TypeError(f"Filtros no reconocidos: {fields}")

        params: dict[str, str] = {
            "category_standard": "ebiblio",
            "page": str(page),
        }
        if keywords:
            params["keywords"] = str(keywords)
        for name, value in filters.items():
            if value is None or value is False:
                continue
            if name == "availability" and value is True:
                params[name] = "available"
            else:
                params[name] = str(value)

        search_url = urljoin(self.base_url, "/resources")
        request_url = f"{search_url}?{urlencode(params)}"
        html = self._fetch(request_url)
        parsed = parse_search_results(html, self.base_url)
        next_page_url = parsed.next_page_url
        return SearchResults(
            items=parsed.items,
            current_page=(
                parsed.current_page
                if parsed.current_page > 1 or page == 1
                else page
            ),
            page_numbers=parsed.page_numbers,
            next_page_url=next_page_url,
        )

    def search_all(
        self,
        keywords: str = "",
        *,
        max_pages: int = 100,
        **filters: Any,
    ) -> list[SearchResult]:
        """Recorre páginas siguientes hasta el final o ``max_pages``."""
        if max_pages < 1:
            raise ValueError("max_pages debe ser un entero positivo.")
        results: list[SearchResult] = []
        page = 1
        while page <= max_pages:
            current = self.search(keywords, page=page, **filters)
            results.extend(current.items)
            if not current.next_page_url:
                break
            next_page = parse_qs(
                urlsplit(current.next_page_url).query
            ).get("page", [])
            page = (
                int(next_page[0])
                if next_page and next_page[0].isdigit()
                else page + 1
            )
        return results
