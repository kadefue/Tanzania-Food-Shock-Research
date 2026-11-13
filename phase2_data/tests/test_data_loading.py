"""
Unit Tests for Data Loading Module (test_data_loading.py).
"""

import pytest
import pandas as pd
from pathlib import Path
from phase2_data.src.data_loading import AASSDataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_standardize_identifiers():
    df_raw = pd.DataFrame({
        "Holding_ID": [" 00-01-23 ", "00-01-24\t"],
        "val": [10, 20]
    })
    df_clean = AASSDataLoader._standardize_identifiers(df_raw)
    assert "HHFARMID" in df_clean.columns
    assert "Holding_ID" not in df_clean.columns
    assert list(df_clean["HHFARMID"]) == ["00-01-23", "00-01-24"]


def test_loader_instantiation():
    loader = AASSDataLoader(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")
    assert loader.raw_data_dir.exists()


def test_load_metadata_only():
    loader = AASSDataLoader(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")
    meta = loader.get_metadata("AASS2025.dta")
    assert meta is not None
    assert "Holding_type" in meta.column_names
