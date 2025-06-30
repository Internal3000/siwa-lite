from dataclasses import dataclass

# Re-create the same class definition from SIWA tokendata.py
@dataclass
class Token:
    ticker: str
    name: str
    address: str
    api_ids: dict
    dexscreener_contract: str
    use_v2: bool = False
    mexc_symbol: str = ''

# Define mock string objects to replace the SIWA API objects
# This is done to allow copy-paste of tokendata.py tokens here avoiding unnecesary API imports
coingecko = "coingecko"
coinmarketcap = "coinmarketcap"
cryptocompare = "cryptocompare"
pyth = "pyth"

# =========================
# TOKENS data
# =========================

BTC = Token('BTC', 'Bitcoin', '', {coingecko: 'bitcoin', coinmarketcap: 1, cryptocompare: 'BTC', pyth: ''}, '')
ETH = Token('ETH', 'Ethereum', {'blockchain': 'Bnb-smart-chain', 'address': '0x2170ed0880ac9a755fd29b2688956bd959f933f8'} , {coinmarketcap: 1027, coingecko: 'ethereum', cryptocompare: 'ETH' , pyth: '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace'}, "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",mexc_symbol = "ETH")
SOL = Token('SOL', 'Solana', '', {coinmarketcap: 5426, coingecko: 'solana', cryptocompare: 'SOL', pyth: '0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d'}, "", mexc_symbol= "SOL")