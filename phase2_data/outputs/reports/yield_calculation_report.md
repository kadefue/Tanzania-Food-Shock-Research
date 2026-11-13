# Crop-Specific Yield Reconstruction & Agronomic Diagnostics Report

**Project:** Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025  
**Deliverable:** Phase 2 Crop Yield Audit  
**Date:** November 2026  

---

## 1. Methodological Resolution of Phase 1 Defect R-07

In the legacy codebase, agricultural yields were calculated by pooling total harvest kilograms across all crops (cassava tubers, cereal grains, pulses, tree crops) and dividing by total farm plot area. This confounded moisture contents, harvest indexes, and crop substitutions into spurious "yield" changes.

In Phase 2, crop yields are reconstructed strictly at the **crop-species level**:
$$Y_{hcs} = \frac{\sum_p P_{hcsp}}{\sum_p A_{hcsp}}$$
where $P_{hcsp}$ is the harvest of crop $c$ on plot $p$ (in kg), and $A_{hcsp}$ is the allocated area of crop $c$ on plot $p$ (in ha), accounting for intercrop shares.

---

## 2. Top Crops Seasonal Yield Summary

| crop_name | season | total_household_observations | valid_agronomic_observations | zero_harvest_count | below_bound_count | above_bound_count | mean_yield_all | median_yield_all | std_yield_all | mean_yield_valid | median_yield_valid | iqr_yield_valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Maize | masika | 9182 | 8268 | 528 | 65 | 320 | 2079.7 | 1002.4 | 4986.2 | 1569.7 | 1050.1 | 1645.8 |
| Maize | vuli | 5697 | 5363 | 259 | 32 | 43 | 1321.2 | 860.2 | 1581.0 | 1307.6 | 930.5 | 1233.8 |
| Beans | masika | 3161 | 2868 | 177 | 24 | 90 | 1014.3 | 504.1 | 3091.1 | 774.5 | 528.9 | 801.5 |
| Paddy | masika | 2467 | 2129 | 137 | 5 | 195 | 4180.6 | 1779.1 | 25943.6 | 2345.8 | 1738.8 | 2578.0 |
| Cassava | vuli | 2162 | 0 | 2161 | 0 | 0 | 0.0 | 0.0 | 0.0 | nan | nan | nan |
| Cassava | masika | 1891 | 0 | 1891 | 0 | 0 | 0.0 | 0.0 | 0.0 | nan | nan | nan |
| Beans | vuli | 1742 | 1645 | 62 | 20 | 15 | 708.3 | 440.3 | 861.2 | 694.1 | 459.5 | 677.3 |
| Banana | vuli | 1670 | 0 | 1669 | 0 | 0 | 0.0 | 0.0 | 0.0 | nan | nan | nan |
| Sunflower | masika | 1636 | 1521 | 102 | 6 | 7 | 1097.1 | 620.3 | 2029.4 | 1075.9 | 659.8 | 938.8 |
| Groundnut | masika | 1629 | 1489 | 126 | 9 | 5 | 1283.4 | 533.5 | 14871.7 | 904.2 | 611.4 | 816.5 |

---

## 3. Agronomic Plausibility Flag Distribution

- **Total Crop-Season Observations:** 51,960
- **Valid Agronomic Range:** 63.1%
- Detailed diagnostics available in:
  - `outputs/audit/crop_season_yield_summary.csv`
  - `outputs/audit/yield_quality_flags.csv`
