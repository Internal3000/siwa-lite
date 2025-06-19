import json
import os
import statistics
from datetime import datetime, timezone
from termcolor import colored
from feeds.data_feed import DataFeed
from collections import deque, defaultdict
from apis.stockapis.financialmodelingprep import FinancialModelingPrepAPI as fmp
from apis.stockapis.finnhub import FinnhubAPI as finnhub
from apis.stockapis.yfinance import YahooFinanceAPI as yfinance
from itertools import combinations, product


class AAPLVSMSFT(DataFeed):
    NAME = "aaplvsmsft"
    ID = 3
    HEARTBEAT = 5
    DATAPOINT_DEQUE = deque([], maxlen=100)
    TICKER_1 = 'AAPL'
    TICKER_2 = 'MSFT'
    MCAP_DEQUE = defaultdict(lambda: defaultdict(lambda: deque(maxlen=10)))
    STALE_DATA_COUNT = 0

    @staticmethod
    def average(values):
        """
        Takes a list and returns the average of the elements
        """
        if values:
            return sum(values) / len(values)
        else:
            return None
    
    @classmethod
    def addstale(cls):
        cls.STALE_DATA_COUNT += 1
        if cls.STALE_DATA_COUNT >= 10: # Change appropriately depending on heartbeat
            cls.log(f"{colored('WARNING STALE DATA:', 'red') } data has remained the same for {cls.STALE_DATA_COUNT} heartbeats")

    @staticmethod
    def log(message):
        """
        Adds UTC timestamp and prints message
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp} UTC] {message}")

    @classmethod
    def detect_outliers_1(cls, apis, ticker, market_caps, prev_data, threshold = 0.2):
        # Compare the single data point with previous data
        for api_1, api_2 in product(apis, repeat = 2):
            datapoint_1 = market_caps[api_1][ticker]
            datapoint_2 = prev_data[api_2][ticker]

            if datapoint_1 == 0 or datapoint_2 == 0:
                continue
            
            relative_diff = abs(datapoint_1 - datapoint_2) / min(datapoint_1, datapoint_2)
            if relative_diff > threshold: 
                cls.log(f"Outlier Removed. Ticker: {ticker}, Source: {api_1}, Value: {market_caps[api_1][ticker]}")
                return []
            else:
                return [market_caps[api_1][ticker]]


    @classmethod
    def detect_outliers_2(cls, apis, ticker, market_caps, prev_data, threshold = 0.2):
        threshold_hit = False
        for api_1, api_2 in combinations(apis, 2):
            datapoint_1 = market_caps[api_1][ticker]
            datapoint_2 = market_caps[api_2][ticker]

            if datapoint_1 == 0 or datapoint_2 == 0:
                continue

            relative_diff = abs(datapoint_1 - datapoint_2) / min(datapoint_1, datapoint_2)
            if relative_diff > threshold: 
                threshold_hit = True
                break
        
        if threshold_hit:                            
            distances = {api : -1 for api in apis}
            # Compare the new data points to each previous data point
            for api_new, api_prev in product(apis, repeat = 2):
                datapoint_1 = market_caps[api_new][ticker]
                datapoint_2 = prev_data[api_prev][ticker]

                if datapoint_1 == 0 or datapoint_2 == 0:
                    continue

                diff = abs(datapoint_1 - datapoint_2)
                
                if diff < distances[api_new] or distances[api_new] == -1:
                    distances[api_new] = diff
            
            max = -1
            outlier_api = ""
            for api in apis:
                if distances[api] > max:
                    max = distances[api]
                    outlier_api = api
            cls.log(f"Outlier Removed. Ticker: {ticker}, Source: {outlier_api}, Value: {market_caps[outlier_api][ticker]}")
            for a in apis:
                if market_caps[a][ticker] != 0 and api != outlier_api:
                    return [market_caps[a][ticker]]
        else:
            val = []
            for a in apis:
                if market_caps[a][ticker] != 0:
                    val.append([market_caps[a][ticker]])
            return val

    @classmethod
    def detect_outliers_3(cls, ticker, market_caps):
        values = {source: market_caps[source][ticker] for source in market_caps}
        median_value = statistics.median(values.values())
        cls.log(f"Using median value: {median_value}")
        return [median_value]

    @classmethod
    def process_source_data_into_siwa_datapoint(cls):
        """
        Processes data from multiple sources and compute AAPL/MSFT market cap ratio
        """
        cls.log(colored("New data point\n", 'blue'))
        tickers = [cls.TICKER_1, cls.TICKER_2]
        apis = [fmp, yfinance, finnhub]
        total_sources = len(apis)
        sources_count = {ticker: 0 for ticker in tickers}
        coloured_tickers = ", ".join([colored(t, 'yellow') for t in tickers])

        current_market_caps = {api().source : {ticker: 0 for ticker in tickers} for api in apis}

        # opens last valid data
        with open("api_logs/market_cap_data.json", "r") as f:
            prev_data = json.load(f)
        
        # this is what we will update the previous data with after this heartbeat
        api_names = []

        for source_cls in apis: # Calls each API to get market caps of all tickers
            source = source_cls()
            source_name = source.source
            api_names.append(source_name)
            cls.log(f"Fetching {coloured_tickers} data from {colored(source_name, 'cyan')}")
            
            data = source.get_market_cap_of_stocks(tickers)
            
            # Logging if data has been received for each ticker of this API and validating it with basic check
            for ticker in tickers:
                value = data.get(ticker, 0)
                if value != 0:
                    cls.log(f"{colored(ticker, 'yellow')} data received from {colored(source_name, 'cyan')}: {colored(str(data[ticker]), 'green')}")
                    sources_count[ticker] += 1
                    # prev_value = prev_data[source_name].get(ticker,0)
                    # if prev_value != 0 and abs(prev_value - value) / prev_value > 0.5: 
                    #     cls.log(f"{colored('WARNING DATA OUT OF THRESHOLD', 'red')}: Ticker: {colored(ticker, 'yellow')}, Source: {colored(source_name, 'cyan')}, Previous Value:{prev_value}, Current Value: {value}")
                    # else:
                    current_market_caps[source_name][ticker] = value
                else:
                    cls.log(f"{colored('WARNING NO DATA', 'red')}: Ticker: {colored(ticker, 'yellow')}, Source: {colored(source_name, 'cyan')}")
            print()

        no_outliers = {api().source : {ticker: 0 for ticker in tickers} for api in apis}

        # Logging the no. of sources data has been received per stock
        outlier_removed_market_caps = {ticker: [] for ticker in tickers}

        for ticker in tickers:
            received = sources_count[ticker]
            color = 'yellow' if received == total_sources else 'red'
            count_str = colored(f'{received}/{total_sources}', color)
            cls.log(f"Received data for {colored(ticker, 'yellow')} from {count_str} sources.")
            
            if received == 3:
                outlier_removed_market_caps[ticker] = cls.detect_outliers_3(ticker, current_market_caps)
            elif received == 2:
                outlier_removed_market_caps[ticker] = cls.detect_outliers_2(api_names, ticker, current_market_caps, prev_data)
            elif received == 1: 
                outlier_removed_market_caps[ticker] = cls.detect_outliers_1(api_names, ticker, current_market_caps, prev_data)
        
        for ticker in tickers: 
            received = len(outlier_removed_market_caps[ticker])
            color = 'yellow' if received == total_sources else 'red'
            count_str = colored(f'{received}/{total_sources}', color)
            cls.log(f"Computing ratio for {colored(ticker, 'yellow')} from {count_str} sources.")
            

        # Error handling for if either of the tickers don't have any final data
        if not outlier_removed_market_caps.get(cls.TICKER_1, None) or not outlier_removed_market_caps.get(cls.TICKER_2, None):
            cls.log(colored(f"Error: Insufficient data to compute {cls.TICKER_1}/{cls.TICKER_2} ratio", "red"))
            cls.addstale()
            return cls.DATAPOINT_DEQUE[-1]
        
        ticker_1_avg = cls.average(outlier_removed_market_caps.get(cls.TICKER_1, None))
        ticker_2_avg = cls.average(outlier_removed_market_caps.get(cls.TICKER_2, None))

        # Saving data to json file (to be used next heartbeat)
        file_path = os.path.join("api_logs", f"market_cap_data.json")
        os.makedirs("api_logs", exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(current_market_caps, f, indent=4)

        cls.log(colored(f"API results logged to {file_path}", "blue"))

        if ticker_1_avg and ticker_2_avg:
            ratio = ticker_1_avg / ticker_2_avg
            cls.log(f"{cls.TICKER_1}/{cls.TICKER_2} ratio: {colored(f'{ratio:.4f}', 'magenta')}")
            print()
            if cls.DATAPOINT_DEQUE and ratio == cls.DATAPOINT_DEQUE[-1]:
                cls.addstale()
            else:
                cls.STALE_DATA_COUNT = 0
            return ratio
        else:
            cls.log(colored(f"Error: Insufficient data to compute {cls.TICKER_1}/{cls.TICKER_2} ratio", "red"))
            return cls.DATAPOINT_DEQUE[-1]
                    
    @classmethod
    def create_new_data_point(cls): 
        return cls.process_source_data_into_siwa_datapoint()