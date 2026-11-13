"""
Crop-Specific Production and Yield Reconstruction Module for Tanzania AASS 2024/2025.

Calculates scientifically defensible, plot-area-share weighted crop yields (Y_hcs = sum(P) / sum(A))
for individual crops across agricultural seasons, applies FAO/NBS agronomic plausible bounds,
and maintains diagnostic flags without silent dropping.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple
import pandas as pd
import numpy as np
import yaml

logger = logging.getLogger("Phase2.YieldCalculation")


class YieldCalculator:
    """
    Computes crop-specific seasonal yields in kg/ha and evaluates agronomic plausibility.
    """

    def __init__(self, settings_path: Union[str, Path] = "phase2_data/config/settings.yaml") -> None:
        with open(settings_path, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)

        self.yield_bounds = self.settings.get("agronomic_yield_bounds_kg_ha", {})
        self.priority_crops = self.settings.get("priority_food_crops", ["Maize", "Paddy", "Beans", "Cassava"])
        self.output_audit_dir = Path(self.settings.get("output_dirs", {}).get("audit", "phase2_data/outputs/audit"))
        self.output_analytical_dir = Path(self.settings.get("output_dirs", {}).get("analytical_data", "phase2_data/outputs/analytical_data"))
        self.output_reports_dir = Path(self.settings.get("output_dirs", {}).get("reports", "phase2_data/outputs/reports"))

        for d in [self.output_audit_dir, self.output_analytical_dir, self.output_reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def calculate_plot_crop_allocated_area(
        self,
        aligned_crop_df: pd.DataFrame,
        season: str
    ) -> pd.DataFrame:
        """
        Calculates plot area allocated to each crop record.
        Allocated Area (ha) = plot_area_ha * (share_pct / 100.0).
        Handles sole-cropping (implicit 100%) and multi-cropping shares.
        """
        df = aligned_crop_df.copy()
        share_col = "s7q02" if season.lower() == "masika" else "s5q02"

        # Determine plot area column
        if "s6q03_Hectares" in df.columns:
            plot_ha = df["s6q03_Hectares"].copy()
        elif "s4q03_Hectares" in df.columns:
            plot_ha = df["s4q03_Hectares"].copy()
        elif "area_ha" in df.columns:
            plot_ha = df["area_ha"].copy()
        else:
            plot_ha = pd.Series(np.nan, index=df.index)

        # Count crops per plot
        plot_key = ["HHFARMID", "MASIKAPLOT__id"] if season.lower() == "masika" else ["HHFARMID", "VULIPLOT__id"]
        crops_on_plot = df.groupby(plot_key)["crop_name_clean"].transform("count")

        # Determine share percentage
        if share_col in df.columns:
            raw_share = pd.to_numeric(df[share_col], errors="coerce")
            # If sole cropped or share is missing, default to 100% for single crop or equal split
            clean_share = np.where(
                raw_share.notna() & (raw_share > 0) & (raw_share <= 100),
                raw_share,
                np.where(crops_on_plot == 1, 100.0, 100.0 / np.maximum(1, crops_on_plot))
            )
        else:
            clean_share = np.where(crops_on_plot == 1, 100.0, 100.0 / np.maximum(1, crops_on_plot))

        df["allocated_crop_area_ha"] = plot_ha * (clean_share / 100.0)
        df["crop_area_share_pct"] = clean_share
        return df

    def compute_household_crop_yields(
        self,
        crop_df: pd.DataFrame,
        season: str
    ) -> pd.DataFrame:
        """
        Aggregates multi-plot production and area for each household and crop:
        Y_hcs = sum(P_hcsp) / sum(A_hcsp).
        Strictly prevents pooling disparate crops.
        """
        # Group by household and standardized crop name
        grouped = crop_df.groupby(["HHFARMID", "crop_name_clean", "crop_group", "is_food_crop"]).agg(
            total_production_kg=("production_kg", "sum"),
            total_allocated_area_ha=("allocated_crop_area_ha", "sum"),
            plot_records_count=("crop_name_clean", "count")
        ).reset_index()

        # Compute yield in kg/ha
        valid_area_mask = (grouped["total_allocated_area_ha"] > 0.0001)
        grouped["yield_kg_ha"] = np.where(
            valid_area_mask,
            grouped["total_production_kg"] / grouped["total_allocated_area_ha"],
            np.nan
        )
        grouped["season"] = season.lower()

        # Apply agronomic plausibility flags
        grouped = self.flag_agronomic_yields(grouped)
        logger.info(
            "Computed %s household crop yields: %d records across %d crops. (Mean: %.1f kg/ha, Median: %.1f kg/ha)",
            season, len(grouped), grouped["crop_name_clean"].nunique(), grouped["yield_kg_ha"].mean(), grouped["yield_kg_ha"].median()
        )
        return grouped

    def flag_agronomic_yields(self, yield_df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluates crop yields against documented agronomic bounds without silent deletion.
        """
        df = yield_df.copy()
        flags = []

        default_bounds = self.yield_bounds.get("default", {"min": 20.0, "max": 15000.0})

        for _, row in df.iterrows():
            y = row["yield_kg_ha"]
            c = row["crop_name_clean"]

            if pd.isna(y):
                flags.append("MISSING_OR_ZERO_AREA")
                continue

            bounds = self.yield_bounds.get(c, default_bounds)
            min_y = bounds.get("min", default_bounds["min"])
            max_y = bounds.get("max", default_bounds["max"])

            if y == 0:
                flags.append("ZERO_HARVEST_COMPLETE_FAILURE")
            elif y < min_y:
                flags.append("FLAG_BELOW_MIN_BOUND")
            elif y > max_y:
                flags.append("FLAG_ABOVE_MAX_BOUND")
            else:
                flags.append("VALID_AGRONOMIC")

        df["agronomic_flag"] = flags
        df["is_agronomically_valid"] = (df["agronomic_flag"] == "VALID_AGRONOMIC")
        return df

    def generate_yield_diagnostics(
        self,
        yields_combined: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
        """
        Produces crop_season_yield_summary.csv, yield_quality_flags.csv, and yield_calculation_report.md.
        """
        # Summary statistics by crop and season
        summary_rows = []
        for (crop, season), grp in yields_combined.groupby(["crop_name_clean", "season"]):
            y_all = grp["yield_kg_ha"].dropna()
            y_valid = grp.loc[grp["is_agronomically_valid"], "yield_kg_ha"]

            if len(y_all) == 0:
                continue

            summary_rows.append({
                "crop_name": crop,
                "season": season,
                "total_household_observations": len(grp),
                "valid_agronomic_observations": len(y_valid),
                "zero_harvest_count": int((grp["agronomic_flag"] == "ZERO_HARVEST_COMPLETE_FAILURE").sum()),
                "below_bound_count": int((grp["agronomic_flag"] == "FLAG_BELOW_MIN_BOUND").sum()),
                "above_bound_count": int((grp["agronomic_flag"] == "FLAG_ABOVE_MAX_BOUND").sum()),
                "mean_yield_all": round(y_all.mean(), 1),
                "median_yield_all": round(y_all.median(), 1),
                "std_yield_all": round(y_all.std(), 1) if len(y_all) > 1 else np.nan,
                "mean_yield_valid": round(y_valid.mean(), 1) if len(y_valid) > 0 else np.nan,
                "median_yield_valid": round(y_valid.median(), 1) if len(y_valid) > 0 else np.nan,
                "iqr_yield_valid": round(y_valid.quantile(0.75) - y_valid.quantile(0.25), 1) if len(y_valid) > 0 else np.nan,
            })

        summary_df = pd.DataFrame(summary_rows).sort_values("total_household_observations", ascending=False)
        out_summary = self.output_audit_dir / "crop_season_yield_summary.csv"
        summary_df.to_csv(out_summary, index=False)
        logger.info("Saved crop season yield summary to %s", out_summary)

        # Flag frequencies
        flag_df = yields_combined["agronomic_flag"].value_counts().reset_index()
        flag_df.columns = ["agronomic_flag", "frequency"]
        flag_df["percent"] = round(100.0 * flag_df["frequency"] / len(yields_combined), 2)
        out_flags = self.output_audit_dir / "yield_quality_flags.csv"
        flag_df.to_csv(out_flags, index=False)
        logger.info("Saved yield quality flags audit to %s", out_flags)

        # Markdown Report
        def _to_md(d: pd.DataFrame) -> str:
            hdrs = list(d.columns)
            res = ["| " + " | ".join(str(h) for h in hdrs) + " |", "| " + " | ".join("---" for _ in hdrs) + " |"]
            for _, r in d.iterrows():
                res.append("| " + " | ".join(str(r[h]) for h in hdrs) + " |")
            return "\n".join(res)

        top_crops = _to_md(summary_df.head(10))
        report_md = f"""# Crop-Specific Yield Reconstruction & Agronomic Diagnostics Report

**Project:** Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025  
**Deliverable:** Phase 2 Crop Yield Audit  
**Date:** November 2026  

---

## 1. Methodological Resolution of Phase 1 Defect R-07

In the legacy codebase, agricultural yields were calculated by pooling total harvest kilograms across all crops (cassava tubers, cereal grains, pulses, tree crops) and dividing by total farm plot area. This confounded moisture contents, harvest indexes, and crop substitutions into spurious "yield" changes.

In Phase 2, crop yields are reconstructed strictly at the **crop-species level**:
$$Y_{{hcs}} = \\frac{{\\sum_p P_{{hcsp}}}}{{\\sum_p A_{{hcsp}}}}$$
where $P_{{hcsp}}$ is the harvest of crop $c$ on plot $p$ (in kg), and $A_{{hcsp}}$ is the allocated area of crop $c$ on plot $p$ (in ha), accounting for intercrop shares.

---

## 2. Top Crops Seasonal Yield Summary

{top_crops}

---

## 3. Agronomic Plausibility Flag Distribution

- **Total Crop-Season Observations:** {len(yields_combined):,}
- **Valid Agronomic Range:** {flag_df.loc[flag_df['agronomic_flag'] == 'VALID_AGRONOMIC', 'percent'].values[0]}%
- Detailed diagnostics available in:
  - `outputs/audit/crop_season_yield_summary.csv`
  - `outputs/audit/yield_quality_flags.csv`
"""
        report_path = self.output_reports_dir / "yield_calculation_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        logger.info("Saved yield calculation report to %s", report_path)

        # Export analytical yields dataset
        analytical_path = self.output_analytical_dir / "crop_season_yields.parquet"
        yields_combined.to_parquet(analytical_path, index=False)
        logger.info("Exported analytical crop-season yields to %s", analytical_path)

        return summary_df, flag_df, report_md
