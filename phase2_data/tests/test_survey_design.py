"""
Unit Tests for Survey Design Module (test_survey_design.py).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from phase2_data.src.survey_design import SurveyDesignAuditor

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_survey_variable_inventory():
    auditor = SurveyDesignAuditor(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    master_df = pd.DataFrame({
        "HHFARMID": ["H1", "H2", "H3"],
        "Holding_type": [2.0, 2.0, 2.0],
        "ea_id": [101, 102, 103],
        "stratum_id": [10, 20, 30],
        "Adjusted_HH_weight": [450.0, 550.0, 650.0],
        "region_id": [1, 2, 3],
        "district_id": [101, 102, 103]
    })

    inv = auditor.audit_survey_variables(master_df)
    assert len(inv) == 7
    status_dict = dict(zip(inv["variable_name"], inv["audit_verdict"]))
    assert status_dict["HHFARMID"] == "VERIFIED_OPERATIONAL"
    assert status_dict["Adjusted_HH_weight"] == "VERIFIED_OPERATIONAL"
    assert status_dict["ea_id"] == "VERIFIED_OPERATIONAL"


def test_weight_assessment_metrics():
    auditor = SurveyDesignAuditor(PROJECT_ROOT / "phase2_data" / "config" / "settings.yaml")

    pop_df = pd.DataFrame({
        "HHFARMID": ["H1", "H2", "H3"],
        "Adjusted_HH_weight": [100.0, 200.0, 300.0],
        "ea_id": [10, 20, 20],
        "stratum_id": [1, 1, 2]
    })

    populations = {"pop_a": pop_df}
    weight_summary, report_md = auditor.audit_weights_across_populations(populations)

    assert len(weight_summary) == 1
    row = weight_summary.iloc[0]
    assert row["unweighted_sample_size"] == 3
    assert row["weighted_population_estimate"] == 600.0
    assert row["weight_mean"] == 200.0
    assert row["weight_min"] == 100.0
    assert row["weight_max"] == 300.0
    assert row["psu_cluster_count"] == 2
    assert row["strata_count"] == 2
