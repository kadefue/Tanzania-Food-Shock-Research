"""
Unit Tests for Crop Harmonisation Module (test_crop_harmonisation.py).
"""

import pytest
import pandas as pd
from pathlib import Path
from phase2_data.src.crop_harmonisation import CropHarmoniser

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_crop_group_mapping():
    harmoniser = CropHarmoniser(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    # Verify major food crops
    assert harmoniser.CROP_GROUP_MAP["Maize"] == ("Cereals", True)
    assert harmoniser.CROP_GROUP_MAP["Paddy"] == ("Cereals", True)
    assert harmoniser.CROP_GROUP_MAP["Beans"] == ("Pulses", True)
    assert harmoniser.CROP_GROUP_MAP["Cassava"] == ("Roots and Tubers", True)

    # Verify non-food industrial crops
    assert harmoniser.CROP_GROUP_MAP["Tobacco"] == ("Cash Crops", False)
    assert harmoniser.CROP_GROUP_MAP["Cotton"] == ("Cash Crops", False)
    assert harmoniser.CROP_GROUP_MAP["Sisal"] == ("Cash Crops", False)


def test_harmonise_crop_table():
    harmoniser = CropHarmoniser(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    class MockMeta:
        variable_value_labels = {
            "MASIKACROP__id": {1: "Maize", 18: "Beans"}
        }

    raw_df = pd.DataFrame({
        "HHFARMID": ["H1", "H1"],
        "MASIKACROP__id": [1, 18]
    })

    harmonised = harmoniser.harmonise_crop_table(raw_df, "masika", MockMeta())
    assert "crop_name_clean" in harmonised.columns
    assert list(harmonised["crop_name_clean"]) == ["Maize", "Beans"]
    assert list(harmonised["crop_group"]) == ["Cereals", "Pulses"]
    assert list(harmonised["is_food_crop"]) == [True, True]
