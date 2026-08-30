"""
Match synthetic internal positions to real NSE market observations.

The internal positions are synthetic, while the market data comes
from the real NSE option-chain dataset.

This module performs the data join only.
It does NOT perform valuation calculations.
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------

POSITIONS_FILE = Path(
    "data/processed/synthetic_positions.csv"
)

MARKET_DATA_FILE = Path(
    "data/processed/nse_option_chain_transformed.csv"
)

OUTPUT_FILE = Path(
    "data/processed/position_market_matches.csv"
)


# ---------------------------------------------------------------------
# MATCHING KEYS
# ---------------------------------------------------------------------

POSITION_KEYS = [
    "trade_date",
    "underlying",
    "expiry_date",
    "option_type",
    "strike_price",
]

MARKET_KEYS = [
    "observation_date",
    "underlying",
    "expiry_date",
    "option_type",
    "strike_price",
]


# ---------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------

def load_positions(
    filepath: Path,
) -> pd.DataFrame:
    """Load synthetic internal positions."""

    return pd.read_csv(
        filepath,
        parse_dates=[
            "trade_date",
            "expiry_date",
        ],
    )


def load_market_data(
    filepath: Path,
) -> pd.DataFrame:
    """Load transformed real NSE market data."""

    return pd.read_csv(
        filepath,
        parse_dates=[
            "observation_date",
            "expiry_date",
        ],
    )


# ---------------------------------------------------------------------
# PREPARE MARKET DATA
# ---------------------------------------------------------------------

def prepare_market_data(
    market_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Rename the market observation date to trade_date
    so that the two datasets share the same matching key.
    """

    market_data = market_data.copy()

    market_data = market_data.rename(
        columns={
            "observation_date": "trade_date"
        }
    )

    return market_data


# ---------------------------------------------------------------------
# MATCH POSITIONS
# ---------------------------------------------------------------------

def match_positions_to_market(
    positions: pd.DataFrame,
    market_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match each synthetic internal position with
    its corresponding NSE market observation.

    The matching key is:

        trade_date
        underlying
        expiry_date
        option_type
        strike_price
    """

    market_data = prepare_market_data(
        market_data
    )

    # Only bring market fields needed downstream.
    market_columns = [
        "trade_date",
        "underlying",
        "expiry_date",
        "option_type",
        "strike_price",
        "open_interest",
        "change_in_open_interest",
        "volume",
        "implied_volatility",
        "market_price",
        "price_change",
        "bid_quantity",
        "bid_price",
        "ask_price",
        "ask_quantity",
        "valuation_price",
        "valuation_price_source",
        "underlying_spot",
        "moneyness",
        "days_to_expiry",
        "time_to_expiry",
        "intrinsic_value",
    ]

    market_data = market_data[
        market_columns
    ].copy()

    # Ensure the market dataset has one observation
    # per contract/date matching key.
    duplicate_market_rows = market_data[
        market_data.duplicated(
            subset=POSITION_KEYS,
            keep=False,
        )
    ]

    if not duplicate_market_rows.empty:
        raise ValueError(
            "Duplicate market observations found "
            "for matching keys:\n"
            f"{duplicate_market_rows}"
        )

    # Perform a LEFT JOIN so every internal position
    # remains visible even if a market match is missing.
    matched = positions.merge(
        market_data,
        on=POSITION_KEYS,
        how="left",
        indicator=True,
        validate="one_to_one",
    )

    # Explicit match status.
    matched["market_match_status"] = (
        matched["_merge"]
        .map(
            {
                "both": "MATCHED",
                "left_only": "UNMATCHED",
                "right_only": "UNEXPECTED",
            }
        )
    )

    matched = matched.drop(
        columns=["_merge"]
    )

    return matched


# ---------------------------------------------------------------------
# VALIDATE MATCHES
# ---------------------------------------------------------------------

def validate_market_matches(
    matched: pd.DataFrame,
) -> None:
    """
    Fail loudly if any synthetic position cannot
    be matched to real NSE market data.
    """

    unmatched = matched[
        matched["market_match_status"]
        == "UNMATCHED"
    ]

    if not unmatched.empty:
        raise ValueError(
            "Unmatched internal positions found:\n"
            f"{unmatched[POSITION_KEYS + ['position_id']]}"
        )


# ---------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------

def run_matching_pipeline() -> pd.DataFrame:
    """Run the complete position-to-market matching process."""

    print("Loading synthetic internal positions...")

    positions = load_positions(
        POSITIONS_FILE
    )

    print(
        f"Internal positions: "
        f"{len(positions)}"
    )

    print(
        "\nLoading transformed NSE market data..."
    )

    market_data = load_market_data(
        MARKET_DATA_FILE
    )

    print(
        f"Market observations: "
        f"{len(market_data)}"
    )

    print("\nMatching positions to NSE data...")

    matched = match_positions_to_market(
        positions,
        market_data,
    )

    validate_market_matches(
        matched
    )

    return matched


# ---------------------------------------------------------------------
# SCRIPT ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":

    matched_data = run_matching_pipeline()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    matched_data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )

    print(
        "\n=== MATCH SUMMARY ==="
    )

    print(
        matched_data[
            "market_match_status"
        ].value_counts()
    )

    print(
        "\n=== POSITION / MARKET MATCHES ==="
    )

    display_columns = [
        "position_id",
        "trade_date",
        "underlying",
        "expiry_date",
        "option_type",
        "strike_price",
        "quantity",
        "position_side",
        "valuation_price",
        "valuation_price_source",
        "implied_volatility",
        "underlying_spot",
        "time_to_expiry",
        "intrinsic_value",
        "market_match_status",
    ]

    print(
        matched_data[
            display_columns
        ].to_string(index=False)
    )