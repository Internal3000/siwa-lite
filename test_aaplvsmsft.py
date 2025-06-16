import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import json
import numpy as np
from collections import deque, defaultdict
from datetime import datetime, timezone
import os
import copy
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
                            "AAPL": 130,
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

    def test_detect_outliers_with_no_outlier_pump_3_datapoints(self):
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
                            "AAPL": 150,
                            "MSFT": 0
                        },
                        "YahooFinance": {
                            "AAPL": 150,
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
                                        "AAPL": 150,
                                        "MSFT": 0
                                    },
                                    "YahooFinance": {
                                        "AAPL": 150,
                                        "MSFT": 0
                                    },
                                    "Finnhub": {
                                        "AAPL": 130,
                                        "MSFT": 0
                                    }
                                })
        
    def test_detect_outliers_with_outlier_pump_3_datapoints(self):
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




if __name__ == '__main__':
    # Test runner configuration
    unittest.main(verbosity=2)