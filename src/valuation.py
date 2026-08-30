"""
Position-level valuation engine.

This module calculates market value from the matched
internal positions and real NSE market observations.

It deliberately separates:
    1. Market price
    2. Signed position quantity
    3. Position market value

Contract lot-size treatment is kept explicit and is NOT
silently assumed here.
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/position_market_matches.csv"
)

OUTPUT_FILE = Path(
    "data/processed/position_valuation.csv"
)


# ---------------------------------------------------------------------
# VALUATION
# ---------------------------------------------------------------------

def calculate_position_market_value(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate position-level market value.

    Formula:

        market_value = quantity × valuation_price

    Quantity is signed:
        positive = long
        negative = short

    This is a unit-based valuation. Contract lot size is
    deliberately not applied at this stage.
    """

    df = df.copy()

    df["position_market_value"] = (
        df["quantity"]
        * df["valuation_price"]
    )

    return df


# ---------------------------------------------------------------------
# INTRINSIC VALUE
# ---------------------------------------------------------------------

def calculate_position_intrinsic_value(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate signed position intrinsic value.

    Formula:

        position_intrinsic_value =
            quantity × intrinsic_value
    """

    df = df.copy()

    df["position_intrinsic_value"] = (
        df["quantity"]
        * df["intrinsic_value"]
    )

    return df


# ---------------------------------------------------------------------
# TIME VALUE
# ---------------------------------------------------------------------

def calculate_position_time_value(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate option time value.

    Contract-level:

        time_value =
            market_price - intrinsic_value

    Position-level:

        position_time_value =
            quantity × time_value
    """

    df = df.copy()

    df["time_value"] = (
        df["valuation_price"]
        - df["intrinsic_value"]
    )

    df["position_time_value"] = (
        df["quantity"]
        * df["time_value"]
    )

    return df


# ---------------------------------------------------------------------
# COMPLETE VALUATION
# ---------------------------------------------------------------------

def value_positions(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply all position-level valuation calculations.
    """

    df = calculate_position_market_value(df)

    df = calculate_position_intrinsic_value(df)

    df = calculate_position_time_value(df)

    return df


# ---------------------------------------------------------------------
# VALUATION SUMMARY
# ---------------------------------------------------------------------

def create_valuation_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create an aggregate valuation summary.
    """

    summary = pd.DataFrame({
        "total_market_value": [
            df["position_market_value"].sum()
        ],
        "total_intrinsic_value": [
            df["position_intrinsic_value"].sum()
        ],
        "total_time_value": [
            df["position_time_value"].sum()
        ],
    })

    return summary


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print("Loading matched position-market data...")

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

        # Ensure every position has a market match
    unmatched = df[
        df["market_match_status"] != "MATCHED"
    ]

    if not unmatched.empty:
        details = unmatched[
            ["position_id", "market_match_status"]
        ].to_string(index=False)

        raise ValueError(
            "Cannot value unmatched positions:\n"
            f"{details}"
        )

    # Run valuation
    valued = value_positions(df)

    # Save result
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    valued.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # Summary
    summary = create_valuation_summary(
        valued
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )

    print(
        "\n=== POSITION VALUATION ==="
    )

    display_columns = [
        "position_id",
        "option_type",
        "strike_price",
        "quantity",
        "valuation_price",
        "position_market_value",
        "intrinsic_value",
        "position_intrinsic_value",
        "time_value",
        "position_time_value",
    ]

    print(
        valued[
            display_columns
        ].to_string(index=False)
    )

    print(
        "\n=== PORTFOLIO VALUATION SUMMARY ==="
    )

    print(
        summary.to_string(index=False)
    )