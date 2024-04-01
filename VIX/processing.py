import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from VIX.constatns import SPREAD_MULTIPLIER, SPREAD_MIN


class Processing:
    @staticmethod
    def calculate_yield_curve(dataframe):
        """
        Calculates the average interest rate for each expiry date in a pandas DataFrame.

        Parameters:
        - dataframe: A pandas DataFrame containing at least two columns: 'expiry' and 'implied_interest_rate'.

        Returns:
        - A pandas DataFrame containing the average implied interest rate for each unique expiry date.
        """
        dataframe = dataframe.sort_values(by="expiry", ascending=False)

        grouped = (
            dataframe.groupby("expiry")["implied_interest_rate"].mean().reset_index()
        )

        return grouped[
            ["expiry", "implied_interest_rate", "days_to_expiry", "years_to_expiry"]
        ]

    @staticmethod
    def build_interest_rate_term_structure(df):
        # Group by expiry date and calculate the average implied interest rate for each expiry
        interest_rate_term_structure = df.groupby("expiry")["rimp"].mean().reset_index()

        # Rename columns for clarity
        interest_rate_term_structure.rename(
            columns={"rimp": "average_implied_interest_rate"}, inplace=True
        )

        return interest_rate_term_structure

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

    @staticmethod
    def calculate_wij(options_df, futures_df):
        futures_df["expiry"] = pd.to_datetime(futures_df["expiry"])
        options_df["expiry"] = pd.to_datetime(options_df["expiry"])

        options_df.sort_values(by=["expiry", "strike"], inplace=True)

        merged_df = options_df.merge(
            futures_df, on="expiry", how="left", suffixes=("_x", "_y")
        )

        merged_df["K_prev"] = merged_df["strike"].shift(1)
        merged_df["K_next"] = merged_df["strike"].shift(-1)

        merged_df["Delta_K"] = (merged_df["K_next"] - merged_df["K_prev"]) / 2
        merged_df["Delta_K"].fillna(method="bfill", inplace=True)
        merged_df["Delta_K"].fillna(method="ffill", inplace=True)

        merged_df["w_ij"] = (
            np.exp(merged_df["implied_interest_rate"] * merged_df["years_to_expiry"])
            * merged_df["Delta_K"]
        ) / (merged_df["strike"] ** 2)

        return merged_df

    @staticmethod
    def calculate_sigma_it_squared_for_all(w_ij_df):
        T_i = w_ij_df["years_to_expiry"].mean()
        F_i = w_ij_df["Fimp"].mean()
        K_i_ATM = w_ij_df["KATM"].mean()

        sigma_squared = (1 / T_i) * (
            np.sum(0.5 * w_ij_df["w_ij"] * w_ij_df["mid_price"])
            - ((F_i / K_i_ATM) - 1) ** 2 * len(w_ij_df)
        )

        return sigma_squared

    @staticmethod
    def interpolate_implied_interest_rates(options_df, futures_df):
        options_expires = options_df["expiry"].unique()
        futures_expires = futures_df["expiry"].unique()

        missing_expires = sorted(list(set(options_expires) - set(futures_expires)))

        futures_df["expiry_ordinal"] = pd.to_datetime(futures_df["expiry"]).apply(
            lambda x: x.toordinal()
        )
        missing_expiries_ordinal = [
            pd.to_datetime(date).toordinal() for date in missing_expires
        ]

        interp_func = interp1d(
            futures_df["expiry_ordinal"],
            futures_df["implied_interest_rate"],
            kind="linear",
            fill_value="extrapolate",
        )

        interpolated_rates = interp_func(missing_expiries_ordinal)

        interpolated_rates_df = pd.DataFrame(
            {"expiry": missing_expires, "implied_interest_rate": interpolated_rates}
        )

        return interpolated_rates_df

    @staticmethod
    def calculate_delta_K(df):
        df = df.sort_values(by="strike").reset_index(drop=True)
        print(df)
        delta_K = pd.Series(dtype=float)
        delta_K[0] = df.loc[1, "strike"] - df.loc[0, "strike"]
        delta_K[df.index[-1]] = (
            df.loc[df.index[-1], "strike"] - df.loc[df.index[-1] - 1, "strike"]
        )

        for i in range(1, len(df) - 1):
            delta_K[i] = (df.loc[i + 1, "strike"] - df.loc[i - 1, "strike"]) / 2

        return delta_K
