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

    def test_detect_outliers_with_1_outlier_3_datapoints(self):
        """Test outlier detection with 1 outlier, 3 data points."""
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
                            "AAPL": 101,
                            "MSFT": 0
                        }
                    }
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
        
        result = AAPLVSMSFT.detect_outliers_3(apis, "AAPL", new_data, prev_data)
        self.assertEqual(result,{
                                    "FinancialModelingPrep": {
                                        "AAPL": 101,
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
                                })
        
    def test_detect_outliers_with_no_outlier_3_datapoints(self):
        """Test outlier detection with no outlier, 3 data points."""
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
                            "AAPL": 101,
                            "MSFT": 0
                        }
                    }
        new_data = {
                        "FinancialModelingPrep": {
                            "AAPL": 101.2,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 99.5,
                            "MSFT": 0
                        },
                        "Finnhub": {
                            "AAPL": 102,
                            "MSFT": 0
                        }
                    }
        
        result = AAPLVSMSFT.detect_outliers_3(apis, "AAPL", new_data, prev_data)
        self.assertEqual(result,{
                                    "FinancialModelingPrep": {
                                        "AAPL": 101.2,
                                        "MSFT": 0
                                    },
                                    "YahooFinance": {
                                        "AAPL": 99.5,
                                        "MSFT": 0
                                    },
                                    "Finnhub": {
                                        "AAPL": 102,
                                        "MSFT": 0
                                    }
                                })

    def test_detect_outliers_with_no_outlier_pump_3_datapoints(self):
        """Test outlier detection with no outlier, post pump."""
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
                            "AAPL": 132,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 134,
                            "MSFT": 0
                        },
                        "Finnhub": {
                            "AAPL": 120,
                            "MSFT": 0
                        }
                    }
        
        result = AAPLVSMSFT.detect_outliers_3(apis, "AAPL", new_data, prev_data)
        self.assertEqual(result,{
                                    "FinancialModelingPrep": {
                                        "AAPL": 132,
                                        "MSFT": 0
                                    },
                                    "YahooFinance": {
                                        "AAPL": 134,
                                        "MSFT": 0
                                    },
                                    "Finnhub": {
                                        "AAPL": 120,
                                        "MSFT": 0
                                    }
                                })
        
    def test_detect_outliers_with_outlier_pump_3_datapoints(self):
        """Test outlier detection with one outlier following a pump."""
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
                            "AAPL": 100,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 130,
                            "MSFT": 0
                        },
                        "Finnhub": {
                            "AAPL": 130,
                            "MSFT": 0
                        }
                    }
        
        result = AAPLVSMSFT.detect_outliers_3(apis, "AAPL", new_data, prev_data)
        self.assertEqual(result,{
                                    "FinancialModelingPrep": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    },
                                    "YahooFinance": {
                                        "AAPL": 130,
                                        "MSFT": 0
                                    },
                                    "Finnhub": {
                                        "AAPL": 130,
                                        "MSFT": 0
                                    }
                                })
        
    def test_detect_outliers_with_1_outlier_2_datapoints(self):
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

    def test_detect_outliers_with_1_outlier_1_datapoint(self):
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
                            "AAPL": 0,
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
        
    def test_detect_outliers_with_no_outlier_1_datapoint(self):
        """Test outlier detection with no outlier, 1 data point."""
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
                            "AAPL": 0,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 110.5,
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
                                        "AAPL": 110.5,
                                        "MSFT": 0
                                    },
                                    "Finnhub": {
                                        "AAPL": 0,
                                        "MSFT": 0
                                    }
                                })
        
    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_normal_3_data(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 3 data points'''
        aapl = [2900000000000, 2890000000000, 2870000000000]
        msft = [3500000000000, 3510000000000, 3490000000000]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1] + aapl[2]) / 3
        expected_msft_avg = (msft[0] + msft[1] + msft[2]) / 3
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)

    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_3_data_1_big_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data with 1 blatant outlier'''
        aapl = [2900000000000, 2890000000000, 42069]
        msft = [3500000000000, 3510000000000, 3490000000000]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1]) / 2
        expected_msft_avg = (msft[0] + msft[1] + msft[2]) / 3
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)

    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_3_data_1_small_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data with 1 not so obvious outlier outlier'''
        aapl = [2900000000000, 2890000000000, 3490000000000]
        msft = [3500000000000, 3510000000000, 3490000000000]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1]) / 2
        expected_msft_avg = (msft[0] + msft[1] + msft[2]) / 3
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)

    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_normal_pump(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data points with 1 blatant outlier'''
        aapl = [2900000000000, 2890000000000, 2880000000000]
        msft = [3800000000000, 3810000000000, 3790000000000]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1] + aapl[2]) / 3
        expected_msft_avg = (msft[0] + msft[1] + msft[2]) / 3
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)
        
    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_pump_1_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 3 data points, post pump, 1 outlier'''
        aapl = [2900000000000, 2890000000000, 2870000000000]
        msft = [4500000000000, 4510000000000, 3490000000000]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1] + aapl[2]) / 3
        expected_msft_avg = (msft[0] + msft[1]) / 2
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)


    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_pump_normal_2_datapoints(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 normal data points'''
        aapl = [2900000000000, 2890000000000, 2870000000000]
        msft = [3490000000000, 3530000000000, 0]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1] + aapl[2]) / 3
        expected_msft_avg = (msft[0] + msft[1]) / 2
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)

    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_pump_2_datapoints(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 data points, post pump'''
        aapl = [2900000000000, 2890000000000, 2870000000000]
        msft = [4500000000000, 4510000000000, 0]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1] + aapl[2]) / 3
        expected_msft_avg = (msft[0] + msft[1]) / 2
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)
    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_pump_2_datapoints_1_outlier(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 2 data points, 1 outlier'''
        aapl = [2900000000000, 2890000000000, 2870000000000]
        msft = [3480000000000, 4510000000000, 0]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1] + aapl[2]) / 3
        expected_msft_avg = msft[0]
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)


    
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_pump_1_datapoint_normal(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        '''Test feed with normal 1 data points, no outlier'''
        aapl = [2900000000000, 2890000000000, 2870000000000]
        msft = [3480000000000, 0, 0]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_aapl_avg = (aapl[0] + aapl[1] + aapl[2]) / 3
        expected_msft_avg = msft[0]
        expected_ratio = expected_aapl_avg / expected_msft_avg

        self.assertEqual(result, expected_ratio)

    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "FinancialModelingPrep": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "YahooFinance": {"AAPL": 2900000000000, "MSFT": 3510000000000},
        "Finnhub": {"AAPL": 2900000000000, "MSFT": 3510000000000}
    }''')
    @patch("feeds.stock_mcaps.apple_vs_ms.fmp")
    @patch("feeds.stock_mcaps.apple_vs_ms.finnhub")
    @patch("feeds.stock_mcaps.apple_vs_ms.yfinance")
    def test_process_source_data_into_siwa_datapoint_pump_1_datapoint_normal(
        self, mock_yfinance, mock_finnhub, mock_fmp, mock_file
    ):
        AAPLVSMSFT.DATAPOINT_DEQUE.append(120)
        '''Test feed with normal 1 data points, no outlier'''
        aapl = [2900000000000, 2890000000000, 2870000000000]
        msft = [4480000000000, 0, 0]

        mock_fmp.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[0], "MSFT": msft[0]}
        mock_yfinance.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[1], "MSFT": msft[1]}
        mock_finnhub.return_value.get_market_cap_of_stocks.return_value = {"AAPL": aapl[2], "MSFT": msft[2]}

        mock_fmp.return_value.source = 'FinancialModelingPrep'
        mock_finnhub.return_value.source = 'Finnhub'
        mock_yfinance.return_value.source = 'YahooFinance'

        result = AAPLVSMSFT.process_source_data_into_siwa_datapoint()

        expected_ratio = 120

        self.assertEqual(result, expected_ratio)



if __name__ == '__main__':
    # Test runner configuration
    unittest.main(verbosity=2)