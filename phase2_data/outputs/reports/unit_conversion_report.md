# Unit Conversion & Measurement Harmonisation Report

**Project:** Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025  
**Deliverable:** Phase 2 Measurement Audit  
**Date:** November 2026  

---

## 1. Overview of Agricultural Units in AASS 2024/2025

The Tanzania AASS collects agricultural production using a combination of standardized metric containers and traditional local units. 
In the 2024/2025 round (Wave 3, Catalog 69), the National Bureau of Statistics (NBS) provides an officially validated and imputed production variable `harvest_ton` (in metric tonnes) for both seasons (`MASIKACROP` and `VULICROP`).

### Summary of Harvest Conversion Protocol
1. **Primary Standard**: Official NBS `harvest_ton * 1000.0` converts directly to kilograms (kg).
2. **Secondary Local Container Conversion**: In Masika, raw quantities (`s7q08c`) and unit codes (`s7q08c_unit`) are harmonized using NBS/FAO bulk densities (e.g. Debe = 18.0 kg, Large Sack = 100.0 kg, Medium Sack = 50.0 kg).
3. **Area Metric Harmonisation**: Plot areas are standardized in hectares (ha) using measured GPS / farmer estimates (`s6q03_Hectares`, `s4q03_Hectares`), with acre conversions (1 acre = 0.404686 ha) applied where hectares were unpopulated.

---

## 2. Unit Audit Summary

- **Masika Total Records Audited:** 38,602
- **Vuli Total Records Audited:** 24,664
- **Primary Source Used:** NBS Official Metric Tonnes (`harvest_ton`) supplemented by local unit conversions.
- **Conversion Audit Table:** Exported to `outputs/audit/unit_conversion_audit.csv`.
