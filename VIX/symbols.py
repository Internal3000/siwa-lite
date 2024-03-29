import pandas as pd
import requests

from VIX.constatns import BINANCE_API_OPTIONS_URL


class DerivativeSymbolsFetcher:
    def __init__(self, exchange):
        self.exchange = exchange

    def fetch_symbols(self, market_type="all", base="BTC", quote="USD"):
        self.exchange.load_markets()
        markets_df = pd.DataFrame(self.exchange.markets).transpose()

        markets_df = markets_df[
            (markets_df["base"] == base) & (markets_df["quote"] == quote)
        ]
        markets_df = markets_df[markets_df["symbol"].str.contains(f"{base}/{quote}")]

        symbols = {"futures": [], "options": []}

        if market_type in ["all", "futures.py"]:
            symbols["futures"] = markets_df[markets_df["type"] == "future"][
                "symbol"
            ].tolist()

        if market_type in ["all", "options"]:
            if self.exchange.id == "binance":
                symbols["options"] = self.fetch_binance_options_symbols()
            else:
                symbols["options"] = markets_df[markets_df["type"] == "option"][
                    "symbol"
                ].tolist()

        return symbols if market_type == "all" else symbols[market_type]

    @staticmethod
    def fetch_binance_options_symbols():
        data = DerivativeSymbolsFetcher.get_response(
            BINANCE_API_OPTIONS_URL + "/eapi/v1/exchangeInfo"
        )["optionSymbols"]
        data_df = pd.DataFrame(data)
        symbols = data_df["symbol"].loc[data_df["symbol"].str.contains("BTC-")]
        return symbols.tolist()

    @staticmethod
    def get_response(url):
        try:
            with requests.Session() as session:
                response = session.get(url)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise requests.exceptions.RequestException(
                        f"Status code: {response.status_code} - Reason: {response.reason}"
                    )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error while fetching data from {url}: {e}")
