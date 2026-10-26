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
2. FeatureEngineer: Target formulation (Yield Volatility Index), input deltas,
   Shannon crop diversity, labor shifts, plot management, and feature scaling/encoding.
3. VolatilityPredictor: Gradient boosting regressor (LightGBM/XGBoost) with Spatial
   Cross-Validation grouped by Enumeration Area (EA) geography and hyperparameter optimization.
4. ModelInterpreter: SHAP-based global feature attribution and local household explanations.
5. PipelineOrchestrator: End-to-end execution, evaluation, and artifact generation.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadstat
import shap
from sklearn.compose import ColumnTransformer
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

    # Empirical unit-to-kg conversion factors for East African traditional units
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
            # Attempt case-insensitive match
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
            # Fill missing or zero values from raw calculation
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
        # Identify area columns (Hectares)
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
        # Yield is undefined if area <= 0; clip outliers for numerical robustness
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
# 2. FEATURE ENGINEER
# ==============================================================================

class FeatureEngineer:
    """
    Constructs the Yield Volatility Index and domain-specific predictive smallholder features.

    Calculates input deltas, Shannon crop portfolio diversity, labor allocation shifts,
    and plot management strategies (crop rotation, fallow land, permanent crops).
    Applies standard scikit-learn transformers.
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
        self.feature_names_: List[str] = []

    def compute_target(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Formulates the Yield Volatility Index (Y_vol):
            Y_vol = |Y_m - Y_v| / ((Y_m + Y_v) / 2)

        Filters smallholders that cultivate in both seasons and have positive average yields.

        Args:
            df: DataFrame containing 'yield_masika' (Y_m) and 'yield_vuli' (Y_v).

        Returns:
            Tuple of (Filtered DataFrame, Target Series Y_vol).
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

    @staticmethod
    def _calculate_shannon_diversity(group: pd.DataFrame, crop_col: str, weight_col: str) -> float:
        """Computes the Shannon Diversity Index: H = -sum(p_i * ln(p_i))."""
        totals = group.groupby(crop_col)[weight_col].sum()
        total_sum = totals.sum()
        if total_sum <= 0:
            return 0.0
        p = totals / total_sum
        p = p[p > 0]
        return float(-np.sum(p * np.log(p)))

    def engineer_predictive_features(
        self,
        base_df: pd.DataFrame,
        tables: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Extracts and joins domain features across inputs, crop diversity, labor, and plots.

        Args:
            base_df: Pre-filtered DataFrame of holdings with computed target metadata.
            tables: Dictionary of raw data tables.

        Returns:
            DataFrame containing engineered features indexed by HHFARMID.
        """
        logger.info("Engineering agricultural features...")
        if "HHFARMID" in base_df.columns:
            base_indexed = base_df.set_index("HHFARMID")
        else:
            base_indexed = base_df.copy()
        holdings = pd.DataFrame(index=base_indexed.index)

        # ----------------------------------------------------------------------
        # A. Input Deltas (Fertilizer and Pesticide quantities)
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

        # ----------------------------------------------------------------------
        # B. Shannon Diversity Index for Crop Portfolios
        # ----------------------------------------------------------------------
        mc = tables["masikacrop"].copy()
        vc = tables["vulicrop"].copy()

        # Crop ID columns
        m_crop_col = "MASIKACROP__id" if "MASIKACROP__id" in mc.columns else "crop_id"
        v_crop_col = "VULICROP__id" if "VULICROP__id" in vc.columns else "crop_id"

        shannon_m = mc.groupby("HHFARMID").apply(
            lambda g: self._calculate_shannon_diversity(g, m_crop_col, "production_kg"),
            include_groups=False
        ).rename("shannon_diversity_masika")

        shannon_v = vc.groupby("HHFARMID").apply(
            lambda g: self._calculate_shannon_diversity(g, v_crop_col, "production_kg"),
            include_groups=False
        ).rename("shannon_diversity_vuli")

        crop_count_m = mc.groupby("HHFARMID")[m_crop_col].nunique().rename("num_crops_masika")
        crop_count_v = vc.groupby("HHFARMID")[v_crop_col].nunique().rename("num_crops_vuli")

        # ----------------------------------------------------------------------
        # C. Labor Allocation & Household Demographics
        # ----------------------------------------------------------------------
        hh = tables["household"].copy()
        hh_size = hh.groupby("HHFARMID")["HOUSEHOLD__id"].count().rename("hh_size")
        adult_labor = hh[(hh["s2q04"] >= 15) & (hh["s2q04"] <= 64)].groupby("HHFARMID")["HOUSEHOLD__id"].count().rename("adult_labor_count")
        decision_makers = hh[hh["s2q06"] == 1].groupby("HHFARMID")["HOUSEHOLD__id"].count().rename("decision_maker_count")

        # Head characteristics (s2q03 == 1 is Head)
        heads = hh[hh["s2q03"] == 1].drop_duplicates(subset=["HHFARMID"]).set_index("HHFARMID")
        head_female = (heads["s2q02"] == 2).astype(int).rename("head_is_female")
        head_age = heads["s2q04"].rename("head_age")
        head_ag_training = (heads["s2q09"] == 1).astype(int).rename("head_ag_training")

        # Seasonal labor shortages reported in crops
        labor_shortage_m = mc.groupby("HHFARMID")["s7q06__8"].max().fillna(0).rename("labor_bottleneck_masika")
        labor_shortage_v = vc.groupby("HHFARMID")["s5q06__8"].max().fillna(0).rename("labor_bottleneck_vuli")

        # ----------------------------------------------------------------------
        # D. Plot Management (Crop Rotation, Fallow, Permanent Crops, Irrigation)
        # ----------------------------------------------------------------------
        mp = tables["masikaplot"].copy()
        vp = tables["vuliplot"].copy()

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

        # Number of plots
        plot_count = mp.groupby("HHFARMID")["MASIKAPLOT__id"].count().rename("plot_count")

        # Crop rotation proxy: difference in crop count and composition between seasons
        rotation_proxy = np.abs(crop_count_m.fillna(0) - crop_count_v.fillna(0)).rename("seasonal_crop_rotation_index")

        # ----------------------------------------------------------------------
        # E. Geographic Strata and Master Holding Attributes
        # ----------------------------------------------------------------------
        master = tables["master"].copy().set_index("HHFARMID")
        geo_cols = ["region_id", "stratum_id", "ea_id"]
        master_geo = master[[c for c in geo_cols if c in master.columns]]

        # Combine all features onto base holding roster
        features = holdings.join([
            base_indexed[["area_ha_masika", "area_ha_vuli"]],
            input_df,
            shannon_m,
            shannon_v,
            crop_count_m,
            crop_count_v,
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
            rotation_proxy,
            master_geo
        ], how="left").fillna(0.0)

        # Derived composite ratios
        features["total_farm_area_ha"] = features["area_ha_masika"] + features["area_ha_vuli"]
        features["labor_dependency_ratio"] = features["hh_size"] / (features["adult_labor_count"] + 1.0)
        features["delta_irrigation_share"] = features["irrigation_share_masika"] - features["irrigation_share_vuli"]
        features["delta_shannon_diversity"] = features["shannon_diversity_masika"] - features["shannon_diversity_vuli"]

        logger.info("Engineered %d predictive features across %d holdings.", features.shape[1], len(features))
        return features

    def fit_transform(
        self,
        X_df: pd.DataFrame
    ) -> Tuple[np.ndarray, List[str], np.ndarray]:
        """
        Fits scalers and encoders, separating spatial grouping keys from modeling features.

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
        X_transformed = self.preprocessor_pipeline.fit_transform(X_modeling)

        # Recover clean feature names
        feature_names: List[str] = []
        for name, trans, cols in self.preprocessor_pipeline.transformers_:
            if name == "cat":
                cats = trans.get_feature_names_out(cols)
                feature_names.extend(cats)
            elif name == "num":
                feature_names.extend(cols)

        self.feature_names_ = feature_names
        return X_transformed, self.feature_names_, groups

    def transform(self, X_df: pd.DataFrame) -> np.ndarray:
        """Transforms new observations using the fitted pipeline."""
        if self.preprocessor_pipeline is None:
            raise ValueError("FeatureEngineer preprocessor pipeline has not been fitted.")
        X_modeling = X_df.drop(columns=["ea_id"], errors="ignore")
        return self.preprocessor_pipeline.transform(X_modeling)


# ==============================================================================
# 3. VOLATILITY PREDICTOR
# ==============================================================================

class VolatilityPredictor:
    """
    Supervised gradient boosting regressor for smallholder yield volatility.

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
            model_type: 'lightgbm' or 'xgboost'.
            random_state: Reproducibility seed.
            **model_params: Optional estimator hyperparameters.
        """
        self.model_type = model_type.lower()
        self.random_state = random_state
        self.model_params = model_params
        self.model = self._instantiate_model(self.model_params)

    def _instantiate_model(self, params: Dict[str, Any]) -> Any:
        """Instantiates either LightGBM or XGBoost Regressor."""
        if self.model_type == "lightgbm":
            if not HAS_LIGHTGBM:
                raise ImportError("lightgbm is not installed. Use model_type='xgboost' or install lightgbm.")
            default_params = {
                "n_estimators": 150,
                "learning_rate": 0.05,
                "max_depth": 5,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": self.random_state,
                "verbose": -1,
                "n_jobs": -1,
            }
            default_params.update(params)
            return lgb.LGBMRegressor(**default_params)

        elif self.model_type == "xgboost":
            if not HAS_XGBOOST:
                raise ImportError("xgboost is not installed. Use model_type='lightgbm' or install xgboost.")
            default_params = {
                "n_estimators": 150,
                "learning_rate": 0.05,
                "max_depth": 5,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": self.random_state,
                "verbosity": 0,
                "n_jobs": -1,
            }
            default_params.update(params)
            return xgb.XGBRegressor(**default_params)
        else:
            raise ValueError(f"Unsupported model_type: {self.model_type}. Choose 'lightgbm' or 'xgboost'.")

    def spatial_cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        n_splits: int = 5
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

        Returns:
            Dictionary containing fold-level and aggregated validation metrics.
        """
        gkf = GroupKFold(n_splits=n_splits)
        oof_predictions = np.zeros(len(y))
        fold_metrics = []

        logger.info("Executing %d-Fold Spatial Cross-Validation on %d unique EAs...", n_splits, len(np.unique(groups)))

        for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=groups), start=1):
            X_train, y_train = X[train_idx], y[train_idx]
            X_val, y_val = X[val_idx], y[val_idx]

            fold_model = self._instantiate_model(self.model_params)
            fold_model.fit(X_train, y_train)

            preds = fold_model.predict(X_val)
            oof_predictions[val_idx] = preds

            rmse = np.sqrt(mean_squared_error(y_val, preds))
            mae = mean_absolute_error(y_val, preds)
            r2 = r2_score(y_val, preds)

            fold_metrics.append({"fold": fold, "rmse": rmse, "mae": mae, "r2": r2})
            logger.info("Fold %d - RMSE: %.4f | MAE: %.4f | R^2: %.4f", fold, rmse, mae, r2)

        overall_rmse = np.sqrt(mean_squared_error(y, oof_predictions))
        overall_mae = mean_absolute_error(y, oof_predictions)
        overall_r2 = r2_score(y, oof_predictions)

        results = {
            "overall_rmse": float(overall_rmse),
            "overall_mae": float(overall_mae),
            "overall_r2": float(overall_r2),
            "fold_metrics": fold_metrics,
            "oof_predictions": oof_predictions,
        }
        logger.info(
            "Overall Spatial CV Performance -> RMSE: %.4f | MAE: %.4f | R^2: %.4f",
            overall_rmse, overall_mae, overall_r2
        )
        return results

    def tune_hyperparameters(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        n_splits: int = 5,
        n_iter: int = 15
    ) -> Any:
        """
        Performs spatial hyperparameter optimization via RandomizedSearchCV with GroupKFold.

        Args:
            X: Feature matrix.
            y: Target array.
            groups: Enumeration Area IDs.
            n_splits: Spatial CV folds for tuning.
            n_iter: Number of parameter sampling iterations.

        Returns:
            Best fitted estimator.
        """
        logger.info("Running Spatial Hyperparameter Optimization (%d iterations)...", n_iter)
        gkf = GroupKFold(n_splits=n_splits)

        if self.model_type == "lightgbm":
            param_dist = {
                "n_estimators": [100, 200, 300],
                "learning_rate": [0.01, 0.03, 0.05, 0.1],
                "max_depth": [3, 5, 7, -1],
                "num_leaves": [15, 31, 63],
                "subsample": [0.6, 0.8, 1.0],
                "colsample_bytree": [0.6, 0.8, 1.0],
                "reg_alpha": [0.0, 0.1, 1.0],
                "reg_lambda": [0.0, 0.1, 1.0],
            }
        else:
            param_dist = {
                "n_estimators": [100, 200, 300],
                "learning_rate": [0.01, 0.03, 0.05, 0.1],
                "max_depth": [3, 5, 7],
                "subsample": [0.6, 0.8, 1.0],
                "colsample_bytree": [0.6, 0.8, 1.0],
                "reg_alpha": [0.0, 0.1, 1.0],
                "reg_lambda": [0.0, 0.1, 1.0],
            }

        base_estimator = self._instantiate_model({})
        search = RandomizedSearchCV(
            estimator=base_estimator,
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=gkf.split(X, y, groups=groups),
            scoring="neg_root_mean_squared_error",
            random_state=self.random_state,
            n_jobs=-1
        )
        search.fit(X, y)
        logger.info("Optimal Parameters: %s (Best Score: %.4f)", search.best_params_, -search.best_score_)
        self.model = search.best_estimator_
        return self.model

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
            model: Trained Tree-based regressor (LightGBM/XGBoost).
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

        Identifies the primary features driving the predicted yield volatility higher
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
    Coordinates the end-to-end Machine Learning pipeline from microdata ingestion
    to spatial model validation and SHAP interpretability exports.
    """

    def __init__(
        self,
        data_dir: Union[str, Path] = "data/AASS 2024_2025",
        output_dir: Union[str, Path] = "artifacts/yield_volatility",
        model_type: str = "lightgbm",
        tune_hyperparameters: bool = False,
        random_state: int = 42
    ) -> None:
        """
        Initialize the PipelineOrchestrator.

        Args:
            data_dir: Directory containing raw AASS microdata.
            output_dir: Destination for metrics, logs, and SHAP plots.
            model_type: 'lightgbm' or 'xgboost'.
            tune_hyperparameters: If True, executes spatial RandomizedSearchCV.
            random_state: Seed for reproducibility.
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_type = model_type
        self.tune_hyperparameters = tune_hyperparameters
        self.random_state = random_state

        # Instantiate OOP components
        self.preprocessor = DataPreprocessor(self.data_dir)
        self.engineer = FeatureEngineer()
        self.predictor = VolatilityPredictor(model_type=self.model_type, random_state=self.random_state)
        self.interpreter: Optional[ModelInterpreter] = None

    def run(self) -> Dict[str, Any]:
        """
        Executes the full pipeline sequentially.

        Returns:
            Dictionary containing evaluation metrics and output artifact paths.
        """
        logger.info("=" * 70)
        logger.info("STARTING SMALLHOLDER YIELD VOLATILITY ML PIPELINE")
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
            "Prepared Modeling Matrix: %d smallholders, %d features, %d spatial EAs.",
            X_mat.shape[0], X_mat.shape[1], len(np.unique(groups))
        )

        # Step 3: Spatial Cross-Validation & Modeling
        if self.tune_hyperparameters:
            self.predictor.tune_hyperparameters(X_mat, y_aligned, groups=groups)

        cv_results = self.predictor.spatial_cross_validate(X_mat, y_aligned, groups=groups, n_splits=5)
        self.predictor.fit(X_mat, y_aligned)

        # Step 4: Model Interpretability (SHAP)
        self.interpreter = ModelInterpreter(
            model=self.predictor.model,
            feature_names=feature_names,
            output_dir=self.output_dir / "interpretability"
        )
        importance_df = self.interpreter.explain_global(X_mat, max_display=20)

        # Generate sample local explanation for the first household
        sample_local = self.interpreter.explain_local(X_mat, household_idx=0, top_k=5)

        # Step 5: Export Execution Metadata & Metrics
        metrics_payload = {
            "model_type": self.model_type,
            "holdings_count": int(X_mat.shape[0]),
            "features_count": int(X_mat.shape[1]),
            "enumeration_areas_count": int(len(np.unique(groups))),
            "spatial_cv_rmse": cv_results["overall_rmse"],
            "spatial_cv_mae": cv_results["overall_mae"],
            "spatial_cv_r2": cv_results["overall_r2"],
            "top_5_predictive_features": importance_df.head(5).to_dict(orient="records"),
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
        "--model-type",
        type=str,
        choices=["lightgbm", "xgboost"],
        default="lightgbm",
        help="Regressor architecture to instantiate."
    )
    parser.add_argument(
        "--tune",
        action="store_true",
        help="Execute spatial hyperparameter optimization before cross-validation."
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
        model_type=args.model_type,
        tune_hyperparameters=args.tune,
        random_state=args.random_state
    )
    orchestrator.run()
