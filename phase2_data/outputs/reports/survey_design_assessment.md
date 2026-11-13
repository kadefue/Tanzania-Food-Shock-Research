# Survey Design & Sampling Weight Assessment Report

**Project:** Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025 (Catalog 69)  
**Deliverable:** Phase 2 Survey Methodology Audit  
**Date:** November 2026  

---

## 1. Survey Sample Architecture

The Tanzania AASS is a two-stage stratified cluster sample designed and implemented by the National Bureau of Statistics (NBS):
- **Primary Sampling Units (PSUs):** Enumeration Areas (EAs) selected with Probability Proportional to Size (PPS) within each district stratum (`ea_id`).
- **Secondary Sampling Units (SSUs):** Agricultural households selected systematically within sampled EAs (`HHFARMID`).
- **Stratification:** Stratified by administrative district and agro-ecological zone (`stratum_id`).
- **Sampling Expansion Weight:** `Adjusted_HH_weight` incorporates the inverse selection probabilities at both stages, non-response adjustments, and post-stratification benchmark calibration.

---

## 2. Weight Application Guidelines for Subsequent Analysis

1. **Descriptive Tables (Table 1):** Must strictly utilize `Adjusted_HH_weight` to produce population-representative estimates of mean yields, asset holdings, and shock exposure.
2. **Econometric Regressions (Phase 3):** Must implement Weighted Least Squares (WLS) or survey-calibrated Generalized Linear Models (GLMs).
3. **Variance Estimation:** Design-based standard errors must be computed using **Taylor series linearization** or cluster-robust standard errors clustered at the PSU (`ea_id`) level:
   $$\widehat{\text{Var}}(\hat{\beta}) = (X'WX)^{-1} \left( \sum_{c \in \text{EAs}} u_c' u_c \right) (X'WX)^{-1}$$
4. **Machine Learning Models:** As recommended by survey-methodology best practice, sampling weights can be supplied as sample weights during training, but validation loss must be evaluated on unweighted or domain-standardized test slices.
5. **Sub-population Caution:** When analyzing Population C (Same-Crop Bimodal Cohort), weights should be treated under sub-population domain estimation rules rather than re-normalizing weights to sum to total national smallholders.

---

## 3. Weight Diagnostics Across Cohorts

See detailed numerical audit in:
- `outputs/audit/survey_variable_inventory.csv`
- `outputs/audit/analytical_sample_weight_assessment.csv`
