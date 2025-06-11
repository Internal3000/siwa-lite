import unittest
from unittest.mock import patch, MagicMock
from feeds.stock_mcaps.apple_vs_ms import AAPLVSMSFT

class TestAAPLVSMSFT(unittest.TestCase):
    # Average (trivial)

    def test_average_normal_case(self):
        self.assertEqual(AAPLVSMSFT.average([1, 2, 3]), 2)

    def test_average_empty(self):
        self.assertIsNone(AAPLVSMSFT.average([]))

    def test_average_single(self):
        self.assertEqual(AAPLVSMSFT.average([10]), 10)


    # Winsorizing

    def test_winsorize_trims_extremes(self):
        data = [1, 2, 3, 100]
        result = AAPLVSMSFT.winsorize(data, percent=10)
        self.assertTrue(result[0] >= min(data))
        self.assertTrue(result[-1] <= max(data))
        self.assertEqual(len(result), len(data))

    def test_winsorize_no_change_on_uniform(self):
        data = [10, 10, 10, 10]
        self.assertEqual(AAPLVSMSFT.winsorize(data), data)
