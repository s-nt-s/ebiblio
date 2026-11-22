import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from ebiblio import EbiblioClient


class EbiblioClientTests(unittest.TestCase):
    def setUp(self):
        self.client = EbiblioClient("https://madrid.ebiblio.es/")

    def test_search_builds_form_query(self):
        with patch.object(
            self.client, "_fetch", return_value="<html></html>"
        ) as fetch:
            self.client.search(
                "El hombre",
                author="Alison Bechdel",
                language="spa",
                availability=True,
                medium=None,
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

    def test_accepts_q_alias_and_rejects_unknown_filter(self):
        with patch.object(
            self.client, "_fetch", return_value="<html></html>"
        ) as fetch:
            self.client.search(q="Mabuse")
        self.assertEqual(
            parse_qs(urlsplit(fetch.call_args.args[0]).query)["keywords"],
            ["Mabuse"],
        )
        with self.assertRaises(TypeError):
            self.client.search("Mabuse", made_up_filter="x")

    def test_validates_url_and_page(self):
        with self.assertRaises(ValueError):
            EbiblioClient("madrid.ebiblio.es")
        with self.assertRaises(ValueError):
            self.client.search("Mabuse", page=0)


if __name__ == "__main__":
    unittest.main()
