import pandas as pd

from src.valuation import (
    calculate_position_market_value,
    calculate_position_intrinsic_value,
    calculate_position_time_value,
    value_positions,
)


def sample_position():
    return pd.DataFrame({
        "quantity": [10, -5],
        "valuation_price": [100.0, 50.0],
        "intrinsic_value": [80.0, 20.0],
    })


def test_market_value_respects_position_sign():
    df = sample_position()

    result = calculate_position_market_value(df)

    assert result.loc[0, "position_market_value"] == 1000.0
    assert result.loc[1, "position_market_value"] == -250.0


def test_intrinsic_value_respects_position_sign():
    df = sample_position()

    result = calculate_position_intrinsic_value(df)

    assert result.loc[0, "position_intrinsic_value"] == 800.0
    assert result.loc[1, "position_intrinsic_value"] == -100.0


def test_time_value_is_market_price_minus_intrinsic():
    df = sample_position()

    result = calculate_position_time_value(df)

    assert result.loc[0, "time_value"] == 20.0
    assert result.loc[1, "time_value"] == 30.0


def test_position_time_value_respects_quantity():
    df = sample_position()

    result = calculate_position_time_value(df)

    assert result.loc[0, "position_time_value"] == 200.0
    assert result.loc[1, "position_time_value"] == -150.0


def test_complete_valuation_pipeline():
    df = sample_position()

    result = value_positions(df)

    assert result.loc[0, "position_market_value"] == 1000.0
    assert result.loc[1, "position_market_value"] == -250.0

    assert result.loc[0, "position_intrinsic_value"] == 800.0
    assert result.loc[1, "position_intrinsic_value"] == -100.0

    assert result.loc[0, "position_time_value"] == 200.0
    assert result.loc[1, "position_time_value"] == -150.0
