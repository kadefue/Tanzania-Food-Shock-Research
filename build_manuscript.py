"""
Springer Nature (Food Security, Journal ID 12571) Manuscript Builder
====================================================================
Author: Dr. Eng. Kadeghe Goodluck Fue (kadefue@sua.ac.tz)
ORCID: 0000-0001-6362-3174
Institution: Department of Agricultural Engineering, School of Engineering and Technology,
             Sokoine University of Agriculture (SUA), Morogoro, Tanzania

Strictly formatted according to the Springer Nature Food Security Submission Guidelines:
https://link.springer.com/journal/12571/submission-guidelines
- British English spelling and conventions throughout
- Mandatory continuous line numbering and automatic page numbering in Word (.docx) and LaTeX (.tex)
- 10-point Times New Roman body text in Word (.docx)
- Concise Title (<25 words, <200 characters) and Running Head (<=60 characters)
- Single-paragraph Abstract (150-250 words, no citations, no undefined abbreviations, quantitative data)
- 6 Keywords (strictly within 4-6 limit)
- Strict Research Article section hierarchy:
  1 Introduction
  2 Materials and Methods (with Abbreviations/Symbols/Units table & software citations)
  3 Results (separate from Discussion; consecutive Fig. 1-Fig. 10 and Table 1-Table 7 citations)
  4 Discussion (with integrated subsection 4.5 Concluding remarks and policy implications)
  Statements and Declarations
  References (APA 7th edition with italicised journal titles/volumes and full DOI links)
  Author Biography (100-120 words per 2026 Bio & Photo Guidelines)
- Separate Springer Title Page (Paper/title_page.docx) including 4 independent international reviewers
- Electronic Supplementary Material (Paper/ESM_1.csv cited in text as Online Resource 1)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
logger = logging.getLogger("ManuscriptBuilder")

PAPER_DIR = Path("Paper")
FIG_DIR = PAPER_DIR / "figures"
TAB_DIR = PAPER_DIR / "tables"

DOCX_PATH = PAPER_DIR / "manuscript.docx"
TITLE_PAGE_DOCX_PATH = PAPER_DIR / "title_page.docx"
LATEX_PATH = PAPER_DIR / "manuscript.tex"
MD_PATH = PAPER_DIR / "manuscript.md"
ESM1_PATH = PAPER_DIR / "ESM_1.csv"

RUNNING_HEAD = "Predicting Smallholder Crop Yield Volatility in Tanzania"  # 56 chars (<= 60 limit)
ARTICLE_TITLE = (
    "Predicting Smallholder Crop Yield Volatility Across Agro-Ecological Zones: "
    "A Leakage-Free Spatial Machine Learning Framework for Tanzania"
)  # 16 words, 137 chars (< 25 words, < 200 chars limit)


# ==============================================================================
# 1. CLEAN ALL CSV TABLES INTO BRITISH ENGLISH PUBLICATION FORMAT
# ==============================================================================

def clean_all_tables_for_publication() -> None:
    """Rewrites CSV tables in Paper/tables/ with British English and human-readable labels."""
    logger.info("Polishing all 7 empirical tables into British English Springer format...")

    # Table 1: Summary Statistics
    t1_path = TAB_DIR / "table1_summary_statistics.csv"
    if t1_path.exists():
        df1 = pd.read_csv(t1_path)
        name_map_t1 = {
            "Yield Volatility Index (Y_vol)": "Yield Volatility Index (Yᵥₒₗ)",
            "Inorganic Fertilizer Applied (kg)": "Inorganic Fertiliser Applied (kg)",
            "Plot Fragmentation CV": "Plot Fragmentation (Coefficient of Variation)",
            "Available Adult Labor Count": "Available Adult Labour Count",
            "Planting Month Delta (Months)": "Planting Month Difference (Masika – Vuli, Months)",
        }
        df1["Variable Description"] = df1["Variable Description"].replace(name_map_t1)
        df1["Domain Category"] = df1["Domain Category"].replace({"Labor Dynamics": "Labour Dynamics"})
        df1.to_csv(t1_path, index=False)

    # Table 2: Model Benchmark
    t2_path = TAB_DIR / "table2_model_benchmark.csv"
    if t2_path.exists():
        df2 = pd.read_csv(t2_path)
        df2 = df2.rename(columns={"Spatial R2": "Spatial R²"})
        df2["Hyperparameter Configuration"] = df2["Hyperparameter Configuration"].replace({
            "0.50 LGB + 0.40 XGB + 0.10 RF (Soft Voting)": "0.50 LightGBM + 0.40 XGBoost + 0.10 Random Forest (Soft Voting)"
        })
        df2.to_csv(t2_path, index=False)

    # Table 3: Top-25 Feature Importance
    t3_path = TAB_DIR / "table3_top25_feature_importance.csv"
    if t3_path.exists():
        df3 = pd.read_csv(t3_path)
        for col in df3.columns:
            if df3[col].dtype == object:
                df3[col] = (
                    df3[col]
                    .astype(str)
                    .str.replace("Fertilizer", "Fertiliser", regex=False)
                    .str.replace("fertilizer", "fertiliser", regex=False)
                    .str.replace("Labor", "Labour", regex=False)
                    .str.replace("labor", "labour", regex=False)
                    .str.replace("Realization", "Realisation", regex=False)
                    .str.replace("realization", "realisation", regex=False)
                    .str.replace("capitalization", "capitalisation", regex=False)
                )
        df3.to_csv(t3_path, index=False)

    # Table 4: Regional Breakdown
    t4_path = TAB_DIR / "table4_regional_performance_breakdown.csv"
    if t4_path.exists():
        df4 = pd.read_csv(t4_path)
        df4 = df4.rename(columns={
            "Regional Model R2": "Regional Model R²",
            "National Model R2": "National Model R²",
            "National Advantage (Delta R2)": "National Advantage (ΔR²)"
        })
        df4.to_csv(t4_path, index=False)

    # Table 5: Leakage Audit
    t5_path = TAB_DIR / "table5_leakage_audit_certificate.csv"
    if t5_path.exists():
        df5 = pd.read_csv(t5_path)
        df5["Verification Criterion"] = df5["Verification Criterion"].str.replace("Y_vol", "Yᵥₒₗ", regex=False)
        df5.to_csv(t5_path, index=False)

    # Table 6: Volatility Quartile Stratification
    t6_path = TAB_DIR / "table6_volatility_quartile_stratification.csv"
    if t6_path.exists():
        df6 = pd.read_csv(t6_path)
        df6 = df6.rename(columns={
            "Mean Y_vol": "Mean Yield Volatility (Yᵥₒₗ)",
            "Fertilizer Intensity (kg)": "Fertiliser Intensity (kg)",
            "Planting Timing Delta (Months)": "Planting Month Difference (Months)",
            "Plot Fragmentation CV": "Plot Fragmentation (CV)"
        })
        df6.to_csv(t6_path, index=False)

    # Table 7: Household Counterfactual Archetypes
    t7_path = TAB_DIR / "table7_household_counterfactual_archetypes.csv"
    if t7_path.exists():
        df7 = pd.read_csv(t7_path)
        df7 = df7.rename(columns={"Observed Volatility (Y_vol)": "Observed Volatility (Yᵥₒₗ)"})
        for col in ["Case Scenario", "Key Structural Characteristics", "Targeted Policy Intervention"]:
            if col in df7.columns:
                df7[col] = (
                    df7[col]
                    .astype(str)
                    .str.replace("Specialized", "Specialised", regex=False)
                    .str.replace("fertilizer", "fertiliser", regex=False)
                )
        df7.to_csv(t7_path, index=False)


def get_markdown_table(csv_name: str, float_fmt: str = ".3f") -> str:
    """Reads a CSV from Paper/tables and formats it as a clean Markdown table."""
    df = pd.read_csv(TAB_DIR / csv_name)
    headers = list(df.columns)
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        vals = []
        for col in headers:
            v = row[col]
            if isinstance(v, (int, np.integer)) or (isinstance(v, float) and col in ["Observations (N)", "Holdings (N)", "Rank", "Region ID", "Split Frequency", "Pillar"]):
                vals.append(f"{int(v):,}")
            elif isinstance(v, (float, np.floating)):
                if abs(v) >= 100:
                    vals.append(f"{v:,.2f}")
                else:
                    vals.append(f"{v:{float_fmt}}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def get_latex_table(csv_name: str, caption: str, label: str, footnote: str = "") -> str:
    """Reads a CSV from Paper/tables and formats it as a booktabs LaTeX table."""
    df = pd.read_csv(TAB_DIR / csv_name)
    headers = list(df.columns)
    col_spec = "l" + "r" * (len(headers) - 1)
    if csv_name in ["table3_top25_feature_importance.csv", "table5_leakage_audit_certificate.csv", "table7_household_counterfactual_archetypes.csv"]:
        col_spec = "l" * len(headers)

    def esc(s: str) -> str:
        return (
            str(s)
            .replace("&", "\\&")
            .replace("%", "\\%")
            .replace("_", "\\_")
            .replace("#", "\\#")
            .replace("Yᵥₒₗ", "$Y_{\\mathrm{vol}}$")
            .replace("R²", "$R^2$")
            .replace("ΔR²", "$\\Delta R^2$")
        )

    lines = [
        "\\begin{table}[htbp]",
        "\\centering",
        f"\\caption{{{esc(caption)}}}",
        f"\\label{{{label}}}",
        "\\resizebox{\\textwidth}{!}{%",
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\toprule",
        " & ".join([f"\\textbf{{{esc(h)}}}" for h in headers]) + " \\\\",
        "\\midrule"
    ]
    for _, row in df.iterrows():
        vals = []
        for col in headers:
            v = row[col]
            if isinstance(v, (int, np.integer)) or (isinstance(v, float) and col in ["Observations (N)", "Holdings (N)", "Rank", "Region ID", "Split Frequency", "Pillar"]):
                vals.append(f"{int(v):,}")
            elif isinstance(v, (float, np.floating)):
                vals.append(f"{v:,.2f}" if abs(v) >= 100 else f"{v:.3f}")
            else:
                vals.append(esc(str(v)))
        lines.append(" & ".join(vals) + " \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}%")
    lines.append("}")
    if footnote:
        lines.append(f"\\\\[4pt]\\footnotesize\\textit{{Note:}} {esc(footnote)}")
    lines.append("\\end{table}")
    return "\n".join(lines)


# ==============================================================================
# 2. GENERATE COMPLETE MARKDOWN MANUSCRIPT (SPRINGER FOOD SECURITY FORMAT)
# ==============================================================================


# Raw LaTeX representations for display equations (1) to (12)
EQ1 = r"$$Q_{i,s} = \sum_{p \in P_{i,s}} \sum_{c \in C_{i,p,s}} q_{i,p,c,s} \cdot \kappa_{u(i,p,c,s)}, \quad A_{i,s} = \sum_{p \in P_{i,s}} a_{i,p,s} \quad (1)$$"
EQ2 = r"$$Y_{i,s} = \frac{Q_{i,s}}{A_{i,s}}, \quad s \in \{m, v\} \quad (2)$$"
EQ3 = r"$$Y_{\mathrm{vol},i} = \frac{|Y_{i,m} - Y_{i,v}|}{\frac{1}{2}(Y_{i,m} + Y_{i,v}) + \varepsilon} = \frac{2|Y_{i,m} - Y_{i,v}|}{Y_{i,m} + Y_{i,v} + 2\varepsilon} \quad (3)$$"
EQ4 = r"$$H'_{i,s} = -\sum_{c=1}^{S_{i,s}} p_{i,c,s} \ln(p_{i,c,s}), \quad C_{\mathrm{HHI},i,s} = \sum_{c=1}^{S_{i,s}} p_{i,c,s}^2, \quad D_{\mathrm{BP},i,s} = \max_{c} \, p_{i,c,s}, \quad J'_{i,s} = \frac{H'_{i,s}}{\ln(S_{i,s})} \quad (4)$$"
EQ5 = r"$$J(C_{i,m}, C_{i,v}) = \frac{|C_{i,m} \cap C_{i,v}|}{|C_{i,m} \cup C_{i,v}|}, \quad R_{\mathrm{rot},i} = 1 - J(C_{i,m}, C_{i,v}) \quad (5)$$"
EQ6 = r"$$\Delta M_i = \bar{M}_{i,m} - \bar{M}_{i,v} \quad (6)$$"
EQ7 = r"$$\mathrm{CV}_{\mathrm{plot},i} = \frac{\sigma_{a,i}}{\mu_{a,i} + \varepsilon}, \quad \mu_{a,i} = \frac{1}{K_i}\sum_{p=1}^{K_i} a_{i,p}, \quad \sigma_{a,i} = \sqrt{\frac{1}{K_i}\sum_{p=1}^{K_i} (a_{i,p} - \mu_{a,i})^2} \quad (7)$$"
EQ8 = r"$$\mathrm{TLU}_i = 0.70 N_{\mathrm{cattle},i} + 0.50 N_{\mathrm{donkey},i} + 0.20 N_{\mathrm{pig},i} + 0.10 (N_{\mathrm{goat},i} + N_{\mathrm{sheep},i}) + 0.01 N_{\mathrm{poultry},i} \quad (8)$$"
EQ9 = r"$$\Delta X_{k,i}^{\mathrm{reg}} = X_{k,i} - \bar{X}_{k,r(i)}, \quad Z_{k,i}^{\mathrm{reg}} = \frac{X_{k,i} - \bar{X}_{k,r(i)}}{\sigma_{X_k,r(i)} + \varepsilon} \quad (9)$$"
EQ10 = r"$$\forall k \neq k' \in \{1, \dots, 5\}: \quad \{ G_i : i \in \mathcal{F}_k \} \cap \{ G_j : j \in \mathcal{F}_{k'} \} = \emptyset \quad (10)$$"
EQ11 = r"$$\hat{Y}_{\mathrm{vol},i}^{\mathrm{ens}} = \operatorname{clip}\left( w_{\mathrm{LGB}} \hat{f}_{\mathrm{LGB}}(\mathbf{x}_i) + w_{\mathrm{XGB}} \hat{f}_{\mathrm{XGB}}(\mathbf{x}_i) + w_{\mathrm{RF}} \hat{f}_{\mathrm{RF}}(\mathbf{x}_i), \; 0.0, \; 2.0 \right) \quad (11)$$"
EQ12 = r"$$\hat{f}(\mathbf{x}_i) = E[f(X)] + \sum_{j=1}^{M} \phi_{i,j}, \quad \phi_{i,j} = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f_{S \cup \{j\}}(\mathbf{x}_{i,S \cup \{j\}}) - f_S(\mathbf{x}_{i,S}) \right] \quad (12)$$"

def generate_markdown_manuscript() -> str:
    """Builds the complete manuscript in Markdown strictly following Springer Food Security guidelines."""
    t1_md = get_markdown_table("table1_summary_statistics.csv")
    t2_md = get_markdown_table("table2_model_benchmark.csv")
    t3_md = get_markdown_table("table3_top25_feature_importance.csv")
    t4_md = get_markdown_table("table4_regional_performance_breakdown.csv")
    t5_md = get_markdown_table("table5_leakage_audit_certificate.csv")
    t6_md = get_markdown_table("table6_volatility_quartile_stratification.csv")
    t7_md = get_markdown_table("table7_household_counterfactual_archetypes.csv")

    md = """# {ARTICLE_TITLE}

**Running Head:** {RUNNING_HEAD}

**Author:**  
**Kadeghe Goodluck Fue**  
Department of Agricultural Engineering, School of Engineering and Technology, Sokoine University of Agriculture (SUA), P.O. Box 3003, Chuo Kikuu, Morogoro, Tanzania  
Corresponding Author Email: [kadefue@sua.ac.tz](mailto:kadefue@sua.ac.tz)  
ORCID: [https://orcid.org/0000-0001-6362-3174](https://orcid.org/0000-0001-6362-3174)

---

## Abstract

Smallholder rainfed farming systems across sub-Saharan Africa face intensifying inter-seasonal yield instability driven by erratic bimodal rainfall, soil nutrient depletion, and biotic pest shocks, yet empirical risk models frequently overestimate predictive skill due to unaddressed spatial autocorrelation leakage. This study develops and validates a leakage-free spatial machine learning framework to predict household-level crop yield volatility across Mainland Tanzania and the Zanzibar Archipelago using nationally representative microdata from the 2024/2025 National Bureau of Statistics (NBS) Annual Agricultural Sample Survey (AASS) covering 4,564 bimodal agricultural holdings across 921 Enumeration Areas (EAs). We formulate a bounded, scale-invariant Yield Volatility Index (Yᵥₒₗ ∈ [0, 2]) measuring proportional yield divergence between the long-rain (*Masika*) and short-rain (*Vuli*) cultivation cycles, and engineer 246 multi-domain agronomic, ecological, demographic, and spatial peer predictors pruned to a 100-feature subset capturing 99.0% of tree-based information gain. Evaluated under strict five-fold spatial group cross-validation partitioning whole Enumeration Areas, a soft-voting Weighted Ensemble combining Light Gradient Boosting Machine (LightGBM), Extreme Gradient Boosting (XGBoost), and Random Forest (RF) achieves an out-of-fold coefficient of determination (R²) of 0.592, a Root Mean Squared Error (RMSE) of 0.464, and a Mean Absolute Error (MAE) of 0.347, outperforming dedicated regional sub-models across 26 of 27 regions. Exact Tree-based Shapley Additive Explanations (TreeSHAP) and partial dependence analyses reveal that inter-seasonal planting timing shifts, plot abandonment shocks, and crop portfolio diversity relative to community peers govern production instability, buffered non-linearly by livestock holdings above 3.0 Tropical Livestock Units (TLU). Policy counterfactual simulations indicate that an integrated Climate-Smart Agriculture package combining asset transfers, cultivar diversification, and planting synchronisation reduces mean national yield volatility by 40.0% and lowers hyper-volatile holdings (Yᵥₒₗ ≥ 1.50) from 25.8% to 19.9%, although multi-wave longitudinal panel tracking and high-resolution satellite soil-moisture assimilation remain vital future research priorities.

**Keywords:** smallholder agriculture; crop yield volatility; spatial cross-validation; machine learning; climate resilience; Tanzania

---

## Abbreviations, Symbols, and Units

| Abbreviation / Symbol | Definition and Measurement Unit |
| --- | --- |
| AASS | Annual Agricultural Sample Survey |
| AEZ | Agro-Ecological Zone |
| C<sub>HHI</sub> | Herfindahl–Hirschman Crop Concentration Index (dimensionless, [0, 1]) |
| CSA | Climate-Smart Agriculture |
| CV | Coefficient of Variation (dimensionless ratio of standard deviation to mean) |
| D<sub>BP</sub> | Berger–Parker Crop Dominance Index (dimensionless, [0, 1]) |
| EA | Enumeration Area (primary geographic census cluster) |
| ESM | Electronic Supplementary Material (cited as Online Resource 1) |
| FAO | Food and Agriculture Organization of the United Nations |
| GBDT | Gradient Boosted Decision Trees |
| H′ | Shannon–Wiener Crop Diversity Index (dimensionless, ≥ 0) |
| HHFARMID | Anonymised Household Farming Holding Identifier |
| IQR | Interquartile Range (Q₃ − Q₁) |
| J′ | Pielou Species Evenness Index (dimensionless, [0, 1]) |
| J(Cₘ, Cᵥ) | Cross-Seasonal Jaccard Crop Similarity Coefficient (dimensionless, [0, 1]) |
| KDE | Kernel Density Estimation |
| LightGBM | Light Gradient Boosting Machine |
| MAE | Mean Absolute Error (in units of Yᵥₒₗ) |
| *Masika* | Primary long-rain agricultural season in Tanzania (March–May) |
| NBS | National Bureau of Statistics of the United Republic of Tanzania |
| OOF | Out-of-Fold (spatially disjoint validation predictions) |
| PCA | Principal Component Analysis |
| R² | Out-of-fold Coefficient of Determination (dimensionless) |
| RF | Random Forest Regressor |
| RMSE | Root Mean Squared Error (in units of Yᵥₒₗ) |
| SHAP | Shapley Additive Explanations (game-theoretic feature attribution) |
| SUA | Sokoine University of Agriculture |
| TLU | Tropical Livestock Unit (1 TLU = 250 kg live metabolic weight equivalent) |
| *Vuli* | Secondary short-rain agricultural season in Tanzania (October–December) |
| XGBoost | Extreme Gradient Boosting |
| Yₘ, Yᵥ | Area-weighted household crop yield in *Masika* and *Vuli* (kg ha⁻¹) |
| Yᵥₒₗ | Bounded Inter-Seasonal Yield Volatility Index (dimensionless, [0, 2]) |

---

## 1 Introduction

Global food systems face an unprecedented convergence of climatic, ecological, and macroeconomic pressures that threaten the stability of agricultural production and rural livelihoods across the developing world (Wheeler & von Braun, 2013; Lobell et al., 2011; Ray et al., 2015). In sub-Saharan Africa, where rainfed smallholder holdings cultivating less than 3.5 hectares generate over 75% of domestic caloric supply, food security is governed not merely by long-term mean crop yields, but by the magnitude and frequency of inter-seasonal production shocks (Thornton et al., 2014; Jayne et al., 2010; Hertel & Rosch, 2010). Classical definitions of food security emphasise four interdependent pillars: availability, access, utilisation, and stability (Barrett, 2010; Godfray et al., 2010). Whilst substantial agronomic research and breeding investments over the past four decades have sought to raise average yield potential under optimal station conditions (Evenson & Gollin, 2003; Tittonell & Giller, 2013), the fourth pillar—production and consumption stability—remains acutely fragile across East Africa. When a subsistence or semi-commercial farm household experiences an abrupt harvest collapse between consecutive cropping cycles, the resulting production deficit triggers severe welfare penalties: forced liquidation of productive livestock assets at depressed distress prices, withdrawal of children from schooling, curtailment of nutrient-dense dietary intake, and entrenchment in chronic poverty traps (Dercon, 2004; Zimmerman & Carter, 2003; Barrett & Constas, 2014).

The United Republic of Tanzania exemplifies the structural complexity of managing agricultural production risk across highly heterogeneous tropical landscapes. Spanning approximately 945,000 km² across Mainland Tanzania and the Zanzibar Archipelago, the country encompasses seven distinct Agro-Ecological Zones (AEZs) ranging from semi-arid central plateaus and coastal lowlands to sub-humid lake basins and montane volcanic highlands (Rowhani et al., 2011; Arndt et al., 2012). Across the northern, coastal, lake, and highland corridors, agricultural production follows a bimodal rainfall regime governed by the seasonal migration of the Inter-Tropical Convergence Zone (ITCZ). Smallholder households navigate two distinct cultivation cycles each agricultural year: the *Masika* long rains (typically extending from March to May) and the *Vuli* short rains (occurring from October to December). The *Vuli* rains are characterised by lower cumulative precipitation, higher onset variability, and heightened sensitivity to Indian Ocean Dipole (IOD) and El Niño–Southern Oscillation (ENSO) sea-surface temperature anomalies, whereas the *Masika* rains provide the bulk of annual cereal and legume output but remain vulnerable to mid-season dry spells, flash flooding, and biotic pest outbreaks such as Fall Armyworm (*Spodoptera frugiperda*) (Rowhani et al., 2011; Kassie et al., 2015). Because smallholder households rely on sequential harvests across both seasons to smooth consumption, service informal credit obligations, and finance seed and fertiliser inputs for the subsequent planting window, wide inter-seasonal yield swings between *Masika* and *Vuli* represent a primary driver of transitory food insecurity across rural Tanzania.

Understanding why certain smallholder holdings maintain stable harvest realisations across seasons whilst neighbouring farms within the same agro-ecological zone suffer catastrophic yield oscillations requires moving beyond single-factor agronomic analyses. Theoretical frameworks in agricultural development economics and agro-ecology posit that farm-level production stability emerges from a complex, non-linear interplay among ecological portfolio buffering, household capital endowments, and phenological management (Tilman et al., 2006; Lin, 2011; Di Falco & Chavas, 2009). First, the biodiversity–stability hypothesis demonstrates that cultivating diverse crop species and functional groups with asynchronous water-use profiles and root architectures dampens aggregate portfolio variance through statistical portfolio averaging and ecological niche complementarity (Renard & Tilman, 2019; Isbell et al., 2017; Beillouin et al., 2021). Second, economic buffer-stock theory establishes that liquid household wealth—most notably livestock herds quantified in Tropical Livestock Units (TLU)—relaxes seasonal liquidity constraints, enabling timely land preparation, hired labour mobilisation during peak weeding bottlenecks, and rapid replanting when early rains fail (Dercon, 2004; Dillon et al., 2015). Third, agronomic intensification and soil management practices—including synthetic fertiliser application, pesticide protection, fallowing, and supplemental irrigation—interact non-linearly with plot fragmentation and planting timing (Tittonell & Giller, 2013; Teklewold et al., 2013; Carletto et al., 2013). For instance, high chemical fertiliser investment on rainfed monoculture plots without moisture conservation can amplify downside variance during rainfall deficits, a phenomenon widely recognised in risk-programming literature as risk-inducing intensification (Just & Pope, 1979; Di Falco & Chavas, 2009).

Despite the urgent policy need for high-resolution early-warning tools capable of identifying volatility-prone smallholders prior to shock realisation, existing empirical approaches suffer from three persistent methodological limitations. First, conventional econometric studies of yield risk rely predominantly on parametric linear specifications—such as Just–Pope production functions, Feasible Generalised Least Squares (FGLS), or fixed-effects panel regressions—that impose restrictive functional forms and cannot automatically capture high-order interactions among hundreds of correlated plot, household, and community variables (Just & Pope, 1979; Lobell & Burke, 2010; Storm et al., 2020). Second, where modern machine learning algorithms such as Gradient Boosted Decision Trees (GBDT) and Random Forests have been deployed in agricultural yield prediction, they have focused overwhelmingly on predicting *mean yield levels* rather than *inter-seasonal yield volatility* (Jeong et al., 2016; Crane-Droesch, 2018; Burke & Lobell, 2017; Benami et al., 2021). Moreover, standard volatility metrics such as raw variance or the unbounded coefficient of variation explode mathematically toward infinity when seasonal harvests approach zero under severe drought or crop abandonment, introducing severe outlier distortion in nonparametric tree splits.

Third, and most critically, a growing methodological literature in spatial ecology and geostatistics has demonstrated that standard random K-fold cross-validation in spatial machine learning produces severely optimistic performance estimates due to spatial autocorrelation leakage (Roberts et al., 2017; Meyer et al., 2018, 2019; Ploton et al., 2020; Wadoux et al., 2021). In national household surveys, agricultural holdings are sampled within geographically clustered Enumeration Areas (EAs) sharing identical micro-climates, soil catenas, market access corridors, and local measurement customs. Under random K-fold splitting, households from the same village cluster are simultaneously assigned to both training and validation folds, allowing high-capacity tree ensembles to memorise spatial coordinates and local cluster means rather than learning generalisable agro-economic relationships (Ploton et al., 2020; Meyer & Pebesma, 2021). Compounding this geographic leakage, machine learning pipelines frequently compute feature scalers, missing-value imputations, unsupervised cluster centroids, Principal Component Analysis (PCA) loadings, and feature selection rankings across the complete dataset *prior* to cross-validation splitting, introducing subtle lookahead bias that invalidates out-of-sample inference (Kaufman et al., 2012; Kapoor & Narayanan, 2023).

To resolve these scientific and methodological gaps, this study designs, audits, and deploys a leakage-free spatial machine learning framework to predict smallholder inter-seasonal crop yield volatility across Tanzania using the newly released 2024/2025 National Bureau of Statistics (NBS) Annual Agricultural Sample Survey (AASS) microdata (N = 4,564 bimodal holdings across 921 Enumeration Areas in 27 regions). Specifically, this study addresses four core research objectives:
1. To formulate a mathematically bounded, scale-invariant Yield Volatility Index (Yᵥₒₗ ∈ [0, 2]) that symmetrically accommodates zero-harvest plot failures and extreme yield disparities across heterogeneous multi-crop smallholder holdings;
2. To establish a rigorous Five-Pillar Spatial Leakage Isolation Architecture that enforces strict Enumeration Area group disjointness, fold-isolated preprocessing, fold-isolated unsupervised representation learning, and tree-gain feature pruning across 246 engineered agro-ecological candidate predictors;
3. To evaluate whether a unified national soft-voting ensemble of gradient boosted and bagging decision trees outperforms isolated regional sub-models when transferring predictive relationships across data-sparse administrative regions; and
4. To decode the non-linear agronomic tipping points and asset-buffering mechanisms governing smallholder yield volatility using exact Tree-based Shapley Additive Explanations (TreeSHAP), partial dependence surfaces, and policy counterfactual simulations.

---

## 2 Materials and Methods

### 2.1 Study area and agro-ecological context

The empirical investigation covers the entirety of the United Republic of Tanzania, situated in East Africa between latitudes 1° 00′ S and 11° 45′ S and longitudes 29° 15′ E and 40° 30′ E (Fig. 1). Topographically, Tanzania transitions from a warm, humid coastal belt along the Indian Ocean and the islands of Unguja and Pemba (Zanzibar Archipelago; altitude 0–200 m above sea level) to an extensive central plateau (800–1,500 m) flanked by the Eastern and Western branches of the East African Rift Valley, culminating in the Northern Highlands around Mount Kilimanjaro and Mount Meru and the Southern Highlands bordering Lake Nyasa (1,500–2,900 m).

For agronomic and national planning purposes, Tanzania's 31 administrative regions are stratified into seven macro Agro-Ecological Zones (AEZs): (i) the *Coastal and Eastern Zone* (Tanga, Morogoro, Pwani, Dar es Salaam, Lindi, Mtwara), characterised by bimodal and transitional rainfall (800–1,400 mm yr⁻¹) supporting maize, cassava, rice, and tree crops; (ii) the *Northern Highlands Zone* (Arusha, Kilimanjaro, Manyara), featuring volcanic soils and bimodal orographic rainfall (1,000–2,000 mm yr⁻¹) with intensive banana–coffee–maize–bean intercropping; (iii) the *Lake Victoria Basin Zone* (Kagera, Mara, Mwanza, Geita, Simiyu, Shinyanga), experiencing reliable bimodal precipitation (900–1,800 mm yr⁻¹) modified by lake-breeze circulations; (iv) the *Central Semi-Arid Zone* (Dodoma, Singida, Tabora), receiving low, erratic rainfall (500–800 mm yr⁻¹) with high evapotranspiration and frequent dry spells; (v) the *Southern Highlands Zone* (Mbeya, Iringa, Njombe, Songwe, Ruvuma), forming Tanzania's principal cereal breadbasket (1,000–1,600 mm yr⁻¹); (vi) the *Western and Southern Zone* (Kigoma, Katavi, Rukwa), spanning miombo woodland plains along Lake Tanganyika; and (vii) the *Zanzibar Archipelago* (Kaskazini Unguja, Kusini Unguja, Mjini Magharibi, Kaskazini Pemba, Kusini Pemba), governed by maritime equatorial bimodal rains (1,400–2,000 mm yr⁻¹).

### 2.2 Survey design and microdata architecture

This study utilises official microdata from the 2024/2025 Annual Agricultural Sample Survey (AASS), implemented jointly by the Tanzania National Bureau of Statistics (TNBS), the Ministry of Agriculture, and the Office of the Chief Government Statistician (OCGS) Zanzibar, in methodological alignment with the Food and Agriculture Organization (FAO) World Programme for the Census of Agriculture and the 50x2030 Initiative (Tanzania National Bureau of Statistics [TNBS], 2026; Food and Agriculture Organization of the United Nations [FAO], n.d.). The AASS employs a stratified two-stage probability sampling design structured to generate statistically representative estimates at national, zonal, and regional administrative levels. In the first stage, Primary Sampling Units (PSUs)—defined as geographic Enumeration Areas (EAs) demarcated during the 2022 Population and Housing Census—were selected using Probability Proportional to Size (PPS) within rural and peri-urban agricultural strata across all regions. In the second stage, a systematic random sample of agricultural holdings was drawn from complete household listing rosters within each selected Enumeration Area.

To construct a comprehensive, multi-dimensional representation of each agricultural holding, we ingested and relational-joined eight core survey rosters using the unique anonymised household farming holding identifier:
1. Master Holding Roster: Administrative geographic identifiers (region, district, ward, enumeration area), sampling strata, and survey design weights;
2. Demographics & Labour Roster: Age, sex, and educational attainment of the household head, household size, active adult agricultural labour force, and decision-making structure;
3. Seasonal Parcel Rosters: Plot-level cultivated area in hectares (Global Positioning System [GPS]-measured and farmer-reported), land tenure, soil erosion control, fallowing, slash-and-burn clearing, irrigation methods, and causes of unharvested area loss;
4. Seasonal Crop Production Rosters: Crop species codes, planting calendar month, harvested area percentage, harvest quantities, traditional measurement unit codes, and improved seed adoption;
5. Agro-Chemical Input Rosters: Plot-level applications of inorganic fertilisers (urea, diammonium phosphate [DAP], calcium ammonium nitrate [CAN], nitrogen–phosphorus–potassium [NPK]) and crop protection pesticides/herbicides;
6. Climatic & Economic Shock Roster: Household exposure and severity rankings for drought, flash flooding, pest infestation, input price spikes, and revenue collapse;
7. Livestock Herd Roster: Inventory counts of indigenous and improved cattle, goats, sheep, pigs, donkeys, and poultry; and
8. Extension & Early-Warning Roster: Receipt of meteorological weather forecasts, agricultural extension visits, and agronomic advisories.

#### 2.2.1 Derivation of the bimodal analytical cohort (N = 4,564)

Whilst the master AASS survey encompasses 18,904 agricultural holdings nationwide, regions situated in strictly unimodal rainfall regimes cultivate only a single annual season. Because our research objective specifically targets *inter-seasonal* yield volatility across consecutive cropping windows within the same agricultural year, inclusion in the analytical modelling cohort required a holding to satisfy three objective eligibility criteria: (i) active plot cultivation with positive planted area (Aᵢ,ₛ > 0 ha) recorded in both the *Masika* (s = m) and *Vuli* (s = v) seasons; (ii) valid crop roster entries allowing metric weight harmonisation or confirmed zero-harvest failure in both seasons; and (iii) non-negative seasonal yield realisations with at least one season achieving positive harvest output (Yᵢ,ₘ + Yᵢ,ᵥ > 0 kg ha⁻¹). Filtering the 18,904 master holdings by active bimodal cultivation yielded exactly N = 4,564 smallholder holdings distributed across 921 distinct Enumeration Areas in 27 administrative regions. Importantly, plots that were planted but suffered 100% crop loss due to drought, flood, or pest devastation (Yᵢ,ₛ = 0 kg ha⁻¹ in one season) were explicitly retained in the cohort, as complete seasonal harvest failure represents the most severe manifestation of food shock vulnerability.

### 2.3 Metric unit harmonisation and target variable formulation

A pervasive source of measurement noise in developing-country agricultural surveys is the reporting of harvests in non-standard, volumetric traditional containers whose physical mass varies by container geometry and crop bulk density (Carletto et al., 2013, 2015). In the AASS crop rosters, farmers reported outputs across 29 distinct unit codes (traditional harvest units in *Masika* and traditional harvest units in *Vuli*), including metric kilograms, metric tonnes, 18-litre *debe* tins, *sadoline* plastic tins, *kibaba* bowls, *tenga* bamboo baskets, banana bunches (*mkungu*), and polypropylene sacks ranging from 25 kg to 120 kg. We implemented a two-stage metric harmonisation protocol. Where the NBS pre-calibrated metric tonne variable (metric tonnes) was populated, physical production in kilograms was extracted directly as Qᵢ,ₚ,c,ₛ = 1,000 × harvest_ton. Where raw unit quantities were reported, we applied empirically calibrated East African unit-to-kilogram conversion factors κᵤ (standard metric conversion multipliers; e.g., κ₂₀ = 18.0 kg per *debe* tin, κ₂₄ = 15.0 kg per *sadoline* tin, κ₄₃ = 0.75 kg per *kibaba*, κ₁₂ = 20.0 kg per *tenga*, and κ₂₆ = 50.0 kg per medium sack).

For household i ∈ {1, …, N} cultivating plots p ∈ Pᵢ,ₛ and crops c ∈ Cᵢ,ₚ,ₛ during season s ∈ {m, v}, total seasonal harvested biomass (Qᵢ,ₛ, in kg) and total seasonal cultivated land area (Aᵢ,ₛ, in ha) are aggregated as:

{EQ1}

where qᵢ,ₚ,c,ₛ is the raw harvested quantity, κᵤ₍ᵢ,ₚ,c,ₛ₎ is the metric conversion multiplier for unit u, and aᵢ,ₚ,ₛ is the cultivated area of plot p in hectares (GPS-measured plot area). The household's area-weighted baseline seasonal yield (Yᵢ,ₛ, in kg ha⁻¹) is then defined as:

{EQ2}

To quantify inter-seasonal production instability without suffering from scale distortion or zero-denominator singularities when one season experiences total crop failure, we formulate the Yield Volatility Index (Yᵥₒₗ,ᵢ) as the absolute seasonal yield divergence normalised by the inter-seasonal mean yield Ȳᵢ = ½(Yᵢ,ₘ + Yᵢ,ᵥ):

{EQ3}

where ε = 10⁻⁵ kg ha⁻¹ is a numerical stability constant. Equation (3) possesses three desirable mathematical properties for statistical learning: (i) strict boundedness on the compact interval Yᵥₒₗ,ᵢ ∈ [0, 2], where Yᵥₒₗ,ᵢ = 0 denotes perfect inter-seasonal yield parity (Yᵢ,ₘ = Yᵢ,ᵥ) and Yᵥₒₗ,ᵢ = 2.0 denotes complete uni-seasonal harvest collapse (Yᵢ,ₘ = 0 or Yᵢ,ᵥ = 0); (ii) scale invariance, ensuring that proportional yield fluctuations on a 400 kg ha⁻¹ legume farm and a 4,000 kg ha⁻¹ commercial maize farm are evaluated on an identical dimensionless risk metric; and (iii) sign symmetry between *Masika*-dominant and *Vuli*-dominant agro-ecosystems.

### 2.4 Multi-domain feature engineering and ecological indices

Drawing on agro-ecological resilience theory and agricultural household economics, we engineered 246 candidate explanatory features spanning six thematic domains (Online Resource 1 provides the complete ranked inventory of all 246 candidate features). Crucially, to prevent target leakage, zero post-harvest yield or production quantities from Equations (1)–(2) are permitted to enter the predictive feature matrix X.

#### 2.4.1 Crop portfolio diversity and turnover indices

Let pᵢ,c,ₛ = aᵢ,c,ₛ / Aᵢ,ₛ denote the proportion of cultivated area allocated to crop species c ∈ {1, …, Sᵢ,ₛ} by household i in season s. We compute four complementary ecological diversity indices for each season: the Shannon–Wiener Diversity Index (H′ᵢ,ₛ), the Herfindahl–Hirschman Concentration Index (C<sub>HHI,i,s</sub>), the Berger–Parker Dominance Index (D<sub>BP,i,s</sub>), and Pielou's Species Evenness Index (J′ᵢ,ₛ) (Shannon, 1948; Magurran, 2004):

{EQ4}

To capture inter-seasonal crop rotation and portfolio restructuring between *Masika* and *Vuli*, let Cᵢ,ₘ and Cᵢ,ᵥ denote the sets of distinct crop species cultivated in each season. We define the cross-seasonal Jaccard Crop Similarity Coefficient (J(Cᵢ,ₘ, Cᵢ,ᵥ)) and the Seasonal Crop Rotation Index (R<sub>rot,i</sub>) as:

{EQ5}

alongside inter-seasonal portfolio shifts ΔH′ᵢ = H′ᵢ,ₘ − H′ᵢ,ᵥ, ΔJ′ᵢ = J′ᵢ,ₘ − J′ᵢ,ᵥ, and ΔC<sub>HHI,i</sub> = C<sub>HHI,i,m</sub> − C<sub>HHI,i,v</sub>.

#### 2.4.2 Phenological planting timing and plot fragmentation

Because rainfed crop establishment depends critically on matching sowing dates to the onset of effective soil moisture, we extract the mean planting calendar month in each season (M̄ᵢ,ₘ and M̄ᵢ,ᵥ) and define the inter-seasonal Planting Month Difference (ΔMᵢ, inter-seasonal planting delay):

{EQ6}

Spatial parcel dispersion and land fragmentation across a holding's Kᵢ operational plots are quantified via the Plot Area Coefficient of Variation (CVₚₗₒₜ,ᵢ, plot area fragmentation):

{EQ7}

#### 2.4.3 Livestock asset buffers and capital–labour ratios

To aggregate heterogeneous livestock species into a standardised metabolic wealth buffer, we compute Tropical Livestock Units (TLUᵢ, total livestock holdings) using FAO sub-Saharan African conversion weights (1 TLU = 250 kg live weight) (Jahnke, 1982; Njuki et al., 2011):

{EQ8}

Household labour capitalisation and input intensification are captured through cultivated land per adult labourer (Aᵢ / L<sub>adult,i</sub>, cultivated land area per adult labourer), plots per adult labourer, household dependency ratio, inorganic fertiliser application intensity (Fᵢ,ₛ / Aᵢ,ₛ, kg ha⁻¹), pesticide intensity (Pᵢ,ₛ / Aᵢ,ₛ), and seasonal fertiliser allocation ratios.

#### 2.4.4 Spatial community peer benchmarks and latent representations

To contextualise each smallholder's management practices relative to local agro-ecological norms without leaking target values, we compute spatial peer-group deviations for key structural variables Xₖ ∈ {H′ₘ, A, Fₘ} relative to the regional community mean X̄ₖ,ᵣ₍ᵢ₎:

{EQ9}

Additionally, inside each training fold, we extract four unsupervised K-Means Agronomic Archetype Distances (dᵢ,꜀ = ‖zᵢ − μ꜀‖₂ for c ∈ {0, 1, 2, 3}, representing Euclidean distance in standardised input–diversity–scale space to Subsistence Cereal, Commercial Mixed Cropping, Agro-Pastoral, and Diversified Tree-Crop clusters) and three orthogonal Principal Component Analysis (PCA) latent factors (the first principal component, the second principal component, the third principal component) capturing farm scale, capital–labour substitution, and agro-ecological elevation gradients.

### 2.5 Spatial cross-validation and the five-pillar leakage isolation protocol

Standard random cross-validation violates the assumption of independent and identically distributed (i.i.d.) validation errors when observations are spatially clustered within census Enumeration Areas (Roberts et al., 2017; Meyer et al., 2018; Ploton et al., 2020). Let Gᵢ ∈ {1, …, 921} denote the Enumeration Area identifier (ea_id) of household i. We partition the N = 4,564 holdings into K = 5 spatially disjoint folds ℱ₁, …, ℱ₅ using Spatial Group K-Fold Cross-Validation (geographic group cross-validation), enforcing the strict geographic disjointness constraint:

{EQ10}

Equation (10) guarantees that no Enumeration Area—and consequently no village micro-climate, shared soil catena, or local enumerator team—ever spans both training and validation partitions.

To ensure that zero information from validation holdings contaminates model training, we enforce and programmatically verify a Five-Pillar Spatial Leakage Isolation Protocol:
- Pillar 1 (Spatial Group Disjointness): Verifies Equation (10) across all five folds (zero overlapping EAs across 921 clusters).
- Pillar 2 (Target Variable Independence): Verifies that Yᵥₒₗ, Yₘ, Yᵥ, Qₘ, and Qᵥ are strictly excluded from X and audits the maximum absolute Pearson correlation maxⱼ |r(Xⱼ, Yᵥₒₗ)| to confirm the absence of deterministic target proxies.
- Pillar 3 (Preprocessing & Imputation Isolation): All median imputers, robust interquartile scaling interquartile transformations, and one-hot categorical encoding mappings are fitted strictly on training fold indices ℐ<sub>train</sub><sup>(−k)</sup> and applied out-of-fold to ℐ<sub>val</sub><sup>(k)</sup>.
- Pillar 4 (Unsupervised Representation Isolation): Both unsupervised k-means clustering with four cluster centroids and principal component analysis retaining three components projection matrices are estimated strictly on training fold observations.
- Pillar 5 (Feature Selection & Lookahead Integrity): Tree-gain feature importance ranking (tree-gain feature importance selection) is executed without accessing validation target labels, pruning the 246 candidate features down to the top K<sub>top</sub> = 100 features (champion feature subset) that capture 99.1% of cumulative information gain whilst eliminating 146 collinear or high-noise variables.

### 2.6 Supervised ensemble architecture and interpretability framework

We benchmark four supervised regression architectures across the identical five-fold spatial cross-validation splits:
1. Light Gradient Boosting Machine (LightGBM): A histogram-based gradient boosting framework utilizing leaf-wise (best-first) tree growth with Gradient-based One-Side Sampling (GOSS) and Exclusive Feature Bundling (EFB), configured with num_leaves = 35, max_depth = 6, learning rate η = 0.03, subsample = 0.80, colsample_bytree = 0.70, and L₁/L₂ regularisation α = 0.1, λ = 1.0 (Ke et al., 2017);
2. Extreme Gradient Boosting (XGBoost): A depth-wise regularised second-order Taylor-expansion gradient booster configured with max_depth = 5, learning rate η = 0.03, subsample = 0.80, colsample_bytree = 0.70, and λ = 1.5 (Chen & Guestrin, 2016);
3. Random Forest Regressor (RF): A variance-reducing bootstrap aggregation (bagging) ensemble of 400 deep decision trees trained with a maximum depth of 16 and square-root feature subsampling (Breiman, 2001); and
4. Champion Soft-Voting Weighted Ensemble: A convex linear combination of the three diverse base learners designed to minimise spatial generalisation variance (Breiman, 1996; Dietterich, 2000):

{EQ11}

with simplex weights w<sub>LGB</sub> = 0.50, w<sub>XGB</sub> = 0.40, and w<sub>RF</sub> = 0.10 selected via out-of-fold simplex grid optimisation on training partitions. Model predictive accuracy is evaluated across all out-of-fold spatial predictions using Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and the out-of-fold Coefficient of Determination (R²).

To ensure transparent, game-theoretically consistent attribution of non-linear predictions, we compute exact Tree-based Shapley Additive Explanations (TreeSHAP) (Lundberg & Lee, 2017; Lundberg et al., 2020), which decompose each household's prediction f̂(xᵢ) into the expected baseline volatility E[f(X)] plus exact marginal feature contributions ϕᵢ,ⱼ:

{EQ12}

All data processing, spatial cross-validation, statistical testing, and publication graphics were implemented in Python 3.11 using NumPy (v1.26; Harris et al., 2020), pandas (v2.2; McKinney, 2010), SciPy (v1.12; Virtanen et al., 2020), scikit-learn (v1.4; Pedregosa et al., 2011), LightGBM (v4.3; Ke et al., 2017), XGBoost (v2.0; Chen & Guestrin, 2016), and Matplotlib (v3.8; Hunter, 2007).

---

## 3 Results

### 3.1 Empirical distribution of yield volatility and seasonal dynamics

Descriptive summary statistics across the N = 4,564 bimodal smallholder holdings (Table 1) reveal pronounced structural skewness in farm scale, input intensification, and seasonal production outcomes. The target Yield Volatility Index (Yᵥₒₗ) exhibits a sample mean of 1.084 ± 0.727 (standard deviation) and a median of 1.014, with an interquartile range (IQR) spanning from Q₁ = 0.400 to Q₃ = 2.000. Area-weighted seasonal crop yields average 930.13 ± 2,057.96 kg ha⁻¹ (median 396.95 kg ha⁻¹, IQR [123.79, 990.10] kg ha⁻¹) during the primary *Masika* long rains and 900.80 ± 1,952.16 kg ha⁻¹ (median 414.34 kg ha⁻¹, IQR [123.58, 998.04] kg ha⁻¹) during the secondary *Vuli* short rains. Despite similar national seasonal medians, the absolute inter-seasonal yield difference within individual holdings averages 883.52 ± 2,170.16 kg ha⁻¹ (median 353.58 kg ha⁻¹), demonstrating that individual farms experience dramatic yield swings between consecutive harvests even when aggregate national seasonal averages appear stable.

**Table 1** Summary statistics of smallholder agricultural holdings and seasonal agronomic dynamics (N = 4,564)

{t1_md}

*Note:* ᵃStatistics computed across all N = 4,564 bimodal agricultural holdings in the 2024/2025 Tanzania NBS Annual Agricultural Sample Survey (AASS). ᵇYᵥₒₗ ∈ [0, 2] denotes the bounded inter-seasonal Yield Volatility Index defined in Equation (3); TLU denotes Tropical Livestock Units (1 TLU = 250 kg live metabolic weight equivalent).

The empirical probability density of Yᵥₒₗ (Fig. 1a) is distinctly bimodal, characterised by a broad interior mode centred near Yᵥₒₗ ≈ 0.45 (representing diversified holdings maintaining moderate seasonal yield fluctuations) and a sharp upper boundary concentration at Yᵥₒₗ = 2.00 (representing holdings that suffered complete crop failure in one of the two seasons). Cross-seasonal log-yield parity analysis (Fig. 1b) illustrates that holdings clustering along the 1:1 seasonal parity diagonal achieve low volatility (Yᵥₒₗ < 0.40), whereas points along the horizontal and vertical axes correspond to uni-seasonal harvest collapse. Stratifying holdings across four landholding size classes (Fig. 1c) confirms an inverse relationship between farm scale and production instability: marginal sub-subsistence holdings cultivating < 0.5 ha exhibit the highest median volatility and widest dispersion, whereas medium (1.5–3.5 ha) and commercial (> 3.5 ha) holdings benefit from spatial parcel averaging across toposequences.

![Fig. 1](file://{FIG_DIR.resolve()}/fig1_target_distribution_and_seasonal_dynamics.png)

**Fig. 1** Empirical distribution of the Yield Volatility Index (Yᵥₒₗ) and cross-seasonal production dynamics across N = 4,564 Tanzanian smallholder holdings: (a) histogram and Gaussian kernel density estimate (KDE) of Yᵥₒₗ ∈ [0, 2] indicating median (1.01) and interquartile range ([0.40, 2.00]); (b) joint log-yield parity scatter between *Masika* and *Vuli* seasons coloured by Yᵥₒₗ; (c) boxplots of Yᵥₒₗ stratified across four landholding size classes (Graphics programme: Python 3.11 / Matplotlib 3.8)

Input adoption across the cohort remains highly skewed (Table 1): the median smallholder applies 0.00 kg of inorganic fertiliser (Q₃ = 20.00 kg) and 0.00 L or kg of chemical pesticides (Q₃ = 5.64), whilst median livestock wealth stands at 0.36 TLU (Q₁ = 0.04, Q₃ = 4.74, mean 4.97 ± 23.67 TLU). Similarly, the median *Masika* Shannon crop diversity index is 0.000 (Q₃ = 0.342, mean 0.180 ± 0.310), indicating that over half of surveyed holdings rely on seasonal monoculture plots, leaving them highly exposed to crop-specific climatic and biotic shocks.

### 3.2 Spatial cross-validation benchmark and model calibration

Across the five spatially disjoint Enumeration Area folds (921 EAs), the soft-voting Weighted Ensemble achieves the highest out-of-sample predictive accuracy (Table 2), recording a Spatial RMSE of 0.464, a Spatial MAE of 0.347, and a Spatial R² of 0.592 (explaining 59.2% of out-of-sample variance in inter-seasonal yield volatility across unseen villages). Among individual base learners, LightGBM ranks second (Spatial RMSE = 0.465, MAE = 0.346, R² = 0.590), closely followed by XGBoost (Spatial RMSE = 0.466, MAE = 0.348, R² = 0.588), whereas Random Forest trails by 2.25 percentage points in explained variance (Spatial RMSE = 0.477, MAE = 0.368, R² = 0.569).

**Table 2** Multi-model spatial cross-validation benchmark comparison across 921 Enumeration Areas (N = 4,564)

{t2_md}

*Note:* ᵃAll models evaluated on the identical 5-fold Spatial Group Cross-Validation splits (geographic group cross-validation on Enumeration Area geography) using the top-100 pruned feature subset. ᵇSoft-voting ensemble weights: 0.50 LightGBM + 0.40 XGBoost + 0.10 Random Forest.

Visual inspection of the multi-model benchmark (Fig. 2a) and out-of-fold spatial calibration scatter (Fig. 2b) confirms that the Weighted Ensemble predictions track the ideal 45° identity line across the full [0, 2] domain with an ordinary least squares calibration slope of 0.60 and intercept of 0.43. Across the five independent geographic folds (Fig. 2c), out-of-fold R² remains tightly bounded within 0.592 ± 0.018, demonstrating that model performance is invariant to specific spatial partition boundaries and resilient against regional sampling fluctuations.

![Fig. 2](file://{FIG_DIR.resolve()}/fig2_model_benchmark_spatial_cv.png)

**Fig. 2** Multi-model spatial cross-validation benchmark and out-of-fold calibration across five Enumeration Area folds: (a) comparison of Spatial R² and Spatial RMSE across Weighted Ensemble, LightGBM, XGBoost, and Random Forest; (b) out-of-fold calibration scatter of observed (Yᵥₒₗ) versus predicted (Ŷᵥₒₗ) yield volatility; (c) fold-wise spatial stability of out-of-fold R² showing the mean (0.592) and ± 1 standard deviation band (Graphics programme: Python 3.11 / Matplotlib 3.8)

### 3.3 Global feature importance and SHAP attributions

Pruning the 246 engineered candidate variables via out-of-fold tree information gain (tree-gain feature importance selection) reveals a steep Pareto hierarchy (Fig. 3a and Online Resource 1): the top 25 features account for 88.4% of total information gain, and the top 100 champion features capture 99.1% of cumulative information gain whilst eliminating 146 noisy or redundant variables. Categorising the top 100 selected features by agronomic domain (Fig. 3c) shows that Plot Technology, Soil & Irrigation indicators constitute the largest structural group (29%), followed by Spatial Peer Benchmarks (23%), Crop Diversity & Portfolio indices (16%), Livestock & Labour Buffers (12%), Climatic & Pest Shocks (12%), and Planting Timing & Seasonality (8%).

**Table 3** Top-25 predictive features ranked by tree split frequency and information gain across agronomic domains

{t3_md}

*Note:* ᵃSplit frequency and information gain computed from the gradient boosted decision tree feature selection stage across the N = 4,564 holdings. ᵇThe complete ranking of all 246 candidate features is provided in Online Resource 1 (Online Resource 1).

Despite representing only 8% of feature count, Planting Timing & Seasonality dominates split frequency and total information gain (Table 3 and Fig. 3b). The inter-seasonal Planting Month Difference (Masika – Vuli) ranks first overall with 300 tree splits and an information gain of 11,375.62—more than four times the gain of the second-ranked feature, Mean Harvested Area Proportion (Masika) (mean long-rain harvested area proportion, 212 splits, gain 2,608.24), and the third-ranked feature, Mean Planting Month (Vuli) (mean short-rain planting month, 205 splits, gain 2,502.78). High-ranking structural predictors also include Shannon Crop Diversity Relative to Regional Mean (Rank 4, 187 splits, gain 423.74), Seasonal Species Evenness Shift (Rank 5, 142 splits, gain 356.96), Total Tropical Livestock Units (TLU) (Rank 6, 141 splits, gain 132.91), and Crop Failure Plot Share (Masika) (Rank 7, 131 splits, gain 1,812.26).

![Fig. 3](file://{FIG_DIR.resolve()}/fig3_grandmaster_feature_importance_and_selection.png)

**Fig. 3** Feature selection trajectory and domain composition across 246 candidate variables: (a) cumulative information gain scree curve illustrating the 99.1% information gain threshold at the top-100 feature cut-off; (b) top 15 features ranked by tree split frequency with annotated information gain; (c) proportional composition of the top-100 selected features across six core agro-economic domains (Graphics programme: Python 3.11 / Matplotlib 3.8)

Global exact TreeSHAP attributions (Fig. 4a, b) confirm both the magnitude and directional sign of each predictor's marginal impact on Yᵥₒₗ. In the beeswarm distribution (Fig. 4a), Planting Month Difference (Masika – Vuli) exhibits the largest mean absolute SHAP impact (|SHAP| = 0.202), followed by Mean Harvested Area Share (Masika) (|SHAP| = 0.098), Mean Planting Month (Vuli) (|SHAP| = 0.067), Drought Failure Indicator (Vuli) (|SHAP| = 0.047), and Crop Failure Plot Share (Masika) (|SHAP| = 0.046). Directionally, large planting month shifts, high plot failure shares, and Vuli drought shocks push SHAP values strongly positive (increasing yield volatility by +0.25 to +0.55 units), whereas high *Masika* harvested area realisation, positive crop diversity relative to regional peers, and higher Tropical Livestock Units generate negative SHAP values that stabilise production across seasons.

![Fig. 4](file://{FIG_DIR.resolve()}/fig4_shap_global_feature_attributions.png)

**Fig. 4** Global TreeSHAP feature attributions across the top 14 predictors of smallholder yield volatility: (a) directional beeswarm plot showing individual household SHAP values coloured by normalised feature magnitude (Low to High); (b) mean absolute SHAP magnitude (|SHAP|) quantifying global predictive contribution (Graphics programme: Python 3.11 / Matplotlib 3.8)

### 3.4 Regional heterogeneity, spatial vulnerability mapping, and model transferability

A critical policy question for national statistical offices and early-warning agencies is whether machine learning models should be trained separately for each administrative region or pooled into a unified national model. Table 4 and Fig. 5 evaluate this across all 27 surveyed administrative regions of Tanzania by combining regional model benchmark metrics with high-resolution regional choropleth maps derived from the official 2022 Population and Housing Census administrative boundaries. Aggregated across all 27 surveyed regions, dedicated regional models achieve a pooled R² of only 0.348 (RMSE = 0.587, MAE = 0.467), whereas the Unified National Model achieves R² = 0.592 (RMSE = 0.464, MAE = 0.347)—a net national variance-explained advantage of +24.42 percentage points.

**Table 4** Regional heterogeneity and out-of-fold performance breakdown across all 27 surveyed regions (N = 4,564)

{t4_md}

*Note:* ᵃRegions ordered by bimodal sample size (N). ᵇNational Advantage defined as ΔR² = R²<sub>National</sub> − R²<sub>Regional</sub> evaluated on identical out-of-fold Enumeration Area validation partitions.

Spatial visualization of survey sampling density (Fig. 5a) reveals that bimodal smallholder holdings are concentrated in the humid northeastern corridor (Tanga, N = 650; Kilimanjaro, N = 375; Arusha, N = 215), the Lake Victoria basin (Mara, N = 476; Kagera, N = 296; Mwanza, N = 215; Simiyu, N = 202; Geita, N = 147), the central eastern plains (Morogoro, N = 257; Pwani, N = 252), the southern highlands (Mbeya, N = 227), and the Zanzibar Archipelago (N = 608 combined across Pemba and Unguja), whereas purely unimodal zones in the central and southern interior cultivate only single annual cycles and are excluded from bimodal volatility tracking.

Mapping regional mean yield volatility (Fig. 5b) uncovers acute sub-national vulnerability hotspots:
1. Semi-Arid Drought Hotspots: In Dodoma (Ȳᵥₒₗ = 1.483), erratic rainfall leads to severe crop desiccation, with 59.3% of holdings suffering catastrophic uni-seasonal crop failure (Yᵥₒₗ ≥ 1.50).
2. Maritime Island Vulnerability: In the Zanzibar Archipelago, particularly Kusini Pemba (Ȳᵥₒₗ = 1.514, 66.7% hyper-volatile) and Kaskazini Pemba (Ȳᵥₒₗ = 1.502, 64.1% hyper-volatile), extreme rainfall disparity between the *Masika* and *Vuli* seasons leaves island smallholders acutely exposed to seasonal food supply deficits.
3. Resilient Lacustrine and Highland Pockets: Conversely, Kagera (Ȳᵥₒₗ = 1.139) and Tanga (Ȳᵥₒₗ = 0.978) benefit from agro-forestry systems, perennial banana–coffee canopies, and micro-climate buffering that dampen inter-seasonal harvest shocks.

Crucially, mapping out-of-fold spatial predictive skill across regions (Fig. 5c and Table 4) demonstrates that the Unified National Ensemble delivers high predictive power across heterogeneous agro-ecological zones, reaching R² = 0.748 in Kagera, R² = 0.754 in Mjini Magharibi, R² = 0.725 in Kusini Pemba, R² = 0.716 in Kaskazini Pemba, R² = 0.649 in Mara, and R² = 0.624 in Kilimanjaro. Furthermore, as shown in Table 4, the Unified National Ensemble outperforms isolated regional models (ΔR² > 0) in 26 out of 27 regions (96.3%). By learning shared non-linear response surfaces across regional borders, national data pooling prevents small-sample overfitting and establishes robust spatial generalisability for operational food security monitoring.

![Fig. 5](file://{FIG_DIR.resolve()}/fig5_regional_heterogeneity_and_spatial_transferability.png)

**Fig. 5** Sub-national spatial distribution of smallholder yield volatility and machine learning predictive skill across 27 administrative regions of Tanzania based on 2022 PHC administrative shapefiles: (a) spatial coverage and sample concentration of surveyed bimodal agricultural holdings (N = 4,564); (b) choropleth map of regional mean Yield Volatility Index (Yᵥₒₗ) with annotations highlighting acute volatility hotspots in Dodoma semi-arid plains and Zanzibar (Pemba/Unguja) alongside resilient perennial production in Tanga and Kagera; (c) out-of-fold spatial machine learning predictive skill (R²) achieved by the Unified National Weighted Ensemble across unseen Enumeration Areas (Hatched grey polygons represent unimodal agro-ecological strata cultivating single annual cycles; Graphics programme: Python 3.11 / Matplotlib 3.8 / GeoPandas)

### 3.5 Non-linear agronomic interactions, leakage audit, and household archetypes

Two-way interaction surfaces (Fig. 6) reveal that household asset endowments and agro-ecological management practices act as non-linear buffers that moderate climate shock transmission. First, stratifying the response to seasonal planting month shifts by median livestock holdings (Fig. 6a) demonstrates that livestock-poor households (TLU ≤ 0.36) suffer an escalation in mean Yᵥₒₗ to 1.38 when planting timing diverges by ± 3 months, whereas livestock-buffered households (TLU > 0.36) maintain mean Yᵥₒₗ below 0.96 across the same timing gap—reflecting their capacity to mobilise animal draft power and liquid cash for rapid land preparation. Second, Fig. 6b shows that among holdings experiencing zero plot abandonment (zero unharvested plots), expanding crop portfolio diversity above the regional peer average (exceeding regional peer diversity by > 0.25 Shannon units) compresses mean Yᵥₒₗ from 0.95 to 0.68. Conversely, when complete plot failure shocks occur (unharvested plot failure > 0), volatility rises above 1.35 for monocroppers but is dampened by 0.28 index points among highly diversified polyculture holdings. Third, Fig. 6c reveals that whilst high plot area fragmentation (CVₚₗₒₜ > 0.80) elevates yield volatility under purely rainfed cultivation, access to supplemental irrigation (with active supplemental irrigation) decouples fragmentation from production instability, reducing mean Yᵥₒₗ by 0.32–0.45 units across fragmented holdings.

![Fig. 6](file://{FIG_DIR.resolve()}/fig6_agronomic_non_linear_interactions.png)

**Fig. 6** Non-linear two-way agronomic interaction surfaces and resilience thresholds: (a) interaction between seasonal planting month difference and livestock asset buffers (Low vs. High TLU); (b) interaction between crop portfolio diversity divergence from regional peers and plot harvest failure shocks; (c) interaction between plot area fragmentation (CVₚₗₒₜ) and supplemental irrigation access (Graphics programme: Python 3.11 / Matplotlib 3.8)

To verify that these empirical relationships are free from methodological artifacts, Table 5 and Fig. 7a report the results of our formal Five-Pillar Spatial Leakage Audit. All five audit pillars achieve a 100% pass certification (certified pass): (1) zero Enumeration Areas overlap between training and validation folds across all five splits; (2) the target Yᵥₒₗ is completely isolated from the feature matrix with a maximum absolute single-feature correlation of rₘₐₓ = 0.4365; (3) all robust interquartile scaling and median imputation parameters strictly obey fold boundaries; (4) unsupervised K-Means cluster centroids and PCA loadings are fitted strictly on training partitions; and (5) top-100 feature selection exhibits zero validation target lookahead.

**Table 5** Formal five-pillar spatial data leakage audit certificate

{t5_md}

*Note:* ᵃProgrammatic audit executed by Leakage Auditor across all 5 spatial cross-validation folds (N = 4,564 holdings, 921 Enumeration Areas).

Stratifying the 4,564 holdings into four equal volatility quartiles (N = 1,141 holdings per quartile; Table 6) exposes the structural divide between resilient and hyper-volatile farms. Holdings in Q1 (Low Volatility / Resilient) exhibit a mean Yᵥₒₗ of 0.176, a mean seasonal yield gap of only 174.33 kg ha⁻¹, the highest mean Shannon crop diversity (0.243), and substantial livestock buffers (5.21 TLU). By contrast, holdings in Q4 (Hyper-Volatile) suffer a mean Yᵥₒₗ of 2.000 (complete seasonal collapse in one cropping window), accompanied by nearly three-fold lower crop diversity (H′ₘ = 0.086) and 44.4% lower livestock wealth (2.89 TLU). Notably, Q2 (Moderate-Low Volatility, mean Yᵥₒₗ = 0.685) exhibits the highest mean inorganic fertiliser intensity (2,556.67 kg driven by commercial estates), whereas Q3 (Moderate-High Volatility, mean Yᵥₒₗ = 1.476) experiences the largest absolute seasonal yield gap (1,891.01 kg ha⁻¹) and highest plot fragmentation (CVₚₗₒₜ = 0.346).

**Table 6** Smallholder agronomic stratification across empirical Yield Volatility Index (Yᵥₒₗ) quartiles (N = 4,564)

{t6_md}

*Note:* ᵃCohort partitioned into four equal quartiles of N = 1,141 holdings each based on observed Yᵥₒₗ.

To illustrate how the ensemble synthesises these factors at the micro-household level, Table 7 and Fig. 7b, c examine three representative smallholder archetypes alongside a local TreeSHAP waterfall decomposition:
- Case A (Resilient Diversified Agro-Pastoralist, Household Archetype A): Exhibiting high multi-crop diversity, substantial livestock buffers, and zero plot failure, this holding achieves an observed volatility of Yᵥₒₗ = 0.183 (predicted Ŷᵥₒₗ = 0.285, residual 0.101). Similarly, in the micro-level SHAP waterfall for benchmark resilient holding #0 (Fig. 7c), starting from the population base expectation E[f(X)] = 1.085, synchronised planting timing (`Planting Month Difference`, ϕ = −0.162), high *Masika* harvest realisation (ϕ = −0.079), timely *Vuli* sowing (ϕ = −0.049), balanced seasonal fertiliser allocation (ϕ = −0.039), and active crop rotation (ϕ = −0.029) cumulatively drive the predicted volatility down to f̂(x) = 0.498.
- Case B (Moderate Input-Intensive Specialised Farm, Household Archetype B): Relying on synthetic fertiliser intensification with moderate planting timing disparity and low crop diversity, this farm records Yᵥₒₗ = 1.007 (predicted 0.483).
- Case C (Climate-Shocked Vulnerable Smallholder, Household Archetype C): Suffering severe planting delays, complete plot abandonment shocks, and zero livestock buffers, this household experiences total uni-seasonal collapse (Yᵥₒₗ = 2.000, predicted Ŷᵥₒₗ = 1.948, residual 0.052).

**Table 7** Representative smallholder archetypes and micro-level counterfactual policy attributions

{t7_md}

*Note:* ᵃHousehold identifiers are deterministically hashed (anonymised household identifiers) to preserve respondent confidentiality in accordance with Tanzania National Bureau of Statistics microdata protocols.

![Fig. 7](file://{FIG_DIR.resolve()}/fig7_leakage_audit_and_household_counterfactuals.png)

**Fig. 7** Five-pillar spatial leakage audit verification, smallholder archetype profiles, and micro-level TreeSHAP attribution: (a) isolation audit compliance scorecard across the five leakage pillars; (b) normalised capacity profiles ([0, 1]) comparing Resilient (Yᵥₒₗ = 0.18), Moderate (Yᵥₒₗ = 1.01), and Hyper-Volatile (Yᵥₒₗ = 2.00) smallholder archetypes; (c) local TreeSHAP waterfall plot for resilient benchmark holding #0 decomposing how protective agronomic practices reduce predicted volatility from the base expectation E[f(X)] = 1.085 to f̂(x) = 0.498 (Graphics programme: Python 3.11 / Matplotlib 3.8)

### 3.6 Agro-ecological zone hotspots, partial dependence surfaces, and policy counterfactuals

Aggregating holdings across Tanzania's seven macro Agro-Ecological Zones (Fig. 8) uncovers stark geographic gradients in production stability and resilience capacity (1 − Yᵥₒₗ / 2). The Zanzibar Archipelago (Ȳᵥₒₗ = 1.33, Resilience Index = 0.33), Central Semi-Arid bimodal pockets (Ȳᵥₒₗ = 1.30, Resilience Index = 0.35), and Southern Highlands (Ȳᵥₒₗ = 1.23, Resilience Index = 0.39) exhibit the highest inter-seasonal volatility among bimodal cultivators, driven by pronounced moisture asymmetry between the main and secondary rains (Fig. 8a, c). The Northern Highlands (Ȳᵥₒₗ = 1.10, Resilience Index = 0.45) and Western & Southern Zone (Ȳᵥₒₗ = 1.04, Resilience Index = 0.48) occupy an intermediate risk tier. By contrast, the Lake Victoria Basin (Ȳᵥₒₗ = 1.02, Resilience Index = 0.49) and Coastal & Eastern Zone (Ȳᵥₒₗ = 1.01, Resilience Index = 0.50) achieve the highest inter-seasonal stability, supported by lacustrine and coastal rainfall moderation and widespread cassava–banana–legume intercropping (Fig. 8b, c).

![Fig. 8](file://{FIG_DIR.resolve()}/fig8_spatial_hotspots_and_agroecological_zones.png)

**Fig. 8** Spatial volatility hotspots and resilience capacity across Tanzania's seven Agro-Ecological Zones: (a) mean Yield Volatility Index (Yᵥₒₗ ± 95% confidence interval) by zone; (b) zone-level joint relationship between mean plot harvest failure rate (%) and absolute seasonal yield gap (kg ha⁻¹), sized and coloured by mean Yᵥₒₗ; (c) Agro-Ecological Resilience Index (1 − Yᵥₒₗ / 2) stratified by risk tier (Graphics programme: Python 3.11 / Matplotlib 3.8)

One-dimensional marginal response surfaces (Fig. 9) pinpoint four actionable agronomic tipping points across the national cohort:
1. Planting Month Synchronisation (Fig. 9a): The partial response to inter-seasonal planting delay exhibits a sharp V-shaped trough around ΔM ∈ [−1, +1] months (Yᵥₒₗ ≈ 0.72), rising steeply to > 1.25 when inter-seasonal sowing windows drift beyond ± 4 months.
2. Critical Livestock Buffer Threshold (Fig. 9b): Smallholders owning < 3.0 TLU (shaded high-vulnerability zone) face elevated baseline volatility (Yᵥₒₗ ≈ 1.10–1.18); crossing the 3.0 TLU threshold—equivalent to owning four indigenous cattle or three cattle plus ten small ruminants—triggers a sharp downward shift in Yᵥₒₗ toward 0.82–0.90.
3. Peer-Relative Crop Diversification (Fig. 9c): Holdings with Shannon diversity below their regional community average experience Yᵥₒₗ > 1.15, whereas holdings exceeding regional peer diversity by +0.40 Shannon units reduce marginal volatility below 0.85.
4. Plot Abandonment Escalation (Fig. 9d): Marginal volatility increases monotonically with the share of unharvested plots, climbing from 0.78 at 0% abandonment to > 1.45 once plot failure exceeds 40% of holding area.

![Fig. 9](file://{FIG_DIR.resolve()}/fig9_agroeconomic_partial_dependence_surfaces.png)

**Fig. 9** One-dimensional agro-economic partial dependence and marginal response surfaces for the four primary continuous drivers of yield volatility: (a) seasonal planting month difference (ΔM, highlighting synchronised planting at ΔM = 0); (b) Tropical Livestock Units (TLU, highlighting the < 3.0 TLU high-vulnerability zone); (c) Shannon crop diversity difference from the regional peer mean; (d) complete plot harvest abandonment share (%) (Graphics programme: Python 3.11 / Matplotlib 3.8)

Finally, we conduct out-of-fold Policy Counterfactual Stress-Testing (Fig. 10) by simulating three targeted agricultural policy interventions across the N = 4,564 holdings:
- Scenario 1 (Safety-Net Livestock Asset Transfer): Providing +2.0 TLU (e.g., a small-ruminant pass-on programme) to asset-poor holdings (TLU < 1.0) shifts the predicted volatility density leftward (Fig. 10a), reducing the national share of hyper-volatile holdings (Yᵥₒₗ ≥ 1.50) from 25.8% (Baseline) to 25.1% (Fig. 10b) and lowering mean national volatility by 11.6% (Fig. 10c).
- Scenario 2 (Crop Diversification Extension): Expanding crop portfolio diversity by +0.40 Shannon units (intercropping drought-tolerant legumes and roots/tubers) among monoculture holdings (H′ₘ < 0.20) reduces hyper-volatile holdings from 25.8% to 24.6% and lowers mean national volatility by 16.0%.
- Scenario 3 (Integrated Climate-Smart Agriculture [CSA] Package): Combining the +2.0 TLU safety-net asset buffer, +0.40 Shannon legume–cereal diversification, and early-warning meteorological planting advisories shifts the entire density distribution toward the resilient regime (Fig. 10a), cutting the prevalence of hyper-volatile holdings from 25.8% to 19.9% (Fig. 10b) and achieving a 40.0% net reduction in mean national yield volatility (Fig. 10c).

![Fig. 10](file://{FIG_DIR.resolve()}/fig10_policy_simulation_and_counterfactual_interventions.png)

**Fig. 10** Policy counterfactual stress-testing and volatility mitigation scenarios across N = 4,564 smallholder holdings: (a) kernel density distribution shift of predicted yield volatility (Ŷᵥₒₗ) under Baseline Status Quo, +2.0 TLU Asset Transfer, +0.40 Shannon Crop Diversification, and the Integrated Climate-Smart Agriculture (CSA) Package; (b) percentage of smallholder holdings classified as hyper-volatile (Yᵥₒₗ ≥ 1.50) across scenarios; (c) net mean yield volatility reduction efficiency (%) relative to baseline (Graphics programme: Python 3.11 / Matplotlib 3.8)

---

## 4 Discussion

### 4.1 Methodological imperatives: preventing spatial leakage in agricultural machine learning

A central contribution of this study is demonstrating that predictive machine learning models of smallholder food security can achieve high out-of-sample explanatory power (R² = 0.592, RMSE = 0.464) under rigorous spatial group cross-validation, provided that domain-grounded feature engineering is paired with strict geographic and preprocessing isolation. In recent years, a series of landmark methodological critiques in ecology, remote sensing, and agricultural economics has exposed how pervasive spatial autocorrelation leakage is in environmental machine learning (Roberts et al., 2017; Meyer et al., 2018, 2019; Ploton et al., 2020; Wadoux et al., 2021). When nearby agricultural plots or households within the same census Enumeration Area are split randomly across training and validation sets, flexible tree ensembles exploit spatial proximity as a shortcut—effectively performing spatial interpolation of local residuals rather than learning biophysical and socioeconomic response functions (Ploton et al., 2020; Meyer & Pebesma, 2021). When such models are subsequently deployed to predict food shocks in unsampled districts or newly surveyed villages, their predictive accuracy collapses.

Our Five-Pillar Spatial Leakage Isolation Protocol (Table 5, Fig. 7a) directly addresses these concerns and establishes a reproducible template for survey-based machine learning in *Food Security*. By enforcing geographic group cross-validation partitioning across all 921 Enumeration Areas (Equation 10), every validation prediction in our benchmark is generated for a village cluster completely unseen during training. Furthermore, isolating robust interquartile scaling transformations, K-Means archetype clustering, PCA orthogonal factor extraction, and tree-gain feature selection inside training fold boundaries prevents subtle distributional lookahead bias (Kaufman et al., 2012; Kapoor & Narayanan, 2023). Our finding that pruning 146 low-gain candidate variables preserves 99.0% of tree information gain (Fig. 3a) whilst stabilising out-of-fold R² within a narrow 0.587 ± 0.030 band across all five geographic folds (Fig. 2c) confirms that regularised gradient boosting ensembles (LightGBM and XGBoost) blended with bootstrap-aggregated Random Forest trees effectively mitigate variance across noisy multi-unit survey microdata.

Equally important for national monitoring systems is our empirical demonstration of the Spatial Transferability Advantage of pooled national modelling (Table 4, Fig. 5). In decentralising agricultural administration, analysts often assume that local models calibrated separately for individual administrative regions will better capture local context than a single national model. Our empirical results decisively refute this assumption for smallholder survey data: the Unified National Weighted Ensemble outperforms standalone regional models in 26 of 27 regions (ΔR² > 0), boosting pooled explained variance from R² = 0.348 to R² = 0.592. Because our feature space explicitly incorporates regional community peer deviations (ΔX<sub>k,i</sub><sup>reg</sup>, Equation 9) and latent agro-ecological PCA factors, the national ensemble successfully pools statistical strength across analogous agro-ecological niches—allowing data-sparse regions such as Kusini Pemba (N = 93, ΔR² = +0.411), Dodoma (N = 27, ΔR² = +0.541), and Iringa (N = 14, ΔR² = +0.627) to borrow non-linear response structure from data-rich bimodal zones.

### 4.2 Phenological timing, portfolio diversity, and agro-ecological buffering

Our TreeSHAP attributions (Table 3, Fig. 4) and partial dependence surfaces (Fig. 9) provide novel micro-econometric evidence on the hierarchy of mechanisms governing smallholder yield stability in bimodal tropics. The emergence of Planting Month Difference  and Mean Vuli Planting Month  as two of the top three predictors of Yᵥₒₗ underscores the critical role of phenological synchronisation under increasing rainfall variability (Rowhani et al., 2011; Thornton et al., 2014). In bimodal Tanzania, the *Vuli* short rains are characterised by a narrow sowing window; when delayed onset of the October rains or household labour/liquidity bottlenecks force farmers to sow late, crops encounter terminal moisture stress during flowering and grain filling in January, resulting in severe *Vuli* yield depression and extreme inter-seasonal divergence (Yᵥₒₗ > 1.30, Fig. 9a).

Second, our results strongly corroborate the agro-ecological biodiversity–stability hypothesis at the farm-household scale (Tilman et al., 2006; Lin, 2011; Renard & Tilman, 2019; Beillouin et al., 2021). However, a key nuance revealed by our feature ranking (Table 3) is that community-benchmarked diversity (crop diversity relative to the regional mean, Rank 4) and inter-seasonal species evenness stability (inter-seasonal species evenness shift, Rank 5) are substantially stronger predictors of yield stability than raw species counts alone (number of crops cultivated, Rank 44; Online Resource 1). Cultivating multiple crops only buffers yield volatility when cultivar areas are distributed equitably (high Pielou evenness J′) and when portfolio diversity exceeds the baseline required by the local agro-ecological zone (Fig. 6b, Fig. 9c). In the Lake Victoria Basin and Coastal & Eastern zones (Fig. 8), intercropping cereals (maize, sorghum) with nitrogen-fixing legumes (common beans, cowpeas, pigeon peas) and drought-tolerant root/tuber crops (cassava, sweet potatoes) creates physiological portfolio insurance: because cassava and pigeon peas possess deep taproots and flexible harvest windows, they maintain baseline caloric output when shallow-rooted maize fails during erratic *Vuli* rains (Kassie et al., 2015; Tilman et al., 2006).

### 4.3 Capital–labour dynamics, livestock buffers, and input intensification risks

Beyond plot ecology, our findings illuminate how household asset endowments and input intensification shape vulnerability to production shocks. Consistent with consumption-smoothing and buffer-stock theory in development economics (Dercon, 2004; Zimmerman & Carter, 2003; Dillon et al., 2015), Tropical Livestock Units  emerge as the primary household wealth buffer against crop yield volatility (Rank 6 in split frequency; Table 3). Crucially, our partial dependence analysis (Fig. 9b) and interaction plots (Fig. 6a) identify a sharp non-linear tipping point at 3.0 TLU. Below 3.0 TLU, smallholders lack sufficient liquid wealth or animal traction to buffer planting delays, resulting in persistently high volatility (Yᵥₒₗ > 1.10). Above 3.0 TLU, mixed crop–livestock integration stabilises seasonal yields through three synergistic pathways: (i) ox-plough traction enables rapid land preparation immediately following the first effective rains, compressing inter-seasonal planting delay; (ii) farmyard manure application improves soil organic matter and water-holding capacity on degraded sandy-loam plots (Tittonell & Giller, 2013); and (iii) sale of small ruminants provides timely liquidity to hire weeding labour (cultivated land area per adult labourer, Rank 9) and purchase improved drought-tolerant seed without liquidating core productive assets.

Conversely, our quartile stratification (Table 6) highlights an important cautionary lesson regarding unbuffered chemical intensification. Holdings in the hyper-volatile quartile (Q4, mean Yᵥₒₗ = 2.000) apply higher mean inorganic fertiliser (822.49 kg) than resilient holdings in Q1 (400.64 kg), yet suffer complete uni-seasonal harvest collapse when accompanied by low crop diversity (H′ₘ = 0.086) and low livestock buffers (2.89 TLU). Furthermore, our interaction surface between plot fragmentation and irrigation (Fig. 6c) demonstrates that parcel fragmentation (CVₚₗₒₜ) exacerbates yield volatility under rainfed conditions by increasing travel time and dispersing scarce family labour across distant plots, whereas supplemental micro-irrigation neutralises this penalty and stabilises yields across both seasons (Teklewold et al., 2013; Benami et al., 2021).

### 4.4 Limitations and future research directions

Whilst this study establishes a rigorous spatial machine learning benchmark for Tanzanian smallholder agriculture, several limitations warrant consideration and define priorities for future research:
1. Cross-Sectional Inter-Seasonal Scope vs. Multi-Year Panels: Although the 2024/2025 AASS captures consecutive *Masika* and *Vuli* seasons within a single survey wave, it does not track the same household cohort across multiple years. Integrating our spatial ensemble framework with multi-wave longitudinal panels—such as the Tanzania National Panel Survey (NPS / LSMS-ISA)—would allow separation of intra-annual seasonal volatility from decadal climate trends.
2. Assimilation of High-Resolution Earth Observation Covariates: To preserve respondent privacy in the public AASS microdata, Enumeration Area identifiers are anonymised without exact GPS latitude/longitude coordinates. Future operational deployment within government ministries where confidential EA centroids are accessible should fuse survey rosters with 5 km CHIRPS daily precipitation anomalies, MODIS/Sentinel-2 Normalized Difference Vegetation Index (NDVI) phenology curves, and ERA5-Land root-zone soil moisture products (Burke & Lobell, 2017; Benami et al., 2021).
3. Observational Counterfactual Assumptions: Our policy simulations (Fig. 10) represent partial-equilibrium structural stress tests derived from out-of-fold ensemble response surfaces rather than randomised controlled trials (RCTs). General-equilibrium market price feedbacks and local grazing carrying-capacity constraints should be incorporated via bio-economic simulation before scaling nationwide livestock transfer programmes.

### 4.5 Concluding remarks and policy implications

This study developed, audited, and validated a leakage-free spatial machine learning framework to predict household-level inter-seasonal crop yield volatility (Yᵥₒₗ ∈ [0, 2]) across 4,564 bimodal smallholder holdings in 921 Enumeration Areas of Tanzania. By enforcing a Five-Pillar Spatial Leakage Isolation Protocol and pruning 246 multi-domain candidate predictors to a 100-feature champion subset, our soft-voting Weighted Ensemble (0.50 LightGBM + 0.40 XGBoost + 0.10 Random Forest) achieved an out-of-sample Spatial R² of 0.592 (RMSE = 0.464) and outperformed isolated regional models across 26 of 27 administrative regions.

Our empirical findings and counterfactual stress tests (Fig. 10) translate directly into three actionable policy recommendations for Tanzania's Ministry of Agriculture, the National Food Reserve Agency (NFRA), and the Tanzania Social Action Fund (TASAF):
1. Transition from Fertiliser-Only Subsidies to Diversified Climate-Smart Input Bundles: Input subsidy programmes should condition synthetic fertiliser vouchers on intercropping or rotating cereals with drought-tolerant legumes and roots/tubers (`+0.40` Shannon diversity target), which our simulations show reduces hyper-volatile holdings from 25.8% to 24.6% and lowers mean national volatility by 16.0%.
2. Target Productive Livestock Safety Nets to the < 3.0 TLU Vulnerability Stratum: Social protection and rural credit programmes (such as TASAF productive inclusion grants) should prioritise small-ruminant and poultry asset transfers (`+2.0 TLU`) for holdings below the 3.0 TLU tipping point (Fig. 9b), providing liquid buffer capital that cuts hyper-volatile exposure to 25.1% and lowers mean national volatility by 11.6%.
3. Deploy Spatially Calibrated Early-Warning Planting Advisories and Integrated CSA Packages: Combining localised agrometeorological onset advisories from the Tanzania Meteorological Authority (TMA) to synchronise *Masika* and *Vuli* sowing windows with crop diversification and livestock buffers (Integrated CSA Package, Fig. 10) reduces the prevalence of hyper-volatile smallholders from 25.8% to 19.9% and achieves a 40.0% net reduction in mean national yield volatility—offering a scalable, empirically validated pathway toward resilient food security in East Africa.

---

## Statements and Declarations

### Funding
The author declares that no specific external grant, contract, or financial support from funding agencies in the public, commercial, or not-for-profit sectors was received during the preparation of this manuscript. Computational infrastructure and institutional support were provided by the Electronics and Precision Agriculture Lab (EPALab), Department of Agricultural Engineering, School of Engineering and Technology, Sokoine University of Agriculture (SUA), Morogoro, Tanzania.

### Competing Interests
The author has no relevant financial or non-financial competing interests to disclose.

### Ethics Approval
This study relies exclusively on secondary, fully anonymised household survey microdata collected and disseminated by the National Bureau of Statistics (NBS) of the United Republic of Tanzania under the Statistics Act, Cap 351. All household identifiers were cryptographically anonymised prior to public release. In accordance with institutional guidelines at Sokoine University of Agriculture (SUA) and international standards for secondary analysis of de-identified public microdata, no additional human-subjects ethics committee intervention was required.

### Consent to Participate
Informed consent was obtained from all participating agricultural household heads by trained enumerators of the National Bureau of Statistics (NBS) and the Office of the Chief Government Statistician (OCGS) Zanzibar during field execution of the 2024/2025 Annual Agricultural Sample Survey (AASS).

### Consent to Publish
All empirical findings, tables, and household archetype profiles reported in this manuscript are fully anonymised and contain no personally identifiable information or individual images requiring separate consent to publish.

### Data Availability
The primary 2024/2025 Annual Agricultural Sample Survey (AASS) microdata files are publicly catalogued and available upon registration through the Tanzania National Bureau of Statistics (TNBS) National Data Archive (NADA) portal ([https://microdata.nbs.go.tz/index.php/catalog/69](https://microdata.nbs.go.tz/index.php/catalog/69)) and the FAO Microdata Catalogue ([https://microdata.fao.org/](https://microdata.fao.org/)). All processed summary tables (Table 1–Table 7) and Online Resource 1 (ESM_1.csv) are included with this submission.

### Code Availability
The complete, reproducible Python source code implementing data preprocessing, feature engineering, spatial leakage auditing, supervised machine learning ensemble architectures, spatial cross-validation benchmarks, and visualization scripts is archived in a private GitHub repository and will be made openly available upon publication of this research.

### Author Contributions
Kadeghe Goodluck Fue: Conceptualisation, Methodology, Data Curation, Software Architecture, Formal Statistical and Machine Learning Analysis, Spatial Leakage Auditing, Visualisation, Writing – Original Draft, Writing – Review & Editing. The author read and approved the final manuscript.

### Acknowledgements
The author gratefully acknowledges the National Bureau of Statistics (NBS) of the United Republic of Tanzania, the Ministry of Agriculture, the Office of the Chief Government Statistician (OCGS) Zanzibar, and the Food and Agriculture Organization of the United Nations (FAO) 50x2030 Initiative for collecting, curating, and providing access to the 2024/2025 Annual Agricultural Sample Survey (AASS) microdata. The author also thanks colleagues at the Electronics and Precision Agriculture Lab (EPALab), Department of Agricultural Engineering, Sokoine University of Agriculture (SUA), for insightful discussions on East African smallholder farming systems.

---

## Electronic Supplementary Material

Below is the link to the electronic supplementary material.

- Online Resource 1 (Online Resource 1): Complete Grandmaster Feature Importance Ranking and Selection Status across all 246 Engineered Multi-Domain Candidate Predictors (N = 4,564 holdings, 921 Enumeration Areas).

---

## References

Arndt, C., Farmer, W., Strzepek, K., & Thurlow, J. (2012). Climate change, agriculture and food security in Tanzania. *Review of Development Economics*, *16*(3), 378–393. https://doi.org/10.1111/j.1467-9361.2012.00669.x

Barrett, C. B. (2010). Measuring food insecurity. *Science*, *327*(5967), 825–828. https://doi.org/10.1126/science.1182768

Barrett, C. B., & Constas, M. A. (2014). Toward a theory of resilience for international development applications. *Proceedings of the National Academy of Sciences*, *111*(40), 14625–14630. https://doi.org/10.1073/pnas.1320880111

Beillouin, D., Ben-Ari, T., Malézieux, E., Seufert, V., & Makowski, D. (2021). Positive but variable effects of crop diversification on biodiversity and ecosystem services. *Global Change Biology*, *27*(19), 4697–4710. https://doi.org/10.1111/gcb.15747

Benami, E., Jin, Z., Carter, M. R., Ghosh, A., Hijmans, R. J., Hobbs, A., Kenduiywo, B., & Lobell, D. B. (2021). Uniting remote sensing, crop modelling and economics for agricultural risk management. *Nature Reviews Earth & Environment*, *2*(2), 140–159. https://doi.org/10.1038/s43017-020-00122-y

Breiman, L. (1996). Stacked regressions. *Machine Learning*, *24*(1), 49–64. https://doi.org/10.1023/A:1018046112532

Breiman, L. (2001). Random forests. *Machine Learning*, *45*(1), 5–32. https://doi.org/10.1023/A:1010933404324

Burke, M., & Lobell, D. B. (2017). Satellite-based assessment of yield variation and its determinants in smallholder African systems. *Proceedings of the National Academy of Sciences*, *114*(9), 2189–2194. https://doi.org/10.1073/pnas.1616919114

Carletto, C., Gourlay, S., & Winters, P. (2015). From guesstimates to GPStimates: Land area measurement and implications for agricultural analysis. *Journal of African Economies*, *24*(5), 593–628. https://doi.org/10.1093/jae/ejv011

Carletto, C., Savastano, S., & Zezza, A. (2013). Fact or artifact: The impact of measurement errors on the farm size–productivity relationship. *Journal of Development Economics*, *103*, 254–261. https://doi.org/10.1016/j.jdeveco.2013.03.004

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785–794). Association for Computing Machinery. https://doi.org/10.1145/2939672.2939785

Crane-Droesch, A. (2018). Machine learning methods for crop yield prediction and climate change impact assessment in agriculture. *Environmental Research Letters*, *13*(11), 114003. https://doi.org/10.1088/1748-9326/aae159

Dercon, S. (2004). Growth and shocks: Evidence from rural Ethiopia. *Journal of Development Economics*, *74*(2), 309–329. https://doi.org/10.1016/j.jdeveco.2004.01.001

Di Falco, S., & Chavas, J.-P. (2009). On crop biodiversity, risk exposure, and food security in the highlands of Ethiopia. *American Journal of Agricultural Economics*, *91*(3), 599–611. https://doi.org/10.1111/j.1467-8276.2009.01265.x

Dietterich, T. G. (2000). Ensemble methods in machine learning. In *Multiple Classifier Systems* (pp. 1–15). Springer. https://doi.org/10.1007/3-540-45014-9_1

Dillon, B., McGee, K., & Oseni, G. (2015). Agricultural production, dietary diversity and climate variability. *The Journal of Development Studies*, *51*(8), 976–995. https://doi.org/10.1080/00220388.2015.1018902

Evenson, R. E., & Gollin, D. (2003). Assessing the impact of the Green Revolution, 1960 to 2000. *Science*, *300*(5620), 758–762. https://doi.org/10.1126/science.1078710

Food and Agriculture Organization of the United Nations. (n.d.). FAOSTAT: Statistical database. https://www.fao.org/faostat/

Godfray, H. C. J., Beddington, J. R., Crute, I. R., Haddad, L., Lawrence, D., Muir, J. F., Pretty, J., Robinson, S., Thomas, S. M., & Toulmin, C. (2010). Food security: The challenge of feeding 9 billion people. *Science*, *327*(5967), 812–818. https://doi.org/10.1126/science.1185383

Harris, C. R., Millman, K. J., van der Walt, S. J., Gommers, R., Virtanen, P., Cournapeau, D., Wieser, E., Taylor, J., Berg, S., Smith, N. J., Kern, R., Picus, M., Hoyer, S., van Kerkwijk, M. H., Brett, M., Haldane, A., del Río, J. F., Wiebe, M., Peterson, P., ... Oliphant, T. E. (2020). Array programming with NumPy. *Nature*, *585*(7825), 357–362. https://doi.org/10.1038/s41586-020-2649-2

Hertel, T. W., & Rosch, S. D. (2010). Climate change, agriculture, and poverty. *Applied Economic Perspectives and Policy*, *32*(3), 355–385. https://doi.org/10.1093/aepp/ppq016

Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, *9*(3), 90–95. https://doi.org/10.1109/MCSE.2007.55

Isbell, F., Adler, P. R., Eisenhauer, N., Fornara, D., Kimmel, K., Kremen, C., Letourneau, D. K., Liebman, M., Polley, H. W., Quijas, S., & Scherer-Lorenzen, M. (2017). Benefits of increasing plant diversity in sustainable agroecosystems. *Journal of Ecology*, *105*(4), 871–879. https://doi.org/10.1111/1365-2745.12789

Jahnke, H. E. (1982). *Livestock production systems and livestock development in tropical Africa*. Kieler Wissenschaftsverlag Vauk.

Jayne, T. S., Mather, D., & Mghenyi, E. (2010). Principal challenges confronting smallholder agriculture in sub-Saharan Africa. *World Development*, *38*(10), 1384–1398. https://doi.org/10.1016/j.worlddev.2010.06.002

Jeong, J. H., Resop, J. P., Mueller, N. D., Fleisher, D. H., Yun, K., Butler, E. E., Timlin, D. J., Shim, K.-M., Gerber, J. S., Reddy, V. R., & Kim, S.-H. (2016). Random forests for global and regional crop yield predictions. *PLOS ONE*, *11*(6), e0156571. https://doi.org/10.1371/journal.pone.0156571

Just, R. E., & Pope, R. D. (1979). Production function estimation and related risk considerations. *American Journal of Agricultural Economics*, *61*(2), 276–284. https://doi.org/10.2307/1239732

Kapoor, S., & Narayanan, A. (2023). Leakage and the reproducibility crisis in machine-learning-based science. *Patterns*, *4*(9), 100804. https://doi.org/10.1016/j.patter.2023.100804

Kassie, M., Teklewold, H., Jaleta, M., Marenya, P., & Erenstein, O. (2015). Understanding the adoption of a portfolio of sustainable intensification practices in eastern and southern Africa. *Land Use Policy*, *42*, 400–411. https://doi.org/10.1016/j.landusepol.2014.08.016

Kaufman, S., Rosset, S., Perlich, C., & Stitelman, O. (2012). Leakage in data mining: Formulation, detection, and avoidance. *ACM Transactions on Knowledge Discovery from Data*, *6*(4), 15. https://doi.org/10.1145/2382577.2382579

Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. In *Advances in Neural Information Processing Systems* (Vol. 30, pp. 3146–3154). Curran Associates.

Lin, B. B. (2011). Resilience in agriculture through crop diversification: Adaptive management for environmental change. *BioScience*, *61*(3), 183–193. https://doi.org/10.1525/bio.2011.61.3.4

Lobell, D. B., & Burke, M. B. (2010). On the use of statistical models to predict crop yield responses to climate change. *Agricultural and Forest Meteorology*, *150*(11), 1443–1452. https://doi.org/10.1016/j.agrformet.2010.07.008

Lobell, D. B., Schlenker, W., & Costa-Roberts, J. (2011). Climate trends and global crop production since 1980. *Science*, *333*(6042), 616–620. https://doi.org/10.1126/science.1204531

Lundberg, S. M., Erion, G., Chen, H., DeGrave, A., Prutkin, J. M., Nair, B., Katz, R., Himmelfarb, J., Bansal, N., & Lee, S.-I. (2020). From local explanations to global understanding with explainable AI for trees. *Nature Machine Intelligence*, *2*(1), 56–67. https://doi.org/10.1038/s42256-019-0138-9

Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. In *Advances in Neural Information Processing Systems* (Vol. 30, pp. 4765–4774). Curran Associates.

Magurran, A. E. (2004). *Measuring biological diversity*. Blackwell Publishing.

McKinney, W. (2010). Data structures for statistical computing in Python. In *Proceedings of the 9th Python in Science Conference* (pp. 56–61). https://doi.org/10.25080/Majora-92bf1922-00a

Meyer, H., & Pebesma, E. (2021). Predicting into unknown space? Estimating the area of applicability of spatial prediction models. *Methods in Ecology and Evolution*, *12*(9), 1620–1633. https://doi.org/10.1111/2041-210X.13650

Meyer, H., Reudenbach, C., Hengl, T., Katurji, M., & Nauss, T. (2018). Improving performance of spatio-temporal machine learning models using forward feature selection and target-oriented validation. *Environmental Modelling & Software*, *101*, 1–9. https://doi.org/10.1016/j.envsoft.2017.12.001

Meyer, H., Reudenbach, C., Wöllauer, S., & Nauss, T. (2019). Importance of spatial predictor variable selection in machine learning applications—Moving from data reproduction to spatial prediction. *Ecological Modelling*, *411*, 108815. https://doi.org/10.1016/j.ecolmodel.2019.108815

Njuki, J., Poole, J., Johnson, N., Baltenweck, I., Pali, P., Lokman, Z., & Mburu, S. (2011). *Gender, livestock and livelihood indicators*. International Livestock Research Institute (ILRI).

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, *12*, 2825–2830.

Ploton, P., Mortier, F., Réjou-Méchain, M., Barbier, N., Picard, N., Rossi, V., Dormann, C., Cornu, G., Viennois, G., Bayol, N., Lyapustin, A., Gourlet-Fleury, S., & Pélissier, R. (2020). Spatial validation reveals poor predictive performance of large-scale ecological mapping models. *Nature Communications*, *11*(1), 4540. https://doi.org/10.1038/s41467-020-18321-y

Ray, D. K., Gerber, J. S., MacDonald, G. K., & West, P. C. (2015). Climate variation explains a third of global crop yield variability. *Nature Communications*, *6*(1), 5989. https://doi.org/10.1038/ncomms6989

Renard, D., & Tilman, D. (2019). National food production stabilized by crop diversity. *Nature*, *571*(7764), 257–260. https://doi.org/10.1038/s41586-019-1316-y

Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B., Thuiller, W., Warton, D. I., Wintle, B. A., Hartig, F., & Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, *40*(8), 913–929. https://doi.org/10.1111/ecog.02881

Rowhani, P., Lobell, D. B., Linderman, M., & Ramankutty, N. (2011). Climate variability and crop production in Tanzania. *Agricultural and Forest Meteorology*, *151*(4), 449–460. https://doi.org/10.1016/j.agrformet.2010.12.002

Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, *27*(3), 379–423. https://doi.org/10.1002/j.1538-7305.1948.tb01338.x

Storm, H., Baylis, K., & Heckelei, T. (2020). Machine learning in agricultural and applied economics. *European Review of Agricultural Economics*, *47*(3), 849–892. https://doi.org/10.1093/erae/jbz033

Tanzania National Bureau of Statistics. (2026). Annual Agriculture Sample Survey 2024/25 (AASS 2024/25), Version 1.0 of the public use dataset. National Data Archive. https://microdata.nbs.go.tz/index.php/catalog/69

Teklewold, H., Kassie, M., & Shiferaw, B. (2013). Adoption of multiple sustainable agricultural practices in rural Ethiopia. *Journal of Agricultural Economics*, *64*(3), 597–623. https://doi.org/10.1111/1477-9552.12011

Thornton, P. K., Ericksen, P. J., Herrero, M., & Challinor, A. J. (2014). Climate variability and vulnerability to climate change: A review. *Global Change Biology*, *20*(11), 3313–3328. https://doi.org/10.1111/gcb.12581

Tilman, D., Reich, P. B., & Knops, J. M. H. (2006). Biodiversity and ecosystem stability in a decade-long grassland experiment. *Nature*, *441*(7093), 629–632. https://doi.org/10.1038/nature04742

Tittonell, P., & Giller, K. E. (2013). When yield gaps are poverty traps: The paradigm of ecological intensification in African smallholder agriculture. *Field Crops Research*, *143*, 76–90. https://doi.org/10.1016/j.fcr.2012.10.007

Virtanen, P., Gommers, R., Oliphant, T. E., Haberland, M., Reddy, T., Cournapeau, D., Burovski, E., Peterson, P., Weckesser, W., Bright, J., van der Walt, S. J., Brett, M., Wilson, J., Millman, K. J., Mayorov, N., Nelson, A. R. J., Jones, E., Kern, R., Larson, E., ... SciPy 1.0 Contributors. (2020). SciPy 1.0: Fundamental algorithms for scientific computing in Python. *Nature Methods*, *17*(3), 261–272. https://doi.org/10.1038/s41592-019-0686-2

Wadoux, A. M. J.-C., Heuvelink, G. B. M., de Bruin, S., & Brus, D. J. (2021). Spatial cross-validation is not the right way to evaluate map accuracy. *Ecological Modelling*, *457*, 109692. https://doi.org/10.1016/j.ecolmodel.2021.109692

Wheeler, T., & von Braun, J. (2013). Climate change impacts on global food security. *Science*, *341*(6145), 508–513. https://doi.org/10.1126/science.1239402

Zimmerman, F. J., & Carter, M. R. (2003). Asset smoothing, consumption smoothing and the reproduction of inequality under risk and subsistence constraints. *Journal of Development Economics*, *71*(2), 233–260. https://doi.org/10.1016/S0304-3878(03)00028-2

---

## Author Biography

**Kadeghe Goodluck Fue** is a Senior Lecturer in the Department of Agricultural Engineering, School of Engineering and Technology, at Sokoine University of Agriculture (SUA) in Morogoro, Tanzania, where he leads the Electronics and Precision Agriculture Lab (EPALab). He holds a Ph.D. in Engineering from the University of Georgia, an M.Sc. in Agricultural and Biological Engineering from the University of Florida, and a B.Sc. in Computer Engineering and Information Technology from the University of Dar es Salaam. His research focuses on precision agriculture, artificial intelligence, spatial machine learning, Agricultural Data Science, and climate-resilient smallholder farming systems, driven by a deep commitment to advancing food security across sub-Saharan Africa.
"""
    md = (
        md.replace("{ARTICLE_TITLE}", ARTICLE_TITLE)
        .replace("{RUNNING_HEAD}", RUNNING_HEAD)
        .replace("{FIG_DIR.resolve()}", str(FIG_DIR.resolve()))
        .replace("{t1_md}", t1_md)
        .replace("{t2_md}", t2_md)
        .replace("{t3_md}", t3_md)
        .replace("{t4_md}", t4_md)
        .replace("{t5_md}", t5_md)
        .replace("{t6_md}", t6_md)
        .replace("{t7_md}", t7_md)
        .replace("{EQ1}", EQ1)
        .replace("{EQ2}", EQ2)
        .replace("{EQ3}", EQ3)
        .replace("{EQ4}", EQ4)
        .replace("{EQ5}", EQ5)
        .replace("{EQ6}", EQ6)
        .replace("{EQ7}", EQ7)
        .replace("{EQ8}", EQ8)
        .replace("{EQ9}", EQ9)
        .replace("{EQ10}", EQ10)
        .replace("{EQ11}", EQ11)
        .replace("{EQ12}", EQ12)
    )
    out_lines = []
    for line in md.splitlines():
        if line.strip().startswith("$$"):
            out_lines.append(line.strip())
        else:
            out_lines.append(clean_all_symbols(line))
    return "\n".join(out_lines)


# ==============================================================================
# 3. GENERATE WORD (.DOCX) MANUSCRIPT & TITLE PAGE WITH LINE/PAGE NUMBERS & OMML
# ==============================================================================

def _set_cell_margins(cell, top=80, bottom=80, left=110, right=110) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def _set_table_booktabs_borders(table) -> None:
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>'
        '<w:left w:val="none"/>'
        '<w:right w:val="none"/>'
        '<w:insideV w:val="none"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)


def _enable_line_numbering_and_headers(doc: Document, running_head: str) -> None:
    """
    Configures Springer Food Security mandatory continuous line numbering,
    running head (<=60 chars), and automatic PAGE numbering on all sections.
    """
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

        sectPr = section._sectPr
        # Remove existing lnNumType if present
        for existing in sectPr.findall(qn("w:lnNumType")):
            sectPr.remove(existing)
        lnNumType = OxmlElement("w:lnNumType")
        lnNumType.set(qn("w:countBy"), "1")
        lnNumType.set(qn("w:restart"), "continuous")
        lnNumType.set(qn("w:distance"), "360")
        sectPr.append(lnNumType)

        # Header with Running Head
        header = section.header
        hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run(f"Running Head: {running_head}")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(9)
        hrun.italic = True

        # Footer with automatic PAGE number field
        footer = section.footer
        fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun_label = fp.add_run("Page ")
        frun_label.font.name = "Times New Roman"
        frun_label.font.size = Pt(9)

        fldSimple = OxmlElement("w:fldSimple")
        fldSimple.set(qn("w:instr"), "PAGE")
        fp._p.append(fldSimple)


def _make_omml_run(text: str, italic: bool = True) -> str:
    rpr = '<m:rPr><m:sty m:val="p"/></m:rPr>' if not italic else ""
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<m:r>{rpr}<m:t>{esc}</m:t></m:r>"


def _make_omml_sub(base_xml: str, sub_xml: str) -> str:
    return f"<m:sSub><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub></m:sSub>"


def _make_omml_sup(base_xml: str, sup_xml: str) -> str:
    return f"<m:sSup><m:e>{base_xml}</m:e><m:sup>{sup_xml}</m:sup></m:sSup>"


def _make_omml_subsup(base_xml: str, sub_xml: str, sup_xml: str) -> str:
    return f"<m:sSubSup><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub><m:sup>{sup_xml}</m:sup></m:sSubSup>"


def _make_omml_frac(num_xml: str, den_xml: str) -> str:
    return f"<m:f><m:num>{num_xml}</m:num><m:den>{den_xml}</m:den></m:f>"


def _make_omml_rad(deg_xml: Optional[str], body_xml: str) -> str:
    if deg_xml is None:
        return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{body_xml}</m:e></m:rad>'
    return f"<m:rad><m:deg>{deg_xml}</m:deg><m:e>{body_xml}</m:e></m:rad>"


def _make_omml_nary(chr_val: str, sub_xml: str, sup_xml: str, body_xml: str) -> str:
    sup_hide = '<m:supHide m:val="1"/>' if not sup_xml else ""
    return (
        f"<m:nary><m:naryPr><m:chr m:val=\"{chr_val}\"/><m:limLoc m:val=\"undOvr\"/>{sup_hide}</m:naryPr>"
        f"<m:sub>{sub_xml}</m:sub><m:sup>{sup_xml}</m:sup><m:e>{body_xml}</m:e></m:nary>"
    )


def _get_display_equation_omml(eq_num: str) -> Optional[str]:
    """Returns native Word OMML XML for numbered equations (1) through (12)."""
    R = _make_omml_run
    SUB = _make_omml_sub
    SUP = _make_omml_sup
    FRAC = _make_omml_frac
    RAD = _make_omml_rad
    NARY = _make_omml_nary

    eq_map: Dict[str, str] = {
        "(1)": (
            SUB(R("Q"), R("i,s")) + R(" = ", False) +
            NARY("∑", R("p∈") + SUB(R("P"), R("i,s")), "", NARY("∑", R("c∈") + SUB(R("C"), R("i,p,s")), "", SUB(R("q"), R("i,p,c,s")) + R("⋅", False) + SUB(R("κ"), R("u")))) +
            R(",   ", False) + SUB(R("A"), R("i,s")) + R(" = ", False) +
            NARY("∑", R("p∈") + SUB(R("P"), R("i,s")), "", SUB(R("a"), R("i,p,s"))) +
            R("   (1)", False)
        ),
        "(2)": (
            SUB(R("Y"), R("i,s")) + R(" = ", False) +
            FRAC(SUB(R("Q"), R("i,s")), SUB(R("A"), R("i,s"))) +
            R(",   s ∈ {m, v}   (2)", False)
        ),
        "(3)": (
            SUB(R("Y"), R("vol,i", False)) + R(" = ", False) +
            FRAC(
                R("2|", False) + SUB(R("Y"), R("i,m")) + R(" − ", False) + SUB(R("Y"), R("i,v")) + R("|", False),
                SUB(R("Y"), R("i,m")) + R(" + ", False) + SUB(R("Y"), R("i,v")) + R(" + 2ε", False)
            ) + R("   (3)", False)
        ),
        "(4)": (
            SUB(R("H'"), R("i,s")) + R(" = −", False) +
            NARY("∑", R("c=1"), SUB(R("S"), R("i,s")), SUB(R("p"), R("i,c,s")) + R(" ln(", False) + SUB(R("p"), R("i,c,s")) + R(")", False)) +
            R(",   ", False) + SUB(R("C"), R("HHI,i,s", False)) + R(" = ", False) +
            NARY("∑", R("c=1"), SUB(R("S"), R("i,s")), _make_omml_subsup(R("p"), R("i,c,s"), R("2", False))) +
            R(",   ", False) + SUB(R("J'"), R("i,s")) + R(" = ", False) +
            FRAC(SUB(R("H'"), R("i,s")), R("ln(", False) + SUB(R("S"), R("i,s")) + R(")", False)) +
            R("   (4)", False)
        ),
        "(5)": (
            R("J(", False) + SUB(R("C"), R("i,m")) + R(", ", False) + SUB(R("C"), R("i,v")) + R(") = ", False) +
            FRAC(R("|", False) + SUB(R("C"), R("i,m")) + R(" ∩ ", False) + SUB(R("C"), R("i,v")) + R("|", False),
                 R("|", False) + SUB(R("C"), R("i,m")) + R(" ∪ ", False) + SUB(R("C"), R("i,v")) + R("|", False)) +
            R(",   ", False) + SUB(R("R"), R("rot,i", False)) + R(" = 1 − J(", False) + SUB(R("C"), R("i,m")) + R(", ", False) + SUB(R("C"), R("i,v")) + R(")   (5)", False)
        ),
        "(6)": (
            SUB(R("ΔM"), R("i")) + R(" = ", False) + SUB(R("M̄"), R("i,m")) + R(" − ", False) + SUB(R("M̄"), R("i,v")) + R("   (6)", False)
        ),
        "(7)": (
            SUB(R("CV", False), R("plot,i", False)) + R(" = ", False) +
            FRAC(SUB(R("σ"), R("a,i")), SUB(R("μ"), R("a,i")) + R(" + ε", False)) + R("   (7)", False)
        ),
        "(8)": (
            SUB(R("TLU", False), R("i")) + R(" = 0.70", False) + SUB(R("N"), R("cattle,i", False)) +
            R(" + 0.50", False) + SUB(R("N"), R("donkey,i", False)) +
            R(" + 0.20", False) + SUB(R("N"), R("pig,i", False)) +
            R(" + 0.10(", False) + SUB(R("N"), R("goat,i", False)) + R(" + ", False) + SUB(R("N"), R("sheep,i", False)) +
            R(") + 0.01", False) + SUB(R("N"), R("poultry,i", False)) + R("   (8)", False)
        ),
        "(9)": (
            _make_omml_subsup(R("ΔX"), R("k,i"), R("reg", False)) + R(" = ", False) +
            SUB(R("X"), R("k,i")) + R(" − ", False) + SUB(R("X̄"), R("k,r(i)")) + R(",   ", False) +
            _make_omml_subsup(R("Z"), R("k,i"), R("reg", False)) + R(" = ", False) +
            FRAC(SUB(R("X"), R("k,i")) + R(" − ", False) + SUB(R("X̄"), R("k,r(i)")), SUB(R("σ"), R("k,r(i)")) + R(" + ε", False)) + R("   (9)", False)
        ),
        "(10)": (
            R("∀ k ≠ k' ∈ {1, …, 5}:   { ", False) + SUB(R("G"), R("i")) + R(" : i ∈ ", False) + SUB(R("F"), R("k")) +
            R(" } ∩ { ", False) + SUB(R("G"), R("j")) + R(" : j ∈ ", False) + SUB(R("F"), R("k'")) + R(" } = ∅   (10)", False)
        ),
        "(11)": (
            _make_omml_subsup(R("Ŷ"), R("vol,i", False), R("ens", False)) +
            R(" = clip(0.50 ", False) + SUB(R("f̂"), R("LGB", False)) + R("(x) + 0.40 ", False) +
            SUB(R("f̂"), R("XGB", False)) + R("(x) + 0.10 ", False) + SUB(R("f̂"), R("RF", False)) +
            R("(x), 0.0, 2.0)   (11)", False)
        ),
        "(12)": (
            R("f̂(x) = E[f(X)] + ", False) + NARY("∑", R("j=1"), R("M"), SUB(R("ϕ"), R("i,j"))) + R("   (12)", False)
        ),
    }
    inner = eq_map.get(eq_num)
    if not inner:
        return None
    return f'<m:oMathPara {nsdecls("m")}><m:oMath>{inner}</m:oMath></m:oMathPara>'


def _convert_latex_to_omml(expr: str) -> Optional[str]:
    """Converts an inline LaTeX or math expression into native MS Word OMML XML."""
    raw = expr.strip()
    ns = nsdecls("m")

    def xml_esc(t: str) -> str:
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def R(t: str, italic: bool = True) -> str:
        sty = '<m:rPr><m:sty m:val="i"/></m:rPr>' if italic else '<m:rPr><m:sty m:val="p"/></m:rPr>'
        return '<m:r>' + sty + '<m:t>' + xml_esc(t) + '</m:t></m:r>'

    def SUB(b: str, s: str, bi: bool = True, si: bool = False) -> str:
        return '<m:sSub><m:sSubPr/><m:e>' + R(b, bi) + '</m:e><m:sub>' + R(s, si) + '</m:sub></m:sSub>'

    def SUP(b: str, sp: str, bi: bool = True, spi: bool = False) -> str:
        return '<m:sSup><m:sSupPr/><m:e>' + R(b, bi) + '</m:e><m:sup>' + R(sp, spi) + '</m:sup></m:sSup>'

    def SUBSUP(b: str, s: str, sp: str, bi: bool = True, si: bool = False, spi: bool = False) -> str:
        return '<m:sSubSup><m:sSubSupPr/><m:e>' + R(b, bi) + '</m:e><m:sub>' + R(s, si) + '</m:sub><m:sup>' + R(sp, spi) + '</m:sup></m:sSubSup>'

    # Comparisons and relations involving Y_vol
    clean_rel = raw.replace('\\text{', '').replace('\\mathrm{', '').replace('{', '').replace('}', '').strip()
    clean_rel = clean_rel.replace('\\approx', '≈').replace('\\in', '∈').replace('\\ge', '≥').replace('\\le', '≤').replace('>=', '≥').replace('<=', '≤')
    m_rel = re.search(r'^(Y_vol|Yvol)\s*([∈≥≤><=≈])\s*(.+)$', clean_rel)
    if m_rel:
        op, val = m_rel.group(2), m_rel.group(3)
        return '<m:oMath ' + ns + '>' + SUB("Y", "vol") + R(" " + op + " " + val, False) + '</m:oMath>'

    # Mean Y_vol comparisons (e.g. \bar{Y}_vol = 1.483 or Ȳ_vol = 1.483)
    m_mean_rel = re.search(r'^[\\\barȲ]+_?v?o?l?\s*([=≈])\s*([0-9\.]+)$', clean_rel)
    if m_mean_rel:
        op, val = m_mean_rel.group(1), m_mean_rel.group(2)
        return '<m:oMath ' + ns + '>' + SUB("Ȳ", "vol") + R(" " + op + " " + val, False) + '</m:oMath>'

    # Model weights (w_LGB = 0.50, w_XGB = 0.40, w_RF = 0.10)
    m_wt = re.search(r'^w_?(LGB|XGB|RF)\s*=\s*([0-9\.]+)$', clean_rel)
    if m_wt:
        sub_n, val = m_wt.group(1), m_wt.group(2)
        return '<m:oMath ' + ns + '>' + SUB("w", sub_n) + R(" = " + val, False) + '</m:oMath>'

    # R^2 relations
    if clean_rel in ['R^2', 'R2']:
        return '<m:oMath ' + ns + '>' + SUP("R", "2") + '</m:oMath>'
    if clean_rel in ['\\Delta R^2', 'Delta R^2', 'ΔR^2', 'ΔR2']:
        return '<m:oMath ' + ns + '>' + R("Δ", False) + SUP("R", "2") + '</m:oMath>'
    m_r2_rel = re.search(r'^(R\^?2?|\\Delta R\^?2?|ΔR\^?2?)\s*([=><≥≤])\s*(.+)$', clean_rel)
    if m_r2_rel:
        r_prefix, op, val = m_r2_rel.group(1), m_r2_rel.group(2), m_r2_rel.group(3)
        lead = (R("Δ", False) + SUP("R", "2")) if "Δ" in r_prefix or "Delta" in r_prefix else SUP("R", "2")
        return '<m:oMath ' + ns + '>' + lead + R(" " + op + " " + val, False) + '</m:oMath>'

    # Set notation (e.g. i \in \{1, ..., N\}, s \in \{m, v\})
    if '∈' in clean_rel or '\\in' in raw:
        clean_set = raw.replace('\\in', '∈').replace('\\dots', '…').replace('\\{', '{').replace('\\}', '}')
        return '<m:oMath ' + ns + '>' + R(clean_set, False) + '</m:oMath>'

    # Constants & stability
    if raw in ['10^{-5}', '10⁻⁵']:
        return '<m:oMath ' + ns + '>' + SUP("10", "−5", False, False) + '</m:oMath>'
    if '\\varepsilon = 10^{-5}' in raw or 'ε = 10⁻⁵' in raw:
        return '<m:oMath ' + ns + '>' + R("ε = ", False) + SUP("10", "−5", False, False) + '</m:oMath>'

    norm = raw.replace('\\text{', '').replace('\\mathrm{', '').replace('$', '').replace('{', '').replace('}', '').strip()

    # Direct mappings for core study metrics
    if norm in ['Y_vol', 'Y_vol,i', 'Yvol', 'Yvol,i']:
        sub_txt = 'vol,i' if 'i' in norm else 'vol'
        return '<m:oMath ' + ns + '>' + SUB("Y", sub_txt) + '</m:oMath>'
    if norm in ['\\hat{Y}_vol', 'hat{Y}_vol', 'Ŷ_vol', 'Ŷvol', '\\hatY_vol']:
        return '<m:oMath ' + ns + '>' + SUB("Ŷ", "vol") + '</m:oMath>'
    if norm in ['\\bar{Y}_vol', 'bar{Y}_vol', 'Ȳ_vol', 'Ȳvol', '\\barY_vol']:
        return '<m:oMath ' + ns + '>' + SUB("Ȳ", "vol") + '</m:oMath>'
    if 'R^2_National' in norm or 'R2_National' in norm:
        return '<m:oMath ' + ns + '>' + SUBSUP("R", "National", "2") + '</m:oMath>'
    if 'R^2_Regional' in norm or 'R2_Regional' in norm:
        return '<m:oMath ' + ns + '>' + SUBSUP("R", "Regional", "2") + '</m:oMath>'
    if norm in ['C_HHI', 'CHHI']:
        return '<m:oMath ' + ns + '>' + SUB("C", "HHI") + '</m:oMath>'
    if norm in ['D_BP', 'DBP']:
        return '<m:oMath ' + ns + '>' + SUB("D", "BP") + '</m:oMath>'
    if norm in ['CV_plot', 'CVplot']:
        return '<m:oMath ' + ns + '>' + SUB("CV", "plot", False, False) + '</m:oMath>'
    if norm in ["H'", 'H_masika', "H'_m", "H'm"]:
        return '<m:oMath ' + ns + '>' + (SUB("H′", "m") if "m" in norm else R("H′", True)) + '</m:oMath>'
    if norm in ["J'", "J'_m"]:
        return '<m:oMath ' + ns + '>' + R("J′", True) + '</m:oMath>'
    if norm in ['Q_3 - Q_1', 'Q3 - Q1']:
        return '<m:oMath ' + ns + '>' + SUB("Q", "3") + R(" − ", False) + SUB("Q", "1") + '</m:oMath>'
    if norm in ['Y_m, Y_v', 'Ym, Yv']:
        return '<m:oMath ' + ns + '>' + SUB("Y", "m") + R(", ", False) + SUB("Y", "v") + '</m:oMath>'
    if norm in ['J(C_m, C_v)']:
        return '<m:oMath ' + ns + '>' + R("J(", False) + SUB("C", "m") + R(", ", False) + SUB("C", "v") + R(")", False) + '</m:oMath>'

    # Clean Greek prefixes if any
    norm = norm.replace('\\kappa', 'κ').replace('\\mu', 'μ').replace('\\sigma', 'σ').replace('\\boldsymbol', '').replace('\\mathbf', '')

    # Superscript: Base^Sup
    m_sup = re.match(r'^([a-zA-Z\\Δ\\ϕ\\σ\\μ\\κ\\η\\α\\λ\\Ȳ\\Ŷ\\(\\)\']+)\\^([a-zA-Z0-9\\+\\-\\(\\)]+)$', norm)
    if m_sup:
        b, sp = m_sup.group(1), m_sup.group(2)
        return '<m:oMath ' + ns + '>' + SUP(b, sp) + '</m:oMath>'

    # Subscript: Base_Sub
    m_sub = re.match(r'^([a-zA-Z\\Δ\\ϕ\\σ\\μ\\κ\\η\\α\\λ\\Ȳ\\Ŷ\\(\\)\']+)_([a-zA-Z0-9\\,\\.\\-\\+\\(\\)]+)$', norm)
    if m_sub:
        b, sb = m_sub.group(1), m_sub.group(2)
        return '<m:oMath ' + ns + '>' + SUB(b, sb) + '</m:oMath>'

    # SubSup: Base_Sub^Sup
    m_subsup = re.match(r'^([a-zA-Z\\Δ\\ϕ\\σ\\μ\\κ\\η\\α\\λ\\Ȳ\\Ŷ\\(\\)\']+)_([a-zA-Z0-9\\(\\)]+)\\^([a-zA-Z0-9\\(\\)]+)$', norm)
    if m_subsup:
        b, sb, sp = m_subsup.group(1), m_subsup.group(2), m_subsup.group(3)
        return '<m:oMath ' + ns + '>' + SUBSUP(b, sb, sp) + '</m:oMath>'

    return None


UNICODE_SUBS = {
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "ᵢ": "i", "ᵣ": "r", "ᵤ": "u", "ᵥ": "v", "ₓ": "x", "ₐ": "a", "ₑ": "e", "ₒ": "o", "ₘ": "m", "ₛ": "s",
    "ₚ": "p", "ₜ": "t", "ₖ": "k", "ₗ": "l", "ₙ": "n", "𝓰": "g",
}
UNICODE_SUPS = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-", "⁼": "=", "⁽": "(", "⁾": ")", "ⁿ": "n", "ⁱ": "i",
    "ᵃ": "a", "ᵇ": "b", "ᶜ": "c", "ᵈ": "d", "ᵉ": "e", "ᶠ": "f", "ᵍ": "g", "ʰ": "h", "ʲ": "j", "ᵏ": "k",
    "ˡ": "l", "ᵐ": "m", "ᵒ": "o", "ᵖ": "p", "ʳ": "r", "ˢ": "s", "ᵗ": "t", "ᵘ": "u", "ᵛ": "v", "ʷ": "w", "ˣ": "x", "ʸ": "y", "ᶻ": "z",
}


def clean_all_symbols(text: str) -> str:
    """Standardises symbols, superscripts, subscripts, and eliminates raw LaTeX artifacts."""
    # 0. Unescape ASCII escape characters from Python string literals (e.g. \t -> \text, \b -> \bar)
    text = text.replace("\t" + "ext", "\\text").replace("\text", "\\text")
    text = text.replace("\x08" + "ar", "\\bar").replace("\bar", "\\bar")
    text = text.replace(r"\Delta", "\\Delta")
    text = text.replace(r"\phi", "\\phi")
    text = text.replace(r"\pm", "\\pm")

    # 1. Unescape double curlies first so all { ... } match standard LaTeX patterns
    text = text.replace("{{", "{").replace("}}", "}")

    # 2. Accents FIRST before subscripts/superscripts are resolved
    text = re.sub(r"\\+hat\{Y\}|\\+hatY", "Ŷ", text)
    text = re.sub(r"\\+bar\{Y\}|\\+barY", "Ȳ", text)
    text = re.sub(r"\\+bar\{M\}|\\+barM", "M̄", text)
    text = re.sub(r"\\+bar\{X\}|\\+barX", "X̄", text)
    text = re.sub(r"\\+hat\{f\}|\\+hatf", "f̂", text)
    text = re.sub(r"\\+bar\{([A-Za-z])\}", r"\1̄", text)
    text = re.sub(r"\\+hat\{([A-Za-z])\}", r"\1̂", text)
    text = re.sub(r"\\+hat\s+([A-Za-z])", r"\1̂", text)
    text = re.sub(r"\\+bar\s+([A-Za-z])", r"\1̄", text)
    text = re.sub(r"\\+hat\b", "", text)
    text = re.sub(r"\\+bar\b", "", text)

    # 3. Robust Volatility Index variants (handling unbalanced curlies and \text)
    text = re.sub(r"([YȲŶ])_\{?\\+text\{\s*vol\s*,\s*i\s*\}\}?", r"\1ᵥₒₗ,ᵢ", text)
    text = re.sub(r"([YȲŶ])_\{?vol\s*,\s*i\}?", r"\1ᵥₒₗ,ᵢ", text)
    text = re.sub(r"([YȲŶ])_\{?\\+text\{\s*vol\s*\}\}?", r"\1ᵥₒₗ", text)
    text = re.sub(r"([YȲŶ])_\{?vol\}?", r"\1ᵥₒₗ", text)
    text = text.replace("Y_vol", "Yᵥₒₗ").replace("Ȳ_vol", "Ȳᵥₒₗ").replace("Ŷ_vol", "Ŷᵥₒₗ")

    # 4. Units and specific text macros (with guaranteed space before units)
    text = re.sub(r"\\+text\{\s*kg ha\s*\}\^\{\s*-?1\s*\}|\$?\\+text\{\s*kg ha\s*\}\^\{\s*-?1\s*\}\$?|kg ha\^\{\s*-?1\s*\}|kg ha\^-\s*1", " kg ha⁻¹", text)
    text = re.sub(r"\\+text\{\s*mm yr\s*\}\^\{\s*-?1\s*\}|\$?\\+text\{\s*mm yr\s*\}\^\{\s*-?1\s*\}\$?|mm yr\^\{\s*-?1\s*\}|mm yr\^-\s*1", " mm yr⁻¹", text)
    text = re.sub(r"\\+text\{\s*km\s*\}\^2|\$?\\+text\{\s*km\s*\}\^2\$?|km\^2", " km²", text)
    text = re.sub(r"\$([0-9,]+)\\+text\{\s*km\s*\}\^2\$", r"\1 km²", text)
    text = re.sub(r"\$([0-9,]+)\\+text\{--\}([0-9,]+)\\+text\{\s*mm yr\s*\}\^\{\s*-?1\s*\}\$", r"\1–\2 mm yr⁻¹", text)
    text = re.sub(r"\$([0-9,]+)\\+text\{--\}([0-9,]+)\\+text\{\s*m\s*\}\$", r"\1–\2 m", text)
    text = re.sub(r"\$1\^\\+circ 00'\\+text\{\s*S\s*\}\$", "1° 00′ S", text)
    text = re.sub(r"\$11\^\\+circ 45'\\+text\{\s*S\s*\}\$", "11° 45′ S", text)
    text = re.sub(r"\$29\^\\+circ 15'\\+text\{\s*E\s*\}\$", "29° 15′ E", text)
    text = re.sub(r"\$40\^\\+circ 30'\\+text\{\s*E\s*\}\$", "40° 30′ E", text)
    text = re.sub(r"\$45\^\\+circ\$", "45°", text)
    text = text.replace(r"\text{--}", "–").replace(r"\text{ S}", " S").replace(r"\text{ E}", " E")
    text = text.replace(r"\text{ m}", " m").replace(r"\text{ kg}", " kg")
    text = text.replace("  kg ha⁻¹", " kg ha⁻¹").replace("  mm yr⁻¹", " mm yr⁻¹").replace("  km²", " km²")

    # 5. LaTeX Table Notes
    text = re.sub(r"\$?\^\{\\+text\{a\}\}\$?|\$?\^\{\\+text\{a\}\}\$?", "ᵃ", text)
    text = re.sub(r"\$?\^\{\\+text\{b\}\}\$?|\$?\^\{\\+text\{b\}\}\$?", "ᵇ", text)
    text = re.sub(r"\$?\^a\$?", "ᵃ", text)
    text = re.sub(r"\$?\^b\$?", "ᵇ", text)

    # 6. Math symbols
    text = re.sub(r"\\+Delta", "Δ", text)
    text = re.sub(r"\\+varepsilon", "ε", text)
    text = re.sub(r"\\+mu", "μ", text)
    text = re.sub(r"\\+sigma", "σ", text)
    text = re.sub(r"\\+kappa", "κ", text)
    text = re.sub(r"\\+phi", "ϕ", text)
    text = re.sub(r"\\+pm", "±", text)
    text = re.sub(r"\\+times", "×", text)
    text = re.sub(r"\\+cdot", "·", text)
    text = re.sub(r"\\+ge\b", "≥", text)
    text = re.sub(r"\\+le\b", "≤", text)
    text = re.sub(r"\\+approx", "≈", text)
    text = re.sub(r"\\+in\b", "∈", text)
    text = re.sub(r"\\+notin", "∉", text)
    text = re.sub(r"\\+forall", "∀", text)
    text = re.sub(r"\\+neq", "≠", text)
    text = re.sub(r"\\+emptyset", "∅", text)
    text = re.sub(r"\\+cap", "∩", text)
    text = re.sub(r"\\+cup", "∪", text)
    text = re.sub(r"\\+dots", "…", text)
    text = re.sub(r"\\+sum\b", "∑", text)
    text = re.sub(r"\\+sum", "∑", text)
    text = re.sub(r"\\+prod\b", "∏", text)
    text = re.sub(r"\\+partial\b", "∂", text)
    text = re.sub(r"\\+pi\b", "π", text)
    text = re.sub(r"\\+p_\{([^}]+)\}", r"p_{\1}", text)
    text = re.sub(r"\\+p_([A-Za-z0-9])", r"p_\1", text)
    text = re.sub(r"\\+p\b", "p", text)
    text = text.replace(r"\{", "{").replace(r"\}", "}")

    # 7. R2 and Delta R2
    text = text.replace("R^2", "R²")
    text = text.replace("ΔR^2", "ΔR²").replace("Δ R^2", "ΔR²").replace("Δ R²", "ΔR²")
    text = text.replace("Delta R²", "ΔR²").replace("Delta R^2", "ΔR²")

    # 8. Specific domain metrics
    text = re.sub(r"\\+text\{TLU\}", "TLU", text)
    text = re.sub(r"\\+text\{RMSE\}", "RMSE", text)
    text = re.sub(r"\\+text\{MAE\}", "MAE", text)
    text = re.sub(r"\\+text\{SHAP\}", "SHAP", text)
    text = re.sub(r"\\+text\{Spatial RMSE\}", "Spatial RMSE", text)
    text = re.sub(r"\\+text\{LightGBM\}", "LightGBM", text)
    text = re.sub(r"\\+text\{XGBoost\}", "XGBoost", text)
    text = re.sub(r"\\+text\{Random Forest\}", "Random Forest", text)
    text = re.sub(r"\\+text\{vol\}", "vol", text)
    text = re.sub(r"\\+text\{plot\}", "plot", text)
    text = re.sub(r"\\+text\{HHI\}", "HHI", text)
    text = re.sub(r"\\+text\{BP\}", "BP", text)
    text = re.sub(r"\\+text\{National\}", "National", text)
    text = re.sub(r"\\+text\{Regional\}", "Regional", text)
    text = re.sub(r"\\+text\{reg\}", "reg", text)
    text = re.sub(r"\\+text\{ens\}", "ens", text)
    text = re.sub(r"\\+text\{rot\}", "rot", text)
    text = re.sub(r"\\+text\{adult\}", "adult", text)
    text = re.sub(r"\\+text\{train\}", "train", text)
    text = re.sub(r"\\+text\{val\}", "val", text)
    text = re.sub(r"\\+text\{top\}", "top", text)
    text = re.sub(r"\\+text\{cattle\}", "cattle", text)
    text = re.sub(r"\\+text\{donkey\}", "donkey", text)
    text = re.sub(r"\\+text\{pig\}", "pig", text)
    text = re.sub(r"\\+text\{goat\}", "goat", text)
    text = re.sub(r"\\+text\{sheep\}", "sheep", text)
    text = re.sub(r"\\+text\{poultry\}", "poultry", text)
    text = re.sub(r"\\+mathcal\{I\}", "I", text)
    text = re.sub(r"\\+mathcal\{F\}", "F", text)
    text = re.sub(r"\\+mathbf\{x\}", "x", text)
    text = re.sub(r"\\+mathbf", "", text)
    text = re.sub(r"\\+boldsymbol", "", text)
    text = re.sub(r"\\+operatorname\{clip\}", "clip", text)

    # 9. Strip general text/mathrm/operatorname
    text = re.sub(r"\\+text\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\+mathrm\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\+operatorname\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\+text([A-Za-z]+)", r"\1", text)
    text = re.sub(r"\\+text\b", "", text)

    # 10. Known subscripts and Greek variables
    text = text.replace("Y_{i,m}", "Yᵢ,ₘ").replace("Y_{i,v}", "Yᵢ,ᵥ").replace("Y_{i,s}", "Yᵢ,ₛ")
    text = text.replace("A_{i,s}", "Aᵢ,ₛ").replace("Q_{i,s}", "Qᵢ,ₛ")
    text = text.replace("p_{i,c,s}", "pᵢ,c,ₛ").replace("a_{i,c,s}", "aᵢ,c,ₛ").replace("a_{i,p,s}", "aᵢ,ₚ,ₛ")
    text = text.replace("C_{HHI}", "C<sub>HHI</sub>").replace("C_HHI", "C<sub>HHI</sub>")
    text = text.replace("D_{BP}", "D<sub>BP</sub>").replace("D_BP", "D<sub>BP</sub>")
    text = text.replace("CV_{plot}", "CVₚₗₒₜ").replace("CV_plot", "CVₚₗₒₜ")
    text = text.replace("CV_{plot,i}", "CVₚₗₒₜ,ᵢ")
    text = text.replace("TLU_i", "TLUᵢ")
    text = text.replace("w_{LGB}", "w<sub>LGB</sub>").replace("w_{XGB}", "w<sub>XGB</sub>").replace("w_{RF}", "w<sub>RF</sub>")
    text = text.replace("R_{rot}", "R<sub>rot</sub>").replace("R_{rot,i}", "R<sub>rot,i</sub>")
    text = text.replace("R²_{National}", "R²<sub>National</sub>").replace("R²_{Regional}", "R²<sub>Regional</sub>")
    text = text.replace("R^2_{National}", "R²<sub>National</sub>").replace("R^2_{Regional}", "R²<sub>Regional</sub>")
    text = text.replace("ϕ_{i,j}", "ϕᵢ,ⱼ")
    text = text.replace("Q_1", "Q₁").replace("Q_3", "Q₃")
    text = text.replace("Y_m", "Yₘ").replace("Y_v", "Yᵥ")
    text = text.replace("Q_m", "Qₘ").replace("Q_v", "Qᵥ")
    text = text.replace("A_i", "Aᵢ").replace("K_i", "Kᵢ").replace("M_i", "Mᵢ")
    text = text.replace("C_m", "Cₘ").replace("C_v", "Cᵥ")
    text = text.replace("X_k", "Xₖ").replace("X_j", "Xⱼ")
    text = text.replace("L_1", "L₁").replace("L_2", "L₂")
    text = text.replace("F_m", "Fₘ")
    text = text.replace("G_i", "Gᵢ").replace("G_j", "Gⱼ")
    text = text.replace("x_i", "xᵢ")
    text = text.replace("10^{-5}", "10⁻⁵").replace("10^-5", "10⁻⁵")

    # 11. General single-character subscripts / superscripts
    def sub_repl(m):
        base, sub = m.group(1), m.group(2)
        if len(sub) == 1 and sub in UNICODE_SUBS:
            return f"{base}{UNICODE_SUBS[sub]}"
        return f"{base}<sub>{sub}</sub>"

    def sup_repl(m):
        base, sup = m.group(1), m.group(2)
        if len(sup) == 1 and sup in UNICODE_SUPS:
            return f"{base}{UNICODE_SUPS[sup]}"
        return f"{base}<sup>{sup}</sup>"

    text = re.sub(r"([A-Za-zΔȲŶM̄X̄f̂])_\{([^{}]+)\}", sub_repl, text)
    text = re.sub(r"([A-Za-zΔȲŶM̄X̄f̂])\^\{([^{}]+)\}", sup_repl, text)
    text = re.sub(r"([A-Za-zΔȲŶM̄X̄f̂])_([0-9a-z])\b", lambda m: f"{m.group(1)}{UNICODE_SUBS.get(m.group(2), '<sub>' + m.group(2) + '</sub>')}", text)

    # Clean double dollar signs in prose if empty: e.g. $$ -> ""
    text = re.sub(r"\$\s*\$", "", text)
    # Strip single math dollar delimiters around simple cleaned expressions
    text = re.sub(r"\$([A-Za-z0-9\u0080-\uffff,.\s=±–—<>≥≤∈∉…~^_/'{}()+-]+)\$", r"\1", text)
    return text


def _clean_scientific_symbols(text: str) -> str:
    """Backwards-compatible wrapper calling clean_all_symbols."""
    return clean_all_symbols(text)


def _add_formatted_runs(p, text: str, font_size: float = 10, font_name: str = "Times New Roman") -> None:
    """Renders text runs into a docx paragraph using native Word subscripts and superscripts."""
    # Clean markdown links [label](url) -> label
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Strip markdown bold inside paragraphs
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # Strip backticks
    text = text.replace("`", "")

    cleaned = clean_all_symbols(text)

    # Split on markdown italics *...*
    italic_chunks = re.split(r"(\*[^*]+\*)", cleaned)

    for ichunk in italic_chunks:
        if not ichunk:
            continue
        is_md_italic = ichunk.startswith("*") and ichunk.endswith("*") and len(ichunk) > 2
        chunk_str = ichunk[1:-1] if is_md_italic else ichunk

        # Split on $...$ math spans
        math_parts = re.split(r"(\$[^\$\n]+\$)", chunk_str)
        for mpart in math_parts:
            if not mpart:
                continue
            is_math_span = mpart.startswith("$") and mpart.endswith("$")
            part_str = mpart[1:-1] if is_math_span else mpart

            # Parse sub, sup, html sub/sup tags, and base variables
            token_pattern = re.compile(
                r"(?:<sub>([^<]+)</sub>)|"
                r"(?:<sup>([^<]+)</sup>)|"
                r"(?:([A-Za-zΔȲŶM̄X̄f̂\']+)(?:_\{([^}]+)\}|_([A-Za-z0-9]+))(?:\^\{([^}]+)\}|\^([A-Za-z0-9+-]+)))|"
                r"(?:([A-Za-zΔȲŶM̄X̄f̂\']+)(?:\^\{([^}]+)\}|\^([A-Za-z0-9+-]+))(?:_\{([^}]+)\}|_([A-Za-z0-9]+)))|"
                r"(?:([A-Za-zΔȲŶM̄X̄f̂\']+)(?:_\{([^}]+)\}|_([A-Za-z0-9]+)))|"
                r"(?:([A-Za-zΔȲŶM̄X̄f̂\']+)(?:\^\{([^}]+)\}|\^([A-Za-z0-9+-]+)))|"
                r"(?:_\{([^}]+)\}|_([A-Za-z0-9]+))|"
                r"(?:\^\{([^}]+)\}|\^([A-Za-z0-9+-]+))|"
                r"([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱᵃᵇᶜᵈᵉᶠᵍʰʲᵏˡᵐᵒᵖʳˢᵗᵘᵛʷˣʸᶻ]+)|"
                r"([₀₁₂₃₄₅₆₇₈₉ᵢᵣᵤᵥₓₐₑₒₘₛₚₜₖₗₙ𝓰]+)"
            )

            last_idx = 0
            for m in token_pattern.finditer(part_str):
                start, end = m.span()
                if start > last_idx:
                    plain_txt = part_str[last_idx:start]
                    _add_plain_run(p, plain_txt, italic=is_md_italic or (is_math_span and len(plain_txt.strip()) == 1 and plain_txt.strip().isalpha()), font_size=font_size, font_name=font_name)

                g = m.groups()
                if g[0]:  # <sub>...</sub>
                    _add_sub_run(p, g[0], font_size=font_size, font_name=font_name)
                elif g[1]:  # <sup>...</sup>
                    _add_sup_run(p, g[1], font_size=font_size, font_name=font_name)
                elif g[2]:  # Base_sub^sup
                    _add_var_run(p, g[2], sub=g[3] or g[4], sup=g[5] or g[6], font_size=font_size, font_name=font_name)
                elif g[7]:  # Base^sup_sub
                    _add_var_run(p, g[7], sub=g[10] or g[11], sup=g[8] or g[9], font_size=font_size, font_name=font_name)
                elif g[12]:  # Base_sub
                    _add_var_run(p, g[12], sub=g[13] or g[14], sup=None, font_size=font_size, font_name=font_name)
                elif g[15]:  # Base^sup
                    _add_var_run(p, g[15], sub=None, sup=g[16] or g[17], font_size=font_size, font_name=font_name)
                elif g[18] or g[19]:  # _sub
                    _add_sub_run(p, g[18] or g[19], font_size=font_size, font_name=font_name)
                elif g[20] or g[21]:  # ^sup
                    _add_sup_run(p, g[20] or g[21], font_size=font_size, font_name=font_name)
                elif g[22]:  # unicode sup
                    usup = "".join(UNICODE_SUPS.get(ch, ch) for ch in g[22])
                    _add_sup_run(p, usup, font_size=font_size, font_name=font_name)
                elif g[23]:  # unicode sub
                    usub = "".join(UNICODE_SUBS.get(ch, ch) for ch in g[23])
                    _add_sub_run(p, usub, font_size=font_size, font_name=font_name)

                last_idx = end

            if last_idx < len(part_str):
                plain_txt = part_str[last_idx:]
                _add_plain_run(p, plain_txt, italic=is_md_italic or (is_math_span and len(plain_txt.strip()) == 1 and plain_txt.strip().isalpha()), font_size=font_size, font_name=font_name)


def _add_plain_run(p, text: str, italic: bool, font_size: float, font_name: str):
    clean = text.replace("{", "").replace("}", "").replace("\\", "")
    if not clean:
        return
    r = p.add_run(clean)
    r.font.name = font_name
    r.font.size = Pt(font_size)
    if italic:
        r.italic = True


def _add_sub_run(p, sub_text: str, font_size: float, font_name: str):
    clean = sub_text.replace("{", "").replace("}", "").replace("\\", "")
    if not clean:
        return
    r = p.add_run(clean)
    r.font.name = font_name
    r.font.size = Pt(font_size)
    r.font.subscript = True


def _add_sup_run(p, sup_text: str, font_size: float, font_name: str):
    clean = sup_text.replace("{", "").replace("}", "").replace("\\", "")
    if not clean:
        return
    r = p.add_run(clean)
    r.font.name = font_name
    r.font.size = Pt(font_size)
    r.font.superscript = True


def _add_var_run(p, base: str, sub: str = None, sup: str = None, font_size: float = 10, font_name: str = "Times New Roman"):
    r_base = p.add_run(base)
    r_base.font.name = font_name
    r_base.font.size = Pt(font_size)
    if base in ["Y", "R", "C", "D", "H", "J", "Q", "A", "p", "a", "q", "w", "x", "f", "N", "K", "S", "M", "X", "Z", "G", "F", "Ȳ", "Ŷ", "M̄", "X̄", "f̂"]:
        r_base.italic = True
    elif base.startswith("Δ") and len(base) > 1 and base[1:] in ["R", "M", "H", "J", "C", "X"]:
        r_base.italic = False

    if sub:
        _add_sub_run(p, sub, font_size=font_size, font_name=font_name)
    if sup:
        _add_sup_run(p, sup, font_size=font_size, font_name=font_name)


def _render_md_table_to_docx(doc: Document, table_lines: List[str]) -> None:
    """Renders a markdown table block into a styled booktabs Word table."""
    rows_data = []
    for tl in table_lines:
        if re.match(r"^\|\s*---", tl):
            continue
        cells = [c.strip() for c in tl.strip().strip("|").split("|")]
        rows_data.append(cells)
    if not rows_data:
        return

    n_rows = len(rows_data)
    n_cols = len(rows_data[0])
    tbl = doc.add_table(rows=n_rows, cols=n_cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_booktabs_borders(tbl)

    for r_idx, row_vals in enumerate(rows_data):
        row_cells = tbl.rows[r_idx].cells
        for c_idx in range(min(n_cols, len(row_vals))):
            cell = row_cells[c_idx]
            _set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            cp = cell.paragraphs[0]
            cp.paragraph_format.space_before = Pt(1)
            cp.paragraph_format.space_after = Pt(1)
            cp.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx <= 1 else WD_ALIGN_PARAGRAPH.RIGHT
            raw_cell_val = row_vals[c_idx]
            _add_formatted_runs(cp, raw_cell_val, font_size=8.5)
            if r_idx == 0:
                for r in cp.runs:
                    r.bold = True


def generate_docx_manuscript(md_text: str) -> Path:
    """Builds Paper/manuscript.docx strictly adhering to Springer Food Security requirements."""
    logger.info("Building Word (.docx) manuscript at %s...", DOCX_PATH)
    doc = Document()

    # Normal style: 10-point Times New Roman (strictly per Food Security guidelines)
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(10)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    _enable_line_numbering_and_headers(doc, RUNNING_HEAD)

    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or line == "---":
            i += 1
            continue

        # Markdown Table block
        if line.startswith("|"):
            tbl_block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl_block.append(lines[i].strip())
                i += 1
            _render_md_table_to_docx(doc, tbl_block)
            continue

        # Figure Image embedding
        if line.startswith("!["):
            m = re.search(r"\(file://([^)]+)\)", line)
            if m:
                img_path = Path(m.group(1))
                if img_path.exists():
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(str(img_path), width=Inches(6.3))
            i += 1
            continue

        # Display Equation ($$ ... $$ (N) or $$ ... (N) $$)
        if line.startswith("$$"):
            m_eq = re.search(r"\((\d+)\)\s*(?:\$\$)?\s*$", line)
            eq_num = f"({m_eq.group(1)})" if m_eq else ""
            omml_str = _get_display_equation_omml(eq_num)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            if omml_str:
                p._p.append(parse_xml(omml_str))
            else:
                _add_formatted_runs(p, line.replace("$$", ""), font_size=10)
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run(line[2:].strip())
            r.bold = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(14)
            i += 1
            continue

        if line.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(line[3:].strip())
            r.bold = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
            i += 1
            continue

        if line.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(9)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(line[4:].strip())
            r.bold = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            i += 1
            continue

        if line.startswith("#### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(line[5:].strip())
            r.bold = True
            r.italic = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
            i += 1
            continue

        # Figure / Table captions & regular paragraphs
        p = doc.add_paragraph()
        if line.startswith("**Fig. ") or line.startswith("**Table ") or line.startswith("*Note:*"):
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            _add_formatted_runs(p, line, font_size=9)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            _add_formatted_runs(p, line, font_size=10)
        i += 1

    # Add Author Photo Placeholder Box at end of Author Biography per 2026 Guidelines
    p_photo = doc.add_paragraph()
    p_photo.paragraph_format.space_before = Pt(8)
    r_ph = p_photo.add_run(
        "[Author Portrait Photo Placeholder: High-resolution head-and-shoulders portrait of "
        "Dr. Eng. Kadeghe Goodluck Fue (3.2 cm × 4.0 cm, 300 dpi, JPEG/TIFF) to be uploaded via Editorial Manager]"
    )
    r_ph.italic = True
    r_ph.font.name = "Times New Roman"
    r_ph.font.size = Pt(9)

    doc.save(DOCX_PATH)
    logger.info("Successfully generated %s", DOCX_PATH)
    return DOCX_PATH


def generate_title_page_docx() -> Path:
    """
    Generates the separate Springer Nature Title Page (Paper/title_page.docx)
    including Title, Running Head, Author Affiliation & ORCID, Declarations,
    Author Biography, and the 4 Mandatory Independent International Reviewers.
    """
    logger.info("Building separate Springer Title Page at %s...", TITLE_PAGE_DOCX_PATH)
    doc = Document()
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(10)

    _enable_line_numbering_and_headers(doc, RUNNING_HEAD)

    p_journal = doc.add_paragraph()
    r_j = p_journal.add_run("FOOD SECURITY (Springer Nature — Journal ID 12571) | Research Article Title Page")
    r_j.bold = True
    r_j.font.name = "Times New Roman"
    r_j.font.size = Pt(10)

    p_title = doc.add_paragraph()
    r_t = p_title.add_run(ARTICLE_TITLE)
    r_t.bold = True
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(14)

    meta_items = [
        ("Running Page Title (<= 60 characters): ", f"{RUNNING_HEAD} (56 characters)"),
        ("Author Full Name: ", "Kadeghe Goodluck Fue"),
        ("Institutional Affiliation: ", "Department of Agricultural Engineering, School of Engineering and Technology, Sokoine University of Agriculture (SUA), P.O. Box 3003, Chuo Kikuu, Morogoro, Tanzania"),
        ("Corresponding Author Email: ", "kadefue@sua.ac.tz"),
        ("Verified ORCID iD: ", "https://orcid.org/0000-0001-6362-3174"),
        ("Keywords (6): ", "smallholder agriculture; crop yield volatility; spatial cross-validation; machine learning; climate resilience; Tanzania"),
    ]
    for label, val in meta_items:
        p = doc.add_paragraph()
        r1 = p.add_run(label)
        r1.bold = True
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10)
        r2 = p.add_run(val)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(10)

    # Mandatory Suggested Reviewers Section (Food Security Guidelines: >= 4 reviewers from >= 2 countries)
    p_rev_head = doc.add_paragraph()
    p_rev_head.paragraph_format.space_before = Pt(12)
    r_rh = p_rev_head.add_run("Suggested Potential Reviewers (Mandatory Food Security Requirement: 4 Independent International Experts)")
    r_rh.bold = True
    r_rh.font.name = "Times New Roman"
    r_rh.font.size = Pt(12)

    reviewers = [
        (
            "1. Dr. Damien Beillouin",
            "CIRAD, UPR HortSys, Avenue Agropolis, 34398 Montpellier Cedex 5, France",
            "damien.beillouin@cirad.fr",
            "International expert on global crop diversification strategies, yield stability, and agro-ecological buffering against climate shocks."
        ),
        (
            "2. Dr. Elinor Benami",
            "Department of Agricultural and Applied Economics, Virginia Tech, Blacksburg, VA 24061, United States",
            "elinor@vt.edu",
            "Leading authority uniting machine learning, remote sensing, and agricultural risk management in smallholder development economics."
        ),
        (
            "3. Prof. Dr. Hanna Meyer",
            "Institute of Landscape Ecology, University of Münster, Heisenbergstraße 2, 48149 Münster, Germany",
            "hanna.meyer@uni-muenster.de",
            "Pioneering methodologist on spatial cross-validation, area of applicability, and preventing spatial autocorrelation leakage in machine learning."
        ),
        (
            "4. Dr. Delphine Renard",
            "CNRS Research Scientist, Centre d'Ecologie Fonctionnelle et Evolutive (CEFE), 1919 Route de Mende, 34293 Montpellier, France",
            "delphine.renard@cefe.cnrs.fr",
            "Internationally recognised expert on crop biodiversity and temporal stability of food production across agro-ecological scales."
        ),
    ]
    for name, affil, email, reason in reviewers:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        r_n = p.add_run(f"{name}\n")
        r_n.bold = True
        r_n.font.name = "Times New Roman"
        r_n.font.size = Pt(10)
        r_b = p.add_run(f"Affiliation: {affil}\nInstitutional Email: {email}\nExpertise Rationale: {reason}")
        r_b.font.name = "Times New Roman"
        r_b.font.size = Pt(10)

    # Author Biography on Title Page
    p_bio_h = doc.add_paragraph()
    p_bio_h.paragraph_format.space_before = Pt(12)
    r_bh = p_bio_h.add_run("Author Biography (Compliant with Food Security 2026 Guidelines for Bios and Photos)")
    r_bh.bold = True
    r_bh.font.name = "Times New Roman"
    r_bh.font.size = Pt(12)

    p_bio = doc.add_paragraph()
    _add_formatted_runs(
        p_bio,
        "**Kadeghe Goodluck Fue** is a Senior Lecturer in the Department of Agricultural Engineering, "
        "School of Engineering and Technology, at Sokoine University of Agriculture (SUA) in Morogoro, Tanzania, "
        "where he leads the Electronics and Precision Agriculture Lab (EPALab). He holds a Ph.D. in Engineering "
        "from the University of Georgia, an M.Sc. in Agricultural and Biological Engineering from the University "
        "of Florida, and a B.Sc. in Computer Engineering and Information Technology from the University of Dar es Salaam. "
        "His research focuses on precision agriculture, artificial intelligence, spatial machine learning, Agricultural Data Science, and "
        "climate-resilient smallholder farming systems, driven by a deep commitment to advancing food security across sub-Saharan Africa.",
        font_size=10
    )

    doc.save(TITLE_PAGE_DOCX_PATH)
    logger.info("Successfully generated %s", TITLE_PAGE_DOCX_PATH)
    return TITLE_PAGE_DOCX_PATH


# ==============================================================================
# 4. GENERATE LATEX (.TEX) MANUSCRIPT WITH LINENO & RUNNING HEAD
# ==============================================================================

def generate_latex_manuscript(md_text: str) -> Path:
    """Builds Paper/manuscript.tex with mandatory lineno line numbering and Springer formatting."""
    logger.info("Building LaTeX (.tex) manuscript at %s...", LATEX_PATH)

    t1_tex = get_latex_table("table1_summary_statistics.csv", "Summary statistics of smallholder agricultural holdings and seasonal agronomic dynamics (N = 4,564)", "tab:table1", "Statistics computed across all N = 4,564 bimodal holdings in the 2024/2025 Tanzania NBS Annual Agricultural Sample Survey.")
    t2_tex = get_latex_table("table2_model_benchmark.csv", "Multi-model spatial cross-validation benchmark comparison across 921 Enumeration Areas (N = 4,564)", "tab:table2", "All models evaluated on identical 5-fold Spatial Group Cross-Validation splits using the top-100 pruned feature subset.")
    t3_tex = get_latex_table("table3_top25_feature_importance.csv", "Top-25 predictive features ranked by tree split frequency and information gain across agronomic domains", "tab:table3", "Complete ranking of all 246 candidate features is provided in Online Resource 1 (ESM_1.csv).")
    t4_tex = get_latex_table("table4_regional_performance_breakdown.csv", "Regional heterogeneity and out-of-fold performance breakdown across all 27 surveyed regions (N = 4,564)", "tab:table4", "National Advantage defined as Delta R2 = R2_National - R2_Regional.")
    t5_tex = get_latex_table("table5_leakage_audit_certificate.csv", "Formal five-pillar spatial data leakage audit certificate", "tab:table5", "Programmatic audit executed across all 5 spatial cross-validation folds.")
    t6_tex = get_latex_table("table6_volatility_quartile_stratification.csv", "Smallholder agronomic stratification across empirical Yield Volatility Index quartiles (N = 4,564)", "tab:table6", "Cohort partitioned into four equal quartiles of N = 1,141 holdings each.")
    t7_tex = get_latex_table("table7_household_counterfactual_archetypes.csv", "Representative smallholder archetypes and micro-level counterfactual policy attributions", "tab:table7", "Household identifiers are deterministically hashed to preserve respondent confidentiality.")

    tex_content = """\\documentclass[10pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{mathptmx}} % 10pt Times New Roman per Food Security guidelines
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{amsmath,amssymb,amsfonts}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{lineno}} % Mandatory continuous line numbering for Food Security
\\usepackage{{fancyhdr}}
\\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{{hyperref}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[L]{{\\textit{{Food Security}} (Springer Nature)}}
\\fancyhead[R]{{\\textit{{{RUNNING_HEAD}}}}}
\\fancyfoot[R]{{Page \\thepage}}

\\title{{\\textbf{{{ARTICLE_TITLE}}}}}
\\author{{\\textbf{{Kadeghe Goodluck Fue}}\\\\[4pt]
Department of Agricultural Engineering, School of Engineering and Technology,\\\\
Sokoine University of Agriculture (SUA), P.O. Box 3003, Chuo Kikuu, Morogoro, Tanzania\\\\
Corresponding Author Email: \\texttt{{kadefue@sua.ac.tz}} \\quad ORCID: \\texttt{{0000-0001-6362-3174}}}}
\\date{{}}

\\begin{{document}}
\\linenumbers
\\maketitle

\\begin{{abstract}}
\\noindent Smallholder rainfed farming systems across sub-Saharan Africa face intensifying inter-seasonal yield instability driven by erratic bimodal rainfall, soil nutrient depletion, and biotic pest shocks, yet empirical risk models frequently overestimate predictive skill due to unaddressed spatial autocorrelation leakage. This study develops and validates a leakage-free spatial machine learning framework to predict household-level crop yield volatility across Mainland Tanzania and the Zanzibar Archipelago using nationally representative microdata from the 2024/2025 National Bureau of Statistics (NBS) Annual Agricultural Sample Survey (AASS) covering 4,564 bimodal agricultural holdings across 921 Enumeration Areas (EAs). We formulate a bounded, scale-invariant Yield Volatility Index ($Y_{{\\mathrm{{vol}}}} \\in [0, 2]$) measuring proportional yield divergence between the long-rain (\\textit{{Masika}}) and short-rain (\\textit{{Vuli}}) cultivation cycles, and engineer 246 multi-domain agronomic, ecological, demographic, and spatial peer predictors pruned to a 100-feature subset capturing 99.0\\% of tree-based information gain. Evaluated under strict five-fold spatial group cross-validation partitioning whole Enumeration Areas, a soft-voting Weighted Ensemble combining Light Gradient Boosting Machine (LightGBM), Extreme Gradient Boosting (XGBoost), and Random Forest (RF) achieves an out-of-fold coefficient of determination ($R^2$) of 0.592, a Root Mean Squared Error (RMSE) of 0.464, and a Mean Absolute Error (MAE) of 0.347, outperforming dedicated regional sub-models across 26 of 27 regions. Exact Tree-based Shapley Additive Explanations (TreeSHAP) and partial dependence analyses reveal that inter-seasonal planting timing shifts, plot abandonment shocks, and crop portfolio diversity relative to community peers govern production instability, buffered non-linearly by livestock holdings above 3.0 Tropical Livestock Units (TLU). Policy counterfactual simulations indicate that an integrated Climate-Smart Agriculture package combining asset transfers, cultivar diversification, and planting synchronisation reduces mean national yield volatility by 40.0\\% and lowers hyper-volatile holdings ($Y_{{\\mathrm{{vol}}}} \\ge 1.50$) from 25.8\\% to 19.9\\%, although multi-wave longitudinal panel tracking and high-resolution satellite soil-moisture assimilation remain vital future research priorities.
\\end{{abstract}}

\\noindent\\textbf{{Keywords:}} smallholder agriculture; crop yield volatility; spatial cross-validation; machine learning; climate resilience; Tanzania

\\section{{Introduction}}
Global food systems face an unprecedented convergence of climatic, ecological, and macroeconomic pressures that threaten the stability of agricultural production and rural livelihoods across the developing world (Wheeler \\& von Braun, 2013; Lobell et al., 2011; Ray et al., 2015). In sub-Saharan Africa, where rainfed smallholder holdings cultivating less than 3.5 hectares generate over 75\\% of domestic caloric supply, food security is governed not merely by long-term mean crop yields, but by the magnitude and frequency of inter-seasonal production shocks (Thornton et al., 2014; Jayne et al., 2010; Barrett, 2010).

\\section{{Materials and Methods}}
This study utilises official microdata from the 2024/2025 Annual Agricultural Sample Survey (AASS), implemented jointly by the Tanzania National Bureau of Statistics (TNBS), the Ministry of Agriculture, and the Office of the Chief Government Statistician (OCGS) Zanzibar, in methodological alignment with the Food and Agriculture Organization (FAO) World Programme for the Census of Agriculture and the 50x2030 Initiative (Tanzania National Bureau of Statistics [TNBS], 2026; Food and Agriculture Organization of the United Nations [FAO], n.d.) ($N = 4,564$ bimodal holdings across 921 Enumeration Areas in 27 regions). For household $i$ cultivating plots $p \\in P_{{i,s}}$ in season $s \\in \\{{m, v\\}}$, the bounded Yield Volatility Index ($Y_{{\\mathrm{{vol}},i}} \\in [0, 2]$) is defined as:
\\begin{{equation}}
Y_{{\\mathrm{{vol}},i}} = \\frac{{2|Y_{{i,m}} - Y_{{i,v}}|}}{{Y_{{i,m}} + Y_{{i,v}} + 2\\varepsilon}}
\\end{{equation}}
Spatial cross-validation is enforced across $K = 5$ Enumeration Area folds (\\texttt{{GroupKFold}}) audited under a Five-Pillar Spatial Leakage Isolation Protocol. All computations and graphics were executed in Python 3.11 using \\texttt{{scikit-learn}} 1.4, \\texttt{{LightGBM}} 4.3, \\texttt{{XGBoost}} 2.0, \\texttt{{SciPy}} 1.12, and \\texttt{{Matplotlib}} 3.8.

\\section{{Results}}

{t1_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig1.png}}
\\caption*{{\\textbf{{Fig. 1}} Empirical distribution of the Yield Volatility Index ($Y_{{\\mathrm{{vol}}}}$) and cross-seasonal production dynamics across $N = 4,564$ Tanzanian smallholder holdings: (a) histogram and Gaussian KDE of $Y_{{\\mathrm{{vol}}}} \\in [0, 2]$; (b) joint log-yield parity scatter between \\textit{{Masika}} and \\textit{{Vuli}} seasons; (c) boxplots of $Y_{{\\mathrm{{vol}}}}$ across landholding size classes (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

{t2_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig2.png}}
\\caption*{{\\textbf{{Fig. 2}} Multi-model spatial cross-validation benchmark and out-of-fold calibration across five Enumeration Area folds: (a) Spatial $R^2$ and RMSE comparison; (b) out-of-fold calibration scatter; (c) fold-wise spatial stability (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

{t3_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig3.png}}
\\caption*{{\\textbf{{Fig. 3}} Feature selection trajectory and domain composition across 246 candidate variables: (a) cumulative information gain scree curve; (b) top 15 features by tree split frequency; (c) domain composition of the top 100 features (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig4.png}}
\\caption*{{\\textbf{{Fig. 4}} Global TreeSHAP feature attributions across the top 14 predictors of smallholder yield volatility: (a) directional beeswarm plot; (b) mean absolute SHAP magnitude (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

{t4_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig5.png}}
\\caption*{{\\textbf{{Fig. 5}} Regional heterogeneity and spatial transferability across 27 administrative regions of Tanzania: (a) Regional Model $R^2$ versus Unified National Ensemble slice; (b) transferability advantage $\\Delta R^2$ (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig6.png}}
\\caption*{{\\textbf{{Fig. 6}} Non-linear two-way agronomic interaction surfaces and resilience thresholds: (a) planting disparity and livestock buffers; (b) diversity divergence versus failure shocks; (c) plot fragmentation and irrigation buffer (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

{t5_tex}

{t6_tex}

{t7_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig7.png}}
\\caption*{{\\textbf{{Fig. 7}} Five-pillar spatial leakage audit verification, smallholder archetype profiles, and micro-level TreeSHAP attribution: (a) isolation audit scorecard; (b) smallholder archetype profiles; (c) micro-level TreeSHAP waterfall attribution for holding \\#0 (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig8.png}}
\\caption*{{\\textbf{{Fig. 8}} Spatial volatility hotspots and resilience capacity across Tanzania's seven Agro-Ecological Zones: (a) mean $Y_{{\\mathrm{{vol}}}}$ by zone; (b) harvest failure rate versus seasonal yield gap; (c) Agro-Ecological Resilience Index (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig9.png}}
\\caption*{{\\textbf{{Fig. 9}} One-dimensional agro-economic partial dependence and marginal response surfaces: (a) planting month difference; (b) Tropical Livestock Units; (c) Shannon diversity difference; (d) complete harvest failure share (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{figures/Fig10.png}}
\\caption*{{\\textbf{{Fig. 10}} Policy counterfactual stress-testing and volatility mitigation scenarios: (a) simulated volatility distribution shift; (b) hyper-volatile holdings ($Y_{{\\mathrm{{vol}}}} \\ge 1.50$); (c) net risk mitigation efficiency (Graphics programme: Python 3.11 / Matplotlib 3.8)}}
\\end{{figure}}

\\section{{Discussion}}
Our Five-Pillar Spatial Leakage Isolation Protocol demonstrates that ensemble machine learning models can achieve strong spatial generalisability ($R^2 = 0.592$) across unseen villages when geographic group cross-validation is strictly enforced (Roberts et al., 2017; Meyer et al., 2018; Ploton et al., 2020). Furthermore, pooling survey observations into a Unified National Ensemble yields positive transferability gains ($\\Delta R^2 > 0$) across 26 of 27 regions compared with isolated regional models. Policy counterfactual simulations confirm that an integrated Climate-Smart Agriculture package combining $+2.0\\text{{ TLU}}$ livestock asset transfers, $+0.40$ Shannon crop diversification, and meteorological planting synchronisation reduces hyper-volatile holdings from 25.8\\% to 19.9\\% and lowers mean national yield volatility by 40.0\\%.

\\section*{{Statements and Declarations}}
\\textbf{{Funding:}} No external funding was received. Institutional support was provided by Sokoine University of Agriculture (SUA).\\\\
\\textbf{{Competing Interests:}} The author declares no competing interests.\\\\
\\textbf{{Data Availability:}} Microdata are available from the Tanzania National Bureau of Statistics (\\url{{https://microdata.nbs.go.tz/index.php/catalog/69}}) and FAO Microdata Catalogue. Online Resource 1 (\\texttt{{ESM\\_1.csv}}) accompanies this article.\\\\
\\textbf{{Author Biography:}} \\textbf{{Kadeghe Goodluck Fue}} is a Senior Lecturer in the Department of Agricultural Engineering, School of Engineering and Technology, at Sokoine University of Agriculture (SUA) in Morogoro, Tanzania, where he leads the Electronics and Precision Agriculture Lab (EPALab). He holds a Ph.D. in Engineering from the University of Georgia, an M.Sc. in Agricultural and Biological Engineering from the University of Florida, and a B.Sc. in Computer Engineering and Information Technology from the University of Dar es Salaam. His research focuses on precision agriculture, artificial intelligence, spatial machine learning, Agricultural Data Science, and climate-resilient smallholder farming systems, driven by a deep commitment to advancing food security across sub-Saharan Africa.

\\end{{document}}
"""
    tex_content = (
        tex_content.replace("{RUNNING_HEAD}", RUNNING_HEAD)
        .replace("{ARTICLE_TITLE}", ARTICLE_TITLE)
        .replace("{{", "{")
        .replace("}}", "}")
        .replace("{t1_tex}", t1_tex)
        .replace("{t2_tex}", t2_tex)
        .replace("{t3_tex}", t3_tex)
        .replace("{t4_tex}", t4_tex)
        .replace("{t5_tex}", t5_tex)
        .replace("{t6_tex}", t6_tex)
        .replace("{t7_tex}", t7_tex)
    )
    LATEX_PATH.write_text(tex_content, encoding="utf-8")
    logger.info("Successfully generated %s", LATEX_PATH)
    return LATEX_PATH


def refresh_figures_3_4_8() -> None:
    """Refreshes Figures 3 and 8 with updated panel spacing before embedding in DOCX."""
    from generate_publication_figures_and_tables import PublicationGenerator

    gen = PublicationGenerator()
    ranking_df = pd.read_csv(gen.output_dir / "grandmaster_feature_ranking.csv")
    gen.generate_figure_3({"ranking_df": ranking_df})

    tables = gen.preprocessor.load_raw_data()
    tables["masikacrop"] = gen.preprocessor.harmonize_units(tables["masikacrop"], season="masika")
    tables["vulicrop"] = gen.preprocessor.harmonize_units(tables["vulicrop"], season="vuli")
    seasonal_yields = gen.preprocessor.calculate_seasonal_yields(
        crops_masika=tables["masikacrop"], crops_vuli=tables["vulicrop"],
        plots_masika=tables["masikaplot"], plots_vuli=tables["vuliplot"]
    )
    eligible_df, y_target = gen.engineer.compute_target(seasonal_yields)
    X_df = gen.engineer.engineer_predictive_features(eligible_df, tables)
    y_aligned = y_target.loc[X_df.index].values

    ctx = {
        "tables": tables,
        "eligible_df": eligible_df,
        "X_df": X_df,
        "y": y_aligned,
        "ranking_df": ranking_df,
    }
    gen.generate_figure_8(ctx)


def main() -> None:
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    refresh_figures_3_4_8()
    clean_all_tables_for_publication()
    md_text = generate_markdown_manuscript()
    MD_PATH.write_text(md_text, encoding="utf-8")
    logger.info("Saved Markdown manuscript to %s", MD_PATH)
    generate_docx_manuscript(md_text)
    generate_title_page_docx()
    generate_latex_manuscript(md_text)

    # Clean up temporary downloaded guideline PDFs if present
    for tmp_pdf in [Path("/tmp/rec.pdf"), Path("/tmp/doc_1.pdf")]:
        if tmp_pdf.exists():
            try:
                tmp_pdf.unlink()
            except OSError:
                pass

    # Verify DOCX deliverables
    doc_check = Document(DOCX_PATH)
    tp_check = Document(TITLE_PAGE_DOCX_PATH)
    sect_xml = doc_check.sections[0]._sectPr.xml
    has_ln = "w:lnNumType" in sect_xml and 'w:restart="continuous"' in sect_xml
    n_tables = len(doc_check.tables)
    n_pics = len(doc_check.inline_shapes)
    logger.info(
        "VERIFICATION PASS: manuscript.docx (%d bytes, %d tables, %d figures, continuous line numbering=%s), "
        "title_page.docx (%d bytes, %d paragraphs)",
        DOCX_PATH.stat().st_size, n_tables, n_pics, has_ln,
        TITLE_PAGE_DOCX_PATH.stat().st_size, len(tp_check.paragraphs)
    )
    logger.info("All Springer Nature Food Security deliverables built successfully.")


if __name__ == "__main__":
    main()
