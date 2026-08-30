import pandas as pd

from src.validation import (
    validate_required_columns,
    validate_option_types,
    validate_strikes,
    validate_expiry_dates,
    validate_negative_values,
    validate_bid_ask,
    find_duplicate_contracts,
)


def base_dataframe():
    return pd.DataFrame({
        "observation_date": pd.to_datetime(["2026-08-27"]),
        "underlying": ["NIFTY"],
        "expiry_date": pd.to_datetime(["2026-09-01"]),
        "option_type": ["CE"],
        "strike_price": [24000],
        "open_interest": [100],
        "change_in_open_interest": [10],
        "volume": [50],
        "implied_volatility": [15.5],
        "market_price": [250],
        "price_change": [5],
        "bid_quantity": [100],
        "bid_price": [245],
        "ask_price": [255],
        "ask_quantity": [100],
    })


def test_required_columns_exist():
    df = base_dataframe()

    missing = validate_required_columns(df)

    assert missing == []


def test_invalid_option_type_is_detected():
    df = base_dataframe()
    df.loc[0, "option_type"] = "XX"

    invalid = validate_option_types(df)

    assert len(invalid) == 1


def test_invalid_strike_is_detected():
    df = base_dataframe()
    df.loc[0, "strike_price"] = -100

    invalid = validate_strikes(df)

    assert len(invalid) == 1


def test_missing_strike_is_detected():
    df = base_dataframe()
    df.loc[0, "strike_price"] = None

    invalid = validate_strikes(df)

    assert len(invalid) == 1


def test_expired_contract_is_detected():
    df = base_dataframe()
    df.loc[0, "expiry_date"] = pd.Timestamp("2026-08-26")

    invalid = validate_expiry_dates(df)

    assert len(invalid) == 1


def test_negative_market_value_is_detected():
    df = base_dataframe()
    df.loc[0, "volume"] = -10

    invalid = validate_negative_values(df)

    assert len(invalid) == 1


def test_invalid_bid_ask_is_detected():
    df = base_dataframe()
    df.loc[0, "bid_price"] = 300
    df.loc[0, "ask_price"] = 250

    invalid = validate_bid_ask(df)

    assert len(invalid) == 1


def test_duplicate_contract_is_detected():
    df = pd.concat(
        [base_dataframe(), base_dataframe()],
        ignore_index=True,
    )

    duplicates = find_duplicate_contracts(df)

    assert len(duplicates) == 2