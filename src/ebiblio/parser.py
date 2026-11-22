"""Parser tolerante para las fichas HTML de resultados eBiblio."""

from __future__ import annotations

from typing import Mapping, NamedTuple
from types import MappingProxyType
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

from .models import Contributor, Medium, SearchResult, SearchResults


class _Node(NamedTuple):
    tag: str
    attrs: Mapping[str, str]
    children: tuple["_Node | str", ...]

    def text(self) -> str:
        parts = []
        for child in self.children:
            value = child if isinstance(child, str) else child.text()
            if value.strip():
                parts.append(value.strip())
        return " ".join(parts)

    def descendants(self, tag: str | None = None):
        if tag is None or self.tag == tag:
            yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.descendants(tag)

    def has_class(self, name: str) -> bool:
        return name in self.attrs.get("class", "").split()


class _TreeParser(HTMLParser):
    _void_tags = {
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node(
            "document",
            MappingProxyType({}),
            (),
        )
        self.stack = [self.root]
        self._child_lists: dict[int, list[_Node | str]] = {id(self.root): []}

    def finish(self) -> _Node:
        """Devuelve el árbol congelado una vez construido."""
        return self._freeze(self.root)

    def _freeze(self, node: _Node) -> _Node:
        children = tuple(
            self._freeze(child) if isinstance(child, _Node) else child
            for child in self._child_lists[id(node)]
        )
        return _Node(node.tag, node.attrs, children)

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        node = _Node(
            tag,
            MappingProxyType({key: value or "" for key, value in attrs}),
            (),
        )
        self._child_lists[id(self.stack[-1])].append(node)
        self._child_lists[id(node)] = []
        if tag not in self._void_tags:
            self.stack.append(node)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self._void_tags:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if data:
            self._child_lists[id(self.stack[-1])].append(data)


def _first(
    node: _Node,
    *,
    tag: str | None = None,
    class_name: str | None = None,
):
    return next(
        (
            item
            for item in node.descendants(tag)
            if class_name is None or item.has_class(class_name)
        ),
        None,
    )


def _absolute(base_url: str, value: str | None) -> str | None:
    return urljoin(base_url, value) if value else None


def _parse_medium(node: _Node, base_url: str) -> Medium:
    heading = _first(node, tag="h4")
    availability_node = _first(node, class_name="availability")
    count_node = _first(node, class_name="count")
    form = _first(node, tag="form")
    quality_node = next(
        (
            item
            for item in node.descendants("small")
            if item.has_class("lb_neutral")
        ),
        None,
    )
    data_sheet = _first(node, class_name="data-sheet")
    data_text = data_sheet.text().casefold() if data_sheet else ""
    count_match = re.search(r"\d+", count_node.text()) if count_node else None

    return Medium(
        format=heading.text().strip() if heading else "",
        quality=quality_node.text().strip() if quality_node else None,
        availability=(
            availability_node.text().strip() if availability_node else None
        ),
        availability_count=int(count_match.group()) if count_match else None,
        borrow_url=(
            _absolute(base_url, form.attrs.get("action")) if form else None
        ),
        streaming="streaming" in data_text,
        accessible=(
            "lectores de pantalla" in data_text or "texto a voz" in data_text
        ),
    )


def _parse_item(article: _Node, base_url: str) -> SearchResult | None:
    heading = _first(article, tag="h3", class_name="details-content__title")
    title = heading.text().strip() if heading else ""
    if not title:
        return None

    title_link = next(
        (
            link
            for link in article.descendants("a")
            if any(child is heading for child in link.descendants())
        ),
        None,
    )
    resource_path = (
        article.attrs.get("itemtype", "")
        .rstrip("/")
        .rsplit("/", 1)[-1]
        or None
    )
    cover = next(
        (
            image
            for image in article.descendants("img")
            if image.has_class("cover")
        ),
        None,
    )
    description_node = _first(
        article, tag="p", class_name="details-content__body"
    )
    contributors: list[Contributor] = []
    details = _first(article, class_name="details-content__adnl-info")
    if details:
        for row in details.descendants():
            if row.tag != "div" or not row.has_class("media"):
                continue
            label_node = next(
                (
                    child
                    for child in row.children
                    if isinstance(child, _Node)
                    and child.has_class("media__img")
                ),
                None,
            )
            contributor_nodes = [
                child
                for child in row.descendants()
                if child.tag == "div" and child.has_class("contributors")
            ]
            if not label_node or not contributor_nodes:
                continue
            label = label_node.text().rstrip(":").strip().casefold()
            names = []
            for contributor in contributor_nodes[0].descendants("a"):
                name = contributor.text().strip()
                if name and name.casefold() != "none" and name not in names:
                    names.append(name)
            if names:
                contributors.append(Contributor(label, tuple(names)))

    media = tuple(
        _parse_medium(node, base_url)
        for node in article.descendants()
        if node.tag == "div"
        and node.has_class("medium")
        and node.has_class("transaction")
    )
    resource_url = title_link.attrs.get("href") if title_link else None
    if not resource_url:
        resource_link = next(
            (
                link
                for link in article.descendants("a")
                if link.attrs.get("href", "").startswith("/resources/")
            ),
            None,
        )
        resource_url = resource_link.attrs.get("href") if resource_link else ""
    resource_id = (
        resource_url.rstrip("/").rsplit("/", 1)[-1]
        if resource_url
        else None
    )

    return SearchResult(
        title=title,
        url=_absolute(base_url, resource_url) or "",
        resource_type=resource_path,
        resource_id=resource_id,
        cover_url=(
            _absolute(base_url, cover.attrs.get("src")) if cover else None
        ),
        description=(
            description_node.text().strip() if description_node else None
        ),
        contributors=tuple(contributors),
        media=media,
    )


def parse_search_results(html: str, base_url: str) -> SearchResults:
    """Convierte HTML del catálogo en modelos Python."""
    parser = _TreeParser()
    parser.feed(html)
    root = parser.finish()
    articles = (
        node
        for node in root.descendants("article")
        if node.has_class("view-details")
    )
    items = tuple(
        item
        for article in articles
        if (item := _parse_item(article, base_url))
    )

    pagination = next(
        (
            node
            for node in root.descendants("nav")
            if node.has_class("pagination")
        ),
        None,
    )
    page_numbers: list[int] = []
    current_page = 1
    next_href = None
    if pagination:
        next_wrapper = _first(pagination, class_name="next")
        for node in pagination.descendants():
            if node.tag == "span" and node.has_class("current"):
                match = re.search(r"\d+", node.text())
                if match:
                    current_page = int(match.group())
            if node.tag == "a":
                is_in_next_wrapper = next_wrapper and any(
                    child is node for child in next_wrapper.descendants("a")
                )
                is_next_link = "next" in node.attrs.get("rel", "").split()
                if is_next_link or is_in_next_wrapper:
                    next_href = node.attrs.get("href") or None
                match = re.fullmatch(r"\s*\d+\s*", node.text())
                if match:
                    page_numbers.append(int(match.group()))
    return SearchResults(
        items=items,
        current_page=current_page,
        page_numbers=tuple(sorted(set(page_numbers))),
        next_page_url=_absolute(base_url, next_href),
    )
