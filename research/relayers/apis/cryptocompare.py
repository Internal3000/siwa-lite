import requests
import time

from datetime import datetime
from termcolor import colored
from typing import Any, Dict, List
from flask import request, jsonify

from tokens import Token

from tokens import (
    BTC, ETH, SOL
)

class API():

    DEBUG = False

    MARKETS_DATA = {}
    ERROR_DATA = None

    FETCH_NAP = 180
    RETRIES_MAX = 5
    RETRIES_NAP = 10

    tokens = [
        BTC, ETH, SOL
    ]

    API_URL="https://min-api.cryptocompare.com/data/pricemultifull"
    VS_CURRENCY = "USD"
    #ID = "id"
    NAME = "Name"
    LAST_UPDATED = "LASTUPDATE"
    MARKET_CAP = "MKTCAP"
    PRICE = "PRICE"

    TSYMS = "tsyms"
    FSYMS = "fsyms"
    RAW = "RAW"

    @staticmethod
    def time_now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def get_market_data_of_list(cls, tokens: List) -> Dict[str, float]:
            """
            Gets market cap data for the provided list of tokens from CoinGecko API.

            Parameters:
                tokens (List[Token]): List of token dataclass objects for which to fetch market cap data.

            Returns:
                Dict[str, float]: A dictionary with token names as keys and their market cap as values.
            """
            
            # Mock API object to access the source id string
            source = "cryptocompare"

            markets_data = {}
            
            tokens_symbols = [t.api_ids[source] for t in tokens if t.api_ids[source]]
            tokens_symbols = list(set(tokens_symbols))
            
            tokens_upper = [symbol.upper() for symbol in tokens_symbols]
            
            tokens_comma_sep = ','.join(tokens_upper)

            parameters = {
                cls.FSYMS: tokens_comma_sep,
                cls.TSYMS: cls.VS_CURRENCY,
            }
            
            retry_count = 0
            wait_time = cls.RETRIES_NAP
            retry = True
            while retry and retry_count < cls.RETRIES_MAX:
                valid_response = False
                try:
                    response = requests.get(cls.API_URL, params=parameters)
                    if response.status_code == 200:
                        valid_response = True
                        print(f"{cls.time_now()} :: {source} :: Data for {len(tokens)} markets fetched {colored('OK','green')} -> Next update in {cls.FETCH_NAP} secs..")
                except Exception as e:
                    cls.ERROR_DATA = str(e)
                    valid_response = False
                    
                if valid_response:
                    data = response.json()
                    cls.ERROR_DATA = None
                    retry = False
                else:
                    data = None
                    if cls.ERROR_DATA:
                        print(f"\n{cls.time_now()} {colored('ERROR','red')} description: \n\n {cls.ERROR_DATA}\n")
                    retry_count += 1
                    print(f"{cls.time_now()} {colored('ERROR','red')} Failed to fetch markets data. Retrying ({retry_count}/{cls.RETRIES_MAX}) in {wait_time} secs...")
                    time.sleep(wait_time)
                    wait_time *= 2

                    if retry_count == cls.RETRIES_MAX:
                        print(f"{cls.time_now()} {colored('WARNING','yellow')} Maximum retry attempts ({cls.RETRIES_MAX}) reached. Next fetch attempt in {cls.FETCH_NAP} secs..")
                        retry = False
            
            return data

    @classmethod
    def relayer_get_tokens(cls, markets_data):
        
        if markets_data:
            vs_currency = request.args.get('tsysms', 'USD')  # Default to 'usd' if not provided
            requested_tokens = request.args.get('fsyms', '').split(',')
            
            response_data = {}
            for item in markets_data[cls.RAW].items():
                symbol = item[0]
                if symbol in requested_tokens:
                    if cls.RAW not in response_data:
                        response_data[cls.RAW] = {}
                    response_data[cls.RAW][symbol] = item[1]

            # print(f"Request from {colored(request.remote_addr,'blue')} to {colored('/tokens','cyan')} with vs_currency: {colored(vs_currency,'green')} and tickers: {colored(requested_tokens,'blue')}")
        else:
            return jsonify({"error": "No markets data available"}), 503
        
        return jsonify(response_data)