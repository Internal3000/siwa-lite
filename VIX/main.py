import ccxt
import pandas as pd

from VIX.futures import FutureFetcher
from VIX.options import OptionFetcher
from VIX.symbols import DerivativeSymbolsFetcher


def main(markets):
    options_df = pd.DataFrame()
    implied_interest_rates_df = pd.DataFrame()

    for market in markets:
        options, implied_interest_rates = process_data_for_market(market)
        options_df = pd.concat([options_df, options])
        implied_interest_rates_df = pd.concat([implied_interest_rates_df, implied_interest_rates])


def process_data_for_market(market):
    if market not in ccxt.exchanges:
        raise ValueError(f"Exchange '{market}' is not supported by ccxt.")
    else:
        exchange = getattr(ccxt, market)()

        '''First, we fetch the symbols for futures and options markets.'''
        derived_markets_symbols = DerivativeSymbolsFetcher(exchange)
        contracts_symbols = derived_markets_symbols.fetch_symbols(market_type="all")

        '''Next, we fetch the options and implied interest rates for the futures contracts.'''
        futures = FutureFetcher(exchange)
        implied_interest_rates = futures.fetch_all_implied_interest_rates(
            contracts_symbols["futures"]
        )

        '''Finally, we fetch the options data for the options contracts.'''
        option = OptionFetcher(exchange)
        options = option.fetch_all_options(contracts_symbols["options"])

        return options, implied_interest_rates


if __name__ == "__main__":
    markets = ["binance", "okx", "deribit"]
    try:
        main(markets)
    except ValueError as e:
        print(e)
