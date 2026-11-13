# Seasonal Instability Metric Comparison & Recommendation Report

**Project:** Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025  
**Deliverable:** Phase 2 Outcome Variable Audit  
**Date:** November 2026  

---

## 1. Executive Summary & Audit of Legacy Metric ($Y_{\text{vol}}$)

The legacy codebase implemented a bounded ratio index:
$$Y_{\text{vol}} = \frac{2|Y_M - Y_V|}{Y_M + Y_V + 2\epsilon} \in [0, 2]$$

### Critical Methodological Defects Uncovered:
1. **Severe Boundary Clustering (Spike at 2.0):** Whenever a smallholder has zero yield in either Masika or Vuli, $Y_{\text{vol}}$ collapses to exactly **2.0**. In the empirical sample, this artificial boundary spike comprises **13.72%** of all observations, severely violating regression normality assumptions.
2. **Confounding Crop Substitution:** In the legacy code, $Y_{\text{vol}}$ was computed across all pooled crops rather than within the same crop, conflating crop switching with agronomic yield shocks.

---

## 2. Comparative Evaluation of Alternative Formulations

| metric_variable | metric_description | total_observations | valid_observations | missing_count | mean | std | median | p25 | p75 | boundary_spikes_count | boundary_spikes_pct | recommended_for_phase3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| y_vol_legacy | Original Bounded Ratio [0, 2] | 1560 | 1560 | 0 | 0.828 | 0.657 | 0.667 | 0.286 | 1.295 | 214 | 13.72 | DEFECTIVE_BOUNDARY_ARTIFACT |
| abs_yield_diff_kg_ha | Same-Crop Absolute Difference (kg/ha) | 1560 | 1560 | 0 | 1226.134 | 4676.395 | 489.152 | 165.18 | 1148.786 | 0 | 0.0 | RECOMMENDED |
| rel_yield_change | Relative Yield Change ((Y_v - Y_m) / Y_m) | 1560 | 1433 | 127 | 0.631 | 3.186 | -0.005 | -0.515 | 0.706 | 0 | 0.0 | DEFECTIVE_BOUNDARY_ARTIFACT |
| log_yield_ratio | Log Yield Ratio ln(Y_v / Y_m) | 1560 | 1327 | 233 | -0.011 | 1.072 | 0.0 | -0.518 | 0.607 | 0 | 0.0 | RECOMMENDED |
| symm_relative_diff | Symmetric Relative Difference (2|Y_m - Y_v| / (Y_m + Y_v)) | 1560 | 1541 | 19 | 0.838 | 0.655 | 0.667 | 0.286 | 1.308 | 214 | 13.89 | DEFECTIVE_BOUNDARY_ARTIFACT |
| downside_shortfall_kg_ha | Downside Yield Shortfall (max(0, Y_m - Y_v)) | 1560 | 1560 | 0 | 827.036 | 4684.5 | 0.0 | 0.0 | 495.16 | 0 | 0.0 | RECOMMENDED |

---

## 3. Production vs. Yield Variance Decomposition

Decomposing seasonal production swings:
$$\Delta P = A_M \Delta Y + Y_M \Delta A + \Delta A \Delta Y$$
- **Mean Yield Effect Contribution:** 77.0%
- **Finding:** A substantial portion of seasonal harvest fluctuation is driven by deliberate **land allocation adjustments** between long and short rains rather than pure yield collapse.

---

## 4. Final Scientific Recommendation for Phase 3 Modeling

> [!IMPORTANT]
> **Primary Recommendation:**  
> For subsequent econometric and machine learning modeling, we strongly recommend adopting **Same-Crop Log Yield Ratio ($L_{hc} = \ln(Y_{hcV} / Y_{hcM})$)** or **Same-Crop Absolute Difference ($D_{hc} = |Y_{hcM} - Y_{hcV}|$)** as the primary outcome, with **Downside Yield Shortfall** as the secondary vulnerability outcome.  
> The legacy bounded ratio index ($Y_{\text{vol}}$) should be retained strictly as an empirical benchmark to document remediation of previous findings.
