import pandas as pd

from src.adjustments import (
    calculate_bid_ask_adjustment,
    calculate_liquidity_adjustment,
    calculate_economic_consistency,
    calculate_total_adjustment,
    apply_adjustments,
)


def sample_position():
    return pd.DataFrame({
        "quantity": [10, -5],
        "position_market_value": [1000.0, -250.0],
        "adjusted_market_value": [1000.0, -250.0],
        "bid_price": [99.0, 49.0],
        "ask_price": [101.0, 51.0],
        "volume": [100, 100],
        "open_interest": [100, 100],
        "valuation_price": [100.0, 50.0],
        "intrinsic_value": [80.0, 20.0],
    })


def test_bid_ask_spread_is_calculated():
    df = sample_position()

    result = calculate_bid_ask_adjustment(df)

    assert result.loc[0, "bid_ask_spread"] == 2.0
    assert result.loc[1, "bid_ask_spread"] == 2.0


def test_bid_ask_adjustment_is_based_on_absolute_quantity():
    df = sample_position()

    result = calculate_bid_ask_adjustment(df)

    # spread = 2
    # half spread = 1
    # factor = 0.50
    #
    # 10 × 1 × 0.50 = 5
    #  5 × 1 × 0.50 = 2.5

    assert result.loc[0, "bid_ask_adjustment"] == 5.0
    assert result.loc[1, "bid_ask_adjustment"] == 2.5


def test_normal_liquidity_receives_no_adjustment():
    df = sample_position()

    result = calculate_liquidity_adjustment(df)

    assert result.loc[0, "liquidity_flag"] == "NORMAL_LIQUIDITY"
    assert result.loc[1, "liquidity_flag"] == "NORMAL_LIQUIDITY"

    assert result["liquidity_adjustment"].sum() == 0.0


def test_low_liquidity_is_detected():
    df = sample_position()

    df.loc[0, "volume"] = 1

    result = calculate_liquidity_adjustment(df)

    assert result.loc[0, "liquidity_flag"] == "LOW_LIQUIDITY"
    assert result.loc[0, "liquidity_adjustment"] == 10.0


def test_price_below_intrinsic_is_flagged():
    df = sample_position()

    df.loc[0, "valuation_price"] = 70.0
    df.loc[0, "intrinsic_value"] = 80.0

    result = calculate_economic_consistency(df)

    assert (
        result.loc[0, "economic_consistency_flag"]
        == "PRICE_BELOW_INTRINSIC"
    )


def test_consistent_price_is_not_flagged():
    df = sample_position()

    result = calculate_economic_consistency(df)

    assert result.loc[0, "economic_consistency_flag"] == "OK"
    assert result.loc[1, "economic_consistency_flag"] == "OK"


def test_total_adjustment_is_sum_of_components():
    df = sample_position()

    df = calculate_bid_ask_adjustment(df)
    df = calculate_liquidity_adjustment(df)
    df = calculate_total_adjustment(df)

    result_value = df.loc[0, "total_adjustment"]
    assert result_value == 5.0


def test_adjusted_market_value_is_reduced_by_adjustment():
    df = sample_position()

    df = calculate_bid_ask_adjustment(df)
    df = calculate_liquidity_adjustment(df)
    df = calculate_total_adjustment(df)

    assert df.loc[0, "adjusted_market_value"] == 995.0


def test_complete_adjustment_pipeline():
    df = sample_position()

    result = apply_adjustments(df)

    assert "bid_ask_adjustment" in result.columns
    assert "liquidity_adjustment" in result.columns
    assert "total_adjustment" in result.columns
    assert "adjusted_market_value" in result.columns
    assert "economic_consistency_flag" in result.columns
