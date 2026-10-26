# Tanzania Food Shock Research

**Author:** Kadeghe Goodluck Fue (<kadefue@sua.ac.tz>)  
**Affiliation:** Sokoine University of Agriculture (SUA)  

Empirical data repository and microdata processing pipeline for analyzing agricultural production, household shocks, and food security dynamics in Tanzania.

This research integrates multi-wave microdata from the **Tanzania National Bureau of Statistics (NBS)**, the **Office of the Chief Government Statistician (OCGS) Zanzibar**, and macroeconomic/crop statistics from **FAOSTAT**.

---

## 📌 Research Overview

Agricultural households in Tanzania are increasingly vulnerable to climatic, economic, and biological shocks (e.g., droughts, floods, input price spikes, crop pests, and livestock diseases). This repository organizes survey microdata across multiple agricultural years to investigate:
- Household exposure to covariate and idiosyncratic food shocks (`shocks_roster`).
- Seasonal crop production, yield gaps, and post-harvest crop utilization across both *Masika* (long rainy season) and *Vuli* (short rainy season).
- Input adoption (certified seeds, fertilizers, irrigation, external labor) and credit/financing access.
- Cross-validation between micro-level household survey responses and macro-level FAOSTAT agricultural production trends.

---

## 📂 Repository Structure

```text
Food Shock Research/
├── 01_file_headers/              # Automated schema & column inventories
│   ├── file_headers.csv          # Structured table of file metadata & column lists
│   └── file_headers.txt          # Human-readable column listings for all datasets
│
├── data/                         # Primary empirical datasets
│   ├── AASS 2022_2023/           # Stata (.dta) files for AASS Wave 2022/23 (Catalog 52)
│   ├── AASS 2023_2024/           # Stata (.dta) and CSV exports for AASS Wave 2023/24 (Catalog 60)
│   │   └── CSV AASS2024 Datasets/
│   ├── AASS 2024_2025/           # Stata (.dta) files for AASS Wave 2024/25 (Catalog 69)
│   │   └── shocks_roster.dta     # Core shock exposure & resilience module
│   └── FAOSTAT/                  # National production, yield, and priority crop data
│       ├── tanzania_crop_production_yield_area.csv
│       ├── tanzania_crop_year_wide.csv
│       ├── tanzania_faostat_all.csv
│       └── tanzania_priority_crops.csv
│
├── metadata/                     # Official DDI documentation & survey schemas
│   ├── TZA-NBS.OCGS-AASS-2023-v01.json / .xml
│   ├── TZA_AASS_2023-2024_v01.json / .xml
│   ├── TZA-NBS.OCGS-AASS-2025-v01.json
│   └── ddi-documentation-english-{52,60,69}.pdf
│
├── nbs_aass_metadata/            # Data dictionaries extracted from the NBS microdata portal
│   ├── data_dictionary_catalog_52.csv
│   ├── data_dictionary_catalog_52.json
│   └── data_dictionary_catalog_52.xlsx
│
├── crawl_nbs_dictionary.py       # Web crawler for NBS microdata catalogs & variable metadata
├── detect_files.py               # Memory-efficient header & variable inventory utility
├── requirements.txt              # Python package dependencies
└── README.md                     # Project documentation
```

---

## 📊 Data Sources & Catalogs

### 1. Annual Agricultural Sample Surveys (AASS) — NBS & OCGS
The survey microdata includes household demographics, plot areas, crop planting/harvesting, inputs, livestock, and shocks:

| Survey Round | Catalog ID | Coverage | Key Modules |
| :--- | :---: | :--- | :--- |
| **AASS 2022/2023** | `Catalog 52` | Mainland Tanzania & Zanzibar | `household`, `field`, `masikacrop`, `vulicrop`, `crop_use`, `inputs`, `seeds`, `external_labor_activities`, `aquaculture` |
| **AASS 2023/2024** | `Catalog 60` | Mainland Tanzania & Zanzibar | `HOUSEHOLD`, `FIELD`, `MASIKACROP`, `VULICROP`, `CROP_USE`, `InputRoster_masika/vuli`, `buildings_roster` |
| **AASS 2024/2025** | `Catalog 69` | Mainland Tanzania & Zanzibar | `HOUSEHOLD`, `MASIKACROP`, `VULICROP`, `shocks_roster`, `livestock_type`, `s14_milk`, `s17_aquaculture` |

### 2. FAOSTAT Data
- **Time-series coverage**: Historical production (tonnes), harvested area (ha), and yield (hg/ha) for Tanzania.
- **Priority crops**: Maize, cassava, rice, sorghum, beans, sweet potatoes, and export commodities.

---

## 🛠️ Installation & Environment Setup

### 1. Prerequisites
- Python 3.10+
- Virtual environment tool (`venv`)

### 2. Setup Virtual Environment
```bash
# Clone or navigate to the repository directory
cd "Food Shock Research"

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

*Note: For the web crawler tool (`crawl_nbs_dictionary.py`), ensure `requests`, `beautifulsoup4`, `tqdm`, and `openpyxl` are installed:*
```bash
pip install beautifulsoup4 requests tqdm openpyxl
```

---

## 🚀 Execution & Usage

### 1. Generate Schema & Header Inventory
Extract variable names and file summaries without reading large data matrices into memory:
```bash
python detect_files.py
```
- Scans `data/` recursively for `.dta` (using `pyreadstat`) and `.csv` files.
- Generates `01_file_headers/file_headers.csv` and `01_file_headers/file_headers.txt`.

### 2. Scrape NBS Microdata Data Dictionary
Fetch full variable descriptions, questions, value labels, and category codes from the official NBS portal:
```bash
python crawl_nbs_dictionary.py
```
- Fetches metadata from [NBS Microdata Portal](https://microdata.nbs.go.tz).
- Exports structured dictionary tables to `nbs_aass_metadata/` in JSON, CSV, and Excel formats.

---

## 🔬 Key Data Linkages

To merge microdata files within a given survey round:
- **Household-level identifiers**: `holding_id` (or `hhid`) connects `household`, `field`, `shocks_roster`, and `crop_use`.
- **Plot/Field identifiers**: `holding_id` + `FIELD__id` + `MASIKAPLOT__id` / `VULIPLOT__id`.
- **Crop identifiers**: `crop_id` connects seasonal planting/harvesting modules to `crop_use` and `seeds`.
- **Geographic strata**: `region`, `stratum_id`, `ea_id`, and sampling weights (`Weight` / `weight`).

---

## 🤖 Smallholder Yield Volatility Machine Learning Pipeline

Located in [`modeling.py`](file:///Users/kadefue/Research/Food%20Shock%20Research/modeling.py), this pipeline predicts smallholder yield volatility ($Y_{vol}$) across agricultural seasons (Masika vs. Vuli) using 11 multi-relational NBS survey tables. It is structured into two core modeling tiers: **Overall National Benchmark** and **By-Region Spatial Evaluation**.

### 1. Spatial Cross-Validation Benchmark (5-Fold GroupKFold on 921 Enumeration Areas)

Evaluated on the **Top 100 Grandmaster Features** selected from 246 candidate variables:

| Model Architecture | Spatial RMSE ↓ | Spatial MAE ↓ | Spatial $R^2$ ↑ | Train Time |
|---|:---:|:---:|:---:|:---:|
| **Weighted Ensemble** (`0.50 LGB + 0.40 XGB + 0.10 RF`) | **0.4642** | **0.3472** | **0.5920** | 9.19s |
| **LightGBM Regressor** | **0.4655** | **0.3459** | **0.5898** | 6.03s |
| **XGBoost Regressor** | **0.4664** | **0.3484** | **0.5880** | 2.57s |
| **Random Forest Regressor** | **0.4768** | **0.3682** | **0.5694** | 0.51s |

- **Execution Command:**  
  `python modeling.py --data-dir "data/AASS 2024_2025" --output-dir "artifacts/yield_volatility" --compare --top-k 100`

---

### 2. Kaggle Grandmaster Feature Selection & Importance

The pipeline constructs 246 candidate agronomic, climatic, economic, and spatial peer features across 4,564 smallholder holdings. To eliminate noise and multi-collinearity, the `FeatureEngineer.select_grandmaster_features()` module evaluates gradient boosting split frequency and gain importance, pruning 146 zero-importance and redundant variables:

| Rank | Feature Name | Split Importance | Gain Importance | Agronomic Domain Rationale |
|:---:|---|:---:|:---:|---|
| **1** | `plant_month_delta` | 309 | 11,371.22 | Planting month difference between Masika and Vuli (seasonal timing misalignment) |
| **2** | `v_plant_month_mean` | 210 | 2,522.33 | Mean Vuli planting month (vulnerability to short-rain cessation) |
| **3** | `m_harvest_pct_mean` | 197 | 2,596.29 | Average percentage of crop area successfully harvested in Masika |
| **4** | `shannon_diff_from_region_mean` | 188 | 418.64 | Household crop diversity divergence from regional peer community average |
| **5** | `total_livestock_tlu` | 148 | 133.63 | Tropical Livestock Units (TLU) buffer capacity against agricultural crop failure |
| **6** | `m_no_harvest_share` | 135 | 1,822.73 | Proportion of plots suffering complete crop abandonment in Masika |
| **7** | `delta_evenness` | 131 | 342.23 | Seasonal shift in Pielou's crop evenness across cultivated plots |
| **8** | `area_diff_from_region_mean` | 118 | 163.80 | Farm area deviation relative to local agro-ecological peer holdings |
| **9** | `head_age` | 114 | 133.36 | Age of household head (farming experience and adaptive capacity proxy) |
| **10** | `land_per_adult_labor` | 113 | 146.16 | Farm capitalization ratio (hectares cultivated per available adult laborer) |

- **Complete Feature Ranking:** [`artifacts/yield_volatility/grandmaster_feature_ranking.csv`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/grandmaster_feature_ranking.csv)
- **Pruning Gain:** Selecting the Top-100 Grandmaster features lifts Random Forest $R^2$ from `0.5501` to **`0.5694`** and improves overall Ensemble Spatial $R^2$ to **`0.5920`** (Spatial RMSE down to **`0.4642`**).

---

### 3. Formal 5-Pillar Leakage Audit Suite

To ensure absolute scientific validity and zero risk of optimistic test bias, the pipeline incorporates a rigorous automated leakage auditor ([`LeakageAuditor`](file:///Users/kadefue/Research/Food%20Shock%20Research/modeling.py)):

| Pillar | Audit Focus | Verification Criterion | Status |
|:---:|---|---|:---:|
| **1** | **Spatial Group Disjointness** | Zero overlapping Enumeration Areas (`ea_id`) between train & test folds | ✅ **PASS** (0 leaks across 5 folds) |
| **2** | **Target Variable Isolation** | Target $Y_{vol}$ strictly excluded from feature space; max absolute correlation $\le 0.44$ | ✅ **PASS** (Zero target proxies) |
| **3** | **Scaler & Imputation Isolation** | `RobustScaler` and medians fit exclusively on training fold slices | ✅ **PASS** (Strict fold boundaries) |
| **4** | **Unsupervised Representation Isolation** | KMeans cluster centroids and PCA latent components fit strictly on train folds | ✅ **PASS** (Zero test contamination) |
| **5** | **Feature Selection Fold Integrity** | Feature importance ranking uses valid training fold statistics without future lookahead | ✅ **PASS** (Zero lookahead bias) |

- **Audit Certificate:** [`artifacts/yield_volatility/leakage_audit_report.json`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/leakage_audit_report.json) (`CERTIFIED_LEAKAGE_FREE`, 5/5 checks passed).

---

### 4. 🗺️ Regional Sub-Model Analysis

The pipeline trains and evaluates dedicated sub-models for each of Tanzania's 27 agricultural regions with smallholders, comparing local models against the unified national model:

- **Top Regional Models:**
  - **Kagera**: Regional $R^2 = \mathbf{0.6876}$ (RMSE: $0.4040$, $N=296$) | National Model Slice $R^2 = \mathbf{0.7508}$
  - **Mjini Magharibi**: Regional $R^2 = \mathbf{0.5942}$ (RMSE: $0.5305$, $N=80$)
  - **Mara**: Regional $R^2 = \mathbf{0.4620}$ (RMSE: $0.5340$, $N=476$) | National Model Slice $R^2 = \mathbf{0.6502}$
  - **Simiyu**: Regional $R^2 = \mathbf{0.4367}$ (RMSE: $0.4666$, $N=202$)
  - **Katavi**: Regional $R^2 = \mathbf{0.4268}$ (RMSE: $0.6030$, $N=25$)
  - **Kusini Unguja**: Regional $R^2 = \mathbf{0.4223}$ (RMSE: $0.5727$, $N=89$)
- **Overall Pooled Regional Models:** Combined Out-of-Fold $R^2 = \mathbf{0.3478}$ ($\text{RMSE} = 0.5869$), demonstrating that the Unified National Weighted Ensemble ($R^2 = \mathbf{0.5920}$) provides vital cross-regional variance reduction and superior generalization across small regional sample sizes.

---

### 5. Output Artifacts Inventory

- **Benchmark Metrics:** [`artifacts/yield_volatility/pipeline_metrics.json`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/pipeline_metrics.json)
- **Leakage Audit Report:** [`artifacts/yield_volatility/leakage_audit_report.json`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/leakage_audit_report.json)
- **Grandmaster Feature Rankings:** [`artifacts/yield_volatility/grandmaster_feature_ranking.csv`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/grandmaster_feature_ranking.csv)
- **Visual Model Comparison:** [`artifacts/yield_volatility/model_comparison.png`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/model_comparison.png)
- **Regional Performance Breakdown:** [`artifacts/yield_volatility/regional_performance.csv`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/regional_performance.csv)
- **Regional Performance Visualization:** [`artifacts/yield_volatility/regional_performance.png`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/regional_performance.png)
- **SHAP Global Summary:** [`artifacts/yield_volatility/interpretability/shap_summary_plot.png`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/interpretability/shap_summary_plot.png)
- **SHAP Importance Bar:** [`artifacts/yield_volatility/interpretability/shap_importance_bar.png`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/interpretability/shap_importance_bar.png)
- **Household Waterfall:** [`artifacts/yield_volatility/interpretability/household_0_waterfall.png`](file:///Users/kadefue/Research/Food%20Shock%20Research/artifacts/yield_volatility/interpretability/household_0_waterfall.png)

---

## 📄 Author & Attribution

- **Principal Investigator / Author**: Kadeghe Goodluck Fue ([kadefue@sua.ac.tz](mailto:kadefue@sua.ac.tz)), Sokoine University of Agriculture (SUA).
- **Survey Microdata**: Collected and provided by the [National Bureau of Statistics (NBS) Tanzania](https://www.nbs.go.tz/) and [OCGS Zanzibar](https://www.ocgs.go.tz/).
- **International Statistics**: [FAOSTAT, Food and Agriculture Organization of the United Nations](https://www.fao.org/faostat/).


