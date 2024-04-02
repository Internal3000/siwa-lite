from datetime import datetime
from typing import Tuple

import pandas as pd
from pandas import DataFrame

from VIX.constatns import SPREAD_MULTIPLIER, SPREAD_MIN


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

        df_filtered["expiry"] = df_filtered["symbol"].apply(
            lambda x: datetime.strptime(x.split("-")[1], "%y%m%d")
        )

        return df_filtered

    @staticmethod
    def consolidate_option_quotes(df):
        '''
        • Select quotes: maximum of bids and minimum of asks available.
        • Select mark prices: mark price of the option with smallest bid/ask
        spread.
        '''
        df.to_csv("df.csv")
        df = df.copy()
        df.sort_values(by=["symbol", "bid"], inplace=True)
        df["bid"] = df["bid"].astype(float)
        df["ask"] = df["ask"].astype(float)
        df["spread"] = df["ask"] - df["bid"]
        df = df.groupby("symbol").agg(
            bid=("bid", "max"),
            ask=("ask", "min"),
            spread=("spread", "min"),
            mark_price=("mark_price", "first"),
            expiry=("expiry", "first"),
        ).reset_index()

        return df[["symbol", "bid", "ask", "mark_price", "expiry"]]

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
        forward_price = df.loc[
            df["strike"] == min_diff_strike["strike"], "mark_price"
        ].iloc[0]
        Fimp = min_diff_strike["strike"] + forward_price * (
            min_diff_strike["mid_price_call"] - min_diff_strike["mid_price_put"]
        )
        return Fimp

    @staticmethod
    def filter_and_sort_options(df, Fimp):
        KATM = df[df["strike"] < Fimp]["strike"].max()
        RANGE_MULT = 2.5
        Kmin = Fimp / RANGE_MULT
        Kmax = Fimp * RANGE_MULT
        calls_otm = df[(df["strike"] > KATM) & (df["option_type"] == "C")]
        puts_otm = df[(df["strike"] < KATM) & (df["option_type"] == "P")]
        otm_combined = pd.concat([calls_otm, puts_otm])
        otm_filtered = otm_combined[
            (otm_combined["strike"] > Kmin) & (otm_combined["strike"] < Kmax)
        ]
        otm_sorted = otm_filtered.sort_values(by="strike")
        tick_size = df[df["bid"] > 0]["bid"].min()
        consecutive_threshold = 5
        consecutive_count = 0
        to_drop = []

        for index, row in otm_sorted.iterrows():
            if row["bid"] <= tick_size:
                consecutive_count += 1
                to_drop.append(index)
            else:
                consecutive_count = 0
            if consecutive_count >= consecutive_threshold:
                break
        otm_final = otm_sorted.drop(to_drop)

        otm_final["Fimp"] = Fimp
        otm_final["KATM"] = KATM

        current_date = datetime.now()
        otm_final["years_to_expiry"] = (
            otm_final["expiry"] - current_date
        ).dt.days / 365.25

        return otm_final

    def filter(self, options_df: pd.DataFrame) -> tuple[DataFrame, DataFrame]:

        options_df.to_csv("raw_options.csv")
        '''Firstly eliminate invalid quotes, like ask < bid, mark_price < bid, mark_price > ask, mark_price < 0.'''
        valid_options_df = self.eliminate_invalid_quotes(options_df)

        '''Consolidate option quotes by asset, expiry, strike price, and option type.'''
        consolidate_option_quotes = self.consolidate_option_quotes(valid_options_df)

        '''Filter near term and next term options with index maturity days = 30.'''
        near_term_options, next_term_options = self.filter_near_next_term_options(
            valid_options_df
        )

        '''Eliminate large spreads from near term and next term options.'''
        eliminate_large_spreads_near_term, eliminate_large_spreads_next_term = (
            self.eliminate_large_spreads(near_term_options),
            self.eliminate_large_spreads(next_term_options),
        )

        '''Calculate implied forward price for near and next term options.'''
        implied_forward_price_near_term, implied_forward_price_next_term = (
            self.calculate_implied_forward_price(eliminate_large_spreads_near_term),
            self.calculate_implied_forward_price(eliminate_large_spreads_next_term),
        )
        '''Filter and sort near and next term options with OTM options.'''

        filter_and_sort_options_near_term, filter_and_sort_options_next_term = (
            self.filter_and_sort_options(eliminate_large_spreads_near_term, implied_forward_price_near_term),
            self.filter_and_sort_options(eliminate_large_spreads_next_term, implied_forward_price_next_term),
        )

        return filter_and_sort_options_near_term, filter_and_sort_options_next_term
