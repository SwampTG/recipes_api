"""Test calculator functions"""
from django.test import SimpleTestCase

from app import calc


class CalcTests(SimpleTestCase):
    def test_add_numbers(self):
        """Test adding two numbers"""
        res = calc.add(5.0, 6.0)

        self.assertEqual(res, 11.0)

    def test_subtract_numbers(self):
        """Test subtracting numbers."""
        res = calc.subtract(10.0, 15.0)

        self.assertEqual(res, -5.0)
