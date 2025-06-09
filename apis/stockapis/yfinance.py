import yfinance as yf
from typing import Any, Dict, List
from apis.stockapis.stockapi import StockAPI
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# 15 min delayed data
# typically limited to 2,000 requests per hour, or 48,000 per day

class YahooFinanceAPI(StockAPI):
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the YahooFinanceAPI object.
        """
        super().__init__(
            url=None,
            source='YahooFinance'
        )

    @staticmethod
    def get_stock_info(ticker):
        import ipdb; ipdb.set_trace()
        stock = yf.Ticker(ticker)
        return stock.info

    def get_market_cap_of_stocks(self, tickers : List[str]) -> Dict[str, float]:
        '''
        Fetch data by list of stock tickers, and returns the data.

        Parameters:
            tickers (List[str]): List of stocks (by tickers) to fetch.

        Returns:
            Dict[str, float]:
                Dictionary with stock tickers as keys and market cap as values.
        '''
        market_caps = {}
        for ticker in tickers:
            with ThreadPoolExecutor() as executor:
                future = executor.submit(self.get_stock_info, ticker)
                try:
                    info = future.result(timeout=self.TIMEOUT)
                    mcap = info.get('marketCap', 0)
                    market_caps[ticker] = mcap
                except FutureTimeoutError:
                    print(f"Request timed out for ticker: {ticker}")
                    market_caps[ticker] = 0

                except Exception as e:
                    print(f"Error fetching market cap for {ticker}: {e}")
                    market_caps[ticker] = 0
        return market_caps
