from pathlib import Path

import pandas as pd


RAW_FILE = Path(
    "data/raw/nse/option-chain-ED-NIFTY-01-Sep-2026.csv"
)

OUTPUT_FILE = Path(
    "data/processed/nse_option_chain_normalized.csv"
)


CALL_COLUMNS = {
    "OI": "open_interest",
    "CHNG IN OI": "change_in_open_interest",
    "VOLUME": "volume",
    "IV": "implied_volatility",
    "LTP": "market_price",
    "CHNG": "price_change",
    "BID QTY": "bid_quantity",
    "BID": "bid_price",
    "ASK": "ask_price",
    "ASK QTY": "ask_quantity",
}


PUT_COLUMNS = {
    "OI.1": "open_interest",
    "CHNG IN OI.1": "change_in_open_interest",
    "VOLUME.1": "volume",
    "IV.1": "implied_volatility",
    "LTP.1": "market_price",
    "CHNG.1": "price_change",
    "BID QTY.1": "bid_quantity",
    "BID.1": "bid_price",
    "ASK.1": "ask_price",
    "ASK QTY.1": "ask_quantity",
}


def load_nse_option_chain(file_path: Path) -> pd.DataFrame:
    """
    Load the raw NSE option-chain CSV.

    The first row contains grouped CALLS/PUTS labels,
    while the second row contains the actual field names.
    """

    return pd.read_csv(
        file_path,
        header=1
    )


def clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert NSE numeric fields into numeric pandas types.

    NSE uses '-' to represent missing values.
    """

    df = df.copy()

    df = df.replace("-", pd.NA)

    numeric_columns = [
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
        "strike_price",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.replace(",", "", regex=False)
                .str.strip()
            )

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def normalize_option_chain(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the NSE wide CALL/PUT structure into
    one option contract per row.
    """

    # Rename strike column first
    df = df.rename(
        columns={
            "STRIKE": "strike_price"
        }
    )

    # -------------------------
    # CALLS
    # -------------------------

    call_data = df[
        list(CALL_COLUMNS.keys()) + ["strike_price"]
    ].copy()

    call_data = call_data.rename(
        columns=CALL_COLUMNS
    )

    call_data["option_type"] = "CE"

    # -------------------------
    # PUTS
    # -------------------------

    put_data = df[
        list(PUT_COLUMNS.keys()) + ["strike_price"]
    ].copy()

    put_data = put_data.rename(
        columns=PUT_COLUMNS
    )

    put_data["option_type"] = "PE"

    # -------------------------
    # Combine CALL + PUT
    # -------------------------

    normalized = pd.concat(
        [call_data, put_data],
        ignore_index=True
    )

    # -------------------------
    # Add dataset metadata
    # -------------------------

    normalized["underlying"] = "NIFTY"
    normalized["expiry_date"] = pd.Timestamp(
        "2026-09-01"
    )
    normalized["observation_date"] = pd.Timestamp(
        "2026-08-27"
    )

    # -------------------------
    # Clean numeric fields
    # -------------------------

    normalized = clean_numeric_columns(
        normalized
    )

    # -------------------------
    # Arrange columns
    # -------------------------

    normalized = normalized[
        [
            "observation_date",
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
        ]
    ]

    # Sort for easier analysis
    normalized = normalized.sort_values(
        by=[
            "strike_price",
            "option_type"
        ]
    ).reset_index(drop=True)

    return normalized


def main() -> None:
    """Run the NSE ingestion and normalization pipeline."""

    print("Loading NSE option-chain data...")

    raw_data = load_nse_option_chain(
        RAW_FILE
    )

    print(
        f"Raw dataset: "
        f"{raw_data.shape[0]} rows × "
        f"{raw_data.shape[1]} columns"
    )

    normalized_data = normalize_option_chain(
        raw_data
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    normalized_data.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Normalized dataset: "
        f"{normalized_data.shape[0]} rows × "
        f"{normalized_data.shape[1]} columns"
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )

    print("\n=== SAMPLE ===")
    print(
        normalized_data.head(10).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()