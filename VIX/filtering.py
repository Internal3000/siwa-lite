from datetime import datetime
from typing import Tuple

import pandas as pd
from pandas import DataFrame

from VIX.constatns import SPREAD_MULTIPLIER, SPREAD_MIN


class Filtering:
    @staticmethod
    def eliminate_invalid_quotes(df):
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
    def filter_near_next_term_options(df, index_maturity_days=30):
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

    def filter(self, df: pd.DataFrame) -> tuple[DataFrame, DataFrame]:
        valid_options_df = self.eliminate_invalid_quotes(df)
        near_term_options, next_term_options = self.filter_near_next_term_options(
            valid_options_df
        )
        eliminate_large_spreads_near_term = self.eliminate_large_spreads(
            near_term_options
        )
        eliminate_large_spreads_next_term = self.eliminate_large_spreads(
            next_term_options
        )
        calculate_implied_forward_price_near_term = (
            self.calculate_implied_forward_price(eliminate_large_spreads_near_term)
        )
        filter_and_sort_options_near_term = self.filter_and_sort_options(
            eliminate_large_spreads_near_term, calculate_implied_forward_price_near_term
        )
        filter_and_sort_options_near_term.to_csv("near_term_filtered.csv", index=False)

        return eliminate_large_spreads_near_term, eliminate_large_spreads_next_term
