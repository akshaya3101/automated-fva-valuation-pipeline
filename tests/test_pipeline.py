from pathlib import Path
import subprocess
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_FILE = PROJECT_ROOT / "run_pipeline.py"
FINAL_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "fva_portfolio_summary.csv"
)


def test_pipeline_file_exists():
    assert PIPELINE_FILE.exists()


def test_pipeline_runs_successfully():
    result = subprocess.run(
        [sys.executable, str(PIPELINE_FILE)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "Pipeline failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_pipeline_reports_success():
    result = subprocess.run(
        [sys.executable, str(PIPELINE_FILE)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "PIPELINE COMPLETED SUCCESSFULLY" in result.stdout


def test_final_fva_output_is_created():
    assert FINAL_OUTPUT.exists()


def test_final_fva_output_has_expected_columns():
    df = pd.read_csv(FINAL_OUTPUT)

    expected_columns = [
        "original_market_value",
        "valuation_adjustments",
        "adjusted_market_value",
        "funding_adjustment",
        "final_fva_adjusted_value",
    ]

    for column in expected_columns:
        assert column in df.columns


def test_final_fva_output_contains_one_portfolio_summary():
    df = pd.read_csv(FINAL_OUTPUT)

    assert len(df) == 1


def test_final_fva_value_is_calculated():
    df = pd.read_csv(FINAL_OUTPUT)

    row = df.iloc[0]

    expected = (
        row["adjusted_market_value"]
        - row["funding_adjustment"]
    )

    assert abs(
        row["final_fva_adjusted_value"] - expected
    ) < 1e-6
