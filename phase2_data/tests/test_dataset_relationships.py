"""
Unit Tests for Dataset Relationships Module (test_dataset_relationships.py).
"""

import pytest
import pandas as pd
from pathlib import Path
from phase2_data.src.dataset_relationships import DatasetRelationshipManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_audit_merge_no_duplication():
    mgr = DatasetRelationshipManager(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    left = pd.DataFrame({"HHFARMID": ["H1", "H2"], "weight": [10.0, 20.0]})
    right = pd.DataFrame({"HHFARMID": ["H1", "H2"], "plot_area": [1.5, 2.5]})

    merged, log = mgr.audit_merge(left, right, "left", "right", on=["HHFARMID"], expected_relation="1:1")
    assert log["status"] == "PASS"
    assert log["cartesian_duplicates"] == 0
    assert len(merged) == 2


def test_audit_merge_detects_cartesian_expansion():
    mgr = DatasetRelationshipManager(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    left = pd.DataFrame({"HHFARMID": ["H1"], "weight": [10.0]})
    right = pd.DataFrame({"HHFARMID": ["H1", "H1"], "val": [1, 2]})

    merged, log = mgr.audit_merge(left, right, "left", "right", on=["HHFARMID"], expected_relation="1:1")
    assert log["status"] == "FAIL_DUPLICATION"
    assert log["cartesian_duplicates"] == 1
    assert len(merged) == 2
