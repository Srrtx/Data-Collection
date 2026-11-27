import unittest
from unittest.mock import Mock, patch

from src import scrape


class ListingCarsTests(unittest.TestCase):
    def test_fetch_rejects_empty_http_202_without_retrying_parser(self):
        response = Mock(status_code=202, content=b"", text="")
        session = Mock()
        session.get.return_value = response

        with self.assertRaisesRegex(RuntimeError, "unexpected HTTP status 202"):
            scrape.fetch(session, scrape.LISTING_URL, retries=3, delay=0)

        self.assertEqual(session.get.call_count, 1)

    def test_listing_retries_when_response_lacks_sch_data_json(self):
        html = (
            '<script>var SchDataJSON={"cars":'
            '[{"type":"car","cid":"123"}]};</script>'
        )
        with patch.object(
            scrape, "fetch", side_effect=["<html>temporary response</html>", html]
        ) as fetch:
            with patch.object(scrape.time, "sleep") as sleep:
                cars = scrape.listing_cars(object(), 1)

        self.assertEqual([car["cid"] for car in cars], ["123"])
        self.assertEqual(fetch.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_listing_raises_after_three_responses_without_sch_data_json(self):
        with patch.object(
            scrape, "fetch", return_value="<html>temporary response</html>"
        ) as fetch:
            with patch.object(scrape.time, "sleep") as sleep:
                with self.assertRaisesRegex(ValueError, "SchDataJSON not found"):
                    scrape.listing_cars(object(), 0.5)

        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(sleep.call_count, 2)


if __name__ == "__main__":
    unittest.main()
