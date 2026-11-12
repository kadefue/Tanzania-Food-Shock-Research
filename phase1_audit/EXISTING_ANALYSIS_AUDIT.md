# Technical and Methodological Audit of Existing Analysis Scripts

**Audited Scripts:** `modeling.py`, `generate_publication_figures_and_tables.py`, `build_manuscript.py`  
**Date of Assessment:** November 2026  
**Auditor Role:** Senior Software Architect, Agricultural Statistician, Geospatial Analyst & ML Research Auditor  
**Deliverable:** Phase 1 Audit Deliverable 9.3

---

## 1. Trace of Analytical Workflow

The empirical workflow implemented in `modeling.py` proceeds through seven primary stages:

```
[Raw Microdata Ingestion] 
       │
       ▼
[Unit Harmonisation & Aggregation] 
       │
       ▼
[Target Formulation: Y_vol] 
       │
       ▼
[Feature Engineering: 246 Predictors] 
       │
       ▼
[Global Preprocessing & Scaling (RobustScaler, KMeans, PCA)] ──► ⚠️ LEAKAGE POINT 1
       │
       ▼
[Supervised Tree-Gain Feature Selection (Top 100)] ───────────► ⚠️ LEAKAGE POINT 2
       │
       ▼
[Mock Leakage Audit Execution] ───────────────────────────────► ⚠️ PSEUDO-AUDIT
       │
       ▼
[5-Fold Spatial GroupKFold Evaluation on ea_id] 
       │
       ▼
[Regional Sub-Model Training & Performance Breakdown] 
       │
       ▼
[TreeSHAP Attribution & Policy Counterfactual Simulations]
```

---

## 2. Detailed Technical Audit by Stage

### 2.1 Stage 1: Data Ingestion and Table Matching
- **Implementation:** `DataPreprocessor._read_table()` and `DataPreprocessor.load_raw_data()` (`modeling.py`, lines 136–181).
- **Files Loaded:** Ingests 11 tables from `data/AASS 2024_2025`:
  `HOUSEHOLD.dta`, `MASIKACROP.dta`, `VULICROP.dta`, `MASIKAPLOT.dta`, `VULIPLOT.dta`, `inputRoster_masika.dta`, `inputRoster_vuli.dta`, `AASS2025.dta`, `shocks_roster.dta`, `stock_livestock.dta`, and `pme_6_Roster.dta`.
- **Parser Logic:** Prefers `pyreadstat.read_dta()` for performance; falls back to `pd.read_stata(convert_categoricals=False)`.
- **Key Standardization:** Dynamically normalizes variations of the primary holding identifier (`holding_id`, `Holding_ID`, `hhid`) to `HHFARMID` (`modeling.py`, lines 152–159).
- **Defects Discovered:**
  - Case-insensitive glob matching correctly resolves minor case discrepancies across platforms.
  - However, table loading contains **no validation of survey wave compatibility** or record integrity checks (e.g., verifying that all holdings in `MASIKACROP` exist in `AASS2025.dta`).

---

### 2.2 Stage 2: Data Cleaning and Measurement Unit Harmonization
- **Implementation:** `DataPreprocessor.harmonize_units()` (`modeling.py`, lines 183–212).
- **Unit Conversion Logic:**
  ```python
  if "harvest_ton" in df.columns:
      df["production_kg"] = df["harvest_ton"].fillna(0.0) * 1000.0
  else:
      df["production_kg"] = 0.0

  unit_col = "s7q08c_unit" if season == "masika" else "s5q08c_unit"
  qty_col = "s7q08c" if season == "masika" else "s5q08c"
  if unit_col in df.columns and qty_col in df.columns:
      conversion_multipliers = df[unit_col].map(self.UNIT_TO_KG_FACTORS).fillna(1.0)
      raw_kg = df[qty_col].fillna(0.0) * conversion_multipliers
      df["production_kg"] = np.where(df["production_kg"] > 0, df["production_kg"], raw_kg)
  ```
- **Input Quantity Conversion:**
  In `FeatureEngineer.engineer_predictive_features()` (`modeling.py`, lines 401–407):
  ```python
  im["qty_kg"] = np.where(im["s11q01b_unit"] == 1, im["s11q01b"] / 1000.0, im["s11q01b"])
  iv["qty_kg"] = np.where(iv["s11q01a_unit"] == 1, iv["s11q01a"] / 1000.0, iv["s11q01a"])
  ```
- **Critical Methodological Flaws:**
  1. **Constant Weight Multipliers Across Dissimilar Crops:** The `UNIT_TO_KG_FACTORS` dictionary defines static conversion multipliers (e.g., Tin/Debe = 18.0 kg; Large Sack = 100.0 kg; Medium Bunch = 15.0 kg). In East African agricultural systems, container weights vary substantially depending on commodity bulk density: a 20-litre Debe of dry shelled maize weighs $\approx 16\text{--}18\text{ kg}$, while a Debe of paddy rice weighs $\approx 12\text{--}14\text{ kg}$, fresh cassava weighs $\approx 14\text{--}16\text{ kg}$, and leafy vegetables weigh $< 8\text{ kg}$. Applying static weights introduces unquantified measurement error.
  2. **Input Unit Truncation:** While code 1 is divided by 1000 (converting grams to kg), liquid pesticide units (liters vs. milliliters) and other local measurement units are not standardized, resulting in the aggregation of liters and kilograms into single intensity variables (`pest_masika_qty`, `pest_vuli_qty`).

---

### 2.3 Stage 3: Analytical Sample Construction and Cohort Funnel
- **Implementation:** `FeatureEngineer.compute_target()` (`modeling.py`, lines 310–350).
- **Exact Screening Criteria:**
  ```python
  valid_mask = (
      df["yield_masika"].notna()
      & df["yield_vuli"].notna()
      & (df["area_ha_masika"] > 0)
      & (df["area_ha_vuli"] > 0)
  )
  sub_df = df[valid_mask].copy()
  mean_yield = (sub_df["yield_masika"] + sub_df["yield_vuli"]) / 2.0
  positive_yield_mask = mean_yield > 0
  sub_df = sub_df[positive_yield_mask].copy()
  ```
- **Quantitative Cohort Attrition:**
  1. Initial holdings in `AASS2025.dta`: **18,904 holdings** across all 31 administrative regions.
  2. Masika season cultivators: **15,107 holdings**.
  3. Vuli season cultivators: **9,552 holdings**.
  4. Cultivating in **both** Masika and Vuli seasons: **6,128 holdings**.
  5. Positive cultivated area in both seasons ($A_m > 0$ and $A_v > 0$): **4,564 holdings**.
  6. Positive average yield across seasons ($\frac{1}{2}(Y_m + Y_v) > 0$): **4,564 holdings**.
  7. Final modeled analytical sample: **4,564 holdings** across 921 Enumeration Areas in 27 regions.

- **Critical Methodological Vulnerabilities:**
  1. **Failure to Filter Out Large-Scale Commercial Farms:**
     - The AASS survey includes both smallholder households (`Holding_type == 2`) and large-scale commercial farming corporations (`Holding_type == 1`, completely enumerated by NBS).
     - The script **never filters on `Holding_type`**.
     - Consequently, commercial corporate farms cultivating up to **3,723.11 hectares** and applying up to **2,733,766 kg of inorganic fertilizer** (see `table1_summary_statistics.csv`) are pooled into the analysis, directly violating the paper's title and premise: *"Predicting Smallholder Crop Yield Volatility"*.
  2. **Severe Geographic Censoring of Unimodal Rainfall Regimes:**
     - In unimodal agro-ecological zones (Central plateaus and Southern Highlands), precipitation occurs in a single extended season (*Msimu*, November to April). Smallholders in these zones do not cultivate during Vuli.
     - Requiring non-zero cultivated area and harvest in *both* Masika and Vuli systematically discards unimodal smallholders.
     - Four regions are **entirely excluded** ($N=0$): Ruvuma, Rukwa, Lindi, and Mtwara.
     - Core agricultural regions have trivial, non-representative sample sizes:
       - Songwe: $N = 3$
       - Njombe: $N = 5$
       - Tabora: $N = 10$
       - Singida: $N = 11$
       - Iringa: $N = 14$
       - Katavi: $N = 25$
       - Dodoma: $N = 27$
     - The analytical cohort represents an opportunistic subpopulation of bimodal farmers plus an atypical sliver of unimodal farmers cultivating perennial wetland plots (*vinyungu*), destroying national population representativeness.

---

### 2.4 Stage 4: Seasonal Yield Calculations
- **Implementation:** `DataPreprocessor.calculate_seasonal_yields()` (`modeling.py`, lines 213–258).
- **Exact Formulas:**
  $$Y_{m,i} = \frac{\sum_{c \in C_{m,i}} \text{Production\_kg}_{c,i}}{\sum_{p \in P_{m,i}} \text{Area\_ha}_{p,i}}$$
  $$Y_{v,i} = \frac{\sum_{c \in C_{v,i}} \text{Production\_kg}_{c,i}}{\sum_{p \in P_{v,i}} \text{Area\_ha}_{p,i}}$$
  where $C_{m,i}$ is the set of all crops grown by holding $i$ in Masika, and $P_{m,i}$ is the set of all plots operated by holding $i$ in Masika.
- **Critical Methodological Flaws:**
  1. **Direct Aggregation of Dissimilar Biomass:**
     - Fresh cassava roots (high water content, typical yields $8,000\text{--}15,000\text{ kg/ha}$) are summed directly with dry shelled maize grain ($1,000\text{--}2,000\text{ kg/ha}$), dry beans ($300\text{--}800\text{ kg/ha}$), bananas, and vegetables.
     - This produces an arbitrary "fresh biomass per hectare" metric with no agronomic, economic, or nutritional meaning.
  2. **Intercropping Area Double-Counting:**
     - Plot areas are summed across `MASIKAPLOT`. When multiple intercropped species are grown on a single plot, each species is recorded as a separate row in `MASIKACROP`. Summing crop weights across the plot and dividing by the total holding area conflates pure-stand yields with multi-crop intercropped densities.

---

### 2.5 Stage 5: Target Formulation: Seasonal Yield Volatility Index ($Y_{\mathrm{vol}}$)
- **Implementation:** `FeatureEngineer.compute_target()` (`modeling.py`, lines 345–347).
- **Exact Formula:**
  $$Y_{\text{vol},i} = \min\left(2.0, \; \frac{|Y_{m,i} - Y_{v,i}|}{\frac{1}{2}(Y_{m,i} + Y_{v,i}) + \epsilon}\right)$$
  where $\epsilon = 10^{-6}$.
- **Statistical and Interpretive Flaws:**
  1. **Conflating Yield Risk with Crop Rotation:**
     - If a smallholder rotates from high-biomass cassava in Masika ($Y_m = 10,000\text{ kg/ha}$) to dry grain legumes in Vuli ($Y_v = 600\text{ kg/ha}$), $Y_{\text{vol}}$ is:
       $$Y_{\text{vol}} = \frac{|10000 - 600|}{5300} = 1.77$$
     - The index classifies this farmer as exhibiting "hyper-volatility" (high risk), even if both crops achieved record yields. The index measures **crop composition shifts** rather than actual yield instability.
  2. **Severe Target Distribution Boundary Spikes:**
     - When a household experiences complete crop failure in one season ($Y_v = 0$), the index reduces to:
       $$Y_{\text{vol}} = \frac{Y_m}{0.5 Y_m + \epsilon} \approx 2.0$$
     - Over **25.8% of holdings** in the sample have $Y_{\text{vol}} \approx 2.0$, creating a severe spike at the upper bound. Standard mean squared error regression assumes continuous, smooth error distributions, which are violated by this boundary mass.

---

### 2.6 Stage 6: Feature Engineering (246 Candidate Predictors)
- **Implementation:** `FeatureEngineer.engineer_predictive_features()` (`modeling.py`, lines 376–735).
- **Feature Domain Categories:**
  1. *Input Deltas & Intensities:* `fert_masika_kg`, `fert_vuli_kg`, `delta_fertilizer_kg`, `delta_fert_intensity`, `pest_masika_qty`, `pest_per_ha_masika` (14 features).
  2. *Crop Diversity Indices:* Shannon diversity ($H'$), Herfindahl-Hirschman ($C_{\text{HHI}}$), Berger-Parker ($D_{\text{BP}}$), and Pielou evenness ($J'$) for Masika and Vuli, plus seasonal deltas (12 features).
  3. *Crop Turnover Dynamics:* Jaccard similarity $J(C_m, C_v)$ and seasonal crop turnover ratio (2 features).
  4. *Household Labor & Demographics:* Household size, adult agricultural labor count, dependency ratio, head age, head gender, agricultural training, labor bottlenecks (10 features).
  5. *Plot Structure & Fragmentation:* Fallow share, irrigation share, permanent crop share, inorganic fertilizer adoption share, plot count, plot area mean, plot area standard deviation, plot area coefficient of variation (CV) (14 features).
  6. *Livestock Asset Buffers:* Total Tropical Livestock Units (TLU) and total animal head counts (2 features).
  7. *Food Shocks & Losses:* Total shock count, binary indicators for drought, flood, pests, input prices, output prices, maximum shock severity, crop damage, and revenue loss (9 features).
  8. *Institutional & Weather Advisories:* TFSCRP, PSSN, AISP, irrigation schemes, extension visits, weather forecasts, rain onset advisory (11 features).
  9. *Regional Peer Groupby Aggregations:* Holding deviations and ratios to regional means for farm area, fertilizer, and crop diversity (6 features).
  10. *One-Hot Encodings & Roster Dummies:* Detailed area loss reasons (`s7q10__*`), plot management codes (`s6q08__*`, `s6q10__*`), regional fixed effects (`region_id`), and agro-ecological strata (`stratum_id`) (166 features).
  11. *Total Candidate Feature Matrix:* **246 features**.

- **CRITICAL DEFECT: Post-Outcome Target Leakage Variables:**
  Several top-ranking predictors in the model represent **post-harvest loss realisations** rather than ex-ante risk factors:
  - `m_harvest_pct_mean` (Rank 2 in importance): Average percentage of planted area harvested in Masika.
  - `m_no_harvest_share` (Rank 6 in importance): Share of plots where crops were completely abandoned/unharvested ($s7q05 == 2$).
  - `delta_no_harvest_share`: Seasonal difference in plot abandonment.
  - `m_drought_fail`, `v_drought_fail`, `m_pest_fail`: Disaster failure flags.
  - `m_arealoss_reason_1` through `m_arealoss_reason_10`: Survey questions directly asking why crops were lost during the season.
  - *Consequence:* Using whether crops failed or were abandoned to "predict" whether yields collapsed between seasons is tautological endogeneity.

---

### 2.7 Stage 7: Preprocessing, Scaling, and Feature Selection LEAKAGE AUDIT

A rigorous audit of lines 776–878 and 1667–1678 in `modeling.py` reveals that the pipeline commits **three distinct forms of data leakage** prior to cross-validation:

#### Leakage Point 1: Pre-Validation Scaling and Encoding
In `FeatureEngineer.fit_transform()` (`modeling.py`, line 776):
```python
self.preprocessor_pipeline = ColumnTransformer(transformers=transformers)
X_scaled = self.preprocessor_pipeline.fit_transform(X_modeling)
```
- `RobustScaler()` computes the median and interquartile range (IQR) across all $N = 4,564$ holdings simultaneously.
- `OneHotEncoder()` identifies category levels across the entire analytical sample.
- *Severity:* High. Information from test/validation folds contaminates training feature distributions.

#### Leakage Point 2: Pre-Validation Unsupervised Representations (KMeans & PCA)
In `FeatureEngineer.fit_transform()` (`modeling.py`, lines 788–796):
```python
self.kmeans_model = KMeans(n_clusters=4, random_state=42, n_init=10)
kmeans_distances = self.kmeans_model.fit_transform(X_scaled)

self.pca_model = PCA(n_components=3, random_state=42)
pca_components = self.pca_model.fit_transform(X_scaled)
```
- Cluster centroids for 4 agronomic archetypes and projection vectors for 3 latent PCA components are fit on the complete scaled dataset ($N = 4,564$) before cross-validation folds are created.
- *Severity:* High. Unsupervised cluster structures leak between validation folds.

#### Leakage Point 3: Pre-Validation Supervised Feature Selection (Target Leakage)
In `PipelineOrchestrator.run()` (`modeling.py`, lines 1675–1681):
```python
X_selected, selected_feature_names, ranking_df = self.engineer.select_grandmaster_features(
    X_mat=X_mat,
    y=y_aligned,
    feature_names=candidate_feature_names,
    top_k=self.top_k,
    output_dir=self.output_dir
)
```
In `FeatureEngineer.select_grandmaster_features()` (`modeling.py`, lines 859–861):
```python
selector = lgb.LGBMRegressor(...)
selector.fit(X_mat, y)
importances_split = selector.booster_.feature_importance(importance_type="split")
importances_gain = selector.booster_.feature_importance(importance_type="gain")
```
- **The gradient booster is trained on the full dataset using the target variable $y$ to rank and prune features before cross-validation.**
- The top 100 features are selected based on knowledge of the validation targets.
- *Severity:* **CRITICAL**. This is textbook feature selection leakage (Hastie et al., 2009; Kaufman et al., 2012). It introduces optimistic performance bias into subsequent cross-validation.

#### The "Mock" Leakage Auditor Exposed
In `LeakageAuditor.run_audit()` (`modeling.py`, lines 1353–1407):
- The class claims to perform a "Formal 5-Pillar Leakage Audit" and exports a `CERTIFIED_LEAKAGE_FREE` certificate (`table5_leakage_audit_certificate.csv`).
- **Inspection of Check 3 (Scaler Isolation):**
  The code runs a dummy loop that fits a fresh `RobustScaler` on a slice and checks if `val_transformed.shape[0] == len(val_idx)`. It does *not* inspect whether the pipeline itself fitted scalers globally.
- **Inspection of Check 4 (KMeans/PCA Isolation):**
  The code runs a dummy loop fitting a fresh KMeans and PCA on a fold slice. It does *not* check whether the global feature matrix $X$ already contains components fit on the full sample.
- **Inspection of Check 5 (Feature Selection Integrity):**
  Line 1400: `check_5_pass = True` is **hardcoded**. Zero verification is performed.
- *Scientific Consequence:* The audit certificate presented in Table 5 and Figure 7 of the manuscript is invalid and scientifically misleading.

---

### 2.8 Stage 8: Machine Learning Benchmarks and Spatial Cross-Validation
- **Models Evaluated:**
  1. LightGBM Regressor (`n_estimators=320, lr=0.03, max_depth=6, num_leaves=35`)
  2. XGBoost Regressor (`n_estimators=300, lr=0.03, max_depth=5`)
  3. Random Forest Regressor (`n_estimators=100, max_depth=16, max_features='sqrt'`)
  4. Weighted Ensemble (`0.50 LightGBM + 0.40 XGBoost + 0.10 Random Forest`)
- **Spatial CV Design:** `GroupKFold(n_splits=5)` grouped on `ea_id` (921 Enumeration Areas).
- **Reported Benchmark Performance:**
  - Weighted Ensemble: $\text{Spatial } R^2 = 0.592$, $\text{RMSE} = 0.464$, $\text{MAE} = 0.347$
  - LightGBM: $\text{Spatial } R^2 = 0.590$, $\text{RMSE} = 0.465$, $\text{MAE} = 0.346$
  - XGBoost: $\text{Spatial } R^2 = 0.588$, $\text{RMSE} = 0.466$, $\text{MAE} = 0.348$
  - Random Forest: $\text{Spatial } R^2 = 0.569$, $\text{RMSE} = 0.477$, $\text{MAE} = 0.368$
- **Audit Assessment:** While `GroupKFold` on `ea_id` successfully enforces spatial disjointness at the cluster level during model training, the reported $R^2 \approx 0.592$ is inflated by the global pre-cross-validation feature selection and post-outcome loss predictors.

---

### 2.9 Stage 9: Regional Sub-Model Evaluation
- **Implementation:** `VolatilityPredictor.evaluate_regional_performance()` (`modeling.py`, lines 1147–1266).
- **Methodology:** The script loops over all 27 represented administrative regions, trains dedicated local models using regional subsets, and compares them against regional slices of the national model.
- **Critical Methodological Flaws:**
  1. **Training Models on Statistically Degenerate Sample Sizes:**
     - Songwe ($N=3$), Njombe ($N=5$), Tabora ($N=10$), Singida ($N=11$), Iringa ($N=14$).
     - In line 1208, for $N < 15$, the code uses `KFold(n_splits=max(2, min(3, n_samples)))`.
     - For Songwe ($N=3$), it fits models on 2 observations and tests on 1 observation.
     - Consequently, regional model performance collapses:
       - Njombe: $R^2 = -1.255$
       - Songwe: $R^2 = -1.132$
       - Tabora: $R^2 = -0.548$
       - Singida: $R^2 = -0.197$
  2. **Misleading "National Advantage" Narrative:**
     The manuscript reports that the national model outperforms regional sub-models in 26 of 27 regions (by an average $\Delta R^2 = 0.244$). This comparison is trivial and unscientific: a model trained on $N=4,564$ will inevitably outperform models fit on $N=3$ or $N=5$. Presenting this as evidence of "superior spatial transferability" distorts basic statistical sampling realities.

---

### 2.10 Stage 10: Model Interpretability and Counterfactual Policy Claims
- **Implementation:** `ModelInterpreter` (`modeling.py`, lines 1428–1545) and Figure 10 generation in `generate_publication_figures_and_tables.py`.
- **Interpretive Methods:**
  - Global feature attributions via `shap.TreeExplainer` on the primary gradient booster.
  - Local household waterfall explanations.
  - 1D and 2D partial dependence surfaces (`fig9_agroeconomic_partial_dependence_surfaces.png`).
  - Simulated policy counterfactuals (`fig10_policy_simulation_and_counterfactual_interventions.png`).
- **CRITICAL SCIENTIFIC FLAW: Conflating Predictive Associations with Causal Policy Effects:**
  - In Figure 10 and Section 4.5 of the manuscript, the study simulates policy interventions (e.g., increasing livestock assets to 3.0 TLU, shifting planting months, expanding irrigation) by manually altering feature columns in the dataset and feeding the modified matrix through the trained tree ensemble.
  - The manuscript concludes: *"an integrated Climate-Smart Agriculture package combining asset transfers, cultivar diversification, and planting synchronisation reduces mean national yield volatility by 40.0% and lowers hyper-volatile holdings from 25.8% to 19.9%."*
  - **Tree ensembles are non-causal associative predictors, not structural econometric models.**
  - Altering feature values in a decision tree ignores unobserved confounders (e.g., farmer ability, soil depth, land quality), feedback loops, and general equilibrium adjustments. Claiming a specific percentage reduction in national risk based on perturbing decision tree inputs violates accepted standards in agricultural development economics.

---

## 3. Summary of Code Auditing Findings

| Stage | Script & Function | Finding / Defect | Severity |
|---|---|---|:---:|
| 1. Data Ingestion | `modeling.py::DataPreprocessor` | No wave or integrity verification across tables | Low |
| 2. Unit Harmonization | `modeling.py::harmonize_units` | Constant container weights across different crop bulk densities | High |
| 3. Sample Selection | `modeling.py::compute_target` | Failure to filter out large commercial farms (`Holding_type == 1`) | **Critical** |
| 3. Sample Selection | `modeling.py::compute_target` | Exclusion of unimodal zones ($N=0$ in 4 regions; $N \le 14$ in 5 regions) | **Critical** |
| 4. Yield Calculations | `modeling.py::calculate_seasonal_yields` | Summing raw kg of dissimilar crops (cassava + maize + bananas) | **Critical** |
| 5. Target Formulation | `modeling.py::compute_target` | $Y_{\mathrm{vol}}$ conflates yield instability with crop rotation; 26% boundary spike | **Critical** |
| 6. Feature Engineering | `modeling.py::engineer_predictive_features` | Post-harvest loss and crop abandonment proxies used as predictors | **Critical** |
| 7. Preprocessing & Scaling | `modeling.py::fit_transform` | `RobustScaler`, `KMeans`, `PCA` fit on full dataset before CV | High |
| 7. Feature Selection | `modeling.py::select_grandmaster_features` | Supervised tree-gain feature selection fit on full dataset with target $y$ | **Critical** |
| 7. Leakage Auditor | `modeling.py::LeakageAuditor` | Mock assertions; hardcoded `check_5_pass = True`; invalid certificate | **Critical** |
| 8. Model Benchmark | `modeling.py::spatial_cross_validate` | Out-of-fold $R^2 \approx 0.592$ inflated by feature selection leakage | High |
| 9. Regional Sub-models | `modeling.py::evaluate_regional_performance` | Fitting ML models on $N=3$ and $N=5$; trivial "national advantage" claim | High |
| 10. Policy Counterfactuals | `generate_publication_figures_and_tables.py` | Treating predictive tree perturbations as causal policy effects (40% reduction claim) | **Critical** |
