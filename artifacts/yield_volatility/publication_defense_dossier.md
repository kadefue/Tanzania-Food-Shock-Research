# Smallholder Yield Volatility in Tanzania: Scientific Defense Dossier
### Publication-Ready Figures, Tables, and Empirical Defense Portfolio
**Principal Investigator / Author:** Kadeghe Goodluck Fue ([kadefue@sua.ac.tz](mailto:kadefue@sua.ac.tz))  
**Institution:** Department of Agricultural Engineering, School of Engineering and Technology, Sokoine University of Agriculture (SUA)  
**Survey Source:** National Bureau of Statistics (NBS) Annual Agricultural Sample Survey (AASS) Microdata & FAOSTAT  

---

## Executive Summary of Findings
This defense portfolio compiles **10 publication-grade figures** and **7 publication-grade tables** defending the empirical and methodological integrity of our supervised machine learning pipeline predicting smallholder seasonal yield volatility ($Y_{vol}$) across Mainland Tanzania and Zanzibar ($N=4,564$ holdings across 921 Enumeration Areas).
Key empirical proofs established:
1. **Pruned Champion Performance**: Selecting the Top-100 Grandmaster features out of 246 candidates prunes 146 noisy/zero-importance features, boosting Spatial Cross-Validation $R^2$ to **0.5920** and reducing Spatial RMSE to **0.4642** under strictly independent 5-fold EA Group Cross-Validation.
2. **Zero Data Leakage Certified**: Formal 5-pillar audit proves complete spatial, target, scaler, clustering/PCA, and feature selection boundary isolation (`CERTIFIED_LEAKAGE_FREE`).
3. **National Model Spatial Efficiency**: In 26 of 27 regions, the Unified National Weighted Ensemble outperforms regional sub-models ($\Delta R^2 > 0$), providing substantial variance reduction and transferability across heterogeneous agro-ecological zones.
4. **Agronomic Tipping Points**: Planting month disparity (`plant_month_delta`), harvest failure share (`m_no_harvest_share`), and crop diversity divergence (`shannon_diff_from_region_mean`) are the primary predictors of volatility, buffered non-linearly by Tropical Livestock Units (TLU).
5. **Actionable Policy Scenarios**: Counterfactual stress-testing reveals that an integrated Climate-Smart Agriculture package (asset transfer + crop diversification + planting synchronisation) substantially reduces hyper-volatile smallholders.

---

## Part I: Publication-Ready Scientific Figures

### Figure 1: Empirical Distribution of Yield Volatility and Cross-Seasonal Dynamics
![Figure 1: Empirical Distribution of Yield Volatility and Cross-Seasonal Dynamics](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig1_target_distribution_and_seasonal_dynamics.png)

**Figure 1 Scientific Caption & Defense Commentary:**  
Panel (a) displays the bimodal density distribution of the Yield Volatility Index ($Y_{vol} \in [0, 2]$) with median 1.01 and IQR [0.40, 2.00]. Panel (b) illustrates the log-yield parity between Masika (long rains) and Vuli (short rains) seasons coloured by volatility. Panel (c) presents boxplots of volatility across landholding size strata, revealing heightened vulnerability among marginal holdings (<0.5 ha).

---

### Figure 2: Multi-Model Spatial Benchmark and Calibration Curve
![Figure 2: Multi-Model Spatial Benchmark and Calibration Curve](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig2_model_benchmark_spatial_cv.png)

**Figure 2 Scientific Caption & Defense Commentary:**  
Panel (a) compares Spatial RMSE and $R^2$ across Random Forest, XGBoost, LightGBM, and the Weighted Ensemble. Panel (b) displays the out-of-fold calibration scatter between observed and predicted volatility against the ideal 45° parity line ($R^2 = 0.5920$). Panel (c) highlights spatial fold-wise stability across the 5 independent geographic folds.

---

### Figure 3: Grandmaster Feature Selection Trajectory and Importance Hierarchy
![Figure 3: Grandmaster Feature Selection Trajectory and Importance Hierarchy](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig3_grandmaster_feature_importance_and_selection.png)

**Figure 3 Scientific Caption & Defense Commentary:**  
Panel (a) illustrates the cumulative information gain scree curve, demonstrating that the Top 100 features capture 99.1% of predictive gain while pruning 146 noisy variables. Panel (b) highlights the top 15 features by tree split frequency and gain importance. Panel (c) breaks down feature composition across the six core agronomic domains.

---

### Figure 4: SHAP Global Feature Attributions and Directional Effects
![Figure 4: SHAP Global Feature Attributions and Directional Effects](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig4_shap_global_feature_attributions.png)

**Figure 4 Scientific Caption & Defense Commentary:**  
Panel (a) presents the SHAP beeswarm plot displaying directional influence on smallholder yield volatility (planting delays and plot abandonment increase volatility; livestock TLU and crop diversity buffer volatility). Panel (b) shows mean absolute SHAP values ($|\text{SHAP}|$) quantifying relative predictive strength.

---

### Figure 5: Regional Heterogeneity and Spatial Model Transferability
![Figure 5: Regional Heterogeneity and Spatial Model Transferability](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig5_regional_heterogeneity_and_spatial_transferability.png)

**Figure 5 Scientific Caption & Defense Commentary:**  
Panel (a) shows regional model performance across all 27 surveyed regions of Tanzania compared against the Unified National Model slice. Panel (b) details the transferability advantage ($\Delta R^2 = R^2_{\text{National}} - R^2_{\text{Regional}}$), proving the national ensemble's superior sample efficiency across 26 of 27 regions.

---

### Figure 6: Non-Linear Agronomic Interactions and Resilience Thresholds
![Figure 6: Non-Linear Agronomic Interactions and Resilience Thresholds](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig6_agronomic_non_linear_interactions.png)

**Figure 6 Scientific Caption & Defense Commentary:**  
Panel (a) depicts the interaction between seasonal planting delays and livestock assets (TLU). Panel (b) demonstrates how crop portfolio diversity buffers holdings against complete harvest failures. Panel (c) illustrates how supplemental irrigation mitigates the volatility-inducing impact of plot fragmentation.

---

### Figure 7: Redesigned 5-Pillar Leakage Audit Verification and Household Counterfactuals
![Figure 7: Redesigned 5-Pillar Leakage Audit Verification and Household Counterfactuals](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig7_leakage_audit_and_household_counterfactuals.png)

**Figure 7 Scientific Caption & Defense Commentary:**  
Panel (a) provides the 5-pillar isolation audit scorecard showing 100% compliance across spatial, target, scaler, latent representation, and feature selection boundaries. Panel (b) presents comparative capacity profiles across three distinct smallholder archetypes. Panel (c) displays a micro-level SHAP waterfall explanation for resilient benchmark holding #0.

---

### Figure 8: Agro-Ecological Zones and Volatility Hotspots
![Figure 8: Agro-Ecological Zones and Volatility Hotspots](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig8_spatial_hotspots_and_agroecological_zones.png)

**Figure 8 Scientific Caption & Defense Commentary:**  
Panel (a) details mean yield volatility across Tanzania's seven agro-ecological zones with 95% confidence intervals. Panel (b) charts harvest failure rate against seasonal yield gap by zone. Panel (c) displays the Agro-Ecological Resilience Index ($1 - Y_{vol}/2$).

---

### Figure 9: Agro-Economic Partial Dependence and Marginal Response Surfaces
![Figure 9: Agro-Economic Partial Dependence and Marginal Response Surfaces](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig9_agroeconomic_partial_dependence_surfaces.png)

**Figure 9 Scientific Caption & Defense Commentary:**  
Displays partial dependence response curves for the top 4 non-linear continuous drivers: (a) seasonal planting disparity, (b) livestock TLU assets, (c) crop diversity divergence, and (d) harvest plot abandonment percentage.

---

### Figure 10: Policy Counterfactual Stress-Testing & Volatility Mitigation Scenarios
![Figure 10: Policy Counterfactual Stress-Testing & Volatility Mitigation Scenarios](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/figures/fig10_policy_simulation_and_counterfactual_interventions.png)

**Figure 10 Scientific Caption & Defense Commentary:**  
Panel (a) simulates the leftward distribution shift of yield volatility under three targeted interventions versus the status quo. Panel (b) illustrates the sharp drop in hyper-volatile smallholders ($Y_{vol} \ge 1.50$) under an integrated Climate-Smart Agriculture package. Panel (c) illustrates net risk mitigation efficiency.

---

## Part II: Publication-Ready Empirical Tables

### Table 1: Summary Statistics of Smallholder Holdings and Seasonal Agronomic Dynamics (N=4,564)
- **CSV Source:** [`table1_summary_statistics.csv`](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/tables/table1_summary_statistics.csv)

| Variable Description | Domain Category | Observations (N) | Mean | Std Dev | Q1 (25%) | Median | Q3 (75%) | Min | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Yield Volatility Index (Yᵥₒₗ) | Target Variable | 4564 | 1.0843 | 0.7267 | 0.4000 | 1.0142 | 2.0000 | 0.0000 | 2.0000 |
| Masika Harvest Yield (kg/ha) | Crop Production | 4564 | 930.13 | 2057.96 | 123.79 | 396.95 | 990.10 | 0.0000 | 64126.85 |
| Vuli Harvest Yield (kg/ha) | Crop Production | 4564 | 900.80 | 1952.16 | 123.58 | 414.34 | 998.04 | 0.0000 | 59394.25 |
| Seasonal Yield Difference (kg/ha) | Crop Production | 4564 | 883.52 | 2170.16 | 133.50 | 353.58 | 872.51 | 0.0000 | 62855.23 |
| Total Cultivated Area (ha) | Farm Structure | 4564 | 16.6457 | 140.55 | 1.0000 | 2.0200 | 4.0469 | 0.0060 | 3723.11 |
| Masika Plot Area (ha) | Farm Structure | 4564 | 8.2849 | 70.3094 | 0.4313 | 1.0008 | 2.0234 | 0.0030 | 1861.55 |
| Vuli Plot Area (ha) | Farm Structure | 4564 | 8.3608 | 70.3203 | 0.4246 | 0.9940 | 2.0301 | 0.0007 | 1861.55 |
| Inorganic Fertiliser Applied (kg) | Input Intensification | 4564 | 1086.25 | 41528.35 | 0.0000 | 0.0000 | 20.0000 | 0.0000 | 2733766.67 |
| Pesticide Applied (L or kg) | Input Intensification | 4564 | 118.26 | 1613.45 | 0.0000 | 0.0000 | 5.6375 | 0.0000 | 96500.00 |
| Shannon Crop Diversity Index | Crop Diversification | 4564 | 0.1801 | 0.3098 | -0.0000 | 0.0000 | 0.3423 | 0.0000 | 1.6879 |
| Plot Fragmentation (Coefficient of Variation) | Plot Heterogeneity | 4564 | 0.3048 | 0.3758 | 0.0000 | 0.1151 | 0.5522 | 0.0000 | 3.1519 |
| Tropical Livestock Units (TLU) | Asset Buffers | 4564 | 4.9689 | 23.6655 | 0.0400 | 0.3600 | 4.7375 | 0.0000 | 1112.47 |
| Head of Household Age (Years) | Household Demographics | 4564 | 48.7149 | 17.5355 | 37.0000 | 50.0000 | 61.0000 | 0.0000 | 106.00 |
| Available Adult Labour Count | Labour Dynamics | 4564 | 2.8168 | 1.7663 | 2.0000 | 2.0000 | 4.0000 | 0.0000 | 15.0000 |
| Masika Harvest Percentage (%) | Harvest Outcomes | 4564 | 66.6637 | 31.5221 | 48.0000 | 89.0000 | 89.0000 | 0.0000 | 89.0000 |
| Planting Month Difference (Masika – Vuli, Months) | Agronomic Timing | 4564 | -4.2817 | 3.7081 | -7.0000 | -6.0000 | 0.0000 | -11.0000 | 10.0000 |


---

### Table 2: Multi-Model Spatial Cross-Validation Benchmark Comparison
- **CSV Source:** [`table2_model_benchmark.csv`](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/tables/table2_model_benchmark.csv)

| Model Architecture | Spatial RMSE | Spatial MAE | Spatial R² | Hyperparameter Configuration | Training Time (s) |
| --- | --- | --- | --- | --- | --- |
| Weighted Ensemble | 0.4642 | 0.3472 | 0.5920 | 0.50 LightGBM + 0.40 XGBoost + 0.10 Random Forest (Soft Voting) | 9.1900 |
| LightGBM | 0.4655 | 0.3459 | 0.5898 | num_leaves=35, lr=0.03, colsample=0.7 | 6.0300 |
| XGBoost | 0.4664 | 0.3484 | 0.5880 | max_depth=5, lr=0.03, colsample=0.7 | 2.5700 |
| Random Forest | 0.4768 | 0.3682 | 0.5694 | max_depth=16, max_features=sqrt | 0.5100 |


---

### Table 3: Top-25 Grandmaster Feature Importance & Agronomic Domain Classifications
- **CSV Source:** [`table3_top25_feature_importance.csv`](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/tables/table3_top25_feature_importance.csv)

| Rank | Agronomic Variable Name | Agronomic Domain | Split Frequency | Gain Importance | Agronomic Description & Rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Planting Month Difference (Masika – Vuli) | Agronomic Timing | 277 | 11357.75 | Inter-seasonal gap in crop establishment timing between long and short rains |
| 2 | Mean Planting Month (Vuli) | Agronomic Timing | 201 | 2510.90 | Calendar timing of Vuli short-rain crop sowing relative to rainy season onset |
| 3 | Mean Harvested Area Share (Masika) | Harvest Outcomes | 191 | 2633.40 | Average proportion of cultivated holding area successfully harvested in Masika |
| 4 | Crop Diversity vs Regional Mean | Crop Diversity | 185 | 412.05 | Holding-level portfolio diversification benchmarked against regional peer average |
| 5 | Crop Failure Plot Share (Masika) | Failure Shocks | 128 | 1754.42 | Proportion of cultivated parcels experiencing total crop loss or abandonment |
| 6 | Tropical Livestock Units (TLU) | Asset Buffers | 126 | 110.46 | Aggregated herd size providing liquid capital buffer against acute crop failure |
| 7 | Seasonal Crop Evenness Shift | Crop Diversity | 125 | 330.83 | Inter-seasonal change in cultivar species evenness and abundance parity |
| 8 | Cultivated Land per Adult Labourer | Labour Dynamics | 123 | 145.07 | Household labour capitalisation ratio (cultivated hectares per active adult) |
| 9 | Mean Planting Month (Masika) | Agronomic Timing | 115 | 316.38 | Calendar month of Masika long-rain crop sowing and field establishment |
| 10 | Farm Area vs Regional Mean (ha) | Farm Structure | 109 | 164.06 | Deviation of total cultivated farm size from regional agro-ecological average |
| 11 | Mean Operational Plot Area (ha) | Plot Heterogeneity | 109 | 141.22 | Average operational parcel size across the agricultural holding |
| 12 | Age of Household Head (Years) | Demographics | 107 | 127.30 | Farming experience and managerial human capital of the primary decision-maker |
| 13 | Subsistence Cereal Cluster Distance | Latent Archetype | 103 | 122.00 | Euclidean distance to regional Subsistence Cereal Monoculture cluster |
| 14 | Capital–Labour Latent Factor (PCA 2) | Latent PCA | 100 | 131.06 | Orthogonal dimension capturing input capital investment versus labour reliance |
| 15 | Drought Failure Indicator (Vuli) | Climatic Shocks | 97 | 1673.90 | Binary indicator of severe drought-induced crop failure during the short rains |
| 16 | Plot Fragmentation (Area CV) | Plot Heterogeneity | 97 | 134.83 | Spatial fragmentation and parcel size inequality across operational plots |
| 17 | Total Livestock Head Count | Asset Buffers | 96 | 100.69 | Total absolute number of domestic farm animals owned by the household |
| 18 | Commercial Cropping Cluster Distance | Latent Archetype | 94 | 200.89 | Euclidean distance to regional Commercial Mixed Cropping farming cluster |
| 19 | Fertiliser vs Regional Mean (kg) | Input Technology | 89 | 107.91 | Synthetic fertiliser usage rate relative to local farming community benchmark |
| 20 | Fallow Land Proportion (Masika) | Soil Management | 88 | 381.43 | Proportion of holding area maintained under fallow for soil fertility restoration |
| 21 | Plot Area Standard Deviation (ha) | Plot Heterogeneity | 87 | 95.3249 | Dispersion and size disparity among cultivated parcels within the holding |
| 22 | Seasonal Fertiliser Ratio | Agro-economic | 85 | 281.73 | Predictive feature |
| 23 | Pesticide Intensity (Masika, kg/ha) | Input Technology | 84 | 89.8900 | Chemical crop protection intensity per cultivated hectare during long rains |
| 24 | Minimum Harvest Share (Masika) | Harvest Outcomes | 82 | 456.97 | Lowest plot-level harvest realisation rate observed within the holding |
| 25 | Agro-Ecological Latent Factor (PCA 3) | Latent PCA | 80 | 112.45 | Orthogonal dimension capturing topography, altitude, and thermal gradients |


---

### Table 4: Regional Heterogeneity & Sub-Model Performance Breakdown (All 27 Regions)
- **CSV Source:** [`table4_regional_performance_breakdown.csv`](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/tables/table4_regional_performance_breakdown.csv)

| Region ID | Region Name | Holdings (N) | Regional Model RMSE | Regional Model R² | National Model RMSE | National Model R² | National Advantage (ΔR²) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | Tanga | 650 | 0.6229 | 0.2022 | 0.4674 | 0.5509 | 0.3487 |
| 20 | Mara | 476 | 0.5340 | 0.4620 | 0.4314 | 0.6489 | 0.1868 |
| 3 | Kilimanjaro | 375 | 0.6074 | 0.3455 | 0.4604 | 0.6240 | 0.2785 |
| 18 | Kagera | 296 | 0.4040 | 0.6876 | 0.3629 | 0.7480 | 0.0603 |
| 5 | Morogoro | 257 | 0.6706 | 0.0621 | 0.5175 | 0.4415 | 0.3794 |
| 6 | Pwani | 252 | 0.6197 | 0.2706 | 0.4419 | 0.6291 | 0.3585 |
| 12 | Mbeya | 227 | 0.6014 | 0.2725 | 0.5051 | 0.4869 | 0.2144 |
| 19 | Mwanza | 215 | 0.5886 | 0.2795 | 0.5049 | 0.4698 | 0.1903 |
| 2 | Arusha | 215 | 0.5906 | 0.2973 | 0.4586 | 0.5763 | 0.2791 |
| 21 | Manyara | 209 | 0.5920 | 0.2777 | 0.4965 | 0.4921 | 0.2144 |
| 24 | Simiyu | 202 | 0.4666 | 0.4367 | 0.4579 | 0.4577 | 0.0210 |
| 30 | Kaskazini Pemba | 195 | 0.5602 | 0.3530 | 0.3710 | 0.7163 | 0.3632 |
| 27 | Kaskazini Unguja | 151 | 0.5977 | 0.3103 | 0.4727 | 0.5686 | 0.2582 |
| 25 | Geita | 147 | 0.6127 | 0.0497 | 0.5006 | 0.3656 | 0.3159 |
| 31 | Kusini Pemba | 93 | 0.5790 | 0.3145 | 0.3665 | 0.7253 | 0.4108 |
| 28 | Kusini Unguja | 89 | 0.5727 | 0.4223 | 0.4657 | 0.6179 | 0.1956 |
| 29 | Mjini Magharibi | 80 | 0.5305 | 0.5942 | 0.4134 | 0.7536 | 0.1594 |
| 7 | Dar es Salaam | 66 | 0.7240 | -0.0539 | 0.5830 | 0.3165 | 0.3704 |
| 16 | Kigoma | 55 | 0.6467 | -0.0416 | 0.4911 | 0.3992 | 0.4409 |
| 17 | Shinyanga | 53 | 0.5450 | 0.2024 | 0.4991 | 0.3310 | 0.1286 |
| 1 | Dodoma | 27 | 0.6059 | 0.1132 | 0.3783 | 0.6542 | 0.5410 |
| 23 | Katavi | 25 | 0.6030 | 0.4268 | 0.4711 | 0.6502 | 0.2234 |
| 11 | Iringa | 14 | 0.5636 | 0.0511 | 0.3281 | 0.6785 | 0.6274 |
| 13 | Singida | 11 | 0.5318 | -0.1971 | 0.5694 | -0.3725 | -0.1754 |
| 14 | Tabora | 10 | 0.6287 | -0.5477 | 0.4610 | 0.1678 | 0.7155 |
| 22 | Njombe | 5 | 0.4199 | -1.2554 | 0.3869 | -0.9146 | 0.3409 |
| 26 | Songwe | 3 | 0.3721 | -1.1324 | 0.2514 | 0.0269 | 1.1594 |


---

### Table 5: Formal 5-Pillar Spatial Leakage Audit Certificate
- **CSV Source:** [`table5_leakage_audit_certificate.csv`](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/tables/table5_leakage_audit_certificate.csv)

| Pillar | Audit Domain | Verification Criterion | Quantitative Empirical Result | Verification Status |
| --- | --- | --- | --- | --- |
| 1 | Spatial Group Disjointness | Verifies training and validation folds share zero Enumeration Areas (EAs) | Zero overlapping EAs across all 5 spatial cross-validation folds. | CERTIFIED PASS |
| 2 | Target Variable Isolation | Verifies target Yᵥₒₗ is strictly excluded from feature space and no trivial target proxies exist | Target variable completely isolated. Maximum absolute feature correlation: 0.4365. | CERTIFIED PASS |
| 3 | Scaler & Imputation Isolation | Verifies preprocessing scalers and medians are strictly computed on training folds | Preprocessing scalers and imputers conform strictly to out-of-fold fit boundaries. | CERTIFIED PASS |
| 4 | Unsupervised Representation Isolation (KMeans & PCA) | Verifies KMeans cluster centroids and PCA latent components are computed strictly on training data | Latent representations (KMeans agronomic clusters and PCA components) strictly isolated. | CERTIFIED PASS |
| 5 | Feature Selection & Lookahead Integrity | Verifies feature selection ranking does not access validation target values or lookahead timestamps | Top-100 features selected using independent tree-gain importance; validation targets zero-masked. | CERTIFIED PASS |


---

### Table 6: Smallholder Agronomic Stratification across Volatility Quartiles
- **CSV Source:** [`table6_volatility_quartile_stratification.csv`](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/tables/table6_volatility_quartile_stratification.csv)

| Volatility Stratum | Holdings (N) | Mean Yield Volatility (Yᵥₒₗ) | Mean Yield Gap (kg/ha) | Mean Crop Diversity (Shannon) | Complete Harvest Failure Rate (%) | Fertiliser Intensity (kg) | Tropical Livestock Units (TLU) | Planting Month Difference (Months) | Plot Fragmentation (CV) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q1: Low Volatility (Resilient) | 1141 | 0.1761 | 174.32 | 0.2431 | 80.3079 | 400.68 | 5.1957 | 6.0140 | 0.2846 |
| Q2: Moderate-Low Volatility | 1141 | 0.6854 | 631.48 | 0.2306 | 81.6519 | 2556.62 | 4.4559 | 5.9201 | 0.2977 |
| Q3: Moderate-High Volatility | 1141 | 1.4756 | 1891.01 | 0.1607 | 76.1683 | 565.22 | 7.3311 | 5.5752 | 0.3456 |
| Q4: Hyper-Volatile | 1141 | 2.0000 | 837.26 | 0.0859 | 34.2676 | 822.49 | 2.8928 | 1.3705 | 0.2915 |


---

### Table 7: Representative Smallholder Archetypes & Micro-Level Counterfactual Attribution
- **CSV Source:** [`table7_household_counterfactual_archetypes.csv`](file:///home/kadefue/Tanzania-Food-Shock-Research/artifacts/yield_volatility/tables/table7_household_counterfactual_archetypes.csv)

| Case Scenario | Household Identifier | Archetype Classification | Observed Volatility (Yᵥₒₗ) | Model Predicted Volatility | Prediction Error (Residual) | Key Structural Characteristics | Targeted Policy Intervention |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Case A: Resilient Diversified Agro-Pastoralist | 00-68-86-52 | Low Volatility Archetype | 0.1830 | 0.3460 | 0.1630 | High crop diversity, substantial livestock TLU buffer, zero plot failure | Maintain mixed crop-livestock integration and agro-forestry buffers |
| Case B: Moderate Input-Intensive Specialised Farm | 00-19-44-35 | Moderate Volatility Archetype | 1.0070 | 0.5630 | 0.4440 | Synthetic fertiliser application, moderate planting delta, commercial focus | Introduce supplemental micro-irrigation and crop rotation to reduce seasonal yield swings |
| Case C: Climate-Shocked Vulnerable Smallholder | 00-72-59-03 | Hyper-Volatile Archetype | 2.0000 | 1.9710 | 0.0290 | Severe seasonal planting delay, complete plot abandonment shock, zero livestock buffer | Targeted social cash transfers, drought-tolerant seed kits, and early planting advisories |


---
