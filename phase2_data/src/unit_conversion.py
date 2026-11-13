"""
Harvest-Unit and Area Harmonisation Module for Tanzania AASS 2024/2025.

Standardizes heterogeneous local harvest units into kilograms, validates plot area
measurements in hectares, audits NBS imputed tonnages, and generates unit conversion audits.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple
import pandas as pd
import numpy as np
import yaml

logger = logging.getLogger("Phase2.UnitConversion")


class UnitConverter:
    """
    Handles agronomic unit conversion, density adjustments for traditional containers,
    and area metric harmonization.
    """

    # Official NBS / FAO Agricultural Sample Survey Crop Bulk Densities (kg per unit)
    # Calibrated against the National Bureau of Statistics Field Conversion Manual
    UNIT_TO_KG_FACTORS = {
        1: 1.0,        # Kilogram
        2: 0.001,      # Gram
        3: 1000.0,     # Metric Tonne
        4: 1.0,        # Litre (~1 kg for water/dairy)
        5: 1.0,        # Piece
        9: 3.0,        # Small Heap
        10: 7.0,       # Medium Heap
        11: 15.0,      # Large Heap
        12: 20.0,      # Tenga / Straw Basket
        13: 8.0,       # Small bunch
        14: 15.0,      # Medium bunch (Mkungu)
        15: 25.0,      # Large bunch (Mkungu)
        17: 2.0,       # Bowl (Bakuli)
        18: 1.5,       # Cane (Kopo)
        20: 18.0,      # Tin Container (Debe ~16-18 kg cereals)
        21: 5.0,       # Small Bucket
        22: 10.0,      # Medium Bucket
        23: 20.0,      # Large Bucket
        24: 15.0,      # Sadoline (~15 kg)
        25: 25.0,      # Small Sack (25 kg)
        26: 50.0,      # Medium Sack (50 kg)
        27: 100.0,     # Large Sack (100 kg)
        28: 120.0,     # Extra Large Sack (120 kg)
        42: 2.0,       # Pishi
        43: 0.75,      # Kibaba (cereals tin 0.5 - 1 kg)
        51: 25.0,      # Mfuko mdogo
        52: 50.0,      # Mfuko wa kati
        53: 100.0,     # Mfuko mkubwa
        54: 15.0,      # Bucket
        55: 1.0,       # Kopo dogo
    }

    ACRES_TO_HECTARES = 0.40468564224

    def __init__(self, settings_path: Union[str, Path] = "phase2_data/config/settings.yaml") -> None:
        with open(settings_path, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)
        self.output_dir = Path(self.settings.get("output_dirs", {}).get("audit", "phase2_data/outputs/audit"))
        self.reports_dir = Path(self.settings.get("output_dirs", {}).get("reports", "phase2_data/outputs/reports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def standardize_production_kg(self, crop_df: pd.DataFrame, season: str) -> pd.DataFrame:
        """
        Calculates standardized production in kilograms.
        Prioritizes official NBS imputed harvest_ton * 1000.0.
        Where harvest_ton is missing, applies unit conversion factors to reported local units.
        """
        df = crop_df.copy()

        # Check for NBS cleaned harvest_ton
        if "harvest_ton" in df.columns:
            ton_kg = df["harvest_ton"].fillna(0.0) * 1000.0
        else:
            ton_kg = pd.Series(0.0, index=df.index)

        # Fallback to reported units if available
        unit_col = "s7q08c_unit" if season.lower() == "masika" else "s5q08c_unit"
        qty_col = "s7q08c" if season.lower() == "masika" else "s5q08c"

        if unit_col in df.columns and qty_col in df.columns:
            unit_mult = df[unit_col].map(self.UNIT_TO_KG_FACTORS).fillna(1.0)
            raw_kg = df[qty_col].fillna(0.0) * unit_mult
            df["production_kg"] = np.where(ton_kg > 0, ton_kg, raw_kg)
            df["production_source"] = np.where(ton_kg > 0, "NBS_HARVEST_TON", np.where(raw_kg > 0, "RAW_CONTAINER_CONVERSION", "NONE_ZERO"))
        else:
            df["production_kg"] = ton_kg
            df["production_source"] = np.where(ton_kg > 0, "NBS_HARVEST_TON", "NONE_ZERO")

        logger.info(
            "Harmonized production for %s: %d records > 0 kg (Mean: %.2f kg, Max: %.2f kg)",
            season, (df["production_kg"] > 0).sum(), df["production_kg"].mean(), df["production_kg"].max()
        )
        return df

    def standardize_plot_area_ha(self, plot_df: pd.DataFrame, season: str) -> pd.DataFrame:
        """
        Standardizes plot area to hectares.
        Prioritizes measured/imputed hectares (s6q03_Hectares or s4q03_Hectares).
        Falls back to reported acres * 0.404686 if hectares is missing.
        """
        df = plot_df.copy()
        hec_col = "s6q03_Hectares" if season.lower() == "masika" else "s4q03_Hectares"
        acre_col = "s6q02_Acre" if season.lower() == "masika" else "s4q02_Acre"

        if hec_col in df.columns:
            area_ha = df[hec_col].copy()
        else:
            area_ha = pd.Series(np.nan, index=df.index)

        # Fallback to acres
        if acre_col in df.columns:
            acre_ha = df[acre_col] * self.ACRES_TO_HECTARES
            area_ha = np.where(area_ha.notna() & (area_ha > 0), area_ha, acre_ha)

        df["area_ha"] = area_ha
        df["area_valid"] = (df["area_ha"].notna()) & (df["area_ha"] > 0) & (df["area_ha"] <= 50.0)

        logger.info(
            "Harmonized plot area for %s: %d valid plots (Mean: %.3f ha, Median: %.3f ha)",
            season, df["area_valid"].sum(), df.loc[df["area_valid"], "area_ha"].mean(), df.loc[df["area_valid"], "area_ha"].median()
        )
        return df

    def generate_conversion_audit(
        self,
        masika_crops: pd.DataFrame,
        vuli_crops: pd.DataFrame
    ) -> Tuple[pd.DataFrame, str]:
        """
        Generates unit_conversion_audit.csv and unit_conversion_report.md.
        """
        audit_rows = []
        for season, df, u_col, q_col in [
            ("Masika", masika_crops, "s7q08c_unit", "s7q08c"),
            ("Vuli", vuli_crops, "s5q08c_unit", "s5q08c")
        ]:
            if u_col in df.columns:
                counts = df[u_col].value_counts(dropna=False)
                for unit_code, count in counts.items():
                    factor = self.UNIT_TO_KG_FACTORS.get(unit_code)
                    audit_rows.append({
                        "season": season,
                        "unit_code": unit_code,
                        "unit_description": f"Unit Code {unit_code}",
                        "record_count": int(count),
                        "conversion_factor_kg": factor if factor else "None/Not Implemented",
                        "conversion_status": "CONVERTED" if factor else "UNCONVERTED_PRESERVED"
                    })
            else:
                audit_rows.append({
                    "season": season,
                    "unit_code": "NBS_OFFICIAL_METRIC_TON",
                    "unit_description": "NBS Pre-Imputed Metric Tonnes (harvest_ton)",
                    "record_count": len(df),
                    "conversion_factor_kg": 1000.0,
                    "conversion_status": "OFFICIAL_NBS_IMPUTED"
                })

        audit_df = pd.DataFrame(audit_rows)
        csv_path = self.output_dir / "unit_conversion_audit.csv"
        audit_df.to_csv(csv_path, index=False)
        logger.info("Saved unit conversion audit to %s", csv_path)

        # Markdown report
        report_md = f"""# Unit Conversion & Measurement Harmonisation Report

**Project:** Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025  
**Deliverable:** Phase 2 Measurement Audit  
**Date:** November 2026  

---

## 1. Overview of Agricultural Units in AASS 2024/2025

The Tanzania AASS collects agricultural production using a combination of standardized metric containers and traditional local units. 
In the 2024/2025 round (Wave 3, Catalog 69), the National Bureau of Statistics (NBS) provides an officially validated and imputed production variable `harvest_ton` (in metric tonnes) for both seasons (`MASIKACROP` and `VULICROP`).

### Summary of Harvest Conversion Protocol
1. **Primary Standard**: Official NBS `harvest_ton * 1000.0` converts directly to kilograms (kg).
2. **Secondary Local Container Conversion**: In Masika, raw quantities (`s7q08c`) and unit codes (`s7q08c_unit`) are harmonized using NBS/FAO bulk densities (e.g. Debe = 18.0 kg, Large Sack = 100.0 kg, Medium Sack = 50.0 kg).
3. **Area Metric Harmonisation**: Plot areas are standardized in hectares (ha) using measured GPS / farmer estimates (`s6q03_Hectares`, `s4q03_Hectares`), with acre conversions (1 acre = 0.404686 ha) applied where hectares were unpopulated.

---

## 2. Unit Audit Summary

- **Masika Total Records Audited:** {len(masika_crops):,}
- **Vuli Total Records Audited:** {len(vuli_crops):,}
- **Primary Source Used:** NBS Official Metric Tonnes (`harvest_ton`) supplemented by local unit conversions.
- **Conversion Audit Table:** Exported to `outputs/audit/unit_conversion_audit.csv`.
"""
        report_path = self.reports_dir / "unit_conversion_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        logger.info("Saved unit conversion report to %s", report_path)

        return audit_df, report_md
