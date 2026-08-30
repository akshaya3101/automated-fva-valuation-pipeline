"""
Transform validated NSE option-chain data into
valuation-ready market data.

Important:
- Raw NSE observations are preserved.
- Missing NSE LTP is NOT fabricated.
- A bid/ask midpoint is used only when LTP is unavailable.
- The source of the valuation price is explicitly recorded.
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/nse_option_chain_normalized.csv"
)

OUTPUT_FILE = Path(
    "data/processed/nse_option_chain_transformed.csv"
)


# ---------------------------------------------------------------------
# MARKET SNAPSHOT
# ---------------------------------------------------------------------

# NIFTY underlying value shown on the NSE option-chain snapshot
# used to obtain the downloaded dataset.
#
# This is an external market observation, NOT synthetic trade data.
UNDERLYING_SPOT = 24090.85


# ---------------------------------------------------------------------
# PRICE TRANSFORMATION
# ---------------------------------------------------------------------

def create_valuation_price(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a valuation price while preserving the original NSE LTP.

    Priority:
        1. NSE LTP
        2. Bid/ask midpoint when LTP is unavailable
        3. NA if neither is available
    """

    df = df.copy()

    # Start with the actual NSE market price (LTP)
    df["valuation_price"] = df["market_price"]

    # Track where the valuation price came from
    df["valuation_price_source"] = "NSE_LTP"

    # Identify rows where LTP is unavailable
    missing_ltp = df["market_price"].isna()

    # Calculate midpoint only where both bid and ask exist
    valid_bid_ask = (
        df["bid_price"].notna()
        & df["ask_price"].notna()
    )

    midpoint = (
        df["bid_price"] + df["ask_price"]
    ) / 2

    use_midpoint = missing_ltp & valid_bid_ask

    df.loc[use_midpoint, "valuation_price"] = midpoint[
        use_midpoint
    ]

    df.loc[use_midpoint, "valuation_price_source"] = (
        "BID_ASK_MID"
    )

    # Rows with no LTP and no usable bid/ask remain NA
    df.loc[
        missing_ltp & ~valid_bid_ask,
        "valuation_price_source"
    ] = "UNAVAILABLE"

    return df


# ---------------------------------------------------------------------
# TIME TO EXPIRY
# ---------------------------------------------------------------------

def calculate_time_to_expiry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate calendar time to expiry in years.

    Convention:
        time_to_expiry = days_to_expiry / 365
    """

    df = df.copy()

    df["days_to_expiry"] = (
        df["expiry_date"] - df["observation_date"]
    ).dt.days

    df["time_to_expiry"] = (
        df["days_to_expiry"] / 365.0
    )

    return df


# ---------------------------------------------------------------------
# MONEINESS
# ---------------------------------------------------------------------

def calculate_moneyness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate option moneyness using the NIFTY spot price.

    moneyness = strike_price / underlying_spot
    """

    df = df.copy()

    df["underlying_spot"] = UNDERLYING_SPOT

    df["moneyness"] = (
        df["strike_price"]
        / df["underlying_spot"]
    )

    return df


# ---------------------------------------------------------------------
# INTRINSIC VALUE
# ---------------------------------------------------------------------

def calculate_intrinsic_value(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate intrinsic value for calls and puts.

    Call:
        max(S - K, 0)

    Put:
        max(K - S, 0)
    """

    df = df.copy()

    call_mask = df["option_type"] == "CE"
    put_mask = df["option_type"] == "PE"

    df["intrinsic_value"] = pd.NA

    df.loc[call_mask, "intrinsic_value"] = (
        df.loc[call_mask, "underlying_spot"]
        - df.loc[call_mask, "strike_price"]
    ).clip(lower=0)

    df.loc[put_mask, "intrinsic_value"] = (
        df.loc[put_mask, "strike_price"]
        - df.loc[put_mask, "underlying_spot"]
    ).clip(lower=0)

    return df


# ---------------------------------------------------------------------
# TRANSFORMATION PIPELINE
# ---------------------------------------------------------------------

def transform_nse_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply all market-data transformations.
    """

    df = df.copy()

    # Ensure dates are proper datetime objects
    df["observation_date"] = pd.to_datetime(
        df["observation_date"]
    )

    df["expiry_date"] = pd.to_datetime(
        df["expiry_date"]
    )

    # 1. Create valuation price
    df = create_valuation_price(df)

    # 2. Calculate time to expiry
    df = calculate_time_to_expiry(df)

    # 3. Calculate moneyness
    df = calculate_moneyness(df)

    # 4. Calculate intrinsic value
    df = calculate_intrinsic_value(df)

    return df


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print("Loading normalized NSE data...")

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Input dataset: "
        f"{df.shape[0]} rows × {df.shape[1]} columns"
    )

    transformed = transform_nse_data(df)

    # Create output directory if necessary
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    transformed.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"Transformed dataset: "
        f"{transformed.shape[0]} rows × "
        f"{transformed.shape[1]} columns"
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )

    print("\n=== PRICE SOURCE SUMMARY ===")

    print(
        transformed[
            "valuation_price_source"
        ].value_counts(dropna=False)
    )

    print("\n=== TRANSFORMED SAMPLE ===")

    print(
        transformed[
            [
                "observation_date",
                "underlying",
                "expiry_date",
                "option_type",
                "strike_price",
                "market_price",
                "bid_price",
                "ask_price",
                "valuation_price",
                "valuation_price_source",
                "underlying_spot",
                "moneyness",
                "days_to_expiry",
                "time_to_expiry",
                "intrinsic_value",
            ]
        ].head(10).to_string(index=False)
    )