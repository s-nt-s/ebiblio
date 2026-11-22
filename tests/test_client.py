import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from ebiblio import EbiblioClient, SearchQuery


class EbiblioClientTests(unittest.TestCase):
    def setUp(self):
        self.client = EbiblioClient("https://madrid.ebiblio.es/")

    def test_search_builds_form_query(self):
        with patch.object(
            self.client, "_fetch", return_value="<html></html>"
        ) as fetch:
            self.client.search(
                SearchQuery(
                    keywords="El hombre",
                    author="Alison Bechdel",
                    language="spa",
                    availability="available",
                ),
            )

        request_url = fetch.call_args.args[0]
        query = parse_qs(urlsplit(request_url).query)
        self.assertEqual(urlsplit(request_url).path, "/resources")
        self.assertEqual(query["keywords"], ["El hombre"])
        self.assertEqual(query["author"], ["Alison Bechdel"])
        self.assertEqual(query["language"], ["spa"])
        self.assertEqual(query["availability"], ["available"])
        self.assertEqual(query["category_standard"], ["ebiblio"])
        self.assertEqual(query["page"], ["1"])
        self.assertNotIn("medium", query)

    def test_search_sends_requested_page(self):
        with patch.object(
            self.client, "_fetch", return_value="<html></html>"
        ) as fetch:
            self.client.search(SearchQuery(keywords="Mabuse"), page=3)

        query = parse_qs(urlsplit(fetch.call_args.args[0]).query)
        self.assertEqual(query["page"], ["3"])

    def test_search_uses_fields_from_search_query(self):
        with patch.object(
            self.client, "_fetch", return_value="<html></html>"
        ) as fetch:
            self.client.search(SearchQuery(keywords="Mabuse"))
        self.assertEqual(
            parse_qs(urlsplit(fetch.call_args.args[0]).query)["keywords"],
            ["Mabuse"],
        )
        self.assertEqual(
            parse_qs(urlsplit(fetch.call_args.args[0]).query)[
                "category_standard"
            ],
            ["ebiblio"],
        )

    def test_search_requires_search_query(self):
        with self.assertRaises(TypeError):
            self.client.search("Mabuse")

    def test_validates_url_and_page(self):
        with self.assertRaises(ValueError):
            EbiblioClient("madrid.ebiblio.es")
        with self.assertRaises(ValueError):
            self.client.search(SearchQuery(keywords="Mabuse"), page=0)


if __name__ == "__main__":
    unittest.main()
