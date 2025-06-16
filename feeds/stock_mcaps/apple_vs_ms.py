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
from itertools import combinations, product


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
    def winsorize(data, percent = 0.4):
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
    

        #return winsorize(np.array(data), limits=[percent/2, percent/2])


    
    @staticmethod
    def detect_outliers_1(apis, ticker, market_cap, prev_data, threshold = 0.2):
        return None


    @staticmethod
    def detect_outliers_2(apis, ticker, market_caps, prev_data, threshold = 0.2):
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

            for api_new, api_prev in product(apis, repeat = 2):
                datapoint_1 = market_caps[api_new][ticker]
                datapoint_2 = prev_data[api_prev][ticker]

                if datapoint_1 == 0 or datapoint_2 == 0:
                    continue

                diff = abs(datapoint_1 - datapoint_2)
                
                if diff < distances[api_new] or distances[api_new] == -1:
                    distances[api_new] = diff
            
            max = 0
            outlier_api = ""
            for api in apis:
                if distances[api] > max:
                    max = distances[api]
                    outlier_api = api
            market_caps[outlier_api][ticker] = 0 

        return market_caps

    @staticmethod
    def detect_outliers_3(apis, ticker, market_caps, prev_data, threshold = 0.2):
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

            for api_1, api_2 in combinations(apis, 2):
                datapoint_1 = market_caps[api_1][ticker]
                datapoint_2 = market_caps[api_2][ticker]

                if datapoint_1 == 0 or datapoint_2 == 0:
                    continue

                diff = abs(datapoint_1 - datapoint_2)
                
                if diff < distances[api_1] or distances[api_2] == -1:
                    distances[api_1] = diff
            
            max = 0
            outlier_api = ""
            for api in apis:
                if distances[api] > max:
                    max = distances[api]
                    outlier_api = api
            market_caps[outlier_api][ticker] = 0 
        return market_caps



    
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
                    
                    prev_value = prev_data[source_name].get(ticker,0)
                    if prev_value != 0 and abs(prev_value - value) / prev_value > 0.5: 
                        cls.log(f"{colored('WARNING DATA OUT OF THRESHOLD', 'red')}: Ticker: {colored(ticker, 'yellow')}, Source: {colored(source_name, 'cyan')}, Previous Value:{prev_value}, Current Value: {value}")
                    else:
                        current_market_caps[source_name][ticker] = value
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
            
            if received >= 3:
                current_market_caps = cls.detect_outliers_3(api_names, ticker, current_market_caps, prev_data)
            elif received == 2:
                current_market_caps = cls.detect_outliers_2(api_names, ticker, current_market_caps, prev_data)
            else: # 1 received
                current_market_caps = cls.detect_outliers_1(api_names, ticker, current_market_caps, prev_data)
        
        # Converts to list for calculating avg
        outlier_removed_market_caps = {ticker: [] for ticker in tickers}
        for ticker in tickers:
            for api in api_names:
                if current_market_caps[api][ticker] != 0:
                    outlier_removed_market_caps[ticker].append(current_market_caps[api][ticker])

        # Error handling for if either of the tickers don't receive any data
        if not outlier_removed_market_caps.get(cls.TICKER_1, None) or not outlier_removed_market_caps.get(cls.TICKER_2, None):
            cls.log(colored(f"Error: Insufficient data to compute {cls.TICKER_1}/{cls.TICKER_2} ratio", "red"))
            return cls.DATAPOINT_DEQUE[-1]
        
        ticker_1_avg = cls.average(outlier_removed_market_caps.get(cls.TICKER_1, None))
        ticker_2_avg = cls.average(outlier_removed_market_caps.get(cls.TICKER_2, None))

        # Saving last valid data to json file (to be used next heartbeat)
        file_path = os.path.join("api_logs", f"market_cap_data.json")
        os.makedirs("api_logs", exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(current_market_caps, f, indent=4)
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