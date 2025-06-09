from datetime import datetime, timezone
from termcolor import colored

from feeds.data_feed import DataFeed
from collections import deque

from apis.stockapis.financialmodelingprep import FinancialModelingPrepAPI as fmp
from apis.stockapis.finnhub import FinnhubAPI as finnhub
from apis.stockapis.yfinance import YahooFinanceAPI as yfinance

class AAPLVSMSFT(DataFeed):
    NAME = "aaplvsmsft"
    ID = 3
    HEARTBEAT = 5
    DATAPOINT_DEQUE = deque([], maxlen=100)
    TICKER_1 = 'AAPL'
    TICKER_2 = 'MSFT'
    MCAP_DEQUE = {}


    @staticmethod
    def average(values):
        """
        Takes a list and returns the average of the elements
        """
        if values:
            return sum(values) / len(values)
        else:
            return None
    
    @staticmethod
    def log(message):
        """
        Adds UTC timestamp and prints message
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp} UTC] {message}")


    @classmethod
    def process_source_data_into_siwa_datapoint(cls):
        """
        Processes data from multiple sources and compute AAPL/MSFT market cap ratio
        """
        cls.log(colored("New data point\n", 'blue'))
        tickers = [cls.TICKER_1, cls.TICKER_2]
        market_caps = {ticker: [] for ticker in tickers}

        apis = [fmp, yfinance, finnhub]
        # apis = [fmp, finnhub]

        total_sources = len(apis)
        coloured_tickers = ", ".join([colored(t, 'yellow') for t in tickers])

        for source_cls in apis: # Calls each API to get market caps of all tickers
            source = source_cls()
            
            cls.log(f"Fetching {coloured_tickers} data from {colored(source.source, 'cyan')}")
            data = source.get_market_cap_of_stocks(tickers)
            # Output message
            for ticker in tickers:
                if data.get(ticker, 0) != 0:
                    cls.log(f"{colored(ticker, 'yellow')} data received from {colored(source.source, 'cyan')}: {colored(str(data[ticker]), 'green')}")
                    cls.MCAP_DEQUE[ticker][source.source].append()
                    market_caps[ticker].append(data.get(ticker, 0))
                else:
                    cls.log(f"{colored('Warning', 'red')}: No data for {colored(ticker, 'yellow')} from {colored(source.source, 'cyan')}")
            print()

        # Logging the no. of sources data has been received per stock
        for ticker in tickers:
            received = len(market_caps.get(ticker, None))
            color = 'yellow' if received == total_sources else 'red'
            count_str = colored(f'{received}/{total_sources}', color)
            cls.log(f"Received data for {colored(ticker, 'yellow')} from {count_str} sources.")

        # Error handling for if either of the tickers don't receive any data
        if not market_caps.get(cls.TICKER_1, None) or not market_caps.get(cls.TICKER_2, None):
            cls.log(colored(f"Error: Insufficient data to compute {cls.TICKER_1}/{cls.TICKER_2} ratio", "red"))
            return cls.DATAPOINT_DEQUE[-1]
        
        ticker_1_avg = cls.average(market_caps.get(cls.TICKER_1, None))
        ticker_2_avg = cls.average(market_caps.get(cls.TICKER_2, None))

        if ticker_1_avg and ticker_2_avg:
            ratio = ticker_1_avg / ticker_2_avg
            cls.log(f"{cls.TICKER_1}/{cls.TICKER_2} ratio: {colored(f'{ratio:.4f}', 'magenta')}")
            print()
            return ratio
        else:
            cls.log(colored(f"Error: Insufficient data to compute {cls.TICKER_1}/{cls.TICKER_2} ratio", "red"))
            return cls.DATAPOINT_DEQUE[-1]
                    
    @classmethod
    def create_new_data_point(cls):
        return cls.process_source_data_into_siwa_datapoint()

