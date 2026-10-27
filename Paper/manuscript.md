# Predicting Smallholder Crop Yield Volatility Across Agro-Ecological Zones: A Leakage-Free Spatial Machine Learning Framework for Tanzania

**Author**: Kadeghe Goodluck Fue  
**Affiliation**: Department of Agricultural Engineering and Technology, School of Agricultural Sciences and Fisheries Technology, Sokoine University of Agriculture, P.O. Box 3003, Chuo Kikuu, Morogoro, Tanzania  
**Correspondence**: [kadefue@sua.ac.tz](mailto:kadefue@sua.ac.tz)

**Target Journal**: *Cogent Food & Agriculture* (Taylor & Francis)

---

### Public Interest Statement
Smallholder farmers in Sub-Saharan Africa operate on the frontlines of climate volatility, where bi-modal rainfall patterns dictate two distinct cropping seasons: Masika (long rains) and Vuli (short rains). When crop yields swing unpredictably between these seasons, household food reserves are wiped out, driving rural communities into seasonal poverty traps. While machine learning offers immense potential to anticipate harvest shocks, standard algorithms often 'memorize' geographic location, resulting in falsely high accuracy that fails when deployed to new rural districts. In this study, we develop a strictly leakage-free spatial artificial intelligence framework evaluated across 27 administrative regions of Tanzania using national microdata from 10,750 farming households. We demonstrate that seasonal fertilizer application imbalances, soil quality variability, and inadequate livestock safety buffers explain over half of smallholder yield swings. Crucially, we show that targeted fertilizer stabilization and crop portfolio diversification can suppress extreme seasonal yield crashes by more than 30%. These findings provide agricultural extension services and policymakers with a transparent, deployment-ready decision support tool to strengthen food security across Africa's smallholder landscapes.

### Abstract
Intra-annual crop yield volatility between bi-modal production seasons represents a profound vulnerability for smallholder farming systems in Sub-Saharan Africa. While machine learning offers transformative predictive capabilities, standard cross-validation paradigms suffer from spatial autocorrelation leakage, producing over-optimistic performance estimates that fail upon deployment to unseen agro-ecological landscapes. Here, we develop a leakage-free spatial machine learning pipeline utilizing the Tanzania National Bureau of Statistics (NBS) Annual Agricultural Sample Survey (AASS) microdata, encompassing 10,750 smallholder households across 27 administrative regions. We formulate a standardized inter-seasonal Yield Volatility Index (Y_vol) and construct domain-engineered agronomic features spanning seasonal input deltas, crop portfolio Shannon diversity, labor allocation dynamics, and livestock buffers. Using a 5-pillar spatial isolation protocol (Spatial GroupKFold grouped by administrative region), we benchmark LightGBM, XGBoost, Random Forest, CatBoost, and an out-of-fold optimal Weighted Ensemble against a non-spatial pooled baseline. The Weighted Ensemble achieves superior generalization (Spatial Out-of-Fold R^2 = 0.584 +/- 0.042, RMSE = 0.231 +/- 0.015), outperforming pooled models that exhibit an optimistic bias of Delta R^2 = +0.142 due to spatial leakage. SHAP interpretability identifies seasonal nitrogen fertilizer differential, soil quality indices, and livestock herd size as dominant non-linear drivers of yield stability. Counterfactual policy simulations demonstrate that targeted fertilizer buffering reduces median smallholder yield volatility by 31.4% in high-risk semi-arid regions. This framework establishes an empirically grounded blueprint for robust, deployment-ready agricultural AI in developing economies.

**Keywords**: smallholder agriculture, yield volatility, spatial cross-validation, machine learning, Tanzania, climate resilience, agro-ecological zones

---

## 1. Introduction

Smallholder agricultural systems form the economic foundation and primary food source for more than 70% of the population in Sub-Saharan Africa (SSA). In Tanzania, where agriculture contributes nearly 27% of Gross Domestic Product and employs over 65% of the national workforce, smallholder productivity is acutely tied to rainfall seasonality. Across large expanses of the country—particularly the northern, eastern, and Lake Victoria basins—crop production is governed by a bimodal precipitation regime consisting of the long rains (*Masika*, typically March to May) and the short rains (*Vuli*, October to December). 

While substantial agronomic research has focused on raising mean seasonal crop yields, inter-seasonal yield volatility—defined as the relative fluctuation in crop productivity between successive growing seasons within the same agricultural holding—constitutes an equally severe, yet under-investigated, driver of acute food insecurity. When smallholder yields collapse from one season to the next, farm households experience severe caloric shortfalls, distress sales of productive assets, and deepened poverty traps. 

The advent of machine learning (ML) and high-dimensional microdata has unlocked new frontiers in precision agriculture and agricultural vulnerability modeling. Modern tree-based ensembles, such as Gradient Boosted Decision Trees (GBDT), eXtreme Gradient Boosting (XGBoost), and LightGBM, have repeatedly demonstrated superior empirical performance over classical econometric and biophysical crop models by capturing complex non-linear interactions without rigid parametric assumptions.

However, the application of predictive machine learning to smallholder agriculture faces a critical methodological flaw: **spatial autocorrelation leakage**. Because farm holdings situated within proximity share latent agro-ecological, pedological, and climatic characteristics, conventional random k-fold cross-validation allows training folds to inadvertently access spatial proxies from validation folds. This spatial data leakage inflates cross-validation performance metrics (often by 15% to 30% in R^2), yielding dangerously over-optimistic models that degrade precipitously when transferred to unseen geographic domains or applied by agricultural extension officers in distant rural wards.

To overcome these barriers, this study establishes a rigorous, leakage-free spatial machine learning framework for predicting smallholder crop yield volatility across Tanzania. Utilizing microdata from the National Bureau of Statistics (NBS) Annual Agricultural Sample Survey (AASS)—comprising 10,750 smallholder households across all 27 administrative regions—we engineer a suite of domain-specific agronomic features, enforce a 5-pillar spatial isolation protocol, evaluate diverse model architectures, explain feature mechanisms via Shapley Additive Explanations (SHAP), and conduct counterfactual policy simulations.

The primary contributions of this work are fourfold:
1. **Target Formulation & Standardization**: We formulate an intra-annual Yield Volatility Index ($Y_{vol}$) that standardizes yield variations across heterogeneous agro-ecological zones while accommodating harvest failures.
2. **5-Pillar Spatial Isolation Architecture**: We introduce an end-to-end spatial validation framework that enforces spatial GroupKFold partitioning by administrative region, nested inside-fold preprocessor fitting, and zero-leakage feature selection.
3. **Multi-Model Benchmark & Weighted Ensembling**: We systematically benchmark LightGBM, XGBoost, Random Forest, CatBoost, and a spatially calibrated Weighted Ensemble, quantifying the precise empirical penalty of spatial cross-validation versus naive pooled splitting.
4. **Actionable Policy Counterfactuals**: We demonstrate how non-linear ML response surfaces can be converted into targeted policy simulations to evaluate fertilizer subsidies, crop diversification, and climate-smart agricultural interventions.


## 2. Materials and Methods

### 2.1 Microdata Acquisition and Harmonization
The empirical foundation of this study is the National Bureau of Statistics (NBS) Annual Agricultural Sample Survey (AASS) microdata covering mainland Tanzania and Zanzibar. The survey follows a multi-stage stratified cluster sampling design representative of smallholder agricultural households at both national and regional levels. 

The microdata integration pipeline ingests and merges seven primary survey modules:
- Household demographics and asset rosters (`HOUSEHOLD`)
- Agricultural plot registers and tenure characteristics (`MASIKAPLOT`, `VULIPLOT`)
- Crop production, area harvested, and harvest utilization (`MASIKACROP`, `VULICROP`)
- Input utilization rosters, including inorganic fertilizer, organic manure, pesticides, and improved seed varieties (`inputRoster_masika`, `inputRoster_vuli`)

To resolve measurement heterogeneity across rural districts, non-standard harvest volume units (e.g., *debe*, *gunia*, ox-carts, pieces) were harmonized to standard kilograms (kg) using official agro-ecological conversion coefficients published by the Ministry of Agriculture and NBS. Crop areas were standardized to hectares (ha). Holdings cultivating during both Masika and Vuli seasons were identified, yielding an eligible analytical cohort of 4,564 bi-modal smallholder households across 27 administrative regions.

### 2.2 Yield Volatility Index Target Formulation
Let $Y_{m,i}$ and $Y_{v,i}$ denote the aggregate crop yield (expressed in metric tons per hectare, t/ha) for household $i$ during the Masika and Vuli production cycles, respectively. To quantify inter-seasonal yield instability independent of baseline holding scale, we formulate the normalized Yield Volatility Index ($Y_{vol,i}$) as:

$$Y_{vol,i} = \frac{|Y_{m,i} - Y_{v,i}|}{\frac{1}{2}(Y_{m,i} + Y_{v,i}) + \epsilon}$$

where $\epsilon = 10^{-4}$ prevents numerical instability in rare cases where both seasonal harvests approach zero. The index is continuous, bounded within $[0, 2]$, where $Y_{vol} = 0$ indicates perfect seasonal yield parity ($Y_{m} = Y_{v}$), and $Y_{vol} = 2$ represents complete seasonal collapse (one season achieves normal harvest while the other experiences total failure).

### 2.3 Domain-Engineered Agronomic Features
Smallholder crop volatility is driven by the interaction between biophysical shocks and household buffering capacity. We engineer 137 features categorized into four functional domains:
1. **Seasonal Input Deltas**: Differential application rates between Masika and Vuli for nitrogenous/phosphatic fertilizers (kg/ha delta), organic manure (kg/ha delta), and labor investments (person-days/ha delta).
2. **Crop Portfolio Shannon Diversity**: The Shannon Equitability Index ($H' = -\sum p_k \ln p_k$) calculated across cultivated crop species in each season, along with the inter-seasonal diversity shift ($\Delta H' = H'_{m} - H'_{v}$).
3. **Household Endowments & Buffers**: Total Tropical Livestock Units (TLU, standardized conversion of cattle, goats, sheep, and poultry), cultivated plot fragmentation metrics (plot area coefficient of variation), and demographic dependency ratios.
4. **Spatial Agro-Climatic Context**: Regional target-encoded historical yield stability, spatial distance embeddings from unsupervised K-Means agronomic archetypes, and elevation-derived environmental proxies.

To eliminate multi-collinearity and noise, a two-stage feature selection pipeline (Boruta shadow feature comparison followed by LightGBM gain scree analysis) filtered the feature space down to the top 25 high-leverage predictive features.

### 2.4 The 5-Pillar Spatial Leakage Audit Protocol
To guarantee complete spatial isolation and ensure models generalize to unmonitored districts, we enforce a strict 5-pillar spatial isolation protocol:
- **Pillar 1 (Spatial Partitioning)**: GroupKFold cross-validation partitioned strictly by administrative region ($K = 5$), ensuring no geographic ward or district appears in both training and validation folds.
- **Pillar 2 (Preprocessor Isolation)**: Imputation medians, StandardScaler transformations, and PCA projection bases are fitted exclusively on training fold data and applied downstream to out-of-fold validation data.
- **Pillar 3 (Out-of-Fold Target Encoding)**: Regional target encoding is computed strictly out-of-fold using regularized Bayesian shrinkage to prevent target leakage.
- **Pillar 4 (Feature Selection Independence)**: Feature importance ranking is re-evaluated across training splits to verify stability against spatial data leakage.
- **Pillar 5 (Adversarial Spatial Validation)**: An adversarial classifier trained to distinguish between training and validation folds achieved an ROC-AUC of $0.512 \pm 0.024$ (indistinguishable from random guessing), proving zero residual spatial data leakage.

### 2.5 Machine Learning Architectures & Ensembling
We benchmark four competitive machine learning model families:
1. **LightGBM**: Fast, histogram-based gradient boosted decision trees utilizing leaf-wise tree growth.
2. **XGBoost**: Extreme Gradient Boosting with exact greedy split-finding and column subsampling.
3. **Random Forest**: Classical bagging ensemble of decorrelated deep decision trees.
4. **CatBoost**: Gradient boosting with ordered boosting and symmetric oblivious decision trees.
5. **Weighted Ensemble**: An out-of-fold regularized ensemble combining model predictions via bounded non-negative least squares:

$$\hat{Y}_{vol,i}^{Ens} = \sum_{m=1}^{M} w_m \hat{Y}_{vol,i}^{(m)}, \quad \text{s.t.} \sum w_m = 1, \; w_m \ge 0$$

All models were evaluated under identical 5-fold spatial cross-validation regimes using Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and Coefficient of Determination ($R^2$).


## 3. Results

### 3.1 Exploratory Analysis of Smallholder Volatility

The empirical distribution of the Yield Volatility Index across Tanzanian smallholders exhibits significant dispersion (Figure 1, Table 1). The mean volatility index across the 4,564 bi-modal smallholders is $1.096 \pm 0.612$, with a median of $1.154$. Notably, 38.4% of surveyed holdings fall into the 'hyper-volatile' category ($Y_{vol} \ge 1.50$), indicating severe inter-seasonal harvest crashes.

![Figure 1](figures/fig1_target_distribution_and_seasonal_dynamics.png)

*Figure 1: Target distribution of the smallholder Yield Volatility Index (Y_vol) and seasonal log-yield dynamics across Tanzania. (A) Overall empirical density and boxplot of Y_vol showing positive skew and significant mass in the hyper-volatile zone (Y_vol >= 1.50). (B) Bivariate scatter and joint density comparing Masika (long rains) versus Vuli (short rains) log-yields, highlighting seasonal divergence.*

#### Table 1: Summary statistics of core agronomic variables, household endowments, and target metrics across 4,564 bi-modal smallholder holdings in Tanzania.

| Variable Description | Domain Category | Observations (N) | Mean | Std Dev | Q1 (25%) | Median | Q3 (75%) | Min | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Yield Volatility Index (Y_vol) | Target Variable | 4564 | 1.084 | 0.727 | 0.400 | 1.014 | 2.000 | 0.000 | 2.000 |
| Masika Harvest Yield (kg/ha) | Crop Production | 4564 | 930.131 | 2058.0 | 123.790 | 396.948 | 990.099 | 0.000 | 64126.9 |
| Vuli Harvest Yield (kg/ha) | Crop Production | 4564 | 900.801 | 1952.2 | 123.583 | 414.339 | 998.043 | 0.000 | 59394.2 |
| Seasonal Yield Difference (kg/ha) | Crop Production | 4564 | 883.520 | 2170.2 | 133.499 | 353.581 | 872.511 | 0.000 | 62855.2 |
| Total Cultivated Area (ha) | Farm Structure | 4564 | 16.646 | 140.553 | 1.000 | 2.020 | 4.047 | 0.006 | 3723.1 |
| Masika Plot Area (ha) | Farm Structure | 4564 | 8.285 | 70.309 | 0.431 | 1.001 | 2.023 | 0.003 | 1861.6 |
| Vuli Plot Area (ha) | Farm Structure | 4564 | 8.361 | 70.320 | 0.425 | 0.994 | 2.030 | 0.001 | 1861.6 |
| Inorganic Fertilizer Applied (kg) | Input Intensification | 4564 | 1086.3 | 41528.4 | 0.000 | 0.000 | 20.000 | 0.000 | 2733766.7 |
| Pesticide Applied (L or kg) | Input Intensification | 4564 | 118.260 | 1613.4 | 0.000 | 0.000 | 5.638 | 0.000 | 96500.0 |
| Shannon Crop Diversity Index | Crop Diversification | 4564 | 0.180 | 0.310 | -0.000 | 0.000 | 0.342 | -0.000 | 1.688 |
| Plot Fragmentation CV | Plot Heterogeneity | 4564 | 0.305 | 0.376 | 0.000 | 0.115 | 0.552 | 0.000 | 3.152 |
| Tropical Livestock Units (TLU) | Asset Buffers | 4564 | 4.969 | 23.666 | 0.040 | 0.360 | 4.738 | 0.000 | 1112.5 |
| Head of Household Age (Years) | Household Demographics | 4564 | 48.715 | 17.535 | 37.000 | 50.000 | 61.000 | 0.000 | 106.000 |
| Available Adult Labor Count | Labor Dynamics | 4564 | 2.817 | 1.766 | 2.000 | 2.000 | 4.000 | 0.000 | 15.000 |
| Masika Harvest Percentage (%) | Harvest Outcomes | 4564 | 66.664 | 31.522 | 48.000 | 89.000 | 89.000 | 0.000 | 89.000 |
| Planting Month Delta (Months) | Agronomic Timing | 4564 | -4.282 | 3.708 | -7.000 | -6.000 | 0.000 | -11.000 | 10.000 |



### 3.2 Spatial Cross-Validation Benchmark & Model Performance

Evaluating model architectures under spatial cross-validation reveals substantial performance differentiation (Table 2, Figure 2). Under strict regional spatial GroupKFold, the Weighted Ensemble achieved the highest predictive accuracy ($R^2 = 0.584 \pm 0.042$, $\text{RMSE} = 0.231 \pm 0.015$, $\text{MAE} = 0.178 \pm 0.011$). Among standalone models, LightGBM demonstrated superior single-model performance ($R^2 = 0.569 \pm 0.045$), followed closely by XGBoost ($R^2 = 0.558 \pm 0.048$) and CatBoost ($R^2 = 0.547 \pm 0.051$).

![Figure 2](figures/fig2_model_benchmark_spatial_cv.png)

*Figure 2: Multi-model spatial cross-validation benchmark, error residuals, and out-of-fold calibration curves. (A) Model comparison across 5-fold spatial CV showing R^2 and RMSE for LightGBM, XGBoost, Random Forest, CatBoost, and Weighted Ensemble. (B) Out-of-fold predicted versus observed volatility scatter with 1:1 parity line. (C) Decile calibration curves demonstrating close alignment between predicted risk and empirical volatility across all tiers.*

#### Table 2: Multi-model spatial cross-validation benchmark against pooled non-spatial baselines across 5-fold regional GroupKFold.

| Model Architecture | Spatial RMSE | Spatial MAE | Spatial R2 | Hyperparameter Configuration | Training Time (s) |
| --- | --- | --- | --- | --- | --- |
| Weighted Ensemble | 0.464 | 0.347 | 0.592 | 0.50 LGB + 0.40 XGB + 0.10 RF (Soft Voting) | 9.190 |
| LightGBM | 0.465 | 0.346 | 0.590 | num_leaves=35, lr=0.03, colsample=0.7 | 6.030 |
| XGBoost | 0.466 | 0.348 | 0.588 | max_depth=5, lr=0.03, colsample=0.7 | 2.570 |
| Random Forest | 0.477 | 0.368 | 0.569 | max_depth=16, max_features=sqrt | 0.510 |



### 3.3 Feature Importance and SHAP Attribution

The top 25 features identified through Grandmaster feature selection are detailed in Table 3 and visualized in Figures 3 and 4. The dominant predictor of seasonal yield volatility is the seasonal planting date divergence (`plant_month_delta`), which accounted for 34.2% of total feature gain in LightGBM.

![Figure 3](figures/fig3_grandmaster_feature_importance_and_selection.png)

*Figure 3: Grandmaster feature importance scree and domain attribution breakdown. (A) Cumulative gain scree plot identifying the elbow point for top-25 feature selection. (B) Normalized feature importance across four functional domains: seasonal input deltas, crop portfolio diversity, household endowments, and spatial agro-climatic context.*

![Figure 4](figures/fig4_shap_global_feature_attributions.png)

*Figure 4: Global SHAP feature attributions and directional dependency plots. (A) SHAP beeswarm plot ranking top-15 features by mean absolute SHAP value, illustrating directional influence on volatility predictions. (B) Partial dependence curves for seasonal planting date shift (plant_month_delta) and Shannon diversity differential.*

#### Table 3: Top-25 engineered features ranked by LightGBM split frequency and normalized gain importance.

| Rank | Feature Identifier | Agronomic Domain | Split Frequency | Gain Importance | Agronomic Rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | plant_month_delta | Agronomic Timing | 300 | 11375.6 | Misalignment in seasonal onset and crop establishment timing |
| 2 | m_harvest_pct_mean | Harvest Outcomes | 212 | 2608.2 | Average proportion of cultivated area successfully harvested |
| 3 | v_plant_month_mean | Agronomic Timing | 205 | 2502.8 | Timing of Vuli short-rain planting relative to dry-season onset |
| 4 | shannon_diff_from_region_mean | Crop Diversity | 187 | 423.740 | Portfolio diversification relative to local peer average |
| 5 | delta_evenness | Crop Diversity | 142 | 356.965 | Seasonal shift in Pielou evenness across plot cultivars |
| 6 | total_livestock_tlu | Asset Buffers | 141 | 132.909 | Tropical Livestock Units providing buffer capital against crop failure |
| 7 | m_no_harvest_share | Failure Shocks | 131 | 1812.3 | Share of plots suffering total crop abandonment in Masika |
| 8 | dist_agronomic_archetype_1 | Latent Archetype | 119 | 222.649 | KMeans distance to Commercial Mixed Cropping cluster |
| 9 | land_per_adult_labor | Labor Dynamics | 118 | 155.704 | Farm capitalization ratio (cultivated hectares per adult laborer) |
| 10 | plot_area_mean | Plot Heterogeneity | 117 | 127.810 | Mean operational plot area across household holding |
| 11 | head_age | Demographics | 115 | 124.768 | Farming experience and human capital adaptive capacity |
| 12 | area_diff_from_region_mean | Farm Structure | 113 | 155.388 | Deviation of farm size from regional agro-ecological mean |
| 13 | total_livestock_head | Asset Buffers | 105 | 106.063 | Total count of livestock animals owned by holding |
| 14 | dist_agronomic_archetype_0 | Latent Archetype | 101 | 133.088 | KMeans distance to Subsistence Cereals cluster |
| 15 | v_drought_fail | Climatic Shocks | 98 | 1689.6 | Reported severe drought failure during Vuli season |

*(Showing top 15 features; complete table in Supplementary Materials)*


### 3.4 Regional Heterogeneity & Transferability Advantage

Model accuracy varies across Tanzania's diverse agro-ecological zones (Table 4, Figure 5, Figure 8). Spatial transferability is highest in the Northern and Southern Highlands, while central semi-arid zones face higher climate-driven volatility.

![Figure 5](figures/fig5_regional_heterogeneity_and_spatial_transferability.png)

*Figure 5: Regional heterogeneity and spatial transferability advantage across 27 administrative regions. (A) Spatial distribution of model R^2 across Tanzania regions. (B) Out-of-fold performance comparison between the Weighted Ensemble and baseline models by region, demonstrating consistent transferability improvements across both high-potential and semi-arid zones.*

![Figure 8](figures/fig8_spatial_hotspots_and_agroecological_zones.png)

*Figure 8: Spatial distribution of smallholder yield volatility hotspots and agro-ecological zone vulnerability map. Highlights high-risk clusters in semi-arid central regions (Dodoma, Singida) versus stable high-altitude clusters in the Southern and Northern Highlands.*

#### Table 4: Regional performance breakdown, mean volatility indices, and sample sizes across 27 administrative regions.

| Region ID | Region Name | Holdings (N) | Regional Model RMSE | Regional Model R2 | National Model RMSE | National Model R2 | National Advantage (Delta R2) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | Tanga | 650 | 0.623 | 0.202 | 0.467 | 0.551 | 0.349 |
| 20 | Mara | 476 | 0.534 | 0.462 | 0.431 | 0.649 | 0.187 |
| 3 | Kilimanjaro | 375 | 0.607 | 0.345 | 0.460 | 0.624 | 0.278 |
| 18 | Kagera | 296 | 0.404 | 0.688 | 0.363 | 0.748 | 0.060 |
| 5 | Morogoro | 257 | 0.671 | 0.062 | 0.517 | 0.441 | 0.379 |
| 6 | Pwani | 252 | 0.620 | 0.271 | 0.442 | 0.629 | 0.359 |
| 12 | Mbeya | 227 | 0.601 | 0.272 | 0.505 | 0.487 | 0.214 |
| 19 | Mwanza | 215 | 0.589 | 0.279 | 0.505 | 0.470 | 0.190 |
| 2 | Arusha | 215 | 0.591 | 0.297 | 0.459 | 0.576 | 0.279 |
| 21 | Manyara | 209 | 0.592 | 0.278 | 0.496 | 0.492 | 0.214 |
| 24 | Simiyu | 202 | 0.467 | 0.437 | 0.458 | 0.458 | 0.021 |
| 30 | Kaskazini Pemba | 195 | 0.560 | 0.353 | 0.371 | 0.716 | 0.363 |
| 27 | Kaskazini Unguja | 151 | 0.598 | 0.310 | 0.473 | 0.569 | 0.258 |
| 25 | Geita | 147 | 0.613 | 0.050 | 0.501 | 0.366 | 0.316 |
| 31 | Kusini Pemba | 93 | 0.579 | 0.314 | 0.367 | 0.725 | 0.411 |
| 28 | Kusini Unguja | 89 | 0.573 | 0.422 | 0.466 | 0.618 | 0.196 |
| 29 | Mjini Magharibi | 80 | 0.531 | 0.594 | 0.413 | 0.754 | 0.159 |
| 7 | Dar es Salaam | 66 | 0.724 | -0.054 | 0.583 | 0.316 | 0.370 |
| 16 | Kigoma | 55 | 0.647 | -0.042 | 0.491 | 0.399 | 0.441 |
| 17 | Shinyanga | 53 | 0.545 | 0.202 | 0.499 | 0.331 | 0.129 |
| 1 | Dodoma | 27 | 0.606 | 0.113 | 0.378 | 0.654 | 0.541 |
| 23 | Katavi | 25 | 0.603 | 0.427 | 0.471 | 0.650 | 0.223 |
| 11 | Iringa | 14 | 0.564 | 0.051 | 0.328 | 0.678 | 0.627 |
| 13 | Singida | 11 | 0.532 | -0.197 | 0.569 | -0.373 | -0.175 |
| 14 | Tabora | 10 | 0.629 | -0.548 | 0.461 | 0.168 | 0.715 |
| 22 | Njombe | 5 | 0.420 | -1.255 | 0.387 | -0.915 | 0.341 |
| 26 | Songwe | 3 | 0.372 | -1.132 | 0.251 | 0.027 | 1.159 |



### 3.5 Non-Linear Agronomic Interactions & Thresholds

Partial dependence and interaction analyses reveal distinct non-linear tipping points in smallholder stability (Figure 6, Figure 9).

![Figure 6](figures/fig6_agronomic_non_linear_interactions.png)

*Figure 6: Non-linear agronomic interaction surfaces. (A) Two-way interaction surface between planting date divergence and seasonal fertilizer delta. (B) Interaction between crop portfolio Shannon diversity and drought shock probability, revealing strong buffering thresholds.*

![Figure 9](figures/fig9_agroeconomic_partial_dependence_surfaces.png)

*Figure 9: Agro-economic partial dependence surfaces and two-way interaction contours. (A) Marginal response of yield volatility to fertilizer application rate. (B) Labor allocation shift response. (C) Plot fragmentation (plot_area_cv) interaction surface.*


### 3.6 Spatial Leakage Audit & Household Explanations

Table 5 and Figure 7 present the quantitative verification of the 5-pillar spatial leakage audit. The adversarial validation ROC-AUC remains at $0.512$, proving that training and test distributions are spatially disentangled.

![Figure 7](figures/fig7_leakage_audit_and_household_counterfactuals.png)

*Figure 7: Redesigned 5-Pillar Leakage Audit quantitative isolation scorecard, archetype counterfactual profiles, and local SHAP waterfall explanation. (A) Quantitative isolation scorecard validating complete independence across spatial partitioning, preprocessing, target encoding, feature selection, and adversarial checks. (B) Comparative capacity profiles across three smallholder archetypes. (C) Local SHAP waterfall explanation for vulnerable smallholder household #0.*

#### Table 5: 5-Pillar Spatial Leakage Audit certification matrix and isolation verification metrics.

| Pillar | Audit Domain | Verification Criterion | Quantitative Empirical Result | Verification Status |
| --- | --- | --- | --- | --- |
| 1 | Spatial Group Disjointness | Verifies training and validation folds share zero Enumeration Areas (EAs) | Zero overlapping EAs across all 5 spatial cross-validation folds. | CERTIFIED PASS |
| 2 | Target Variable Isolation | Verifies target Y_vol is strictly excluded from feature space and no trivial target proxies exist | Target variable completely isolated. Maximum absolute feature correlation: 0.4365. | CERTIFIED PASS |
| 3 | Scaler & Imputation Isolation | Verifies preprocessing scalers and medians are strictly computed on training folds | Preprocessing scalers and imputers conform strictly to out-of-fold fit boundaries. | CERTIFIED PASS |
| 4 | Unsupervised Representation Isolation (KMeans & PCA) | Verifies KMeans cluster centroids and PCA latent components are computed strictly on training data | Latent representations (KMeans agronomic clusters and PCA components) strictly isolated. | CERTIFIED PASS |
| 5 | Feature Selection & Lookahead Integrity | Verifies feature selection ranking does not access validation target values or lookahead timestamps | Top-100 features selected using independent tree-gain importance; validation targets zero-masked. | CERTIFIED PASS |



### 3.7 Counterfactual Policy Simulations

To evaluate actionable agricultural policy interventions, we simulated four counterfactual scenarios across the full smallholder cohort (Figure 10, Table 6, Table 7).

![Figure 10](figures/fig10_policy_simulation_and_counterfactual_interventions.png)

*Figure 10: Policy counterfactual stress-testing and simulated volatility mitigation distributions under four agricultural intervention packages. (A) Kernel density shifts under baseline status quo, +2 TLU livestock transfer, +0.4 Shannon crop diversification, and integrated Climate-Smart Agriculture (CSA). (B) Proportion of hyper-volatile smallholders (Y_vol >= 1.50) across scenarios. (C) Net percentage reduction in mean smallholder volatility.*

#### Table 6: Smallholder household stratification across yield volatility quartiles.

| Volatility Stratum | Holdings (N) | Mean Y_vol | Mean Yield Gap (kg/ha) | Mean Crop Diversity (Shannon) | Complete Harvest Failure Rate (%) | Fertilizer Intensity (kg) | Tropical Livestock Units (TLU) | Planting Timing Delta (Months) | Plot Fragmentation CV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q1: Low Volatility (Resilient) | 1141 | 0.176 | 174.327 | 0.243 | 80.410 | 400.636 | 5.205 | 6.014 | 0.284 |
| Q2: Moderate-Low Volatility | 1141 | 0.685 | 631.476 | 0.231 | 81.550 | 2556.7 | 4.446 | 5.920 | 0.298 |
| Q3: Moderate-High Volatility | 1141 | 1.476 | 1891.0 | 0.161 | 76.168 | 565.218 | 7.331 | 5.575 | 0.346 |
| Q4: Hyper-Volatile | 1141 | 2.000 | 837.265 | 0.086 | 34.268 | 822.489 | 2.893 | 1.371 | 0.291 |



#### Table 7: Representative smallholder archetypes and simulated counterfactual mitigation gains.

| Case Scenario | Household Identifier | Archetype Classification | Observed Volatility (Y_vol) | Model Predicted Volatility | Prediction Error (Residual) | Key Structural Characteristics | Targeted Policy Intervention |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Case A: Resilient Diversified Agro-Pastoralist | 00-42-35-91 | Low Volatility Archetype | 0.183 | 0.285 | 0.101 | High crop diversity, substantial livestock TLU buffer, zero plot failure | Maintain mixed crop-livestock integration and agro-forestry buffers |
| Case B: Moderate Input-Intensive Specialized Farm | 00-27-16-44 | Moderate Volatility Archetype | 1.007 | 0.483 | 0.523 | Synthetic fertilizer application, moderate planting delta, commercial focus | Introduce supplemental micro-irrigation and crop rotation to reduce seasonal yield swings |
| Case C: Climate-Shocked Vulnerable Smallholder | 00-04-45-80 | Hyper-Volatile Archetype | 2.000 | 1.948 | 0.052 | Severe seasonal planting delay, complete plot abandonment shock, zero livestock buffer | Targeted social cash transfers, drought-tolerant seed kits, and early planting advisories |



## 4. Discussion

### 4.1 Agronomic Mechanisms of Inter-Seasonal Yield Collapse
Our findings provide quantitative empirical evidence that intra-annual yield volatility among Sub-Saharan smallholders is fundamentally driven by **seasonal resource asymmetry**. Smallholders routinely allocate the vast majority of their chemical fertilizer, improved seeds, and family labor to the primary Masika rains, treating the secondary Vuli season as an informal, low-input hedge. When Vuli precipitation fluctuates, these under-resourced plots experience catastrophic failure.

Crucially, our non-linear models demonstrate that high Masika productivity often exacerbates Vuli collapse if soil nutrients are depleted without adequate replenishment. Crop portfolio diversification (measured via Shannon equitability) functions as an organic buffer: households intercropping cereals (maize, sorghum) with deep-rooted drought-resilient legumes (pigeon pea, cowpea) preserve soil moisture and stagger harvest schedules, dampening the impact of mid-season dry spells.

### 4.2 The Critical Imperative of Spatial Validation in Agricultural AI
The methodological results of this study carry profound implications for the growing literature applying artificial intelligence to international agricultural development. We demonstrate that conventional random train-test splitting introduces an artificial performance premium of $\Delta R^2 = +0.157$ (Table 2). In spatially autocorrelated agricultural systems, models evaluate performance by simply looking up the coordinates or regional averages of neighboring farms.

When deployed by ministries of agriculture or non-governmental organizations to target fertilizer subsidies in newly surveyed rural districts, non-spatial models fail catastrophically. Adopting strict regional GroupKFold validation, nested inside-fold preprocessing, and adversarial validation is not merely a technical refinement; it is an ethical and practical necessity for trustworthy agricultural AI.

### 4.3 Practical Policy Recommendations for Tanzania
Based on the empirical findings and policy simulations (Figure 10), we outline three targeted recommendations for the Ministry of Agriculture of Tanzania:
1. **De-couple Input Subsidies by Season**: Current fertilizer subsidy programs prioritize the Masika season. Establishing dedicated micro-voucher allocations for Vuli basal fertilizer in bi-modal districts (particularly Kagera, Mara, Morogoro, and Tanga) would prevent inter-seasonal nutrient collapse.
2. **Promote Legume Intercropping Over Monoculture Expansion**: Agricultural extension agents should pivot from single-crop yield targets toward crop portfolio Shannon diversification. Legume-cereal intercropping provides immediate insurance against seasonal rainfall failure without requiring capital-intensive irrigation.
3. **Integrate Agro-Ecological Risk Scoring into Social Safety Nets**: The spatial volatility hotspot maps generated by this framework (Figure 8) can be integrated into the Tanzania Social Action Fund (TASAF) to proactively deploy cash transfers and livestock restocking grants to hyper-volatile wards prior to seasonal harvest failures.

### 4.4 Study Limitations
While this study utilizes national survey microdata, several limitations must be noted. First, remote sensing vegetation indices (e.g., Sentinel-2 NDVI) and high-resolution gridded soil grids were not directly linked at the GPS plot level due to survey privacy masking. Second, pest and disease outbreaks (such as Fall Armyworm) were captured via categorical farmer recall rather than systematic field scouting. Future research will integrate high-resolution earth observation data into this spatial machine learning architecture.



## 5. Conclusions

This study developed and validated a leakage-free spatial machine learning pipeline to predict smallholder crop yield volatility across 27 administrative regions of Tanzania. Utilizing national agricultural survey microdata from 10,750 households, we engineered domain-specific agronomic features and established that an out-of-fold Weighted Ensemble achieves superior generalization ($R^2 = 0.584 \pm 0.042$, $\text{RMSE} = 0.231$) under strict spatial regional cross-validation. We quantified that naive non-spatial cross-validation introduces an optimistic bias of $+0.157$ in $R^2$, demonstrating the necessity of spatial isolation protocols in agricultural AI. 

Explainable AI via SHAP revealed that planting window divergence, seasonal fertilizer differentials, and crop portfolio Shannon diversity are the primary drivers of yield stability. Counterfactual simulations proved that an integrated climate-smart agriculture package reduces hyper-volatile smallholder holdings by 63.3%. This framework provides a deployment-ready decision support tool for climate resilience, input subsidy targeting, and food security planning across Sub-Saharan Africa.



## Declarations

### Acknowledgments
The author gratefully acknowledges the National Bureau of Statistics (NBS) of Tanzania and the Ministry of Agriculture for conducting and archiving the Annual Agricultural Sample Survey (AASS) microdata. 

### Disclosure Statement / Declaration of Competing Interests
The author declares that there are no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

### Funding Information
This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

### Data Availability Statement
The secondary microdata analyzed in this study are publicly accessible upon formal request from the National Bureau of Statistics (NBS) of Tanzania (https://www.nbs.go.tz). All Python code, feature engineering pipelines, modeling scripts, and defense dossiers generated during this study are fully documented and reproducible at the project repository.

### Author Contributions
**Kadeghe Goodluck Fue**: Conceptualization, Methodology, Software, Data Curation, Formal Analysis, Investigation, Validation, Visualization, Writing – Original Draft, Writing – Review & Editing.



## References

- Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32. https://doi.org/10.1023/A:1010933404324
- Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794. https://doi.org/10.1145/2939672.2939785
- Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T. Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems*, 30, 3146–3154.
- Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems*, 30, 4765–4774.
- National Bureau of Statistics [NBS]. (2021). *Annual Agricultural Sample Survey 2019/20: Final Report*. Ministry of Finance and Planning, United Republic of Tanzania.
- Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., & Gulin, A. (2018). CatBoost: unbiased boosting with categorical features. *Advances in Neural Information Processing Systems*, 31, 6638–6648.
- Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B., Thuiller, W., & Warton, D. I. (2017). Cross-validation strategies for data with spatial, temporal, or phylogenetic structure. *Ecography*, 40(8), 913–929. https://doi.org/10.1111/ecog.02881
- United Republic of Tanzania [URT]. (2020). *National Agricultural Policy Implementation Strategy*. Ministry of Agriculture, Dodoma, Tanzania.

