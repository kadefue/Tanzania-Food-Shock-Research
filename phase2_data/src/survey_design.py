"""
Survey Design Assessment and Sampling Weight Module for Tanzania AASS 2024/2025.

Evaluates sampling weights (Adjusted_HH_weight), primary sampling units (ea_id),
strata (stratum_id), and prepares survey variance estimation specifications (Taylor linearization).
Exports survey variable inventories, weight diagnostics, and assessment reports.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple
import pandas as pd
import numpy as np
import yaml

logger = logging.getLogger("Phase2.SurveyDesign")


class SurveyDesignAuditor:
    """
    Audits complex survey design parameters and establishes design-based inference protocols.
    """

    def __init__(self, settings_path: Union[str, Path] = "phase2_data/config/settings.yaml") -> None:
        with open(settings_path, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)
        self.output_audit_dir = Path(self.settings.get("output_dirs", {}).get("audit", "phase2_data/outputs/audit"))
        self.output_reports_dir = Path(self.settings.get("output_dirs", {}).get("reports", "phase2_data/outputs/reports"))

        self.output_audit_dir.mkdir(parents=True, exist_ok=True)
        self.output_reports_dir.mkdir(parents=True, exist_ok=True)

    def audit_survey_variables(self, master_df: pd.DataFrame) -> pd.DataFrame:
        """
        Inventories all survey design variables and creates survey_variable_inventory.csv.
        """
        survey_vars = [
            ("HHFARMID", "Secondary Sampling Unit (SSU) / Household Agricultural Holding ID", "ID"),
            ("ea_id", "Primary Sampling Unit (PSU) / Enumeration Area ID", "Cluster / PSU"),
            ("stratum_id", "Survey Stratification Identifier", "Stratum"),
            ("Adjusted_HH_weight", "Final Post-Stratified Survey Expansion Weight", "Weight"),
            ("region_id", "Administrative Region (1 to 31)", "Geographic Strata"),
            ("district_id", "Administrative District", "Geographic Sub-strata"),
            ("Holding_type", "1=Commercial Large Scale Census, 2=Smallholder Sample", "Domain Indicator"),
        ]

        inv_rows = []
        for var_name, desc, role in survey_vars:
            present = var_name in master_df.columns
            if present:
                col = master_df[var_name]
                non_null = int(col.notna().sum())
                n_unique = int(col.nunique())
                min_val = float(col.min()) if pd.api.types.is_numeric_dtype(col) else np.nan
                max_val = float(col.max()) if pd.api.types.is_numeric_dtype(col) else np.nan
            else:
                non_null = 0
                n_unique = 0
                min_val = np.nan
                max_val = np.nan

            inv_rows.append({
                "variable_name": var_name,
                "role_in_design": role,
                "description": desc,
                "is_present": present,
                "non_null_records": non_null,
                "unique_values_count": n_unique,
                "min_value": min_val,
                "max_value": max_val,
                "audit_verdict": "VERIFIED_OPERATIONAL" if present and non_null > 0 else "MISSING_CRITICAL"
            })

        inv_df = pd.DataFrame(inv_rows)
        out_path = self.output_audit_dir / "survey_variable_inventory.csv"
        inv_df.to_csv(out_path, index=False)
        logger.info("Saved survey variable inventory to %s", out_path)
        return inv_df

    def audit_weights_across_populations(
        self,
        populations: Dict[str, pd.DataFrame]
    ) -> Tuple[pd.DataFrame, str]:
        """
        Computes weight distribution diagnostics across Populations A, B, C, D
        and exports analytical_sample_weight_assessment.csv and survey_design_assessment.md.
        """
        pop_names = {
            "pop_a": "Population A: All Valid Smallholders",
            "pop_b": "Population B: Valid Seasonal Producers",
            "pop_c": "Population C: Same-Crop Bimodal Cohort",
            "pop_d": "Population D: Farming System Cohort"
        }

        weight_rows = []
        for key, df in populations.items():
            if "Adjusted_HH_weight" not in df.columns:
                continue
            w = df["Adjusted_HH_weight"].dropna()
            total_sample = len(df)
            weighted_pop = w.sum()
            mean_w = w.mean()
            std_w = w.std()
            cv_w = std_w / mean_w if mean_w > 0 else 0.0

            weight_rows.append({
                "population_key": key,
                "population_description": pop_names.get(key, key),
                "unweighted_sample_size": total_sample,
                "weighted_population_estimate": round(weighted_pop, 1),
                "weight_min": round(w.min(), 2),
                "weight_q25": round(w.quantile(0.25), 2),
                "weight_median": round(w.median(), 2),
                "weight_q75": round(w.quantile(0.75), 2),
                "weight_max": round(w.max(), 2),
                "weight_mean": round(mean_w, 2),
                "weight_cv": round(cv_w, 3),
                "psu_cluster_count": df["ea_id"].nunique() if "ea_id" in df.columns else np.nan,
                "strata_count": df["stratum_id"].nunique() if "stratum_id" in df.columns else np.nan
            })

        weight_df = pd.DataFrame(weight_rows)
        out_csv = self.output_audit_dir / "analytical_sample_weight_assessment.csv"
        weight_df.to_csv(out_csv, index=False)
        logger.info("Saved analytical sample weight assessment to %s", out_csv)

        # Markdown Report
        report_md = f"""# Survey Design & Sampling Weight Assessment Report

**Project:** Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025 (Catalog 69)  
**Deliverable:** Phase 2 Survey Methodology Audit  
**Date:** November 2026  

---

## 1. Survey Sample Architecture

The Tanzania AASS is a two-stage stratified cluster sample designed and implemented by the National Bureau of Statistics (NBS):
- **Primary Sampling Units (PSUs):** Enumeration Areas (EAs) selected with Probability Proportional to Size (PPS) within each district stratum (`ea_id`).
- **Secondary Sampling Units (SSUs):** Agricultural households selected systematically within sampled EAs (`HHFARMID`).
- **Stratification:** Stratified by administrative district and agro-ecological zone (`stratum_id`).
- **Sampling Expansion Weight:** `Adjusted_HH_weight` incorporates the inverse selection probabilities at both stages, non-response adjustments, and post-stratification benchmark calibration.

---

## 2. Weight Application Guidelines for Subsequent Analysis

1. **Descriptive Tables (Table 1):** Must strictly utilize `Adjusted_HH_weight` to produce population-representative estimates of mean yields, asset holdings, and shock exposure.
2. **Econometric Regressions (Phase 3):** Must implement Weighted Least Squares (WLS) or survey-calibrated Generalized Linear Models (GLMs).
3. **Variance Estimation:** Design-based standard errors must be computed using **Taylor series linearization** or cluster-robust standard errors clustered at the PSU (`ea_id`) level:
   $$\\widehat{{\\text{{Var}}}}(\\hat{{\\beta}}) = (X'WX)^{{-1}} \\left( \\sum_{{c \\in \\text{{EAs}}}} u_c' u_c \\right) (X'WX)^{{-1}}$$
4. **Machine Learning Models:** As recommended by survey-methodology best practice, sampling weights can be supplied as sample weights during training, but validation loss must be evaluated on unweighted or domain-standardized test slices.
5. **Sub-population Caution:** When analyzing Population C (Same-Crop Bimodal Cohort), weights should be treated under sub-population domain estimation rules rather than re-normalizing weights to sum to total national smallholders.

---

## 3. Weight Diagnostics Across Cohorts

See detailed numerical audit in:
- `outputs/audit/survey_variable_inventory.csv`
- `outputs/audit/analytical_sample_weight_assessment.csv`
"""
        report_path = self.output_reports_dir / "survey_design_assessment.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        logger.info("Saved survey design assessment report to %s", report_path)

        return weight_df, report_md
