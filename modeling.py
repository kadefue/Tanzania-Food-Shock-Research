"""
Smallholder Yield Volatility Prediction Pipeline
================================================
Author: Kadeghe Goodluck Fue (kadefue@sua.ac.tz)
Institution: Sokoine University of Agriculture (SUA)

Supervised Machine Learning pipeline predicting smallholder yield volatility
across agricultural seasons (Masika vs. Vuli) using Tanzania National Bureau of
Statistics (NBS) Annual Agricultural Sample Survey (AASS) microdata.

Pipeline Architecture:
1. DataPreprocessor: Ingestion, unit harmonization, and seasonal baseline yield calculation.
2. FeatureEngineer: Target formulation (Yield Volatility Index) + 12 Grandmaster Feature
   Engineering techniques (Spatial groupbys, HHI, Berger-Parker, Pielou evenness, Jaccard turnover,
   input intensities, capital-labor ratios, log1p compression, plot heterogeneity, frequency encoding,
   KMeans archetypes, and PCA orthogonal decomposition).
3. VolatilityPredictor: Spatial Cross-Validation (GroupKFold on EA geography) and multi-model
   benchmarking across LightGBM, XGBoost, and Random Forest.
4. ModelInterpreter: SHAP-based global feature attribution and local household explanations.
5. PipelineOrchestrator: End-to-end execution, multi-model comparison, and artifact generation.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadstat
import shap
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, RandomizedSearchCV
from sklearn.preprocessing import OneHotEncoder, RobustScaler

# Model imports with fallback support
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("YieldVolatilityPipeline")


# ==============================================================================
# 1. DATA PREPROCESSOR
# ==============================================================================

class DataPreprocessor:
    """
    Ingests, harmonizes, and prepares NBS Annual Agricultural Sample Survey microdata.

    Handles loading of seasonal crop tables (MASIKACROP, VULICROP), plot records
    (MASIKAPLOT, VULIPLOT), input applications (inputRoster_masika, inputRoster_vuli),
    household demographic rosters, and master geographic holding metadata.
    """

    # Empirical unit-to-kg conversion factors for East African traditional containers
    UNIT_TO_KG_FACTORS: Dict[int, float] = {
        1: 1.0,        # Kilogram
        2: 0.001,      # Gram
        3: 1000.0,     # Metric Tonne
        4: 1.0,        # Litre (standard crop density equivalent)
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
        20: 18.0,      # Tin (Debe ~16-18 kg)
        21: 5.0,       # Small Bucket
        22: 10.0,      # Medium Bucket
        23: 20.0,      # Large Bucket
        24: 15.0,      # Sadoline (~15 kg)
        25: 25.0,      # Small Sack (25 kg)
        26: 50.0,      # Medium Sack (50 kg)
        27: 100.0,     # Large Sack (100 kg)
        28: 120.0,     # Extra Large Sack (120 kg)
        43: 0.75,      # Kibaba (cereals tin 0.5 - 1 kg)
        51: 25.0,      # Mfuko mdogo
        52: 50.0,      # Mfuko wa kati
        53: 100.0,     # Mfuko mkubwa
        54: 15.0,      # Bucket
        55: 1.0,       # Kopo dogo
    }

    def __init__(self, data_dir: Union[str, Path] = "data/AASS 2024_2025") -> None:
        """
        Initialize the DataPreprocessor.

        Args:
            data_dir: Path to directory containing Stata .dta microdata files.
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Microdata directory not found: {self.data_dir.resolve()}")

    def _read_table(self, filename: str) -> pd.DataFrame:
        """Helper to read Stata dataset with case-insensitive file matching."""
        target_path = self.data_dir / filename
        if not target_path.exists():
            matches = [p for p in self.data_dir.glob("*.dta") if p.name.lower() == filename.lower()]
            if matches:
                target_path = matches[0]
            else:
                raise FileNotFoundError(f"Required table {filename} not found in {self.data_dir}")

        logger.info("Loading %s...", target_path.name)
        df, _ = pyreadstat.read_dta(str(target_path))

        # Standardize holding identifier to HHFARMID
        for candidate in ["holding_id", "Holding_ID", "HHFARMID", "hhid"]:
            if candidate in df.columns and candidate != "HHFARMID":
                df = df.rename(columns={candidate: "HHFARMID"})
        return df

    def load_raw_data(self) -> Dict[str, pd.DataFrame]:
        """
        Loads all required tables for smallholder yield and input modeling.

        Returns:
            Dictionary mapping table keys to loaded DataFrames.
        """
        tables = {
            "household": self._read_table("HOUSEHOLD.dta"),
            "masikacrop": self._read_table("MASIKACROP.dta"),
            "vulicrop": self._read_table("VULICROP.dta"),
            "masikaplot": self._read_table("MASIKAPLOT.dta"),
            "vuliplot": self._read_table("VULIPLOT.dta"),
            "inputs_masika": self._read_table("inputRoster_masika.dta"),
            "inputs_vuli": self._read_table("inputRoster_vuli.dta"),
            "master": self._read_table("AASS2025.dta"),
        }
        return tables

    def harmonize_units(self, crop_df: pd.DataFrame, season: str) -> pd.DataFrame:
        """
        Harmonizes heterogeneous harvest measurement units into standardized kilograms (kg).

        Utilizes NBS imputed metric ton harvest values (`harvest_ton * 1000`) where
        calibrated, and applies conversion multipliers to raw non-standard containers.

        Args:
            crop_df: Seasonal crop DataFrame.
            season: 'masika' or 'vuli'.

        Returns:
            DataFrame with added 'production_kg' column.
        """
        df = crop_df.copy()

        # Check for pre-calibrated metric ton variable
        if "harvest_ton" in df.columns:
            df["production_kg"] = df["harvest_ton"].fillna(0.0) * 1000.0
        else:
            df["production_kg"] = 0.0

        # Harmonize raw unit quantities if available and production_kg is unpopulated
        unit_col = "s7q08c_unit" if season == "masika" else "s5q08c_unit"
        qty_col = "s7q08c" if season == "masika" else "s5q08c"

        if unit_col in df.columns and qty_col in df.columns:
            conversion_multipliers = df[unit_col].map(self.UNIT_TO_KG_FACTORS).fillna(1.0)
            raw_kg = df[qty_col].fillna(0.0) * conversion_multipliers
            df["production_kg"] = np.where(df["production_kg"] > 0, df["production_kg"], raw_kg)

        return df

    def calculate_seasonal_yields(
        self,
        crops_masika: pd.DataFrame,
        crops_vuli: pd.DataFrame,
        plots_masika: pd.DataFrame,
        plots_vuli: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculates baseline seasonal yield-per-hectare (kg/ha) for Masika and Vuli.

        Args:
            crops_masika: Harmonized Masika crop observations.
            crops_vuli: Harmonized Vuli crop observations.
            plots_masika: Masika plot records containing measured/imputed hectares.
            plots_vuli: Vuli plot records containing measured/imputed hectares.

        Returns:
            DataFrame aggregated at the household level containing Y_m, Y_v, and areas.
        """
        m_area_col = "s6q03_Hectares" if "s6q03_Hectares" in plots_masika.columns else "s6q03_hec"
        v_area_col = "s4q03_Hectares" if "s4q03_Hectares" in plots_vuli.columns else "s4q03_hec"

        # Household total harvest (kg)
        m_harvest = crops_masika.groupby("HHFARMID")["production_kg"].sum().rename("harvest_kg_masika")
        v_harvest = crops_vuli.groupby("HHFARMID")["production_kg"].sum().rename("harvest_kg_vuli")

        # Household total cultivated area (ha)
        m_area = plots_masika.groupby("HHFARMID")[m_area_col].sum().rename("area_ha_masika")
        v_area = plots_vuli.groupby("HHFARMID")[v_area_col].sum().rename("area_ha_vuli")

        # Merge seasonal aggregations
        seasonal_df = pd.concat([m_harvest, v_harvest, m_area, v_area], axis=1).reset_index()

        # Compute seasonal baseline yields (kg/ha)
        seasonal_df["yield_masika"] = np.where(
            seasonal_df["area_ha_masika"] > 0,
            seasonal_df["harvest_kg_masika"] / seasonal_df["area_ha_masika"],
            np.nan,
        )
        seasonal_df["yield_vuli"] = np.where(
            seasonal_df["area_ha_vuli"] > 0,
            seasonal_df["harvest_kg_vuli"] / seasonal_df["area_ha_vuli"],
            np.nan,
        )

        return seasonal_df


# ==============================================================================
# 2. FEATURE ENGINEER (WITH 10+ GRANDMASTER TECHNIQUES)
# ==============================================================================

class FeatureEngineer:
    """
    Constructs the Yield Volatility Index and domain-specific predictive smallholder features.

    Implements at least 10 Grandmaster-level Feature Engineering Techniques:
    1.  Spatial Groupby Aggregations (Deviations and Ratios to Regional Peer Means)
    2.  Herfindahl-Hirschman Index (HHI) for Crop Portfolio Concentration
    3.  Berger-Parker Dominance Index (Single-Crop Vulnerability)
    4.  Pielou's Evenness Index (Equitability of Cultivated Portfolio)
    5.  Seasonal Crop Portfolio Jaccard Similarity & Turnover Ratio
    6.  Input Application Intensities (Fertilizer and Pesticide per Hectare)
    7.  Land-to-Labor Endowments & Capital-Labor Ratios
    8.  Non-linear Heavy-Tail Compression (Log1p Transforms & Asymmetry Ratios)
    9.  Farm Parcel Fragmentation & Within-Holding Plot Dispersion
    10. Frequency / Prevalence Encoding of Categorical Strata
    11. Unsupervised Agronomic Archetype Clustering (KMeans Distance Embeddings)
    12. Latent Orthogonal Feature Decomposition (PCA Dimensions)
    """

    FERTILIZER_INPUT_IDS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 23, 24, 25, 26, 27, 28, 29, 30, 31}
    PESTICIDE_INPUT_IDS = {15, 16, 17, 18, 19, 20, 21, 22}

    def __init__(self, epsilon: float = 1e-6) -> None:
        """
        Initialize FeatureEngineer.

        Args:
            epsilon: Numerical stability constant for ratio/log divisions.
        """
        self.epsilon = epsilon
        self.preprocessor_pipeline: Optional[ColumnTransformer] = None
        self.kmeans_model: Optional[KMeans] = None
        self.pca_model: Optional[PCA] = None
        self.feature_names_: List[str] = []

    def compute_target(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Formulates the Yield Volatility Index (Y_vol):
            Y_vol = |Y_m - Y_v| / ((Y_m + Y_v) / 2)

        Filters smallholders that cultivate in both seasons and have positive average yields.

        Args:
            df: DataFrame containing 'yield_masika' (Y_m) and 'yield_vuli' (Y_v).

        Returns:
            Tuple of (Filtered DataFrame, Target Series Y_vol indexed by HHFARMID).
        """
        valid_mask = (
            df["yield_masika"].notna()
            & df["yield_vuli"].notna()
            & (df["area_ha_masika"] > 0)
            & (df["area_ha_vuli"] > 0)
        )
        sub_df = df[valid_mask].copy()

        y_m = sub_df["yield_masika"]
        y_v = sub_df["yield_vuli"]
        mean_yield = (y_m + y_v) / 2.0

        # Require positive average yield across seasons
        positive_yield_mask = mean_yield > 0
        sub_df = sub_df[positive_yield_mask].copy()
        if "HHFARMID" in sub_df.columns:
            sub_df = sub_df.set_index("HHFARMID")

        y_m = sub_df["yield_masika"]
        y_v = sub_df["yield_vuli"]
        mean_yield = (y_m + y_v) / 2.0

        y_vol = np.abs(y_m - y_v) / (mean_yield + self.epsilon)
        # Bounded between [0, 2]
        y_vol = y_vol.clip(lower=0.0, upper=2.0).rename("yield_volatility_index")

        logger.info("Formulated target variable Y_vol for %d eligible holdings.", len(sub_df))
        return sub_df, y_vol

    # --------------------------------------------------------------------------
    # Grandmaster Portfolio Metrics: Shannon, HHI, Berger-Parker, Pielou
    # --------------------------------------------------------------------------
    @staticmethod
    def _compute_portfolio_metrics(group: pd.DataFrame, crop_col: str, weight_col: str) -> Dict[str, float]:
        """Computes Shannon Diversity, HHI Concentration, Berger-Parker, and Pielou Evenness."""
        totals = group.groupby(crop_col)[weight_col].sum()
        total_sum = totals.sum()
        if total_sum <= 0:
            return {"shannon": 0.0, "hhi": 1.0, "berger_parker": 1.0, "evenness": 0.0}

        p = totals / total_sum
        p = p[p > 0]
        s = len(p)

        shannon = float(-np.sum(p * np.log(p)))
        hhi = float(np.sum(p ** 2))
        berger_parker = float(np.max(p))
        evenness = float(shannon / np.log(s)) if s > 1 else 0.0

        return {
            "shannon": shannon,
            "hhi": hhi,
            "berger_parker": berger_parker,
            "evenness": evenness
        }

    def engineer_predictive_features(
        self,
        base_df: pd.DataFrame,
        tables: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Extracts and joins domain features across inputs, crop diversity, labor, and plots.

        Applies 10+ Grandmaster Feature Engineering techniques:
        - Input Intensities per Hectare & Input Deltas
        - Shannon, HHI, Berger-Parker, Pielou Evenness
        - Jaccard Similarity and Seasonal Crop Turnover
        - Regional Groupby Aggregations (Deviations and Ratios to Peer Means)
        - Plot Size Variance & Fragmentation
        - Land-to-Labor and Capital-to-Labor Ratios
        - Log1p Skewness Compression & Asymmetry Indicators
        - Frequency Encoding
        """
        logger.info("Engineering Grandmaster-level agricultural features...")
        if "HHFARMID" in base_df.columns:
            base_indexed = base_df.set_index("HHFARMID")
        else:
            base_indexed = base_df.copy()
        holdings = pd.DataFrame(index=base_indexed.index)

        # ----------------------------------------------------------------------
        # 1. Input Deltas & Application Intensities (Technique 6 & 8)
        # ----------------------------------------------------------------------
        im = tables["inputs_masika"].copy()
        iv = tables["inputs_vuli"].copy()

        # Harmonize input units (Unit 1 = Gram -> / 1000 to get kg; Unit 2 = kg)
        im["qty_kg"] = pd.Series(
            np.where(im["s11q01b_unit"] == 1, im["s11q01b"] / 1000.0, im["s11q01b"]),
            index=im.index
        ).fillna(0.0)
        iv["qty_kg"] = pd.Series(
            np.where(iv["s11q01a_unit"] == 1, iv["s11q01a"] / 1000.0, iv["s11q01a"]),
            index=iv.index
        ).fillna(0.0)

        # Fertilizer kg
        fert_m = (
            im[im["InputRoster_masika__id"].isin(self.FERTILIZER_INPUT_IDS)]
            .groupby("HHFARMID")["qty_kg"]
            .sum()
            .rename("fert_masika_kg")
        )
        fert_v = (
            iv[iv["InputRoster_vuli__id"].isin(self.FERTILIZER_INPUT_IDS)]
            .groupby("HHFARMID")["qty_kg"]
            .sum()
            .rename("fert_vuli_kg")
        )

        # Pesticide qty
        pest_m = (
            im[im["InputRoster_masika__id"].isin(self.PESTICIDE_INPUT_IDS)]
            .groupby("HHFARMID")["qty_kg"]
            .sum()
            .rename("pest_masika_qty")
        )
        pest_v = (
            iv[iv["InputRoster_vuli__id"].isin(self.PESTICIDE_INPUT_IDS)]
            .groupby("HHFARMID")["qty_kg"]
            .sum()
            .rename("pest_vuli_qty")
        )

        input_df = pd.concat([fert_m, fert_v, pest_m, pest_v], axis=1).fillna(0.0)
        input_df["delta_fertilizer_kg"] = input_df["fert_masika_kg"] - input_df["fert_vuli_kg"]
        input_df["abs_delta_fertilizer_kg"] = np.abs(input_df["delta_fertilizer_kg"])
        input_df["delta_pesticide_qty"] = input_df["pest_masika_qty"] - input_df["pest_vuli_qty"]
        input_df["fertilizer_seasonal_ratio"] = input_df["fert_masika_kg"] / (
            input_df["fert_masika_kg"] + input_df["fert_vuli_kg"] + self.epsilon
        )

        # Input Intensities per Hectare
        m_area_s = base_indexed["area_ha_masika"]
        v_area_s = base_indexed["area_ha_vuli"]

        input_df["fert_per_ha_masika"] = input_df["fert_masika_kg"] / (m_area_s + self.epsilon)
        input_df["fert_per_ha_vuli"] = input_df["fert_vuli_kg"] / (v_area_s + self.epsilon)
        input_df["delta_fert_intensity"] = input_df["fert_per_ha_masika"] - input_df["fert_per_ha_vuli"]
        input_df["pest_per_ha_masika"] = input_df["pest_masika_qty"] / (m_area_s + self.epsilon)
        input_df["pest_per_ha_vuli"] = input_df["pest_vuli_qty"] / (v_area_s + self.epsilon)

        # Log1p non-linear transforms
        input_df["log_fert_masika"] = np.log1p(np.maximum(0, input_df["fert_masika_kg"]))
        input_df["log_fert_vuli"] = np.log1p(np.maximum(0, input_df["fert_vuli_kg"]))

        # ----------------------------------------------------------------------
        # 2. Crop Portfolio Metrics (Techniques 2, 3, 4: HHI, Berger-Parker, Pielou)
        # ----------------------------------------------------------------------
        mc = tables["masikacrop"].copy()
        vc = tables["vulicrop"].copy()

        m_crop_col = "MASIKACROP__id" if "MASIKACROP__id" in mc.columns else "crop_id"
        v_crop_col = "VULICROP__id" if "VULICROP__id" in vc.columns else "crop_id"

        # Apply portfolio metrics calculation
        m_port_metrics = mc.groupby("HHFARMID").apply(
            lambda g: pd.Series(self._compute_portfolio_metrics(g, m_crop_col, "production_kg")),
            include_groups=False
        ).rename(columns=lambda c: f"{c}_masika")

        v_port_metrics = vc.groupby("HHFARMID").apply(
            lambda g: pd.Series(self._compute_portfolio_metrics(g, v_crop_col, "production_kg")),
            include_groups=False
        ).rename(columns=lambda c: f"{c}_vuli")

        crop_count_m = mc.groupby("HHFARMID")[m_crop_col].nunique().rename("num_crops_masika")
        crop_count_v = vc.groupby("HHFARMID")[v_crop_col].nunique().rename("num_crops_vuli")

        # ----------------------------------------------------------------------
        # 3. Seasonal Portfolio Jaccard Similarity & Turnover Index (Technique 5)
        # ----------------------------------------------------------------------
        m_crops_set = mc.groupby("HHFARMID")[m_crop_col].apply(lambda s: set(s.dropna().unique()))
        v_crops_set = vc.groupby("HHFARMID")[v_crop_col].apply(lambda s: set(s.dropna().unique()))
        crop_sets_df = pd.concat([m_crops_set.rename("m_set"), v_crops_set.rename("v_set")], axis=1)

        def _calc_jaccard(row: pd.Series) -> Tuple[float, float]:
            s_m = row["m_set"] if isinstance(row["m_set"], set) else set()
            s_v = row["v_set"] if isinstance(row["v_set"], set) else set()
            union_len = len(s_m | s_v)
            if union_len == 0:
                return 0.0, 0.0
            inter_len = len(s_m & s_v)
            jaccard = inter_len / union_len
            turnover = (union_len - inter_len) / union_len
            return float(jaccard), float(turnover)

        jaccard_results = crop_sets_df.apply(_calc_jaccard, axis=1)
        jaccard_similarity = pd.Series([r[0] for r in jaccard_results], index=crop_sets_df.index, name="crop_jaccard_similarity")
        crop_turnover = pd.Series([r[1] for r in jaccard_results], index=crop_sets_df.index, name="crop_turnover_ratio")

        # ----------------------------------------------------------------------
        # 4. Labor Allocation & Household Demographics (Technique 7)
        # ----------------------------------------------------------------------
        hh = tables["household"].copy()
        hh_size = hh.groupby("HHFARMID")["HOUSEHOLD__id"].count().rename("hh_size")
        adult_labor = hh[(hh["s2q04"] >= 15) & (hh["s2q04"] <= 64)].groupby("HHFARMID")["HOUSEHOLD__id"].count().rename("adult_labor_count")
        decision_makers = hh[hh["s2q06"] == 1].groupby("HHFARMID")["HOUSEHOLD__id"].count().rename("decision_maker_count")

        heads = hh[hh["s2q03"] == 1].drop_duplicates(subset=["HHFARMID"]).set_index("HHFARMID")
        head_female = (heads["s2q02"] == 2).astype(int).rename("head_is_female")
        head_age = heads["s2q04"].rename("head_age")
        head_ag_training = (heads["s2q09"] == 1).astype(int).rename("head_ag_training")

        labor_shortage_m = mc.groupby("HHFARMID")["s7q06__8"].max().fillna(0).rename("labor_bottleneck_masika")
        labor_shortage_v = vc.groupby("HHFARMID")["s5q06__8"].max().fillna(0).rename("labor_bottleneck_vuli")

        # ----------------------------------------------------------------------
        # 5. Plot Management, Fragmentation & Dispersion (Techniques 8 & 9)
        # ----------------------------------------------------------------------
        mp = tables["masikaplot"].copy()
        vp = tables["vuliplot"].copy()
        m_area_col = "s6q03_Hectares" if "s6q03_Hectares" in mp.columns else "s6q03_hec"

        # Fallow land indicator (s6q02 == 3 is fallow)
        fallow_m = (mp["s6q02"] == 3).groupby(mp["HHFARMID"]).mean().rename("fallow_share_masika")
        fallow_v = (vp["s4q02"] == 3).groupby(vp["HHFARMID"]).mean().rename("fallow_share_vuli")

        # Permanent crops share (croptype == 2 is permanent)
        perm_share = (mc["croptype"] == 2).groupby(mc["HHFARMID"]).mean().rename("permanent_crop_share")

        # Irrigation adoption (s6q05a == 1)
        irrig_m = (mp["s6q05a"] == 1).groupby(mp["HHFARMID"]).mean().rename("irrigation_share_masika")
        irrig_v = (vp["s4q05a"] == 1).groupby(vp["HHFARMID"]).mean().rename("irrigation_share_vuli")

        # Inorganic & organic fertilizer adoption flags
        inorg_m = (mp["s6q09"] == 1).groupby(mp["HHFARMID"]).mean().rename("inorganic_fert_share_masika")
        inorg_v = (vp["s4q09"] == 1).groupby(vp["HHFARMID"]).mean().rename("inorganic_fert_share_vuli")

        # Plot fragmentation and dispersion metrics
        plot_count = mp.groupby("HHFARMID")["MASIKAPLOT__id"].count().rename("plot_count")
        plot_area_std = mp.groupby("HHFARMID")[m_area_col].std().fillna(0.0).rename("plot_area_std")
        plot_area_mean = mp.groupby("HHFARMID")[m_area_col].mean().fillna(0.0).rename("plot_area_mean")
        plot_area_cv = (plot_area_std / (plot_area_mean + self.epsilon)).rename("plot_area_cv")

        # Seasonal crop rotation proxy
        rotation_proxy = np.abs(crop_count_m.fillna(0) - crop_count_v.fillna(0)).rename("seasonal_crop_rotation_index")

        # ----------------------------------------------------------------------
        # 6. Geographic Strata & Frequency Encoding (Technique 10)
        # ----------------------------------------------------------------------
        master = tables["master"].copy().set_index("HHFARMID")
        geo_cols = ["region_id", "stratum_id", "ea_id"]
        master_geo = master[[c for c in geo_cols if c in master.columns]]

        # Frequency encoding of region and stratum
        region_counts = master["region_id"].value_counts(normalize=True).rename("freq_region")
        master_geo = master_geo.join(master["region_id"].map(region_counts).rename("freq_region"))

        # ----------------------------------------------------------------------
        # Assemble Feature Matrix
        # ----------------------------------------------------------------------
        features = holdings.join([
            base_indexed[["area_ha_masika", "area_ha_vuli"]],
            input_df,
            m_port_metrics,
            v_port_metrics,
            crop_count_m,
            crop_count_v,
            jaccard_similarity,
            crop_turnover,
            hh_size,
            adult_labor,
            decision_makers,
            head_female,
            head_age,
            head_ag_training,
            labor_shortage_m,
            labor_shortage_v,
            fallow_m,
            fallow_v,
            perm_share,
            irrig_m,
            irrig_v,
            inorg_m,
            inorg_v,
            plot_count,
            plot_area_std,
            plot_area_mean,
            plot_area_cv,
            rotation_proxy,
            master_geo
        ], how="left").fillna(0.0)

        # ----------------------------------------------------------------------
        # 7. Cross-Domain Ratios & Asymmetries (Techniques 7 & 8)
        # ----------------------------------------------------------------------
        features["total_farm_area_ha"] = features["area_ha_masika"] + features["area_ha_vuli"]
        features["log_total_farm_area"] = np.log1p(np.maximum(0, features["total_farm_area_ha"]))
        features["labor_dependency_ratio"] = features["hh_size"] / (features["adult_labor_count"] + 1.0)
        features["land_per_adult_labor"] = features["total_farm_area_ha"] / (features["adult_labor_count"] + 1.0)
        features["fert_per_adult_labor"] = (features["fert_masika_kg"] + features["fert_vuli_kg"]) / (features["adult_labor_count"] + 1.0)
        features["plots_per_adult_labor"] = features["plot_count"] / (features["adult_labor_count"] + 1.0)

        features["seasonal_land_asymmetry"] = (features["area_ha_masika"] - features["area_ha_vuli"]) / (
            features["total_farm_area_ha"] + self.epsilon
        )
        features["delta_irrigation_share"] = features["irrigation_share_masika"] - features["irrigation_share_vuli"]
        features["delta_shannon_diversity"] = features["shannon_masika"] - features["shannon_vuli"]
        features["delta_hhi_concentration"] = features["hhi_masika"] - features["hhi_vuli"]
        features["delta_evenness"] = features["evenness_masika"] - features["evenness_vuli"]

        # ----------------------------------------------------------------------
        # 8. Spatial Peer Groupby Aggregations (Technique 1)
        # ----------------------------------------------------------------------
        # Compute regional benchmark means for land, fertilizer, and diversity
        reg_means = features.groupby("region_id")[["total_farm_area_ha", "fert_masika_kg", "shannon_masika"]].transform("mean")
        reg_stds = features.groupby("region_id")[["total_farm_area_ha", "fert_masika_kg", "shannon_masika"]].transform("std").fillna(1.0)

        features["area_diff_from_region_mean"] = features["total_farm_area_ha"] - reg_means["total_farm_area_ha"]
        features["area_ratio_to_region_mean"] = features["total_farm_area_ha"] / (reg_means["total_farm_area_ha"] + self.epsilon)
        features["area_zscore_in_region"] = features["area_diff_from_region_mean"] / (reg_stds["total_farm_area_ha"] + self.epsilon)

        features["fert_diff_from_region_mean"] = features["fert_masika_kg"] - reg_means["fert_masika_kg"]
        features["fert_ratio_to_region_mean"] = features["fert_masika_kg"] / (reg_means["fert_masika_kg"] + self.epsilon)

        features["shannon_diff_from_region_mean"] = features["shannon_masika"] - reg_means["shannon_masika"]

        logger.info(
            "Engineered %d advanced Grandmaster features across %d holdings.",
            features.shape[1], len(features)
        )
        return features

    def fit_transform(
        self,
        X_df: pd.DataFrame
    ) -> Tuple[np.ndarray, List[str], np.ndarray]:
        """
        Fits scalers, encoders, KMeans cluster distances, and PCA components.

        Applies Techniques 11 (KMeans archetypes) and 12 (PCA Latent Decomposition).

        Args:
            X_df: Raw engineered features DataFrame including 'ea_id'.

        Returns:
            Tuple of (Transformed feature array, Feature names list, Group array for spatial CV).
        """
        # Extract spatial grouping variable
        if "ea_id" in X_df.columns:
            groups = X_df["ea_id"].values
            X_modeling = X_df.drop(columns=["ea_id"])
        else:
            groups = np.arange(len(X_df))
            X_modeling = X_df.copy()

        categorical_cols = ["region_id", "stratum_id"]
        cat_present = [c for c in categorical_cols if c in X_modeling.columns]
        num_cols = [c for c in X_modeling.columns if c not in cat_present]

        transformers = []
        if cat_present:
            transformers.append(
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_present)
            )
        if num_cols:
            transformers.append(
                ("num", RobustScaler(), num_cols)
            )

        self.preprocessor_pipeline = ColumnTransformer(transformers=transformers)
        X_scaled = self.preprocessor_pipeline.fit_transform(X_modeling)

        feature_names: List[str] = []
        for name, trans, cols in self.preprocessor_pipeline.transformers_:
            if name == "cat":
                cats = trans.get_feature_names_out(cols)
                feature_names.extend(cats)
            elif name == "num":
                feature_names.extend(cols)

        # ----------------------------------------------------------------------
        # 9. KMeans Agronomic Archetype Clustering (Technique 11)
        # ----------------------------------------------------------------------
        logger.info("Computing KMeans Archetype Cluster Distance Embeddings...")
        self.kmeans_model = KMeans(n_clusters=4, random_state=42, n_init=10)
        kmeans_distances = self.kmeans_model.fit_transform(X_scaled)
        kmeans_feature_names = [f"dist_agronomic_archetype_{k}" for k in range(4)]

        # ----------------------------------------------------------------------
        # 10. Latent Orthogonal PCA Decomposition (Technique 12)
        # ----------------------------------------------------------------------
        logger.info("Extracting top 3 PCA orthogonal components...")
        self.pca_model = PCA(n_components=3, random_state=42)
        pca_components = self.pca_model.fit_transform(X_scaled)
        pca_feature_names = ["pca_latent_comp_1", "pca_latent_comp_2", "pca_latent_comp_3"]

        # Concatenate scaled features with KMeans distances and PCA dimensions
        X_final = np.hstack([X_scaled, kmeans_distances, pca_components])
        feature_names.extend(kmeans_feature_names)
        feature_names.extend(pca_feature_names)

        self.feature_names_ = feature_names
        return X_final, self.feature_names_, groups

    def transform(self, X_df: pd.DataFrame) -> np.ndarray:
        """Transforms new observations using the fitted pipeline."""
        if self.preprocessor_pipeline is None or self.kmeans_model is None or self.pca_model is None:
            raise ValueError("FeatureEngineer preprocessor pipeline has not been fitted.")

        X_modeling = X_df.drop(columns=["ea_id"], errors="ignore")
        X_scaled = self.preprocessor_pipeline.transform(X_modeling)
        kmeans_distances = self.kmeans_model.transform(X_scaled)
        pca_components = self.pca_model.transform(X_scaled)

        return np.hstack([X_scaled, kmeans_distances, pca_components])


# ==============================================================================
# 3. VOLATILITY PREDICTOR & MULTI-MODEL BENCHMARKER
# ==============================================================================

class VolatilityPredictor:
    """
    Supervised regressor benchmarking smallholder yield volatility.

    Supports LightGBM, XGBoost, and Random Forest.
    Employs Spatial Cross-Validation grouped by Enumeration Area (EA) geography
    to prevent spatial autocorrelation leakage.
    """

    def __init__(
        self,
        model_type: str = "lightgbm",
        random_state: int = 42,
        **model_params: Any
    ) -> None:
        """
        Initialize the VolatilityPredictor.

        Args:
            model_type: 'lightgbm', 'xgboost', or 'random_forest'.
            random_state: Reproducibility seed.
            **model_params: Optional estimator hyperparameters.
        """
        self.model_type = model_type.lower()
        self.random_state = random_state
        self.model_params = model_params
        self.model = self._instantiate_model(self.model_type, self.model_params)

    def _instantiate_model(self, mtype: str, params: Dict[str, Any]) -> Any:
        """Instantiates LightGBM, XGBoost, or RandomForest Regressor."""
        mtype = mtype.lower()
        if mtype == "lightgbm":
            if not HAS_LIGHTGBM:
                raise ImportError("lightgbm is not installed.")
            default_params = {
                "n_estimators": 200,
                "learning_rate": 0.04,
                "max_depth": 6,
                "num_leaves": 31,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": self.random_state,
                "verbose": -1,
                "n_jobs": -1,
            }
            default_params.update(params)
            return lgb.LGBMRegressor(**default_params)

        elif mtype == "xgboost":
            if not HAS_XGBOOST:
                raise ImportError("xgboost is not installed.")
            default_params = {
                "n_estimators": 200,
                "learning_rate": 0.04,
                "max_depth": 5,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": self.random_state,
                "verbosity": 0,
                "n_jobs": -1,
            }
            default_params.update(params)
            return xgb.XGBRegressor(**default_params)

        elif mtype in ["random_forest", "rf"]:
            default_params = {
                "n_estimators": 200,
                "max_depth": 14,
                "min_samples_split": 5,
                "min_samples_leaf": 3,
                "max_features": "sqrt",
                "random_state": self.random_state,
                "n_jobs": -1,
            }
            default_params.update(params)
            return RandomForestRegressor(**default_params)

        else:
            raise ValueError(f"Unsupported model_type: {mtype}. Choose 'lightgbm', 'xgboost', or 'random_forest'.")

    def spatial_cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        n_splits: int = 5,
        model_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes Spatial Cross-Validation using Enumeration Area (EA) cluster groups.

        Ensures that smallholders in the same village/EA are kept strictly in either
        the training or validation fold, eliminating spatial leakage.

        Args:
            X: Feature matrix.
            y: Target volatility vector.
            groups: Enumeration Area IDs array.
            n_splits: Number of spatial cross-validation folds.
            model_type: Architecture to test (defaults to self.model_type).

        Returns:
            Dictionary containing fold-level and aggregated validation metrics.
        """
        target_mtype = (model_type or self.model_type).lower()
        gkf = GroupKFold(n_splits=n_splits)
        oof_predictions = np.zeros(len(y))
        fold_metrics = []

        start_time = time.time()
        for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=groups), start=1):
            X_train, y_train = X[train_idx], y[train_idx]
            X_val, y_val = X[val_idx], y[val_idx]

            fold_model = self._instantiate_model(target_mtype, self.model_params)
            fold_model.fit(X_train, y_train)

            preds = fold_model.predict(X_val)
            oof_predictions[val_idx] = preds

            rmse = np.sqrt(mean_squared_error(y_val, preds))
            mae = mean_absolute_error(y_val, preds)
            r2 = r2_score(y_val, preds)

            fold_metrics.append({"fold": fold, "rmse": rmse, "mae": mae, "r2": r2})

        elapsed = time.time() - start_time
        overall_rmse = np.sqrt(mean_squared_error(y, oof_predictions))
        overall_mae = mean_absolute_error(y, oof_predictions)
        overall_r2 = r2_score(y, oof_predictions)

        results = {
            "model_type": target_mtype,
            "overall_rmse": float(overall_rmse),
            "overall_mae": float(overall_mae),
            "overall_r2": float(overall_r2),
            "elapsed_seconds": round(elapsed, 2),
            "fold_metrics": fold_metrics,
            "oof_predictions": oof_predictions,
        }
        logger.info(
            "[%s] Spatial CV -> RMSE: %.4f | MAE: %.4f | R^2: %.4f | Time: %.2fs",
            target_mtype.upper(), overall_rmse, overall_mae, overall_r2, elapsed
        )
        return results

    def compare_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        n_splits: int = 5
    ) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
        """
        Executes benchmark comparison across LightGBM, XGBoost, and Random Forest.

        Evaluates all three architectures using identical Spatial GroupKFold splits.

        Args:
            X: Feature matrix.
            y: Target volatility array.
            groups: Enumeration Area IDs array.
            n_splits: Number of spatial CV folds.

        Returns:
            Tuple of (Comparison summary DataFrame, Full detailed results dictionary).
        """
        logger.info("=" * 70)
        logger.info("STARTING MULTI-MODEL BENCHMARK (LightGBM vs XGBoost vs Random Forest)")
        logger.info("=" * 70)

        architectures = ["lightgbm", "xgboost", "random_forest"]
        comparison_records = []
        detailed_results = {}

        for arch in architectures:
            logger.info("Evaluating %s with 5-Fold Spatial Cross-Validation...", arch.upper())
            res = self.spatial_cross_validate(X, y, groups=groups, n_splits=n_splits, model_type=arch)
            detailed_results[arch] = res
            comparison_records.append({
                "Model": arch.upper(),
                "Spatial RMSE": res["overall_rmse"],
                "Spatial MAE": res["overall_mae"],
                "Spatial R2": res["overall_r2"],
                "Train Time (s)": res["elapsed_seconds"]
            })

        comparison_df = pd.DataFrame(comparison_records).sort_values(by="Spatial RMSE").reset_index(drop=True)
        logger.info("\n" + comparison_df.to_string(index=False))
        return comparison_df, detailed_results

    def fit(self, X: np.ndarray, y: np.ndarray) -> VolatilityPredictor:
        """Fits final regressor on full training dataset."""
        logger.info("Fitting final %s model on all data...", self.model_type)
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generates predictions for yield volatility."""
        return self.model.predict(X)


# ==============================================================================
# 4. MODEL INTERPRETER
# ==============================================================================

class ModelInterpreter:
    """
    Interprets yield volatility drivers using SHAP (SHapley Additive exPlanations).

    Extracts global feature importances, generates summary/beeswarm plots,
    and isolates local household-level risk and protective factors.
    """

    def __init__(
        self,
        model: Any,
        feature_names: List[str],
        output_dir: Union[str, Path] = "artifacts/interpretability"
    ) -> None:
        """
        Initialize ModelInterpreter.

        Args:
            model: Trained Tree-based regressor (LightGBM/XGBoost/RandomForest).
            feature_names: Ordered list of feature names.
            output_dir: Output directory path for plots and explanation tables.
        """
        self.model = model
        self.feature_names = feature_names
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.explainer = shap.TreeExplainer(self.model)

    def explain_global(
        self,
        X: np.ndarray,
        max_display: int = 20
    ) -> pd.DataFrame:
        """
        Extracts global SHAP feature importance and saves summary visual plots.

        Args:
            X: Feature matrix.
            max_display: Maximum number of top features to render.

        Returns:
            DataFrame with mean absolute SHAP values per feature.
        """
        logger.info("Computing global SHAP values across %d observations...", len(X))
        shap_values = self.explainer(X)

        # 1. Summary Beeswarm Plot
        plt.figure(figsize=(10, 8), dpi=300)
        shap.summary_plot(
            shap_values.values,
            features=X,
            feature_names=self.feature_names,
            max_display=max_display,
            show=False
        )
        summary_path = self.output_dir / "shap_summary_plot.png"
        plt.tight_layout()
        plt.savefig(summary_path, bbox_inches="tight")
        plt.close()
        logger.info("Saved SHAP summary plot to %s", summary_path)

        # 2. Global Bar Importance Plot
        plt.figure(figsize=(10, 8), dpi=300)
        shap.plots.bar(shap_values, max_display=max_display, show=False)
        bar_path = self.output_dir / "shap_importance_bar.png"
        plt.tight_layout()
        plt.savefig(bar_path, bbox_inches="tight")
        plt.close()
        logger.info("Saved SHAP feature importance bar plot to %s", bar_path)

        # 3. Formulate Importance DataFrame
        mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
        importance_df = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": mean_abs_shap
        }).sort_values(by="mean_abs_shap", ascending=False).reset_index(drop=True)

        importance_csv = self.output_dir / "feature_importance_shap.csv"
        importance_df.to_csv(importance_csv, index=False)
        return importance_df

    def explain_local(
        self,
        X: np.ndarray,
        household_idx: int,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Computes local SHAP explanation for a specific smallholder household.

        Identifies the primary features driving predicted yield volatility higher
        (risk factors) or lower (protective resilience factors).

        Args:
            X: Feature matrix.
            household_idx: Zero-based row index of the target household.
            top_k: Number of top driving features to report.

        Returns:
            Dictionary containing base value, prediction, and top drivers.
        """
        single_x = X[household_idx : household_idx + 1]
        shap_values_single = self.explainer(single_x)

        base_val = float(shap_values_single.base_values[0])
        pred_val = float(self.model.predict(single_x)[0])
        vals = shap_values_single.values[0]

        impacts = pd.DataFrame({
            "feature": self.feature_names,
            "value": single_x[0],
            "shap_value": vals
        })

        # Top factors increasing volatility
        risk_factors = (
            impacts.sort_values(by="shap_value", ascending=False)
            .head(top_k)
            .to_dict(orient="records")
        )
        # Top factors mitigating volatility
        protective_factors = (
            impacts.sort_values(by="shap_value", ascending=True)
            .head(top_k)
            .to_dict(orient="records")
        )

        # Render Waterfall Plot
        plt.figure(figsize=(9, 6), dpi=300)
        shap.plots.waterfall(shap_values_single[0], max_display=top_k * 2, show=False)
        waterfall_path = self.output_dir / f"household_{household_idx}_waterfall.png"
        plt.tight_layout()
        plt.savefig(waterfall_path, bbox_inches="tight")
        plt.close()

        local_summary = {
            "household_index": household_idx,
            "base_expected_volatility": base_val,
            "predicted_volatility": pred_val,
            "top_risk_drivers": risk_factors,
            "top_protective_drivers": protective_factors,
            "plot_saved_to": str(waterfall_path)
        }
        return local_summary


# ==============================================================================
# 5. PIPELINE ORCHESTRATOR
# ==============================================================================

class PipelineOrchestrator:
    """
    Coordinates the end-to-end Machine Learning pipeline:
    Data Ingestion -> Grandmaster Feature Engineering -> Multi-Model Benchmark
    -> Champion Model Selection -> SHAP Interpretability.
    """

    def __init__(
        self,
        data_dir: Union[str, Path] = "data/AASS 2024_2025",
        output_dir: Union[str, Path] = "artifacts/yield_volatility",
        compare_models: bool = True,
        champion_model_type: str = "lightgbm",
        random_state: int = 42
    ) -> None:
        """
        Initialize the PipelineOrchestrator.

        Args:
            data_dir: Directory containing raw AASS microdata.
            output_dir: Destination for metrics, logs, and SHAP plots.
            compare_models: If True, executes spatial benchmark of LightGBM, XGBoost, and RF.
            champion_model_type: Default architecture if compare_models is False.
            random_state: Seed for reproducibility.
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.compare_models_flag = compare_models
        self.champion_model_type = champion_model_type.lower()
        self.random_state = random_state

        # Instantiate OOP components
        self.preprocessor = DataPreprocessor(self.data_dir)
        self.engineer = FeatureEngineer()
        self.predictor = VolatilityPredictor(model_type=self.champion_model_type, random_state=self.random_state)
        self.interpreter: Optional[ModelInterpreter] = None

    def plot_model_comparison(self, comparison_df: pd.DataFrame) -> Path:
        """Renders visual bar comparison of RMSE, MAE, and R^2 across models."""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=300)

        # RMSE
        axes[0].bar(comparison_df["Model"], comparison_df["Spatial RMSE"], color="#1f77b4", alpha=0.85)
        axes[0].set_title("Spatial RMSE (Lower is Better)", fontweight="bold")
        axes[0].set_ylabel("RMSE")
        axes[0].grid(axis="y", linestyle="--", alpha=0.5)

        # MAE
        axes[1].bar(comparison_df["Model"], comparison_df["Spatial MAE"], color="#ff7f0e", alpha=0.85)
        axes[1].set_title("Spatial MAE (Lower is Better)", fontweight="bold")
        axes[1].set_ylabel("MAE")
        axes[1].grid(axis="y", linestyle="--", alpha=0.5)

        # R^2
        axes[2].bar(comparison_df["Model"], comparison_df["Spatial R2"], color="#2ca02c", alpha=0.85)
        axes[2].set_title("Spatial R² (Higher is Better)", fontweight="bold")
        axes[2].set_ylabel("R² Score")
        axes[2].grid(axis="y", linestyle="--", alpha=0.5)

        chart_path = self.output_dir / "model_comparison.png"
        plt.tight_layout()
        plt.savefig(chart_path, bbox_inches="tight")
        plt.close()
        logger.info("Saved model comparison visual chart to %s", chart_path)
        return chart_path

    def run(self) -> Dict[str, Any]:
        """
        Executes the full pipeline sequentially with multi-model benchmarking.

        Returns:
            Dictionary containing evaluation metrics and output artifact paths.
        """
        logger.info("=" * 70)
        logger.info("STARTING GRANDMASTER SMALLHOLDER YIELD VOLATILITY ML PIPELINE")
        logger.info("=" * 70)

        # Step 1: Ingestion and Preprocessing
        tables = self.preprocessor.load_raw_data()
        crops_m_harm = self.preprocessor.harmonize_units(tables["masikacrop"], season="masika")
        crops_v_harm = self.preprocessor.harmonize_units(tables["vulicrop"], season="vuli")
        tables["masikacrop"] = crops_m_harm
        tables["vulicrop"] = crops_v_harm

        seasonal_yields = self.preprocessor.calculate_seasonal_yields(
            crops_masika=crops_m_harm,
            crops_vuli=crops_v_harm,
            plots_masika=tables["masikaplot"],
            plots_vuli=tables["vuliplot"],
        )

        # Step 2: Feature Engineering & Target Formulation
        eligible_df, y_target = self.engineer.compute_target(seasonal_yields)
        X_df = self.engineer.engineer_predictive_features(eligible_df, tables)

        # Align target index with engineered features
        y_aligned = y_target.loc[X_df.index].values
        X_mat, feature_names, groups = self.engineer.fit_transform(X_df)

        logger.info(
            "Prepared Grandmaster Modeling Matrix: %d smallholders, %d features, %d spatial EAs.",
            X_mat.shape[0], X_mat.shape[1], len(np.unique(groups))
        )

        # Step 3: Multi-Model Benchmark (LightGBM vs. XGBoost vs. Random Forest)
        comparison_dict = {}
        if self.compare_models_flag:
            comparison_df, detailed_cv = self.predictor.compare_models(X_mat, y_aligned, groups=groups, n_splits=5)
            self.plot_model_comparison(comparison_df)

            # Determine champion model based on lowest Spatial RMSE
            best_model_name = comparison_df.iloc[0]["Model"].lower()
            if "lightgbm" in best_model_name:
                champion_mtype = "lightgbm"
            elif "xgboost" in best_model_name:
                champion_mtype = "xgboost"
            else:
                champion_mtype = "random_forest"

            logger.info(">>> Champion Architecture Selected: %s <<<", champion_mtype.upper())
            comparison_dict = comparison_df.to_dict(orient="records")
        else:
            champion_mtype = self.champion_model_type

        # Step 4: Fit Champion Model & Interpret with SHAP
        self.predictor = VolatilityPredictor(model_type=champion_mtype, random_state=self.random_state)
        champion_cv = self.predictor.spatial_cross_validate(X_mat, y_aligned, groups=groups, n_splits=5)
        self.predictor.fit(X_mat, y_aligned)

        self.interpreter = ModelInterpreter(
            model=self.predictor.model,
            feature_names=feature_names,
            output_dir=self.output_dir / "interpretability"
        )
        importance_df = self.interpreter.explain_global(X_mat, max_display=20)
        sample_local = self.interpreter.explain_local(X_mat, household_idx=0, top_k=5)

        # Step 5: Export Execution Metadata & Metrics
        metrics_payload = {
            "champion_model": champion_mtype,
            "holdings_count": int(X_mat.shape[0]),
            "features_count": int(X_mat.shape[1]),
            "enumeration_areas_count": int(len(np.unique(groups))),
            "champion_spatial_cv_rmse": champion_cv["overall_rmse"],
            "champion_spatial_cv_mae": champion_cv["overall_mae"],
            "champion_spatial_cv_r2": champion_cv["overall_r2"],
            "model_comparison": comparison_dict,
            "top_10_predictive_features": importance_df.head(10).to_dict(orient="records"),
            "sample_local_explanation": sample_local
        }

        metrics_file = self.output_dir / "pipeline_metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(metrics_payload, f, indent=4)
        logger.info("Saved pipeline evaluation metrics to %s", metrics_file)

        logger.info("=" * 70)
        logger.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        return metrics_payload


# ==============================================================================
# CLI EXECUTION ENTRY POINT
# ==============================================================================

def parse_args() -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="Predict Smallholder Yield Volatility using Tanzania AASS Microdata."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/AASS 2024_2025",
        help="Path to folder containing AASS Stata .dta tables."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts/yield_volatility",
        help="Path to save evaluation artifacts and SHAP plots."
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        default=True,
        help="Execute multi-model spatial comparison across LightGBM, XGBoost, and Random Forest."
    )
    parser.add_argument(
        "--model-type",
        type=str,
        choices=["lightgbm", "xgboost", "random_forest"],
        default="lightgbm",
        help="Default model if --compare is not set."
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    orchestrator = PipelineOrchestrator(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        compare_models=args.compare,
        champion_model_type=args.model_type,
        random_state=args.random_state
    )
    orchestrator.run()
