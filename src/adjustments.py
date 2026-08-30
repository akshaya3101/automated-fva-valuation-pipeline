"""
Valuation adjustment layer.

This module calculates transparent valuation adjustments
from the matched NSE market data.

Important:
    - Original NSE valuation is preserved.
    - Adjustments are calculated separately.
    - No market observation is overwritten.
    - Synthetic/internal data remains identifiable.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/position_valuation.csv"
)

OUTPUT_FILE = Path(
    "data/processed/position_adjusted_valuation.csv"
)


# ---------------------------------------------------------------------
# ADJUSTMENT PARAMETERS
# ---------------------------------------------------------------------

# Liquidity thresholds.
#
# These are project-model parameters, not NSE-provided values.
MIN_VOLUME_THRESHOLD = 10
MIN_OPEN_INTEREST_THRESHOLD = 10

# Adjustment rate applied to the half bid-ask spread.
#
# This represents the estimated price concession associated
# with exiting a position through the observable market.
BID_ASK_ADJUSTMENT_FACTOR = 0.50

# Liquidity adjustment rate.
#
# This is deliberately small and transparent.
LIQUIDITY_ADJUSTMENT_RATE = 0.01


# ---------------------------------------------------------------------
# BID-ASK ADJUSTMENT
# ---------------------------------------------------------------------

def calculate_bid_ask_adjustment(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate a bid-ask based valuation adjustment.

    Formula:

        spread = ask_price - bid_price

        half_spread = spread / 2

        unit_adjustment =
            half_spread × adjustment_factor

        position_adjustment =
            abs(quantity) × unit_adjustment

    The adjustment is expressed as a positive reserve amount.
    """

    df = df.copy()

    valid_bid_ask = (
        df["bid_price"].notna()
        & df["ask_price"].notna()
        & (df["ask_price"] >= df["bid_price"])
    )

    df["bid_ask_spread"] = np.where(
        valid_bid_ask,
        df["ask_price"] - df["bid_price"],
        np.nan,
    )

    df["half_bid_ask_spread"] = (
        df["bid_ask_spread"] / 2
    )

    df["bid_ask_adjustment"] = np.where(
        valid_bid_ask,
        abs(df["quantity"])
        * df["half_bid_ask_spread"]
        * BID_ASK_ADJUSTMENT_FACTOR,
        0.0,
    )

    return df


# ---------------------------------------------------------------------
# LIQUIDITY ADJUSTMENT
# ---------------------------------------------------------------------

def calculate_liquidity_adjustment(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate a simple liquidity reserve.

    A position receives a liquidity adjustment when either:

        volume < MIN_VOLUME_THRESHOLD

    OR

        open_interest < MIN_OPEN_INTEREST_THRESHOLD

    The reserve is calculated as:

        abs(position_market_value)
        × LIQUIDITY_ADJUSTMENT_RATE

    Missing liquidity fields are treated conservatively as
    insufficient evidence of liquidity.
    """

    df = df.copy()

    low_volume = (
        df["volume"].isna()
        | (df["volume"] < MIN_VOLUME_THRESHOLD)
    )

    low_open_interest = (
        df["open_interest"].isna()
        | (
            df["open_interest"]
            < MIN_OPEN_INTEREST_THRESHOLD
        )
    )

    df["liquidity_flag"] = np.where(
        low_volume | low_open_interest,
        "LOW_LIQUIDITY",
        "NORMAL_LIQUIDITY",
    )

    df["liquidity_adjustment"] = np.where(
        df["liquidity_flag"] == "LOW_LIQUIDITY",
        abs(df["position_market_value"])
        * LIQUIDITY_ADJUSTMENT_RATE,
        0.0,
    )

    return df


# ---------------------------------------------------------------------
# ECONOMIC CONSISTENCY CHECK
# ---------------------------------------------------------------------

def calculate_economic_consistency(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Identify observations where valuation price is below
    theoretical intrinsic value.

    For an option:

        valuation_price >= intrinsic_value

    is the expected economic relationship.

    The observation is NOT changed. It is only flagged.
    """

    df = df.copy()

    df["economic_consistency_flag"] = np.where(
        df["valuation_price"]
        < df["intrinsic_value"],
        "PRICE_BELOW_INTRINSIC",
        "OK",
    )

    return df


# ---------------------------------------------------------------------
# TOTAL ADJUSTMENT
# ---------------------------------------------------------------------

def calculate_total_adjustment(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate all valuation adjustment components.

    Total adjustment:

        bid_ask_adjustment
        + liquidity_adjustment
    """

    df = df.copy()

    df["total_adjustment"] = (
        df["bid_ask_adjustment"]
        + df["liquidity_adjustment"]
    )

    # Adjusted value is reported separately from the original
    # NSE-derived market value.
    df["adjusted_market_value"] = (
        df["position_market_value"]
        - df["total_adjustment"]
    )

    return df


# ---------------------------------------------------------------------
# COMPLETE ADJUSTMENT PIPELINE
# ---------------------------------------------------------------------

def apply_adjustments(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply all valuation adjustments and exception flags.
    """

    df = calculate_bid_ask_adjustment(df)

    df = calculate_liquidity_adjustment(df)

    df = calculate_economic_consistency(df)

    df = calculate_total_adjustment(df)

    return df


# ---------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------

def create_adjustment_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create portfolio-level adjustment summary.
    """

    return pd.DataFrame({
        "market_value": [
            df["position_market_value"].sum()
        ],
        "bid_ask_adjustment": [
            df["bid_ask_adjustment"].sum()
        ],
        "liquidity_adjustment": [
            df["liquidity_adjustment"].sum()
        ],
        "total_adjustment": [
            df["total_adjustment"].sum()
        ],
        "adjusted_market_value": [
            df["adjusted_market_value"].sum()
        ],
    })


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "Loading position valuation data..."
    )

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=[
            "trade_date",
            "expiry_date",
        ],
    )

    print(
        f"Input dataset: "
        f"{df.shape[0]} positions × "
        f"{df.shape[1]} columns"
    )

    # Apply adjustment layer.
    adjusted = apply_adjustments(df)

    # Save output.
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    adjusted.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )

    # ---------------------------------------------------------------
    # POSITION LEVEL REPORT
    # ---------------------------------------------------------------

    print(
        "\n=== POSITION ADJUSTMENTS ==="
    )

    display_columns = [
        "position_id",
        "option_type",
        "strike_price",
        "quantity",
        "position_market_value",
        "bid_ask_spread",
        "bid_ask_adjustment",
        "liquidity_flag",
        "liquidity_adjustment",
        "economic_consistency_flag",
        "total_adjustment",
        "adjusted_market_value",
    ]

    print(
        adjusted[
            display_columns
        ].to_string(index=False)
    )

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------

    summary = create_adjustment_summary(
        adjusted
    )

    print(
        "\n=== ADJUSTMENT SUMMARY ==="
    )

    print(
        summary.to_string(index=False)
    )

    # ---------------------------------------------------------------
    # EXCEPTIONS
    # ---------------------------------------------------------------

    exceptions = adjusted[
        adjusted["economic_consistency_flag"]
        != "OK"
    ]

    print(
        "\n=== ECONOMIC CONSISTENCY EXCEPTIONS ==="
    )

    if exceptions.empty:
        print("No economic consistency exceptions.")

    else:
        print(
            exceptions[
                [
                    "position_id",
                    "option_type",
                    "strike_price",
                    "valuation_price",
                    "intrinsic_value",
                    "economic_consistency_flag",
                ]
            ].to_string(index=False)
        )