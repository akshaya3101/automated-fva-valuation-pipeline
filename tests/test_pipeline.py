"""
End-to-end tests for the Automated FVA Valuation Pipeline.
"""

from pathlib import Path
import subprocess
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def test_pipeline_script_exists():
    """Verify that the main pipeline entry point exists."""

    pipeline_file = PROJECT_ROOT / "run_pipeline.py"

    assert pipeline_file.exists()


def test_main_entry_point_exists():
    """Verify that the application entry point exists."""

    main_file = PROJECT_ROOT / "main.py"

    assert main_file.exists()


def test_required_pipeline_stages_exist():
    """Verify that every pipeline stage exists."""

    required_stages = [
        "ingestion.py",
        "validation.py",
        "transformations.py",
        "synthetic_positions.py",
        "market_matching.py",
        "valuation.py",
        "adjustments.py",
        "funding.py",
        "reporting.py",
    ]

    src_dir = PROJECT_ROOT / "src"

    for stage in required_stages:
        assert (src_dir / stage).exists()


def test_final_fva_output_exists():
    """Verify that the final FVA valuation output exists."""

    output_file = (
        PROCESSED_DIR
        / "position_fva_valuation.csv"
    )

    assert output_file.exists()


def test_portfolio_summary_exists():
    """Verify that the portfolio summary exists."""

    summary_file = (
        PROCESSED_DIR
        / "fva_portfolio_summary.csv"
    )

    assert summary_file.exists()


def test_exception_report_exists():
    """Verify that the exception report exists."""

    exception_file = (
        PROCESSED_DIR
        / "fva_exceptions.csv"
    )

    assert exception_file.exists()


def test_final_fva_output_has_positions():
    """Verify that the final output contains position-level results."""

    output_file = (
        PROCESSED_DIR
        / "position_fva_valuation.csv"
    )

    df = pd.read_csv(output_file)

    assert len(df) > 0
    assert "position_id" in df.columns
    assert "fva_adjusted_market_value" in df.columns


def test_portfolio_summary_reconciles():
    """Verify the final FVA reconciliation."""

    summary_file = (
        PROCESSED_DIR
        / "fva_portfolio_summary.csv"
    )

    df = pd.read_csv(summary_file)

    row = df.iloc[0]

    expected_adjusted = (
        row["original_market_value"]
        - row["valuation_adjustments"]
    )

    expected_final = (
        row["adjusted_market_value"]
        - row["funding_adjustment"]
    )

    assert abs(
        expected_adjusted
        - row["adjusted_market_value"]
    ) < 1e-9

    assert abs(
        expected_final
        - row["final_fva_adjusted_value"]
    ) < 1e-9


def test_pipeline_runs_successfully():
    """
    Execute the complete pipeline through main.py.

    This is the true end-to-end integration test.
    """

    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    assert (
        "PIPELINE COMPLETED SUCCESSFULLY"
        in result.stdout
    )