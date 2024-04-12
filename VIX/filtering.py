from datetime import datetime
from typing import Tuple

import pandas as pd
from pandas import DataFrame

from VIX.constatns import SPREAD_MULTIPLIER, SPREAD_MIN, RANGE_MULT


class Filtering:
    @staticmethod
    def eliminate_invalid_quotes(df):
        """
        Eliminate invalid quotes under the following scenarios:
            • Negative bid/ask spread
            • Mark price is out of bid/ask range6
            • Mark price is not positive.
        """
        df_filtered = df[
            (df["ask"] > df["bid"])
            & (df["mark_price"] >= df["bid"])
            & (df["mark_price"] <= df["ask"])
            & (df["mark_price"] > 0)
        ].copy()

        return df_filtered

    @staticmethod
    def consolidate_option_quotes(df):
        """
        • Select quotes: maximum of bids and minimum of asks available.
        • Select mark prices: mark price of the option with smallest bid/ask
        spread.
        """
        df = df.copy()
        df.sort_values(by=["symbol", "bid"], inplace=True)
        df['spread'] = df['ask'] - df['bid']

        consolidated = df.groupby('symbol').agg({'bid': 'max', 'ask': 'min'})

        min_spread_mark = df.loc[df.groupby('symbol')['spread'].idxmin(), ['symbol', 'mark_price']]

        result = consolidated.merge(min_spread_mark, on='symbol')

        result["expiry"] = result["symbol"].apply(lambda x: datetime.strptime(x.split("-")[1], "%y%m%d"))

        return result

    @staticmethod
    def filter_near_next_term_options(df, index_maturity_days=30):
        """
        Select near and next-term options:
            • Near-term: Options with longest maturity that is less than or equal
            to index maturity
            • Next-term: Options with shortest maturity that is more than index
            maturity
        """
        df["expiry"] = pd.to_datetime(df["expiry"])
        today = datetime.now()
        df["maturity_days"] = (df["expiry"] - today).dt.days

        max_expiry_near_term = df[df["maturity_days"] <= index_maturity_days][
            "expiry"
        ].max()
        near_term_options = df[df["expiry"] == max_expiry_near_term]

        min_expiry_next_term = df[df["maturity_days"] > index_maturity_days][
            "expiry"
        ].min()
        next_term_options = df[df["expiry"] == min_expiry_next_term]

        return near_term_options, next_term_options

    @staticmethod
    def eliminate_large_spreads(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate bid spread as the difference between mark price and bid
        price. Set the bid spread to zero if negative.
            • Calculate ask spread as the difference between ask price and mark
            price. Set the ask spread to zero if negative.
            • Calculate spread as the sum of bid and ask spreads.
            • Calculate the maximum allowed spread (MAS) as the minimum of
            bid and ask spreads, multiplied by SPREAD MULTIPLIER9
            .
            • Calculate the global maximum spread (GMS) as SPREAD MIN10 multiplied by SPREAD MULTIPLIER
            • Remove the quote if its spread is greater than both GMS and MAS.
        """
        df = df.copy()
        df["bid_spread"] = df["mark_price"] - df["bid"]
        df["ask_spread"] = df["ask"] - df["mark_price"]

        df["bid_spread"] = df["bid_spread"].apply(lambda x: x if x > 0 else 0)
        df["ask_spread"] = df["ask_spread"].apply(lambda x: x if x > 0 else 0)

        df["spread"] = df["bid_spread"] + df["ask_spread"]

        MAS = df[["bid_spread", "ask_spread"]].min(axis=1) * SPREAD_MULTIPLIER

        GMS = SPREAD_MIN * SPREAD_MULTIPLIER

        df = df[(df["spread"] <= GMS) | (df["spread"] <= MAS)]

        df["strike"] = df["symbol"].apply(lambda x: int(x.split("-")[2]))
        df["option_type"] = df["symbol"].apply(lambda x: x[-1])

        df["mid_price"] = (df["bid"] + df["ask"]) / 2

        return df

    @staticmethod
    def calculate_implied_forward_price(df):
        """
        Calculate the implied forward price of the strike that has minimum
        absolute mid-price difference between call and put options, for near and
        next-term options:

        Fimp = K +F ×(C −P)

        where F is the forward price,
        C is the call option price, P is put option price, and both options are
        quoted in the amounts of underlying.
        """
        calls = df[df["option_type"] == "C"]
        puts = df[df["option_type"] == "P"]
        combined = calls[["strike", "mid_price"]].merge(
            puts[["strike", "mid_price"]], on="strike", suffixes=("_call", "_put")
        )
        combined["mid_price_diff"] = abs(
            combined["mid_price_call"] - combined["mid_price_put"]
        )
        min_diff_strike = combined.loc[combined["mid_price_diff"].idxmin()]
        # forward_price = df["forward_price"].iloc[0]
        forward_price = df.loc[df["strike"] == min_diff_strike["strike"], "mark_price"].mean()
        Fimp = min_diff_strike["strike"] + forward_price * (
            min_diff_strike["mid_price_call"] - min_diff_strike["mid_price_put"]
        )
        # describe all steps in Fimp calculation
        print(f"Strike: {min_diff_strike['strike']}")
        print(f"Forward price: {forward_price}")
        print(f"Call price: {min_diff_strike['mid_price_call']}")
        print(f"Put price: {min_diff_strike['mid_price_put']}")
        print(f"Implied forward price: {Fimp}")
        return Fimp

    @staticmethod
    def filter_and_sort_options(df, Fimp):
        """
            Set the largest strike that is less than the implied forward Fimp as ATM
            strike KATM for near and next-term options.
        """
        KATM = df[df["strike"] < Fimp]["strike"].max()

        Kmin = Fimp / RANGE_MULT
        Kmax = Fimp * RANGE_MULT

        # Select the options with strikes greater than Kmin and less than Kmax
        filtered_df = df[(df["strike"] > Kmin) & (df["strike"] < Kmax)]
        sorted_filtered_df = filtered_df.sort_values(by="strike", ascending=True)

        return sorted_filtered_df

    def filter(self, options_df: pd.DataFrame) -> tuple[DataFrame, DataFrame]:
        print(f"Length of options: {len(options_df)}")
        """Firstly eliminate invalid quotes, like ask < bid, mark_price < bid, mark_price > ask, mark_price < 0."""
        valid_options_df = self.eliminate_invalid_quotes(options_df)
        print(f"Length of valid options: {len(valid_options_df)}")

        """Consolidate option quotes by asset, expiry, strike price, and option type."""
        consolidate_option_quotes = self.consolidate_option_quotes(valid_options_df)
        print(f"Length of consolidated options: {len(consolidate_option_quotes)}")

        """Filter near term and next term options with index maturity days = 30."""
        near_term_options, next_term_options = self.filter_near_next_term_options(
            consolidate_option_quotes
        )
        print(f"Length of near term options: {len(near_term_options)}")
        print(f"Length of next term options: {len(next_term_options)}")

        """Eliminate large spreads from near term and next term options."""
        eliminate_large_spreads_near_term, eliminate_large_spreads_next_term = (
            self.eliminate_large_spreads(near_term_options),
            self.eliminate_large_spreads(next_term_options),
        )
        print(
            f"Length eliminate large spreads near term: {len(eliminate_large_spreads_near_term)}"
        )
        print(
            f"Length eliminate large spreads next term: {len(eliminate_large_spreads_next_term)}"
        )

        """Calculate implied forward price for near and next term options."""
        implied_forward_price_near_term, implied_forward_price_next_term = (
            self.calculate_implied_forward_price(eliminate_large_spreads_near_term),
            self.calculate_implied_forward_price(eliminate_large_spreads_next_term),
        )
        """Filter and sort near and next term options with OTM options."""
        print(f"Implied forward price near term: {implied_forward_price_near_term}")
        print(f"Implied forward price next term: {implied_forward_price_next_term}")

        filter_and_sort_options_near_term, filter_and_sort_options_next_term = (
            self.filter_and_sort_options(
                eliminate_large_spreads_near_term, implied_forward_price_near_term
            ),
            self.filter_and_sort_options(
                eliminate_large_spreads_next_term, implied_forward_price_next_term
            ),
        )

        print(
            f"Length filter and sort options near term: {len(filter_and_sort_options_near_term)}"
        )
        print(
            f"Length filter and sort options next term: {len(filter_and_sort_options_next_term)}"
        )

        return filter_and_sort_options_near_term, filter_and_sort_options_next_term
