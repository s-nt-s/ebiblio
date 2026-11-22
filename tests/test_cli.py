import contextlib
import io
import json
import unittest
from unittest.mock import patch

from ebiblio.cli import main
from ebiblio.models import Contributor, SearchResult, SearchResults


class EbiblioCliTests(unittest.TestCase):
    def test_search_options_and_json_output(self):
        result = SearchResult(
            title="Fun home",
            url="https://madrid.ebiblio.es/resources/book-123",
            resource_type="Book",
            contributors=(Contributor("autor", ("Alison Bechdel",)),),
        )
        page = SearchResults(
            items=(result,),
            current_page=1,
            next_page_url="https://madrid.ebiblio.es/resources?page=2",
        )
        stdout = io.StringIO()
        with patch("ebiblio.cli.EbiblioClient") as client_class:
            client_class.return_value.search.return_value = page
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "https://madrid.ebiblio.es/",
                        "Fun home",
                        "--author",
                        "Alison Bechdel",
                        "--available",
                        "--json",
                    ]
                )

        self.assertEqual(exit_code, 0)
        client_class.return_value.search.assert_called_once_with(
            "Fun home",
            page=1,
            author="Alison Bechdel",
            availability=True,
        )
        output = json.loads(stdout.getvalue())
        self.assertEqual(output["items"][0]["title"], "Fun home")
        self.assertEqual(
            output["items"][0]["contributors"],
            {"autor": ["Alison Bechdel"]},
        )
        self.assertEqual(output["next_page_url"], page.next_page_url)

    def test_network_errors_return_nonzero(self):
        stderr = io.StringIO()
        with patch("ebiblio.cli.EbiblioClient") as client_class:
            client_class.return_value.search.side_effect = ValueError(
                "bad URL"
            )
            with contextlib.redirect_stderr(stderr):
                exit_code = main(["https://madrid.ebiblio.es/", "Mabuse"])

        self.assertEqual(exit_code, 2)
        self.assertIn("bad URL", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
