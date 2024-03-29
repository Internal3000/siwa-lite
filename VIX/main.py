import ccxt
import pandas as pd

from VIX.futures import FutureFetcher
from VIX.symbols import DerivativeSymbolsFetcher


def main(markets):
    implied_interest_rates_df = pd.DataFrame()
    for market in markets:
        implied_interest_rates = process_data(market)
        implied_interest_rates_df = pd.concat(
            [implied_interest_rates_df, pd.DataFrame(implied_interest_rates)]
        )


def process_data(market):
    if market not in ccxt.exchanges:
        raise ValueError(f"Exchange '{market}' is not supported by ccxt.")
    else:
        exchange = getattr(ccxt, market)()
        derived_markets_fetchers = DerivativeSymbolsFetcher(exchange)
        contracts_symbols = derived_markets_fetchers.fetch_symbols(market_type="all")
        futures = FutureFetcher(exchange)
        implied_interest_rates = futures.fetch_all_implied_interest_rates(
            contracts_symbols["futures"]
        )
        return implied_interest_rates


if __name__ == "__main__":
    markets = ["binance", "okx", "deribit"]
    try:
        main(markets)
    except ValueError as e:
        print(e)
