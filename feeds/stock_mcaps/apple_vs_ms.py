import numpy as np
import json
import os
import copy
from scipy.stats.mstats import winsorize
from datetime import datetime, timezone
from termcolor import colored
from feeds.data_feed import DataFeed
from collections import deque, defaultdict
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
    MCAP_DEQUE = defaultdict(lambda: defaultdict(lambda: deque(maxlen=10)))

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

    @staticmethod
    def winsorize(data, percent = 10):
        """
            Winsorize x based on mean += threshold * std of data_deque.

            Parameters:
                data: data of values you want to winsorize (at least 3)
                percent: 100-x% winsorization (default 10)

            Returns:
                Winsorized list
        """
        lower = np.percentile(data, percent/2)
        upper = np.percentile(data, 100-percent/2)

        output = []
        for x in data:
            cx = min(max(x, lower), upper)
            # if x != cx:
            #     print(f"Winsorized! Old: {x}, New: {cx}")
            output.append(cx)
        return output

    @staticmethod
    def detect_outliers(data, prev_data, threshold=2.0):
        mean = np.mean(prev_data)
        std = np.std(prev_data, ddof=1)  # use sample std deviation

        if std == 0:
            return [abs(x - mean) > 0 for x in data]  # if std=0, any deviation is an outlier

        outliers = [abs((x - mean) / std) > threshold for x in data]
        return outliers

    @classmethod
    def process_source_data_into_siwa_datapoint(cls):
        """
        Processes data from multiple sources and compute AAPL/MSFT market cap ratio
        """
        cls.log(colored("New data point\n", 'blue'))
        tickers = [cls.TICKER_1, cls.TICKER_2]
        apis = [fmp, yfinance, finnhub]
        total_sources = len(apis)
        coloured_tickers = ", ".join([colored(t, 'yellow') for t in tickers])

        market_caps = {ticker: [] for ticker in tickers}

        with open("api_logs/market_cap_data.json", "r") as f:
            prev_data = json.load(f)
        api_results_log = copy.deepcopy(prev_data)

        for source_cls in apis: # Calls each API to get market caps of all tickers
            source = source_cls()
            source_name = source.source

            cls.log(f"Fetching {coloured_tickers} data from {colored(source_name, 'cyan')}")
            
            data = source.get_market_cap_of_stocks(tickers)
            prev_market_caps = {ticker: [] for ticker in tickers}
            # Logging if data has been received for each ticker of this API and validating it with basic check
            for ticker in tickers:
                value = data.get(ticker, 0)
                if value != 0:
                    cls.log(f"{colored(ticker, 'yellow')} data received from {colored(source_name, 'cyan')}: {colored(str(data[ticker]), 'green')}")
                    prev_value = prev_data[source_name].get(ticker,0)
                    prev_market_caps[ticker].append(prev_value)
                    if prev_value != 0 and abs(prev_value - value) / prev_value > 0.1: 
                        cls.log(f"{colored('WARNING DATA OUT OF THRESHOLD', 'red')}: Ticker: {colored(ticker, 'yellow')}, Source: {colored(source_name, 'cyan')}, Previous Value:{prev_value}, Current Value: {value}")
                    else:
                        #Stores new valid data point to update json
                        api_results_log[source_name][ticker] = value
                        market_caps[ticker].append(value)
                else:
                    cls.log(f"{colored('WARNING NO DATA', 'red')}: Ticker: {colored(ticker, 'yellow')}, Source: {colored(source_name, 'cyan')}")
            print()

        # Logging the no. of sources data has been received per stock
        for ticker in tickers:
            received = len(market_caps.get(ticker, None))
            color = 'yellow' if received == total_sources else 'red'
            count_str = colored(f'{received}/{total_sources}', color)
            cls.log(f"Received data for {colored(ticker, 'yellow')} from {count_str} sources.")
            
            mcaps = market_caps.get(ticker, None)
            # if 3 or more data points received, data is winsorized
            if received >= 3:
                # market_caps[ticker] = winsorize(np.array(market_caps.get(ticker, None)), limits=[0.05, 0.05])
                market_caps[ticker] = cls.winsorize(market_caps[ticker])
                if mcaps != market_caps[ticker]:
                    print(f"Winsorized."
                          f"\nOld: {mcaps}"
                          f"\n New: {market_caps[ticker]}")
            else:
                cls.detect_outliers(market_caps[ticker],prev_market_caps[ticker])

        
        # Error handling for if either of the tickers don't receive any data
        if not market_caps.get(cls.TICKER_1, None) or not market_caps.get(cls.TICKER_2, None):
            cls.log(colored(f"Error: Insufficient data to compute {cls.TICKER_1}/{cls.TICKER_2} ratio", "red"))
            return cls.DATAPOINT_DEQUE[-1]
        
        ticker_1_avg = cls.average(market_caps.get(cls.TICKER_1, None))
        ticker_2_avg = cls.average(market_caps.get(cls.TICKER_2, None))

        # Saving last valid data to json file (to be used next heartbeat)
        file_path = os.path.join("api_logs", f"market_cap_data.json")
        os.makedirs("api_logs", exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(api_results_log, f, indent=4)
        cls.log(colored(f"API results logged to {file_path}", "blue"))

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

