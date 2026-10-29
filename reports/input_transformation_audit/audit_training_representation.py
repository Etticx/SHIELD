"""Compare local training values with the official UCI release; infer no scaler."""

import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
URL = (
    "https://archive.ics.uci.edu/static/public/572/"
    "taiwanese%2Bbankruptcy%2Bprediction.zip"
)
SEVEN = [
    "Net Income to Stockholder's Equity",
    "Net Income to Total Assets",
    "Retained Earnings to Total Assets",
    "Debt ratio %",
    "Net worth/Assets",
    "Equity to Liability",
    "Liability to Equity",
]


def main():
    local_path = ROOT / "data/bankruptcy_italian_companies_2023.xlsx"
    local = pd.read_excel(local_path)
    local.columns = local.columns.str.strip()
    archive_path = OUTPUT / "uci_release.zip"
    if archive_path.is_file():
        blob = archive_path.read_bytes()
    else:
        with urllib.request.urlopen(URL, timeout=45) as response:
            blob = response.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        members = archive.namelist()
        with archive.open("data.csv") as handle:
            official = pd.read_csv(handle, float_precision="round_trip")
    official.columns = official.columns.str.strip()
    aliases = {column: column.split(" (Yuan")[0] for column in official.columns if " (Yuan" in column}
    aliases["Bankrupt?"] = "Bankrupt"
    official = official.rename(columns=aliases)
    columns = official.columns.tolist()
    assert set(local.columns) - set(columns) == {"Company"}
    assert set(columns).issubset(local.columns)
    assert len(local) == len(official)
    local_values = local[columns].to_numpy(dtype=float)
    official_values = official[columns].to_numpy(dtype=float)
    assert np.isfinite(local_values).all() and np.isfinite(official_values).all()
    tolerance = 1e-12
    matches = bool(np.allclose(local_values, official_values, rtol=0, atol=tolerance))
    labels_match = bool(np.array_equal(local.Bankrupt, official.Bankrupt))
    ranges = local[SEVEN].describe(percentiles=[0.5]).T[["min", "50%", "max"]]
    # Diagnostic only: this cannot establish any historical accounting convention.
    identity_residual = (
        local["Net Income to Total Assets"]
        / local["Net worth/Assets"].replace(0, np.nan)
        - local["Net Income to Stockholder's Equity"]
    )
    record = {
        "checked_on": "2026-10-28",
        "source_url": URL,
        "archive_sha256": hashlib.sha256(blob).hexdigest(),
        "archive_members": members,
        "local_file": str(local_path.relative_to(ROOT)),
        "local_sha256": hashlib.sha256(local_path.read_bytes()).hexdigest(),
        "local_shape": list(local.shape),
        "uci_shape": list(official.shape),
        "excluded_local_identifier": "Company",
        "column_labels_stripped": True,
        "target_renamed_from": "Bankrupt?",
        "uci_column_aliases": aliases,
        "row_order_preserved": True,
        "comparison_rtol": 0,
        "comparison_atol": tolerance,
        "comparison_tolerance_reason": "Small absolute allowance for floating-point Excel/CSV parsing; no relative tolerance.",
        "all_values_match_within_tolerance": matches,
        "max_absolute_difference": float(np.abs(local_values - official_values).max()),
        "target_values_identical": labels_match,
        "mismatched_values_at_tolerance": int(np.count_nonzero(np.abs(local_values - official_values) > tolerance)),
        "seven_features": SEVEN,
        "median_absolute_ratio_identity_residual": float(identity_residual.abs().median()),
        "identity_residual_is_diagnostic_not_a_recovered_transformation": True,
        "raw_min_max_constants_recovered": False,
        "normalized_column_ranges_are_not_raw_scaler_bounds": True,
    }
    ranges.to_csv(OUTPUT / "seven_training_column_ranges.csv")
    (OUTPUT / "uci_comparison.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, indent=2))
    print(ranges.to_string())
    assert matches and labels_match, "Local values differ from the official release."


if __name__ == "__main__":
    main()
