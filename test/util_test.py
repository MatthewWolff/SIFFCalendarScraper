import logging
import unittest
from datetime import datetime, timedelta

from util import get_logger, parse_int, get_date_delta, get_datetime_from_milliseconds, PACIFIC_TIMEZONE


class TestUtilMethods(unittest.TestCase):
    def test_get_logger(self):
        logger = get_logger(__file__)
        self.assertIsInstance(logger, logging.Logger)

    def test_parse_int(self):
        self.assertEqual(parse_int("123"), 123)
        self.assertEqual(parse_int("abc123def"), 123)
        with self.assertRaises(ValueError):
            parse_int("abc")

    def test_get_date_delta(self):
        self.assertEqual(get_date_delta(0), datetime.now(PACIFIC_TIMEZONE).strftime("%Y-%m-%d"))
        self.assertEqual(get_date_delta(7), (datetime.now(PACIFIC_TIMEZONE) + timedelta(days=7)).strftime("%Y-%m-%d"))

    def test_get_datetime_from_milliseconds(self):
        milliseconds = 1723449313000
        expected_datetime = datetime(2024, 8, 12, 0, 55, 13, tzinfo=PACIFIC_TIMEZONE)
        self.assertEqual(get_datetime_from_milliseconds(str(milliseconds)).date(), expected_datetime.date())


if __name__ == '__main__':
    unittest.main()
