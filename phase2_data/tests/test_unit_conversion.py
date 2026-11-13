"""
Unit Tests for Unit Conversion Module (test_unit_conversion.py).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from phase2_data.src.unit_conversion import UnitConverter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_standardize_production_kg():
    converter = UnitConverter(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    # Case 1: NBS harvest_ton is present (e.g. 0.5 tonnes = 500 kg)
    df1 = pd.DataFrame({"harvest_ton": [0.5, 1.2, 0.0]})
    res1 = converter.standardize_production_kg(df1, "masika")
    assert list(res1["production_kg"]) == [500.0, 1200.0, 0.0]
    assert list(res1["production_source"]) == ["NBS_HARVEST_TON", "NBS_HARVEST_TON", "NONE_ZERO"]

    # Case 2: harvest_ton is NaN, fallback to traditional container (e.g. Debe = 18 kg)
    df2 = pd.DataFrame({
        "harvest_ton": [np.nan],
        "s7q08c": [10.0],
        "s7q08c_unit": [20]  # Tin / Debe (18.0 kg)
    })
    res2 = converter.standardize_production_kg(df2, "masika")
    assert list(res2["production_kg"]) == [180.0]
    assert list(res2["production_source"]) == ["RAW_CONTAINER_CONVERSION"]


def test_standardize_plot_area_ha():
    converter = UnitConverter(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    # Case 1: Hectares directly provided
    df = pd.DataFrame({
        "s6q03_Hectares": [1.5, np.nan],
        "s6q02_Acre": [np.nan, 2.47105]  # ~1.0 ha
    })
    res = converter.standardize_plot_area_ha(df, "masika")
    assert res.loc[0, "area_ha"] == 1.5
    assert pytest.approx(res.loc[1, "area_ha"], 0.01) == 1.0
    assert res.loc[0, "area_valid"] == True
