import pandas as pd


REQUIRED_COLUMNS = [
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


def validate_required_columns(
    df: pd.DataFrame,
) -> list[str]:
    """Check that all required columns exist."""

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    return missing_columns


def validate_option_types(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Return rows containing invalid option types."""

    valid_types = {"CE", "PE"}

    return df[
        ~df["option_type"].isin(valid_types)
    ].copy()


def validate_strikes(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Return rows with invalid strike prices."""

    return df[
        df["strike_price"].isna()
        | (df["strike_price"] <= 0)
    ].copy()


def validate_expiry_dates(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return rows where expiry occurs before
    the market observation date.
    """

    return df[
        df["expiry_date"] < df["observation_date"]
    ].copy()


def validate_negative_values(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return rows containing invalid negative
    values for non-negative market fields.
    """

    non_negative_columns = [
        "open_interest",
        "volume",
        "implied_volatility",
        "bid_quantity",
        "ask_quantity",
    ]

    invalid_rows = pd.Series(
        False,
        index=df.index
    )

    for column in non_negative_columns:
        invalid_rows |= (
            df[column].notna()
            & (df[column] < 0)
        )

    return df[invalid_rows].copy()


def validate_bid_ask(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return rows where both bid and ask exist
    but bid is greater than ask.
    """

    invalid = (
        df["bid_price"].notna()
        & df["ask_price"].notna()
        & (df["bid_price"] > df["ask_price"])
    )

    return df[invalid].copy()


def find_duplicate_contracts(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Return duplicated option contracts."""

    contract_keys = [
        "observation_date",
        "underlying",
        "expiry_date",
        "option_type",
        "strike_price",
    ]

    return df[
        df.duplicated(
            subset=contract_keys,
            keep=False,
        )
    ].copy()

def calculate_data_completeness(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate missing-value statistics for each column.
    """

    completeness = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "total_rows": len(df),
    })

    completeness["missing_percentage"] = (
        completeness["missing_count"]
        / completeness["total_rows"]
        * 100
    )

    completeness["completeness_percentage"] = (
        100
        - completeness["missing_percentage"]
    )

    return completeness.sort_values(
        by="missing_percentage",
        ascending=False,
    )

def run_validation(
    df: pd.DataFrame,
) -> dict:
    """Run all data-quality checks."""

    missing_columns = validate_required_columns(df)

    if missing_columns:
        return {
            "status": "FAILED",
            "missing_columns": missing_columns,
        }

    results = {
        "invalid_option_types": validate_option_types(df),
        "invalid_strikes": validate_strikes(df),
        "invalid_expiry_dates": validate_expiry_dates(df),
        "negative_values": validate_negative_values(df),
        "invalid_bid_ask": validate_bid_ask(df),
        "duplicate_contracts": find_duplicate_contracts(df),
        "completeness": calculate_data_completeness(df),
    }

    return results

def print_validation_report(
    results: dict,
) -> None:
    """Print a readable validation report."""
    if "completeness" in results:
        print("\n=== DATA COMPLETENESS ===")

        completeness = results["completeness"]

        print(
            completeness.to_string(
                formatters={
                    "missing_percentage": "{:.2f}%".format,
                    "completeness_percentage": "{:.2f}%".format,
                }
            )
        )

    print("\n=== DATA QUALITY REPORT ===")

    if results.get("status") == "FAILED":
        print("Status: FAILED")
        print(
            "Missing columns:",
            results["missing_columns"],
        )
        return

    total_errors = 0

    for check_name, invalid_rows in results.items():
        if check_name == "completeness":
            continue
        error_count = len(invalid_rows)
        total_errors += error_count
        status = "PASS" if error_count == 0 else "FAIL"
        print(
            f"{check_name:25} "
            f"{status:5} "
            f"({error_count} rows)"
        )

    print(
        f"\nTotal validation errors: "
        f"{total_errors}"
    )


if __name__ == "__main__":

    input_file = (
        "data/processed/"
        "nse_option_chain_normalized.csv"
    )

    data = pd.read_csv(
        input_file,
        parse_dates=[
            "observation_date",
            "expiry_date",
        ],
    )

    results = run_validation(data)

    print_validation_report(results)
