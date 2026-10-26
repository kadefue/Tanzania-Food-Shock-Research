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

## 📄 Author & Attribution

- **Principal Investigator / Author**: Kadeghe Goodluck Fue ([kadefue@sua.ac.tz](mailto:kadefue@sua.ac.tz)), Sokoine University of Agriculture (SUA).
- **Survey Microdata**: Collected and provided by the [National Bureau of Statistics (NBS) Tanzania](https://www.nbs.go.tz/) and [OCGS Zanzibar](https://www.ocgs.go.tz/).
- **International Statistics**: [FAOSTAT, Food and Agriculture Organization of the United Nations](https://www.fao.org/faostat/).

