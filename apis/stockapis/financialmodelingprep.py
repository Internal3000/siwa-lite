from typing import Any, Dict, List
import requests 
import os
from dotenv import load_dotenv
from apis.stockapis.stockapi import StockAPI

# 250 requests per day

load_dotenv()
api_key = os.getenv("FMP_API_KEY")

class FinancialModelingPrepAPI(StockAPI):
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the FinancialModelingPrepAPI object.
        """
        super().__init__(
            url="https://financialmodelingprep.com",
            source='FinancialModelingPrep'
        )
    
    def get_market_cap_of_stocks(self, tickers: List[str]) -> Dict[str, float]:
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
            try:
                url = f"{self.url}/stable/market-capitalization?symbol={ticker}&apikey={api_key}"
                response = requests.get(url, timeout = self.TIMEOUT)
                data = response.json()
                mcap = data[0]['marketCap']
                market_caps[ticker] = mcap
            except Exception as e:
                print(f"Error fetching market cap for {ticker}: {e}")
                market_caps[ticker] = 0
        return market_caps