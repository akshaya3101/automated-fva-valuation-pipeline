"""
End-to-end automated FVA valuation pipeline.

Runs every stage of the valuation workflow in sequence:

1. Ingestion
2. Validation
3. Transformation
4. Synthetic position generation
5. Market matching
6. Position valuation
7. Valuation adjustments
8. Funding / FVA
9. Portfolio reporting
The pipeline stops immediately if any stage fails.
"""

from pathlib import Path
import subprocess
import sys
import os


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"


PIPELINE_STAGES = [
    ("Ingestion", SRC_DIR / "ingestion.py"),
    ("Validation", SRC_DIR / "validation.py"),
    ("Transformation", SRC_DIR / "transformations.py"),
    ("Synthetic Position Generation", SRC_DIR / "synthetic_positions.py"),
    ("Market Matching", SRC_DIR / "market_matching.py"),
    ("Position Valuation", SRC_DIR / "valuation.py"),
    ("Valuation Adjustments", SRC_DIR / "adjustments.py"),
    ("Funding / FVA", SRC_DIR / "funding.py"),
    ("Portfolio Reporting", SRC_DIR / "reporting.py"),
]


def run_stage(stage_name, script_path):
    print("\n" + "=" * 70)
    print(f"RUNNING: {stage_name}")
    print("=" * 70)

    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return False

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        env=env,
    )

    if result.returncode != 0:
        print(f"\nPIPELINE FAILED at: {stage_name}")
        print(f"Script: {script_path}")
        return False

    print(f"\nCOMPLETED: {stage_name}")
    return True


def main():
    print("=" * 70)
    print("AUTOMATED FVA VALUATION PIPELINE")
    print("=" * 70)

    print("\nPipeline stages:")
    for number, (stage_name, _) in enumerate(PIPELINE_STAGES, start=1):
        print(f"{number}. {stage_name}")

    for stage_name, script_path in PIPELINE_STAGES:
        success = run_stage(stage_name, script_path)

        if not success:
            print("\n" + "=" * 70)
            print("PIPELINE FAILED")
            print("=" * 70)
            sys.exit(1)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print("\nFinal output:")
    print(
        PROJECT_ROOT
        / "data"
        / "processed"
        / "position_fva_valuation.csv"
    )

    print("\nPortfolio summary:")
    print(
        PROJECT_ROOT
        / "data"
        / "processed"
        / "fva_portfolio_summary.csv"
    )


if __name__ == "__main__":
    main()