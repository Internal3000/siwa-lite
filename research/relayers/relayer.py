import sys
import requests
import threading
import time
import argparse

from datetime import datetime
from flask import Flask, request, jsonify
from termcolor import colored

from tokens import Token, TOKENS

from typing import Any, Dict, List
from dataclasses import dataclass

from apis.coingecko import API as API_coingecko
from apis.cryptocompare import API as API_cryptocompare
from apis.coinmarketcap import API as API_coinmarketcap
from apis.coingecko_nfts import API as API_coingecko_nfts

app = Flask(__name__)

VERSION = "0.0.7"
DEBUG = False

API_NAME = None
PORT_DEFAULT = 5500
API_SELECTED = None

APIS = ['coingecko','cryptocompare','coinmarketcap','coingecko_nfts']

parser = argparse.ArgumentParser()

parser.add_argument(
    '--api', 
    type=str,
    default='',
    help='Define the API to relay. Use --api coingecko'
)

parser.add_argument(
    '--port',
    type=int,
    default=PORT_DEFAULT,
    help='Set the TCP port to fetch endpoints data from internal API (default port 5000)'
)

args_parsed = parser.parse_args()

if args_parsed.port:
    PORT = args_parsed.port
else:
    PORT = PORT_DEFAULT

if args_parsed.api:
    API_NAME = args_parsed.api
else:
    print("\nPlease provide an API name using the --api argument.\n")
    print(f"Possible values are: {APIS}\n")
    sys.exit(1)

if API_NAME == "coingecko":
    API_SELECTED = API_coingecko
elif API_NAME == "coingecko_nfts":
    API_SELECTED = API_coingecko_nfts
elif API_NAME == "cryptocompare":
    API_SELECTED = API_cryptocompare
elif API_NAME == "coinmarketcap":
    API_SELECTED = API_coinmarketcap
else:
    print("Invalid API name provided. Possible values are: 'coingecko' and 'cryptocompare'")
    sys.exit(1)

MARKETS_DATA = {}
ERROR_DATA = None

FETCH_NAP = 180
RETRIES_MAX = 5
RETRIES_NAP = 10

def time_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def colorize_dict(data, indent=0):
    """
    Recursively colorizes JSON data for pretty printing.

    Parameters:
        data (Any): The JSON data to colorize.
        indent (int): The current indentation level.

    Returns:
        str: The colorized JSON string.
    """
    result = ""
    if isinstance(data, dict):
        result += "{\n"
        for key, value in data.items():
            result += " " * (indent + 4) + f'"{key}"' + ": " + colorize_dict(value, indent + 4) + ",\n"
        result = result.rstrip(",\n") + "\n" + " " * indent + "}"
    elif isinstance(data, list):
        result += "[\n"
        for item in data:
            result += " " * (indent + 4) + colorize_dict(item, indent + 4) + ",\n"
        result = result.rstrip(",\n") + "\n" + " " * indent + "]"
    elif isinstance(data, str):
        result += colored(f'"{data}"', "green")
    elif isinstance(data, (int, float)):
        result += colored(str(data), "yellow")
    else:
        result += colored(str(data), "red")
    return result

def update_market_data():
    
    global MARKETS_DATA

    # Wait for other threads to load first
    time.sleep(2)
    
    while True:
        api = API_SELECTED()
        MARKETS_DATA = api.get_market_data_of_list(TOKENS)
        
        if DEBUG:
            print(f"\n{colorize_dict(MARKETS_DATA)}\n")
            print(f"\nSleeping {FETCH_NAP}..\n")
        time.sleep(FETCH_NAP)  

@app.route('/tokens', methods=['GET'])
def get_tokens():
            
    global MARKETS_DATA
    relayer_response = API_SELECTED.relayer_get_tokens(MARKETS_DATA)
    return relayer_response

if __name__ == "__main__":
    # Start the market data update thread
    update_thread = threading.Thread(target=update_market_data)
    update_thread.daemon = True
    update_thread.start()

    # Local mode -> Run the Flask app only reachable from localhost
    # app.run(host='127.0.0.1', debug=False, use_reloader=False, port=PORT)
    
    # Network mode -> Run the Flask app reachable from anywhere in the network
    app.run(host='0.0.0.0', debug=False, use_reloader=False, port=PORT)

    update_market_data()

# API request examples:
# curl -G "http://127.0.0.1:5500/tokens" --data-urlencode "vs_currency=usd" --data-urlencode "ids=ethereum,solana,tether-gold"
# curl -G "http://127.0.0.1:5500/tokens" --data-urlencode "vs_currency=usd" --data-urlencode "ids=the-bond-bears,the-boo-bears,bit-bears-by-berachain"