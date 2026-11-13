"""
Unit Tests for Yield Calculation Module (test_yield_calculation.py).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from phase2_data.src.yield_calculation import YieldCalculator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_calculate_yield_formula():
    """
    Prompt §12.1 Yield Test:
    Use manually verifiable examples:
    Production = 1000 kg, Harvested Area = 0.5 ha -> Expected Yield = 2000 kg/ha.
    """
    calc = YieldCalculator(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    crop_df = pd.DataFrame({
        "HHFARMID": ["H1"],
        "crop_name_clean": ["Maize"],
        "crop_group": ["Cereals"],
        "is_food_crop": [True],
        "production_kg": [1000.0],
        "allocated_crop_area_ha": [0.5]
    })

    yield_res = calc.compute_household_crop_yields(crop_df, "masika")
    assert len(yield_res) == 1
    assert yield_res.iloc[0]["yield_kg_ha"] == 2000.0
    assert yield_res.iloc[0]["agronomic_flag"] == "VALID_AGRONOMIC"


def test_multi_plot_aggregation():
    """
    Prompt §12.2 Aggregation Test:
    Verify that multiple plots belonging to the same household, crop, and season
    are aggregated using total production divided by total harvested area.
    Plot 1: 500 kg on 0.5 ha.
    Plot 2: 1500 kg on 1.0 ha.
    Total: 2000 kg on 1.5 ha -> Expected Yield = 1333.33 kg/ha.
    (NOT the unweighted average of plot yields 1000 and 1500, which would be 1250!)
    """
    calc = YieldCalculator(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    crop_df = pd.DataFrame({
        "HHFARMID": ["H1", "H1"],
        "crop_name_clean": ["Maize", "Maize"],
        "crop_group": ["Cereals", "Cereals"],
        "is_food_crop": [True, True],
        "production_kg": [500.0, 1500.0],
        "allocated_crop_area_ha": [0.5, 1.0]
    })

    yield_res = calc.compute_household_crop_yields(crop_df, "masika")
    assert len(yield_res) == 1
    expected_yield = 2000.0 / 1.5
    assert pytest.approx(yield_res.iloc[0]["yield_kg_ha"], 0.01) == expected_yield
    assert yield_res.iloc[0]["total_production_kg"] == 2000.0
    assert yield_res.iloc[0]["total_allocated_area_ha"] == 1.5


def test_yield_outlier_flags():
    """
    Tests agronomic bound detection:
    Maize bounds in config: [50, 8000] kg/ha.
    """
    calc = YieldCalculator(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    crop_df = pd.DataFrame({
        "HHFARMID": ["H1", "H2", "H3", "H4"],
        "crop_name_clean": ["Maize", "Maize", "Maize", "Maize"],
        "crop_group": ["Cereals", "Cereals", "Cereals", "Cereals"],
        "is_food_crop": [True, True, True, True],
        "production_kg": [0.0, 10.0, 2000.0, 20000.0],
        "allocated_crop_area_ha": [1.0, 1.0, 1.0, 1.0]
    })

    yield_res = calc.compute_household_crop_yields(crop_df, "masika")
    flags = dict(zip(yield_res["HHFARMID"], yield_res["agronomic_flag"]))
    assert flags["H1"] == "ZERO_HARVEST_COMPLETE_FAILURE"
    assert flags["H2"] == "FLAG_BELOW_MIN_BOUND"
    assert flags["H3"] == "VALID_AGRONOMIC"
    assert flags["H4"] == "FLAG_ABOVE_MAX_BOUND"
