
import pandas as pd

from src.funding import (
    calculate_funding_exposure,
    calculate_funding_adjustment,
    calculate_fva_adjusted_value,
    calculate_fva,
)


def sample_position():
    return pd.DataFrame({
        "adjusted_market_value": [
            1000.0,
            -500.0,
        ],
        "time_to_expiry": [
            1.0,
            0.5,
        ],
    })


def test_funding_exposure_uses_absolute_value():
    df = sample_position()

    result = calculate_funding_exposure(df)

    assert result.loc[0, "funding_exposure"] == 1000.0
    assert result.loc[1, "funding_exposure"] == 500.0


def test_funding_adjustment_formula():
    df = sample_position()

    df = calculate_funding_exposure(df)

    result = calculate_funding_adjustment(
        df,
        funding_rate=0.07,
    )

    assert result.loc[0, "funding_adjustment"] == 70.0
    assert result.loc[1, "funding_adjustment"] == 17.5


def test_fva_adjusted_value():
    df = sample_position()

    df["funding_adjustment"] = [70.0, 17.5]

    result = calculate_fva_adjusted_value(df)

    assert result.loc[0, "fva_adjusted_market_value"] == 930.0
    assert result.loc[1, "fva_adjusted_market_value"] == -517.5


def test_complete_fva_pipeline():
    df = sample_position()

    result = calculate_fva(
        df,
        funding_rate=0.07,
    )

    assert "funding_exposure" in result.columns
    assert "funding_rate" in result.columns
    assert "funding_adjustment" in result.columns
    assert "fva_adjusted_market_value" in result.columns


def test_funding_rate_is_stored():
    df = sample_position()

    result = calculate_fva(
        df,
        funding_rate=0.05,
    )

    assert result["funding_rate"].iloc[0] == 0.05
