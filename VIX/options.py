import pandas as pd
import requests


class OptionFetcher:
    def __init__(self, exchange):
        self.exchange = exchange

    def fetch_all_options(self, symbols: list[str]) -> pd.DataFrame:
        tickers = self.exchange.fetch_tickers(symbols)
        df = pd.DataFrame(tickers).transpose()

        if self.exchange.id == "deribit":
            return self.process_data(df, "deribit")
        elif self.exchange.id == "okx":
            return self.process_data(df, "okx")
        elif self.exchange.id == "binance":
            return self.process_data(df, "binance")
        else:
            raise ValueError(f"Exchange '{self.exchange.id}' is not supported for options.")

    def process_data(self, df: pd.DataFrame, exchange_type: str) -> pd.DataFrame:
        if exchange_type == 'deribit':
            info_df = pd.json_normalize(df["info"])
            df = df.reset_index(drop=True)
            df["mark_price"] = pd.to_numeric(info_df["mark_price"], errors="coerce").fillna(0.0)
            underlying_prices = pd.to_numeric(info_df["underlying_price"], errors="coerce").fillna(0.0)
            df["bid"] *= underlying_prices
            df["ask"] *= underlying_prices
            df["mark_price"] *= underlying_prices

        elif exchange_type == 'okx':
            response = requests.get("https://www.okx.com/api/v5/public/mark-price?instType=OPTION")
            mark_prices = response.json()["data"]
            mark_prices_df = pd.DataFrame(mark_prices)
            mark_prices_df["symbol"] = mark_prices_df["instId"].apply(self.convert_inst_id_to_symbol)
            mark_prices_df.rename(columns={"markPx": "mark_price"}, inplace=True)
            df["underlying_price"] = self.exchange.fetch_ticker("BTC/USDT")["last"]
            df["bid"] *= df["underlying_price"]
            df["ask"] *= df["underlying_price"]
            df = df.merge(mark_prices_df[["symbol", "mark_price"]], on="symbol", how="left")
            df["mark_price"] = pd.to_numeric(df["mark_price"], errors="coerce").fillna(0.0)
            df["mark_price"] *= df["underlying_price"]

        elif exchange_type == 'binance':
            df["symbol"] = df["symbol"].apply(self.convert_usdt_to_usd)
            df["bid"] = df["info"].apply(lambda x: float(x.get("bidPrice", 0)))
            df["ask"] = df["info"].apply(lambda x: float(x.get("askPrice", 0)))
            mark_price = self.binance_fetcher.fetch_mark_price_options()
            mark_price["symbol"] = mark_price["symbol"].apply(self.transform_symbol_format)
            mark_price.rename(columns={"markPrice": "mark_price"}, inplace=True)
            mark_price["mark_price"] = pd.to_numeric(mark_price["mark_price"], errors="coerce").fillna(0.0)
            df = df.merge(mark_price, on="symbol", how="left")

        df["bid"] = pd.to_numeric(df["bid"], errors="coerce").fillna(0.0)
        df["ask"] = pd.to_numeric(df["ask"], errors="coerce").fillna(0.0)
        df["mark_price"] = pd.to_numeric(df["mark_price"], errors="coerce").fillna(0.0)
        return df[["symbol", "bid", "ask", "mark_price"]]

    @staticmethod
    def convert_inst_id_to_symbol(inst_id: str) -> str:
        parts = inst_id.split("-")
        currency = f"{parts[0]}/{parts[1]}"
        date = parts[2][:2] + parts[2][2:4] + parts[2][4:]
        strike_price = parts[3]
        option_type = parts[4]
        symbol = f"{currency}:{parts[0]}-{date}-{strike_price}-{option_type}"
        return symbol

    @staticmethod
    def transform_symbol_format(symbol):
        parts = symbol.split("-")
        return f"{parts[0]}/USD:USD-{parts[1]}-{parts[2]}-{parts[3]}"

    @staticmethod
    def convert_usdt_to_usd(symbol: str) -> str:
        parts = symbol.split(":")
        converted_parts = [part.replace("USDT", "USD") for part in parts]
        converted_symbol = ":".join(converted_parts)
        return converted_symbol

    @staticmethod
    def get_strike_price_and_option_type(symbol: str) -> tuple[str, str]:
        parts = symbol.split("-")
        strike_price = parts[-2]
        option_type = parts[-1]
        return strike_price, option_type
