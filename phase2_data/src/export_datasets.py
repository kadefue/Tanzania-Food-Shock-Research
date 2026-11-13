"""
Dataset Export and Metadata Serialization Module for Tanzania AASS 2024/2025.

Exports verified, leak-free, clean Parquet microdata tables and analytical cohorts,
ensuring reproducible data storage with schema documentation.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Union
import pandas as pd
import yaml

logger = logging.getLogger("Phase2.ExportDatasets")


class DatasetExporter:
    """
    Manages the serialization and export of clean microdata tables and analytical cohorts.
    """

    def __init__(self, settings_path: Union[str, Path] = "phase2_data/config/settings.yaml") -> None:
        with open(settings_path, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)

        self.cleaned_data_dir = Path(self.settings.get("output_dirs", {}).get("cleaned_data", "phase2_data/outputs/cleaned_data"))
        self.analytical_data_dir = Path(self.settings.get("output_dirs", {}).get("analytical_data", "phase2_data/outputs/analytical_data"))

        self.cleaned_data_dir.mkdir(parents=True, exist_ok=True)
        self.analytical_data_dir.mkdir(parents=True, exist_ok=True)

    def export_cleaned_microdata(
        self,
        master_clean: pd.DataFrame,
        household_clean: pd.DataFrame,
        plots_clean: pd.DataFrame,
        crops_clean: pd.DataFrame
    ) -> Dict[str, Path]:
        """
        Exports cleaned foundational microdata tables to Parquet.
        """
        exports = {}

        # 1. Holdings / Master
        holdings_path = self.cleaned_data_dir / "holdings_clean.parquet"
        master_clean.to_parquet(holdings_path, index=False)
        exports["holdings"] = holdings_path

        # 2. Households
        hh_path = self.cleaned_data_dir / "households_clean.parquet"
        if not household_clean.empty:
            household_clean.to_parquet(hh_path, index=False)
            exports["households"] = hh_path

        # 3. Plots
        plots_path = self.cleaned_data_dir / "plots_clean.parquet"
        plots_clean.to_parquet(plots_path, index=False)
        exports["plots"] = plots_path

        # 4. Crop Records
        crops_path = self.cleaned_data_dir / "crop_records_clean.parquet"
        crops_clean.to_parquet(crops_path, index=False)
        exports["crop_records"] = crops_path

        # 5. Geographic Lookup
        geo_cols = [c for c in ["HHFARMID", "region_id", "district_id", "ward_id", "ea_id", "stratum_id"] if c in master_clean.columns]
        geo_df = master_clean[geo_cols].drop_duplicates()
        geo_path = self.cleaned_data_dir / "geographic_lookup.parquet"
        geo_df.to_parquet(geo_path, index=False)
        exports["geographic_lookup"] = geo_path

        logger.info("Exported %d cleaned microdata tables to %s", len(exports), self.cleaned_data_dir)
        return exports

    def export_analytical_cohorts(
        self,
        populations: Dict[str, pd.DataFrame]
    ) -> Dict[str, Path]:
        """
        Exports analytical cohorts (Populations A, B, C, D) to Parquet.
        """
        exports = {}

        # Population A: All Valid Smallholders
        pop_a_path = self.analytical_data_dir / "sample_all_valid.parquet"
        populations["pop_a"].to_parquet(pop_a_path, index=False)
        exports["pop_a"] = pop_a_path

        # Population B: Valid Seasonal Producers
        pop_b_path = self.analytical_data_dir / "sample_seasonal.parquet"
        populations["pop_b"].to_parquet(pop_b_path, index=False)
        exports["pop_b"] = pop_b_path

        # Population C: Same-Crop Bimodal Cohort
        pop_c_path = self.analytical_data_dir / "sample_same_crop_comparison.parquet"
        populations["pop_c"].to_parquet(pop_c_path, index=False)
        exports["pop_c"] = pop_c_path

        # Population D: Farming System Groups
        pop_d_path = self.analytical_data_dir / "sample_seasonal_farming_systems.parquet"
        populations["pop_d"].to_parquet(pop_d_path, index=False)
        exports["pop_d"] = pop_d_path

        logger.info("Exported %d analytical populations to %s", len(exports), self.analytical_data_dir)
        return exports
