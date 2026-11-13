# Phase 2 Implementation Log: Data Validation, Sample Reconstruction, Crop Harmonisation, and Yield-Instability Measurement

**Project:** Tanzania Agricultural Annual Sample Survey (AASS) Yield Volatility Research  
**Target Journal:** Springer Nature *Food Security*  
**Phase:** Phase 2 (Data Validation, Sample Reconstruction, Crop Harmonisation, and Yield-Instability Measurement)  
**Date:** November 2026  
**Status:** In Progress / Active Execution  

---

## 1. Executive Summary & Purpose

This log documents all technical actions, methodological adaptations, and empirical resolutions implemented during Phase 2. All modifications are explicitly tied to the scientific audit findings and risks documented in Phase 1 (`PROJECT_AUDIT.md`, `DATA_DICTIONARY.md`, `EXISTING_ANALYSIS_AUDIT.md`, `METHODOLOGICAL_RISK_REGISTER.md`, `ANALYSIS_FEASIBILITY_MATRIX.md`, and `PHASE2_IMPLEMENTATION_PLAN.md`).

Phase 2 establishes a trustworthy, leak-free, survey-calibrated, and crop-harmonized analytical microdata infrastructure. It strictly avoids premature machine-learning experiments, econometric regressions, or manuscript rewriting, focusing entirely on resolving foundational data architecture, survey design, crop classification, harvest conversion, and yield instability measurement.

---

## 2. Mapping of Phase 2 Modules to Phase 1 Audit Findings

| Phase 2 Module | Source File | Phase 1 Finding / Risk Addressed | Implementation Rationale & Technical Solution |
|---|---|---|---|
| **1. Configuration & Dictionaries** | `config/settings.yaml`<br>`config/variable_dictionary.yaml` | Feasibility Matrix §2.1; Data Dictionary §3 | Centralizes file paths, agronomic thresholds, random seeds, and official NBS survey schemas outside code logic. |
| **2. Data Loading & Validation** | `src/data_loading.py`<br>`src/data_validation.py` | Risk Register R-01; Existing Analysis §3.1 | Reads raw Stata tables with `pyreadstat`. Standardizes `HHFARMID`, validates key uniqueness, checks missingness, isolates genuine smallholder households (`Holding_type == 2.0`), purging 1,075 commercial mega-farms. |
| **3. Dataset Relationships & Merge Audit** | `src/dataset_relationships.py` | Risk Register R-02; Existing Analysis §3.2 | Audits 1:1, 1:m, and m:1 merges across Household, Plot, Crop, Input, and Shock rosters. Prevents Cartesian duplication of production/area records. |
| **4. Crop Harmonisation** | `src/crop_harmonisation.py` | Risk Register R-03; Project Audit §4.3 | Resolves the critical code-label discrepancy between Masika (e.g. Maize=1) and Vuli (Maize=11). Maps all 119 crops to unified FAO/NBS names, codes, crop groups, and food/non-food categories. |
| **5. Unit Conversion & Harmonisation** | `src/unit_conversion.py` | Risk Register R-04; Data Dictionary §5 | Validates plot area standardization (ha) and harvest production units. Implements crop-specific bulk densities for non-standard local containers (debe, gunia, baskets). Audits NBS imputed `harvest_ton * 1000.0`. |
| **6. Analytical Sample Reconstruction** | `src/sample_selection.py` | Risk Register R-05; Feasibility Matrix §2.2 | Formally reconstructs 4 distinct analytical populations (A: All valid smallholders; B: Seasonal producers; C: Same-crop bimodal cohort; D: Farming system groups) and assesses selection bias. |
| **7. Survey Design Assessment** | `src/survey_design.py` | Risk Register R-06; Methodological Risks §3.1 | Verifies sampling weights (`Adjusted_HH_weight`), strata (`stratum_id`), and PSUs (`ea_id`). Evaluates analytical sample attrition and design-based variance requirements (Taylor linearization). |
| **8. Crop-Specific Yield Reconstruction** | `src/yield_calculation.py` | Risk Register R-07; Existing Analysis §4.1 | Eliminates unweighted biomass pooling across disparate crops. Calculates plot-area-share weighted yields ($Y_{hcs} = \sum P / \sum A$) for priority food crops (Maize, Paddy, Beans, Cassava). Flags outliers with agronomic bounds. |
| **9. Instability Metrics Reconstruction** | `src/volatility_metrics.py` | Risk Register R-08; Methodological Risks §4.2 | Re-evaluates legacy $Y_{\text{vol}}$ formula (which has a 25.8% spike at 2.0) against same-crop absolute difference ($D_{hc}$), relative change ($R_{hc}$), log-ratio ($L_{hc}$), symmetric difference ($S_{hc}$), and downside shortfall. Decomposes production vs. yield variance. |
| **10. Quality Reports & Dataset Export** | `src/data_quality_reports.py`<br>`src/export_datasets.py` | Phase 2 Prompt §11, §13 | Exports verified Parquet and CSV datasets accompanied by exhaustive audit tables and scientific reports. |
| **11. Automated Test Suite** | `tests/test_*.py` | Phase 2 Prompt §12 | 8 automated test suites covering yield calculation, plot aggregation, unit conversion, instability metrics, sample selection, merges, and survey weight integrity. |

---

## 3. Detailed Implementation Milestones

### Milestone 2.1: Infrastructure, Configuration, and Schemas
- **Action:** Created `phase2_data/` directory tree, `config/settings.yaml`, `config/variable_dictionary.yaml`, `requirements.txt`, and `README.md`.
- **Finding Addressed:** Avoid hardcoded thresholds and unversioned paths. Ensure 100% reproducible execution.

### Milestone 2.2: Data Loading, Filtering & Key Integrity
- **Action:** Created `src/data_loading.py` and `src/data_validation.py`.
- **Finding Addressed:** Filter `Holding_type == 2.0` (eliminating commercial farm bias) and standardize household primary keys across all modules.

### Milestone 2.3: Crop Classification & Harmonisation Engine
- **Action:** Created `src/crop_harmonisation.py` and generated `outputs/audit/crop_harmonisation_dictionary.csv`.
- **Finding Addressed:** Eliminates the fatal bug where Maize in Masika (ID 1) and Maize in Vuli (ID 11) were treated as different crops due to differing Stata value labels.

### Milestone 2.4: Area & Harvest Unit Harmonisation Engine
- **Action:** Created `src/unit_conversion.py`, auditing container conversion factors and generating `outputs/audit/unit_conversion_audit.csv`.
- **Finding Addressed:** Enforce crop-specific bulk densities and validate NBS imputed tonnage.

### Milestone 2.5: Analytical Sample Reconstruction & Selection Bias Audit
- **Action:** Created `src/sample_selection.py`, creating Populations A, B, C, D, and generating `outputs/audit/sample_selection_flow.csv` and `sample_comparison.csv`.
- **Finding Addressed:** Accurately delineate bimodal agricultural zones from unimodal ones; assess selection bias of two-season households.

### Milestone 2.6: Survey Design & Variance Estimation Infrastructure
- **Action:** Created `src/survey_design.py`, validating `Adjusted_HH_weight`, `ea_id`, and `stratum_id`.
- **Finding Addressed:** Prevent unweighted estimates and establish survey design structure for subsequent modeling.

### Milestone 2.7: Crop-Specific Yield Rebuilding & Agronomic Outlier Diagnostics
- **Action:** Created `src/yield_calculation.py`, aggregating multi-plot production and flagging outliers.
- **Finding Addressed:** Stop aggregating raw kg of cassava, maize, and beans; produce clean crop-specific yields in kg/ha.

### Milestone 2.8: Instability Metrics Benchmark & Scientific Decomposition
- **Action:** Created `src/volatility_metrics.py`, comparing original $Y_{\text{vol}}$ against same-crop alternative metrics and decomposing production vs. yield variation.
- **Finding Addressed:** Resolve the boundary anomaly at 2.0 and separate crop portfolio changes from yield collapse.

### Milestone 2.9: Dataset Exports, Automated Tests & Master Pipeline Orchestrator
- **Action:** Created `src/export_datasets.py`, `run_phase2.py`, and complete `tests/test_*.py` suite.
- **Finding Addressed:** Full end-to-end reproducibility with test coverage.

### Milestone 2.10: Scientific Reports & Synthesis
- **Action:** Authored comprehensive scientific reports in `outputs/reports/` and root `PHASE2_COMPLETION_REPORT.md`.
- **Finding Addressed:** Peer-reviewed quality documentation for journal reviewers.
