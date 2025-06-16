import yfinance as yf
import pandas as pd
import requests
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("FMP_API_KEY")

ticker_1 = "AAPL"
ticker_2 = "MSFT"
start_date = "2024-06-01"
end_date = "2025-06-01"
tickers = [ticker_1, ticker_2]
market_caps = {}

base_url = "https://financialmodelingprep.com/api/v3/"

def fetch_historical_data(ticker):
    url = f"{base_url}historical-market-capitalization/{ticker}?limit=100&from={start_date}&to={end_date}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    df = df[['date', 'marketCap']].rename(columns={'date': 'timestamp', 'marketCap': f'market_cap_{ticker}'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

for ticker in tickers:
    market_caps[ticker] = fetch_historical_data(ticker)

# Merge dataframes on timestamp
merged_df = pd.merge(
    market_caps[ticker_1],
    market_caps[ticker_2],
    on="timestamp",
    how="inner"
)

# Calculate ratio of AAPL to MSFT market cap
merged_df[f"{ticker_1}/{ticker_2}_ratio"] = merged_df[f"market_cap_{ticker_1}"] / merged_df[f"market_cap_{ticker_2}"]

merged_df = merged_df.sort_values("timestamp")

merged_df.to_csv("market_cap_ratio.csv", index=False)

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# Plot AAPL market cap
axes[0].plot(merged_df['timestamp'], merged_df[f'market_cap_{ticker_1}'], label=f'{ticker_1} Market Cap', color='blue')
axes[0].set_ylabel('Market Cap (USD)')
axes[0].set_title(f'{ticker_1} Market Cap Over Time')
axes[0].legend()
axes[0].grid(True)

# Plot MSFT market cap
axes[1].plot(merged_df['timestamp'], merged_df[f'market_cap_{ticker_2}'], label=f'{ticker_2} Market Cap', color='green')
axes[1].set_ylabel('Market Cap (USD)')
axes[1].set_title(f'{ticker_2} Market Cap Over Time')
axes[1].legend()
axes[1].grid(True)

# Plot AAPL/MSFT market cap ratio
axes[2].plot(merged_df['timestamp'], merged_df[f'{ticker_1}/{ticker_2}_ratio'], label=f'{ticker_1}/{ticker_2} Ratio', color='purple')
axes[2].set_ylabel('Ratio')
axes[2].set_title(f'{ticker_1} to {ticker_2} Market Cap Ratio Over Time')
axes[2].legend()
axes[2].grid(True)

axes[2].set_xlabel('Date')
plt.tight_layout()
plt.show()

