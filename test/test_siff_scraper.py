import os
import unittest
from datetime import datetime

from constants import PACIFIC_TIMEZONE
from model import ShowTime
from siff_scraper import _get_metadata, _extract_showings, _extract_locations
from util import read_html_files, assert_equal_showtime


class TestSIFFScraper(unittest.TestCase):

    def setUp(self):
        self.test_files = read_html_files("inputs" if os.getcwd().endswith("test") else "test/inputs")
        self.reference_showing = ShowTime(
            start_time=datetime(2024, 8, 15, 19, 0, tzinfo=PACIFIC_TIMEZONE),
            end_time=datetime(2024, 8, 15, 20, 46, tzinfo=PACIFIC_TIMEZONE)
        )
        self.current_year = self.reference_showing.start_time.year

    def test_get_metadata_complete(self):
        metadata = _get_metadata(self.test_files["meta"]["complete.html"], self.reference_showing)
        self.assertEqual(metadata, ["USA", "2023", "107 min.", "Greg Kwedar"])

    def test_get_metadata_empty(self):
        metadata = _get_metadata(self.test_files["meta"]["empty.html"], self.reference_showing)
        self.assertEqual(metadata, ["Unknown Country", f"{self.current_year}*", "Unknown Duration", "Unknown Director"])

    def test_get_metadata_missing_country(self):
        metadata = _get_metadata(self.test_files["meta"]["missing_country.html"], self.reference_showing)
        self.assertEqual(metadata, ["Unknown Country", "2024", "90 min.", "Simona Risi"])

    def test_get_metadata_missing_duration(self):
        metadata = _get_metadata(self.test_files["meta"]["missing_duration.html"], self.reference_showing)
        self.assertEqual(metadata, ["Ireland", "2024", "106 min.", "Rich Peppiatt"])

    def test_get_metadata_only_duration(self):
        metadata = _get_metadata(self.test_files["meta"]["only_duration.html"], self.reference_showing)
        self.assertEqual(metadata, ["Unknown Country", f"{self.current_year}*", "91 min.", "Unknown Director"])

    def test_extract_showings(self):
        showings = _extract_showings(self.test_files["movie"]["example.html"])
        expected_showings = [ShowTime(start_time=datetime(2024, 8, 15, 19, 0),
                                      end_time=datetime(2024, 8, 15, 20, 46))]
        self.assertTrue(all(assert_equal_showtime(dt1, dt2) for dt1, dt2 in zip(showings, expected_showings)))

    def test_extract_locations(self):
        locations = _extract_locations(self.test_files["movie"]["example.html"])
        expected_locations = ['SIFF Cinema Egyptian, 805 East Pine Street, Seattle, WA 98122']
        self.assertEqual(locations, expected_locations)


if __name__ == '__main__':
    unittest.main()
