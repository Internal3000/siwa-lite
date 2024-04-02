from datetime import datetime
import numpy as np
import pandas as pd
from typing import List, Dict


class FutureFetcher:
    def __init__(self, exchange) -> None:
        """Initialize with an exchange object to fetch market data."""
        self.exchange = exchange

    def fetch_future_orderbook(self, symbol: str) -> Dict[str, any]:
        """Fetch the future orderbook for a symbol and calculate the forward price."""
        try:
            order_book = self.exchange.fetch_order_book(symbol)
        except Exception as e:
            print(f"Error fetching order book for {symbol}: {e}")
            return {}

        bids_df = pd.DataFrame(
            order_book["bids"], columns=["price", "quantity"]
        ).astype(float)
        asks_df = pd.DataFrame(
            order_book["asks"], columns=["price", "quantity"]
        ).astype(float)

        forward_price = (bids_df["price"].max() + asks_df["price"].min()) / 2
        expiry = symbol.split("-")[1]

        return {"symbol": symbol, "forward_price": forward_price, "expiry": expiry}

    def fetch_spot_price(self, symbol: str = "BTC/USDT") -> float:
        """Fetch the last spot price for a symbol."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker["last"]
        except Exception as e:
            print(f"Error fetching spot price for {symbol}: {e}")
            return 0.0

    def fetch_implied_interest_rate(self, symbol: str) -> Dict[str, any]:
        """Calculate the implied interest rate for a future contract."""
        orderbook = self.fetch_future_orderbook(symbol)
        if not orderbook:
            return {}

        forward_price = orderbook["forward_price"]
        expiry_date = datetime.strptime(orderbook["expiry"], "%y%m%d")
        today = datetime.now()
        days_to_expiry = (expiry_date - today).days
        years_to_expiry = days_to_expiry / 365.25

        spot_price = self.fetch_spot_price()

        implied_interest_rate = 0
        if years_to_expiry != 0:
            implied_interest_rate = (
                np.log(forward_price / spot_price)
            ) / years_to_expiry

        return {
            "expiry": orderbook["expiry"],
            "implied_interest_rate": implied_interest_rate,
            "years_to_expiry": years_to_expiry,
        }

    def fetch_all_implied_interest_rates(self, symbols: List[str]) -> pd.DataFrame:
        """Fetch and calculate implied interest rates for a list of symbols."""
        data = [
            self.fetch_implied_interest_rate(symbol)
            for symbol in symbols
            if self.fetch_implied_interest_rate(symbol)
        ]
        rates_data = pd.DataFrame(data)
        rates_data["expiry"] = pd.to_datetime(
            rates_data["expiry"], format="%y%m%d"
        ).dt.strftime("%Y-%m-%d")
        return rates_data


def mean_implied_interest_rate(implied_interest_rates_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the mean implied interest rate for same expiry contracts."""
    return implied_interest_rates_df.groupby('expiry')['implied_interest_rate'].mean().reset_index()
