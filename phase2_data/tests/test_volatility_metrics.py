"""
Unit Tests for Instability Metrics Module (test_volatility_metrics.py).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from phase2_data.src.volatility_metrics import InstabilityMetricReconstructor

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_volatility_metric_calculations():
    """
    Prompt §12.4 Volatility Tests:
    Use manually verifiable values to test every implemented metric.
    Household 1: Y_m = 2000, Y_v = 1000.
    - Absolute difference: |2000 - 1000| = 1000 kg/ha.
    - Symmetric difference: 2 * |2000 - 1000| / (2000 + 1000) = 2000 / 3000 = 0.6667.
    - Log yield ratio: ln(1000 / 2000) = ln(0.5) = -0.6931.
    - Downside shortfall: max(0, 2000 - 1000) = 1000 kg/ha.
    - Production variance decomposition.
    """
    reconstructor = InstabilityMetricReconstructor(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    yields_df = pd.DataFrame({
        "HHFARMID": ["H1", "H1"],
        "season": ["masika", "vuli"],
        "crop_name_clean": ["Maize", "Maize"],
        "yield_kg_ha": [2000.0, 1000.0],
        "total_production_kg": [2000.0, 1000.0],
        "total_allocated_area_ha": [1.0, 1.0],
        "is_agronomically_valid": [True, True]
    })

    res = reconstructor.compute_same_crop_instability(yields_df, target_crop="Maize")
    assert len(res) == 1
    row = res.iloc[0]

    assert row["abs_yield_diff_kg_ha"] == 1000.0
    assert pytest.approx(row["symm_relative_diff"], 0.001) == 2000.0 / 3000.0
    assert pytest.approx(row["log_yield_ratio"], 0.001) == np.log(0.5)
    assert row["downside_shortfall_kg_ha"] == 1000.0


def test_volatility_zero_boundary():
    """
    Tests the legacy metric boundary behavior where Y_v = 0 collapses to exactly 2.0.
    """
    reconstructor = InstabilityMetricReconstructor(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    yields_df = pd.DataFrame({
        "HHFARMID": ["H1", "H1"],
        "season": ["masika", "vuli"],
        "crop_name_clean": ["Maize", "Maize"],
        "yield_kg_ha": [1500.0, 0.0],
        "total_production_kg": [1500.0, 0.0],
        "total_allocated_area_ha": [1.0, 1.0],
        "is_agronomically_valid": [True, True]
    })

    res = reconstructor.compute_same_crop_instability(yields_df, target_crop="Maize")
    assert pytest.approx(res.iloc[0]["y_vol_legacy"], 0.001) == 2.0
