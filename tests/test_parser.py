import unittest

from ebiblio.parser import _TreeParser, parse_search_results
from ebiblio.models import Contributor


class ParseSearchResultsTests(unittest.TestCase):
    def test_namedtuple_nodes_have_independent_children(self):
        parser = _TreeParser()
        parser.feed("<div><span>uno</span><span>dos</span></div>")
        root = parser.finish()

        div = root.children[0]
        self.assertIsInstance(root.children, tuple)
        self.assertIsInstance(div.children, tuple)
        self.assertEqual(
            [node.text() for node in root.descendants("span")],
            ["uno", "dos"],
        )

    def test_extracts_book_metadata_media_and_pagination(self):
        html = """
        <ul class="list-details">
          <li><article class="view-details" itemscope
              itemtype="http://schema.org/Book">
            <a href="/resources/book-123">
              <h3 class="details-content__title beta">Fun home</h3>
            </a>
            <img class="cover" src="/covers/book.jpg" alt="Fun home">
            <div class="details-content__adnl-info">
              <div class="media"><div class="media__img">Autor:</div>
                <div class="contributors">
                  <a><span>Alison Bechdel</span></a>
                </div>
              </div>
            </div>
            <p class="details-content__body">
              Una memoria &amp; una historia.
            </p>
            <div class="medium transaction">
              <h4 class="epub">EPUB</h4>
              <ul class="data-sheet">
                <li>Streaming</li>
                <li>Compatible con lectores de pantalla</li>
              </ul>
              <div class="availability">
                <span class="count">3</span> ejemplares disponibles
              </div>
              <form action="/media/file/loans_confirmation"></form>
            </div>
          </article></li>
        </ul>
        <nav class="pagination"><span class="page current">1</span>
          <span class="page"><a href="/resources?page=2&amp;q=fun">2</a></span>
          <span class="next">
            <a rel="next" href="/resources?page=2&amp;q=fun">Siguiente</a>
          </span>
        </nav>
        """

        results = parse_search_results(html, "https://madrid.ebiblio.es/")

        self.assertEqual(len(results.items), 1)
        item = results.items[0]
        self.assertEqual(item.title, "Fun home")
        self.assertEqual(
            item.url,
            "https://madrid.ebiblio.es/resources/book-123",
        )
        self.assertEqual(item.resource_type, "Book")
        self.assertEqual(item.resource_id, "book-123")
        self.assertEqual(
            item.cover_url,
            "https://madrid.ebiblio.es/covers/book.jpg",
        )
        self.assertEqual(item.description, "Una memoria & una historia.")
        self.assertEqual(item.authors, ("Alison Bechdel",))
        self.assertIsInstance(item.contributors[0], Contributor)
        self.assertEqual(item.contributors[0].role, "autor")
        self.assertEqual(item.contributors[0].names, ("Alison Bechdel",))
        self.assertEqual(item.media[0].format, "EPUB")
        self.assertEqual(item.media[0].availability_count, 3)
        self.assertTrue(item.media[0].streaming)
        self.assertTrue(item.media[0].accessible)
        self.assertEqual(
            item.media[0].borrow_url,
            "https://madrid.ebiblio.es/media/file/loans_confirmation",
        )
        self.assertEqual(results.current_page, 1)
        self.assertEqual(results.page_numbers, (2,))
        self.assertIsInstance(results.items, tuple)
        self.assertIsInstance(item.contributors, tuple)
        self.assertIsInstance(item.contributors[0].names, tuple)
        self.assertIsInstance(item.media, tuple)
        self.assertEqual(
            results.next_page_url,
            "https://madrid.ebiblio.es/resources?page=2&q=fun",
        )

    def test_ignores_articles_without_a_title(self):
        results = parse_search_results(
            '<article class="view-details"><p>sin título</p></article>',
            "https://madrid.ebiblio.es/",
        )
        self.assertEqual(results.items, ())


if __name__ == "__main__":
    unittest.main()
