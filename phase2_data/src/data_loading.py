"""
Data Loading Module for Tanzania AASS 2024/2025 (Catalog 69).

Provides robust, reproducible loading of raw Stata .dta tables with pyreadstat,
retaining variable labels, value labels, and standardizing holding identifiers across tables.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import pandas as pd
import pyreadstat
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Phase2.DataLoading")


class AASSDataLoader:
    """
    Robust loader for Tanzania Agricultural Annual Sample Survey microdata.
    """

    def __init__(self, settings_path: Union[str, Path] = "phase2_data/config/settings.yaml") -> None:
        self.settings_path = Path(settings_path)
        with open(self.settings_path, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)

        self.raw_data_dir = Path(self.settings.get("raw_data_dir", "data/AASS 2024_2025"))
        if not self.raw_data_dir.exists():
            raise FileNotFoundError(f"Raw data directory does not exist: {self.raw_data_dir}")

        self._metadata_cache: Dict[str, Any] = {}
        self._table_cache: Dict[str, pd.DataFrame] = {}

    def load_table(
        self,
        table_name: str,
        usecols: Optional[List[str]] = None,
        use_cache: bool = True,
        standardize_id: bool = True
    ) -> Tuple[pd.DataFrame, Any]:
        """
        Loads a Stata .dta table by name, returning (DataFrame, Metadata).
        """
        if not table_name.endswith(".dta"):
            table_name = f"{table_name}.dta"

        cache_key = f"{table_name}_{','.join(sorted(usecols)) if usecols else 'ALL'}"
        if use_cache and cache_key in self._table_cache:
            return self._table_cache[cache_key].copy(), self._metadata_cache.get(table_name)

        file_path = self.raw_data_dir / table_name
        if not file_path.exists():
            # Try case-insensitive search
            matches = [p for p in self.raw_data_dir.glob("*.dta") if p.name.lower() == table_name.lower()]
            if matches:
                file_path = matches[0]
            else:
                raise FileNotFoundError(f"Table file not found: {file_path}")

        logger.info("Loading table from %s", file_path)
        df, meta = pyreadstat.read_dta(str(file_path), usecols=usecols)

        # Standardize primary holding identifier
        if standardize_id:
            df = self._standardize_identifiers(df)

        if use_cache:
            self._table_cache[cache_key] = df
            self._metadata_cache[table_name] = meta

        return df.copy(), meta

    @staticmethod
    def _standardize_identifiers(df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardizes holding identifier to HHFARMID as clean stripped string.
        """
        rename_map = {}
        for col in ["holding_id", "Holding_ID", "hhid", "HHID", "hh_id"]:
            if col in df.columns and "HHFARMID" not in df.columns:
                rename_map[col] = "HHFARMID"
                break

        if rename_map:
            df = df.rename(columns=rename_map)

        if "HHFARMID" in df.columns:
            df["HHFARMID"] = df["HHFARMID"].astype(str).str.strip()

        return df

    def get_metadata(self, table_name: str) -> Any:
        """
        Retrieves metadata only for a given table.
        """
        if not table_name.endswith(".dta"):
            table_name = f"{table_name}.dta"
        file_path = self.raw_data_dir / table_name
        _, meta = pyreadstat.read_dta(str(file_path), metadataonly=True)
        return meta

    def load_all_core_tables(self, smallholders_only: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Loads all core analytical tables required for Phase 2.
        If smallholders_only is True, filters to Holding_type == 2.0.
        """
        master_df, master_meta = self.load_table("AASS2025.dta")
        
        # Identify valid smallholders
        if smallholders_only:
            target_type = self.settings.get("sample_parameters", {}).get("holding_type_smallholder", 2.0)
            smallholder_mask = (master_df["Holding_type"] == target_type)
            smallholder_ids = set(master_df.loc[smallholder_mask, "HHFARMID"])
            logger.info("Filtered master to %d smallholder households (Holding_type == %s)", len(smallholder_ids), target_type)
            master_clean = master_df[smallholder_mask].copy()
        else:
            smallholder_ids = set(master_df["HHFARMID"])
            master_clean = master_df.copy()

        tables = {
            "master": master_clean,
            "masikaplot": self._load_and_filter("MASIKAPLOT.dta", smallholder_ids),
            "vuliplot": self._load_and_filter("VULIPLOT.dta", smallholder_ids),
            "masikacrop": self._load_and_filter("MASIKACROP.dta", smallholder_ids),
            "vulicrop": self._load_and_filter("VULICROP.dta", smallholder_ids),
            "household": self._load_and_filter("HOUSEHOLD.dta", smallholder_ids),
            "field": self._load_and_filter("FIELD.dta", smallholder_ids),
            "shocks": self._load_and_filter("shocks_roster.dta", smallholder_ids),
            "livestock": self._load_and_filter("stock_livestock.dta", smallholder_ids),
        }
        return tables

    def _load_and_filter(self, table_name: str, valid_ids: set) -> pd.DataFrame:
        """Helper to load a table and filter to valid holding IDs."""
        try:
            df, _ = self.load_table(table_name)
            if "HHFARMID" in df.columns:
                initial_count = len(df)
                df = df[df["HHFARMID"].isin(valid_ids)].copy()
                logger.info("Loaded %s: %d rows retained (from %d total) for target cohort.", table_name, len(df), initial_count)
            return df
        except FileNotFoundError:
            logger.warning("Table %s not found. Returning empty DataFrame.", table_name)
            return pd.DataFrame()
