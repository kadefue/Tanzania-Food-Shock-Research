"""
Unit Tests for Analytical Sample Selection Module (test_sample_selection.py).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from phase2_data.src.sample_selection import SampleSelector

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_reconstruct_populations():
    selector = SampleSelector(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    master_df = pd.DataFrame({
        "HHFARMID": ["H1", "H2", "H3", "H4"],
        "Holding_type": [2.0, 2.0, 2.0, 1.0],  # H4 is commercial large scale
        "Adjusted_HH_weight": [100.0, 200.0, 300.0, np.nan],
        "region_id": [1, 1, 2, 2],
        "ea_id": [10, 10, 20, 20],
        "stratum_id": [100, 100, 200, 200]
    })

    # H1 grows Maize in both seasons (Bimodal Same Crop)
    # H2 grows Maize in Masika only (Unimodal)
    # H3 grows Paddy in Vuli only (Unimodal)
    mc = pd.DataFrame({
        "HHFARMID": ["H1", "H2"],
        "crop_name_clean": ["Maize", "Maize"],
        "production_kg": [500.0, 600.0]
    })
    vc = pd.DataFrame({
        "HHFARMID": ["H1", "H3"],
        "crop_name_clean": ["Maize", "Paddy"],
        "production_kg": [400.0, 300.0]
    })
    mp = pd.DataFrame({"HHFARMID": ["H1", "H2"], "s6q03_Hectares": [1.0, 1.0]})
    vp = pd.DataFrame({"HHFARMID": ["H1", "H3"], "s4q03_Hectares": [1.0, 1.0]})

    pops = selector.reconstruct_populations(master_df, mc, vc, mp, vp)

    assert len(pops["pop_a"]) == 3  # H1, H2, H3 (H4 excluded as commercial)
    assert len(pops["pop_b"]) == 3  # All three produce in at least one season
    assert len(pops["pop_c"]) == 1  # Only H1 produces Maize in both seasons
    assert pops["pop_c"].iloc[0]["HHFARMID"] == "H1"
