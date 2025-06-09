from typing import Any, Dict, List
import requests
import os 
from dotenv import load_dotenv
from apis.stockapis.stockapi import StockAPI

# max 30 requests per sec (no explicit info on per day)
# 15 min delayed data

load_dotenv()
api_key = os.getenv('FINNHUB_API_KEY')

class FinnhubAPI(StockAPI):
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the FinnhubAPI object.
        """
        super().__init__(
            url="https://finnhub.io/api/v1",
            source='Finnhub'
        )
    
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
            try:
                url = f"{self.url}/stock/profile2?symbol={ticker}&token={api_key}"
                response = requests.get(url, timeout=self.TIMEOUT)
                data = response.json()
                mcap = round(data.get('marketCapitalization', 0)* 1000000) # Finnhub seems to store mcaps in mm
                market_caps[ticker] = mcap
            except Exception as e:
                print(f"Error fetching market cap for {ticker}: {e}")
                market_caps[ticker] = 0
        return market_caps