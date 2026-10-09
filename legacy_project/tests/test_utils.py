# tests/test_utils.py
# Basic tests - coverage is low, written in a hurry

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import calc, fmt, format_date, pct


class TestCalc(unittest.TestCase):

    def test_calc_basic(self):
        result = calc(100, 0.15)
        self.assertEqual(result, 15.0)

    def test_fmt_default(self):
        result = fmt(42)
        self.assertEqual(result, "42")

    def test_format_date(self):
        result = format_date("2024-01-15")
        self.assertEqual(result, "15.01.2024")

    def test_pct_basic(self):
        result = pct(25, 100)
        self.assertEqual(result, 25.0)

    # TODO: add more tests (CR-301 - blocked)


if __name__ == '__main__':
    unittest.main()
