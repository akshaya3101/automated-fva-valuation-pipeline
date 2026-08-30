"""
Portfolio reporting layer.

Creates an audit-friendly summary from the final FVA valuation output.

Input:
    data/processed/position_fva_valuation.csv

Outputs:
    data/processed/fva_portfolio_summary.csv
    data/processed/fva_exceptions.csv
"""


from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/position_fva_valuation.csv"
)

SUMMARY_FILE = Path(
    "data/processed/fva_portfolio_summary.csv"
)

EXCEPTIONS_FILE = Path(
    "data/processed/fva_exceptions.csv"
)


# ---------------------------------------------------------------------
# PORTFOLIO SUMMARY
# ---------------------------------------------------------------------

def create_portfolio_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create a portfolio-level FVA summary.

    The summary reconciles:

        Original market value
        -> valuation adjustments
        -> adjusted market value
        -> funding adjustment
        -> final FVA-adjusted value
    """

    original_market_value = (
        df["position_market_value"].sum()
    )

    valuation_adjustments = (
        df["total_adjustment"].sum()
    )

    adjusted_market_value = (
        df["adjusted_market_value"].sum()
    )

    funding_adjustment = (
        df["funding_adjustment"].sum()
    )

    final_fva_adjusted_value = (
        df["fva_adjusted_market_value"].sum()
    )

    summary = pd.DataFrame({
        "original_market_value": [
            original_market_value
        ],
        "valuation_adjustments": [
            valuation_adjustments
        ],
        "adjusted_market_value": [
            adjusted_market_value
        ],
        "funding_adjustment": [
            funding_adjustment
        ],
        "final_fva_adjusted_value": [
            final_fva_adjusted_value
        ],
    })

    return summary


# ---------------------------------------------------------------------
# POSITION SUMMARY
# ---------------------------------------------------------------------

def create_position_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create a concise position-level reporting table.
    """

    columns = [
        "position_id",
        "trade_date",
        "underlying",
        "expiry_date",
        "option_type",
        "strike_price",
        "quantity",
        "valuation_price",
        "position_market_value",
        "total_adjustment",
        "adjusted_market_value",
        "funding_adjustment",
        "fva_adjusted_market_value",
    ]

    return df[columns].copy()


# ---------------------------------------------------------------------
# EXCEPTION REPORT
# ---------------------------------------------------------------------

def create_exception_report(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Extract positions requiring attention.

    Exceptions include:

        1. Economic consistency exceptions
        2. Low liquidity
        3. Unmatched market observations
    """

    exception_mask = (
        (df["economic_consistency_flag"] != "OK")
        | (df["liquidity_flag"] != "NORMAL_LIQUIDITY")
        | (df["market_match_status"] != "MATCHED")
    )

    exception_columns = [
        "position_id",
        "option_type",
        "strike_price",
        "quantity",
        "valuation_price",
        "intrinsic_value",
        "economic_consistency_flag",
        "liquidity_flag",
        "market_match_status",
        "total_adjustment",
        "funding_adjustment",
        "fva_adjusted_market_value",
    ]

    return df.loc[
        exception_mask,
        exception_columns,
    ].copy()


# ---------------------------------------------------------------------
# REPORT VALIDATION
# ---------------------------------------------------------------------

def validate_report_reconciliation(
    summary: pd.DataFrame,
) -> None:
    """
    Validate the valuation reconciliation.

    Expected relationship:

        original_market_value
        - valuation_adjustments
        = adjusted_market_value

        adjusted_market_value
        - funding_adjustment
        = final_fva_adjusted_value
    """

    row = summary.iloc[0]

    expected_adjusted = (
        row["original_market_value"]
        - row["valuation_adjustments"]
    )

    expected_final = (
        row["adjusted_market_value"]
        - row["funding_adjustment"]
    )

    if abs(
        expected_adjusted
        - row["adjusted_market_value"]
    ) > 1e-9:
        raise ValueError(
            "Valuation reconciliation failed."
        )

    if abs(
        expected_final
        - row["final_fva_adjusted_value"]
    ) > 1e-9:
        raise ValueError(
            "FVA reconciliation failed."
        )


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "Loading final FVA valuation data..."
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

    # -------------------------------------------------------------
    # Portfolio summary
    # -------------------------------------------------------------

    summary = create_portfolio_summary(df)

    validate_report_reconciliation(summary)

    # -------------------------------------------------------------
    # Position summary
    # -------------------------------------------------------------

    position_summary = create_position_summary(df)

    # -------------------------------------------------------------
    # Exception report
    # -------------------------------------------------------------

    exceptions = create_exception_report(df)

    # -------------------------------------------------------------
    # Save outputs
    # -------------------------------------------------------------

    SUMMARY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    position_summary.to_csv(
        "data/processed/fva_position_report.csv",
        index=False,
    )

    exceptions.to_csv(
        EXCEPTIONS_FILE,
        index=False,
    )

    # -------------------------------------------------------------
    # Console report
    # -------------------------------------------------------------

    print(
        f"\nSaved portfolio summary to: "
        f"{SUMMARY_FILE}"
    )

    print(
        "\n=== PORTFOLIO FVA SUMMARY ==="
    )

    print(
        summary.to_string(index=False)
    )

    print(
        "\n=== EXCEPTIONS ==="
    )

    if exceptions.empty:
        print("No exceptions detected.")
    else:
        print(
            exceptions.to_string(
                index=False
            )
        )

    print(
        f"\nException count: "
        f"{len(exceptions)}"
    )