"""
Funding adjustment / FVA layer.

This module calculates a simplified funding adjustment
using the internally defined funding assumption.

IMPORTANT:
    - NSE market data remains unchanged.
    - Funding rate is a SYNTHETIC INTERNAL assumption.
    - The funding adjustment is calculated separately.
    - This is a project-level simplified FVA methodology.
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/position_adjusted_valuation.csv"
)

OUTPUT_FILE = Path(
    "data/processed/position_fva_valuation.csv"
)


# ---------------------------------------------------------------------
# FUNDING ASSUMPTIONS
# ---------------------------------------------------------------------

# Synthetic internal funding rate.
#
# This value does NOT come from NSE.
# It represents an assumed annual funding cost for this project.

FUNDING_RATE = 0.07


# ---------------------------------------------------------------------
# FUNDING EXPOSURE
# ---------------------------------------------------------------------

def calculate_funding_exposure(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate the funding exposure for each position.

    We use the absolute adjusted market value as the
    funding exposure.

    Formula:

        funding_exposure =
            abs(adjusted_market_value)
    """

    df = df.copy()

    df["funding_exposure"] = (
        df["adjusted_market_value"].abs()
    )

    return df


# ---------------------------------------------------------------------
# FUNDING ADJUSTMENT
# ---------------------------------------------------------------------

def calculate_funding_adjustment(
    df: pd.DataFrame,
    funding_rate: float = FUNDING_RATE,
) -> pd.DataFrame:
    """
    Calculate the funding adjustment.

    Formula:

        funding_adjustment =
            funding_exposure
            × funding_rate
            × time_to_expiry

    The funding rate is expressed as a decimal.

        7% = 0.07
    """

    df = df.copy()

    df["funding_rate"] = funding_rate

    df["funding_adjustment"] = (
        df["funding_exposure"]
        * df["funding_rate"]
        * df["time_to_expiry"]
    )

    return df


# ---------------------------------------------------------------------
# FINAL FVA VALUE
# ---------------------------------------------------------------------

def calculate_fva_adjusted_value(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate the final FVA-adjusted market value.

    Formula:

        final_fva_value =
            adjusted_market_value
            - funding_adjustment
    """

    df = df.copy()

    df["fva_adjusted_market_value"] = (
        df["adjusted_market_value"]
        - df["funding_adjustment"]
    )

    return df


# ---------------------------------------------------------------------
# COMPLETE FVA PIPELINE
# ---------------------------------------------------------------------

def calculate_fva(
    df: pd.DataFrame,
    funding_rate: float = FUNDING_RATE,
) -> pd.DataFrame:
    """
    Apply the complete funding/FVA calculation.
    """

    df = calculate_funding_exposure(df)

    df = calculate_funding_adjustment(
        df,
        funding_rate=funding_rate,
    )

    df = calculate_fva_adjusted_value(df)

    return df


# ---------------------------------------------------------------------
# FVA SUMMARY
# ---------------------------------------------------------------------

def create_fva_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create a portfolio-level FVA summary.
    """

    summary = pd.DataFrame({
        "original_market_value": [
            df["position_market_value"].sum()
        ],
        "valuation_adjustments": [
            df["total_adjustment"].sum()
        ],
        "adjusted_market_value": [
            df["adjusted_market_value"].sum()
        ],
        "funding_adjustment": [
            df["funding_adjustment"].sum()
        ],
        "final_fva_adjusted_value": [
            df[
                "fva_adjusted_market_value"
            ].sum()
        ],
    })

    return summary


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "Loading adjusted valuation data..."
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

    print(
        f"\nSynthetic funding rate: "
        f"{FUNDING_RATE:.2%}"
    )

    print(
        "Funding rate source: "
        "SYNTHETIC_INTERNAL"
    )

    # Run FVA calculation.
    fva = calculate_fva(df)

    # Save output.
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fva.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )

    # ---------------------------------------------------------------
    # POSITION-LEVEL FVA
    # ---------------------------------------------------------------

    print(
        "\n=== POSITION FVA ==="
    )

    display_columns = [
        "position_id",
        "option_type",
        "strike_price",
        "quantity",
        "adjusted_market_value",
        "funding_exposure",
        "funding_rate",
        "time_to_expiry",
        "funding_adjustment",
        "fva_adjusted_market_value",
    ]

    print(
        fva[
            display_columns
        ].to_string(index=False)
    )

    # ---------------------------------------------------------------
    # PORTFOLIO SUMMARY
    # ---------------------------------------------------------------

    summary = create_fva_summary(
        fva
    )

    print(
        "\n=== FVA SUMMARY ==="
    )

    print(
        summary.to_string(index=False)
    )