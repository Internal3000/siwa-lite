import unittest
import apis.stockapis 
from unittest.mock import Mock, patch, mock_open, MagicMock
import json
import numpy as np
from collections import deque, defaultdict
from datetime import datetime, timezone
import os
import copy
import apis.stockapis.financialmodelingprep
import apis.stockapis.finnhub
import apis.stockapis.yfinance
from feeds.stock_mcaps.apple_vs_ms import AAPLVSMSFT

class TestAAPLVSMSFT(unittest.TestCase):
    def test_average_with_values(self):
        """Test average method with a list of values."""
        values = [1, 2, 3]
        result = AAPLVSMSFT.average(values)
        self.assertEqual(result, 2.0)
    
    def test_average_with_empty_list(self):
        """Test average method with empty list."""
        values = []
        result = AAPLVSMSFT.average(values)
        self.assertIsNone(result)
    
    def test_average_with_none(self):
        """Test average method with None."""
        result = AAPLVSMSFT.average(None)
        self.assertIsNone(result)
    
    def test_average_with_single_value(self):
        """Test average method with single value."""
        values = [69]
        result = AAPLVSMSFT.average(values)
        self.assertEqual(result, 69.0)

    def test_detect_outlier_3(self):
        """Test outlier detection with 1 outlier, 3 data points."""
        new_data = {
                        "FinancialModelingPrep": {
                            "AAPL": 101,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 100.5,
                            "MSFT": 0
                        },
                        "Finnhub": {
                            "AAPL": 131,
                            "MSFT": 0
                        }
                    }
        
        result = AAPLVSMSFT.detect_outliers_3("AAPL", new_data)
        self.assertEqual(result,{
                                    "FinancialModelingPrep": {
                                        "AAPL": 101,
                                        "MSFT": 0
                                    },
                                    "YahooFinance": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    },
                                    "Finnhub": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    }
                                })
        
    def test_detect_outlier_2(self):
        """Test outlier detection with outlier data."""
        apis = ["FinancialModelingPrep", "YahooFinance", "Finnhub"]
        prev_data = {
                        "FinancialModelingPrep": {
                            "AAPL": 100,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 100.5,
                            "MSFT": 0
                        },
                        "Finnhub": {
                            "AAPL": 0,
                            "MSFT": 0
                        }
                    }
        new_data = {
                        "FinancialModelingPrep": {
                            "AAPL": 101,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 130.5,
                            "MSFT": 0
                        },
                        "Finnhub": {
                            "AAPL": 0,
                            "MSFT": 0
                        }
                    }
        
        result = AAPLVSMSFT.detect_outliers_2(apis, "AAPL", new_data, prev_data)
        self.assertEqual(result,{
                                    "FinancialModelingPrep": {
                                        "AAPL": 101,
                                        "MSFT": 0
                                    },
                                    "YahooFinance": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    },
                                    "Finnhub": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    }
                                })

    def test_detect_outlier_1(self):
        """Test outlier detection with 1 outlier, 1 data point"""
        apis = ["FinancialModelingPrep", "YahooFinance", "Finnhub"]
        prev_data = {
                        "FinancialModelingPrep": {
                            "AAPL": 100,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 100.5,
                            "MSFT": 0
                        },
                        "Finnhub": {
                            "AAPL": 99,
                            "MSFT": 0
                        }
                    }
        new_data = {
                        "FinancialModelingPrep": {
                            "AAPL": 0,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 130.5,
                            "MSFT": 0
                        },
                        "Finnhub": {
                            "AAPL": 0,
                            "MSFT": 0
                        }
                    }
        
        result = AAPLVSMSFT.detect_outliers_1(apis, "AAPL", new_data, prev_data)
        self.assertEqual(result,{
                                    "FinancialModelingPrep": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    },
                                    "YahooFinance": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    },
                                    "Finnhub": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    }
                                })
        
    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_siwa_3_data_points(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 3 data points'''
        aapl = [101, 100, 99.5]
        msft = [102, 99, 98]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = aapl[1]
        expected_msft_avg = msft[1]
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)

    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_siwa_3_data_points_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data with 1 outlier'''
        aapl = [99.5, 103, 42069]
        msft = [100.5, 100, 99]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = aapl[1]
        expected_msft_avg = msft[1]
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)
    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_siwa_3_data_points_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data with 1 outlier'''
        aapl = [99.5, 103, 42069]
        msft = [100.5, 100, 99]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = aapl[1]
        expected_msft_avg = msft[1]
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)
    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_siwa_2_data_points_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data'''
        aapl = [99.5, 100.2, 0]
        msft = [100.5, 100, 99]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0]+aapl[1])/2
        expected_msft_avg = msft[1]
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)

    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_siwa_2_data_points_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data with 1 outlier'''
        aapl = [99.5, 120, 0]
        msft = [100.5, 100, 99]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = aapl[0]
        expected_msft_avg = msft[1]
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)

    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_siwa_1_data_points_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data with 1 outlier'''
        aapl = [0, 121, 0]
        msft = [100.5, 100, 99]
        AAPLVSMSFT.DATAPOINT_DEQUE.append(42069)

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        self.assertEqual(result, 42069)


    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_siwa_1_data_points(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data with 1 outlier'''
        aapl = [0, 101, 0]
        msft = [100.5, 100, 99]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()
        
        expected_aapl_avg = aapl[1]
        expected_msft_avg = msft[1]
        expected_ratio = expected_aapl_avg / expected_msft_avg


        self.assertEqual(result, expected_ratio)


    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_siwa_no_data(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with no data points'''
        aapl = [0, 0, 0]
        msft = [100.5, 100, 99]
        AAPLVSMSFT.DATAPOINT_DEQUE.append(69)

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        self.assertEqual(result, 69)

    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 100, "MSFT": 100},
        "YahooFinance": {"AAPL": 100, "MSFT": 100},
        "Finnhub": {"AAPL": 100, "MSFT": 100}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_stale_data(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Testing message for stale data'''
        aapl = [100, 100, 100]
        msft = [100, 100, 100]
        AAPLVSMSFT.DATAPOINT_DEQUE.append(1)

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'
        for i in range (1, 10):
            AAPLVSMSFT.process_source_data_into_siwa_datapoint()









if __name__ == '__main__':
    # Test runner configuration
    unittest.main(verbosity=2)