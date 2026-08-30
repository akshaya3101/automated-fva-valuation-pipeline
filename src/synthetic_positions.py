"""
Generate synthetic internal option positions.

These positions are hypothetical internal portfolio data.
They are NOT NSE transaction records.

The contracts are deliberately selected from strikes
available in the real NSE option-chain snapshot.
"""

from pathlib import Path

import pandas as pd


OUTPUT_FILE = Path(
    "data/processed/synthetic_positions.csv"
)


POSITIONS = [
    {
        "position_id": "POS001",
        "trade_date": "2026-08-27",
        "underlying": "NIFTY",
        "expiry_date": "2026-09-01",
        "option_type": "CE",
        "strike_price": 24000,
        "quantity": 50,
        "position_side": "LONG",
    },
    {
        "position_id": "POS002",
        "trade_date": "2026-08-27",
        "underlying": "NIFTY",
        "expiry_date": "2026-09-01",
        "option_type": "PE",
        "strike_price": 24000,
        "quantity": 50,
        "position_side": "LONG",
    },
    {
        "position_id": "POS003",
        "trade_date": "2026-08-27",
        "underlying": "NIFTY",
        "expiry_date": "2026-09-01",
        "option_type": "CE",
        "strike_price": 24500,
        "quantity": -25,
        "position_side": "SHORT",
    },
    {
        "position_id": "POS004",
        "trade_date": "2026-08-27",
        "underlying": "NIFTY",
        "expiry_date": "2026-09-01",
        "option_type": "PE",
        "strike_price": 23500,
        "quantity": -25,
        "position_side": "SHORT",
    },
    {
        "position_id": "POS005",
        "trade_date": "2026-08-27",
        "underlying": "NIFTY",
        "expiry_date": "2026-09-01",
        "option_type": "CE",
        "strike_price": 23000,
        "quantity": 100,
        "position_side": "LONG",
    },
    {
        "position_id": "POS006",
        "trade_date": "2026-08-27",
        "underlying": "NIFTY",
        "expiry_date": "2026-09-01",
        "option_type": "PE",
        "strike_price": 25000,
        "quantity": 100,
        "position_side": "LONG",
    },
]


def create_positions() -> pd.DataFrame:
    """Create the synthetic internal position dataset."""

    df = pd.DataFrame(POSITIONS)

    df["trade_date"] = pd.to_datetime(
        df["trade_date"]
    )

    df["expiry_date"] = pd.to_datetime(
        df["expiry_date"]
    )

    # Explicit provenance flag.
    df["data_source"] = "SYNTHETIC_INTERNAL"

    return df


def validate_position_contracts(
    positions: pd.DataFrame,
    market_data: pd.DataFrame,
) -> None:
    """
    Verify that every synthetic position refers to
    a contract available in the real NSE dataset.
    """

    market_keys = market_data[
        [
            "underlying",
            "expiry_date",
            "option_type",
            "strike_price",
        ]
    ].drop_duplicates()

    position_keys = positions[
        [
            "underlying",
            "expiry_date",
            "option_type",
            "strike_price",
        ]
    ].drop_duplicates()

    merged = position_keys.merge(
        market_keys,
        on=[
            "underlying",
            "expiry_date",
            "option_type",
            "strike_price",
        ],
        how="left",
        indicator=True,
    )

    missing = merged[
        merged["_merge"] == "left_only"
    ]

    if not missing.empty:
        raise ValueError(
            "Synthetic positions reference "
            "contracts not found in NSE market data:\n"
            f"{missing}"
        )


if __name__ == "__main__":

    market_file = Path(
        "data/processed/"
        "nse_option_chain_transformed.csv"
    )

    market_data = pd.read_csv(
        market_file,
        parse_dates=[
            "observation_date",
            "expiry_date",
        ],
    )

    positions = create_positions()

    validate_position_contracts(
        positions,
        market_data,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    positions.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"Created {len(positions)} synthetic positions."
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("\n=== SYNTHETIC POSITIONS ===")

    print(
        positions.to_string(index=False)
    )

    print(
        "\nContract validation: PASS"
    )