import json
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen
from unittest.mock import patch

from ebiblio.models import Contributor, SearchQuery, SearchResult
from ebiblio.server import _make_handler, _parse_search_query


class SearchQueryParsingTests(unittest.TestCase):
    def test_builds_search_query_from_get_parameters(self):
        query = _parse_search_query(
            "keywords=Fun+Home&language=spa&availability=available"
        )

        self.assertEqual(
            query,
            SearchQuery(
                keywords="Fun Home",
                language="spa",
                availability="available",
            ),
        )

    def test_rejects_unknown_or_repeated_fields(self):
        with self.assertRaises(ValueError):
            _parse_search_query("url=http://localhost/")
        with self.assertRaises(ValueError):
            _parse_search_query("language=spa&language=eng")


class SearchServerTests(unittest.TestCase):
    def setUp(self):
        self.httpd = HTTPServer(
            ("127.0.0.1", 0),
            _make_handler(
                (
                    "https://catalog-a.example/",
                    "https://catalog-b.example/",
                ),
                4,
            ),
        )
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join()
        self.httpd.server_close()

    def test_search_returns_merged_json_results(self):
        result = SearchResult(
            title="Fun Home",
            url="https://catalog-a.example/resources/123",
            contributors=(Contributor("autor", ("Alison Bechdel",)),),
        )
        with patch("ebiblio.server.EbiblioClient") as client_class:
            client_class.return_value.search_all.return_value = (result,)
            with urlopen(
                f"{self.base_url}/search?keywords=Fun+Home&language=spa"
            ) as response:
                self.assertEqual(response.status, 200)
                body = json.loads(response.read())

        self.assertEqual(len(body), 2)
        self.assertEqual(body[0]["title"], "Fun Home")
        self.assertEqual(
            body[0]["contributors"],
            [{"role": "autor", "names": ["Alison Bechdel"]}],
        )
        calls = client_class.return_value.search_all.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0].args[0],
            SearchQuery(keywords="Fun Home", language="spa"),
        )
        self.assertEqual(calls[0].kwargs, {"max_pages": 4})

    def test_unknown_query_field_returns_400(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(f"{self.base_url}/search?url=http://localhost/")
        self.assertEqual(error.exception.code, 400)

    def test_unknown_route_returns_404(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(f"{self.base_url}/")
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
