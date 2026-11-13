"""
Unit Tests for Data Validation Module (test_data_validation.py).
"""

import pytest
import pandas as pd
from pathlib import Path
from phase2_data.src.data_validation import DataValidator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_validate_dataset_schema():
    validator = DataValidator(
        schema_dict_path=PROJECT_ROOT / "phase2_data" / "config" / "variable_dictionary.yaml",
        settings_path=PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml"
    )

    # Synthetic master table
    df_valid = pd.DataFrame({
        "HHFARMID": ["H1", "H2", "H3"],
        "Holding_type": [2.0, 2.0, 2.0],
        "region_id": [1, 2, 3],
        "district_id": [101, 102, 103],
        "ward_id": [1, 1, 1],
        "ea_id": [10, 20, 30],
        "stratum_id": [100, 200, 300],
        "Adjusted_HH_weight": [500.0, 600.0, 700.0]
    })
    res = validator.validate_dataset_schema("AASS2025", df_valid)
    assert res["validation_status"] == "PASS"
    assert res["pk_duplicate_rows"] == 0
    assert res["missing_required_variables"] == "None"


def test_validate_duplicate_keys():
    validator = DataValidator(
        schema_dict_path=PROJECT_ROOT / "phase2_data" / "config" / "variable_dictionary.yaml",
        settings_path=PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml"
    )
    df_dups = pd.DataFrame({
        "HHFARMID": ["H1", "H1"],
        "Holding_type": [2.0, 2.0],
        "region_id": [1, 1],
        "district_id": [101, 101],
        "ward_id": [1, 1],
        "ea_id": [10, 10],
        "stratum_id": [100, 100],
        "Adjusted_HH_weight": [500.0, 500.0]
    })
    res = validator.validate_dataset_schema("AASS2025", df_dups)
    assert res["pk_duplicate_rows"] == 1
    assert res["validation_status"] == "WARN"
