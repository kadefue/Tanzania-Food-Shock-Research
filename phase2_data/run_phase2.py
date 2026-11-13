#!/usr/bin/env python3
"""
Master Pipeline Orchestrator for Phase 2:
Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025.

Executes the complete, reproducible Phase 2 pipeline:
1. Ingest & standardize microdata (Filtering genuine smallholders Holding_type == 2)
2. Validate schemas & missingness patterns
3. Harmonise cross-season crop taxonomy (119 crops)
4. Standardize production (kg) and plot areas (ha)
5. Audit dataset relationships & prevent Cartesian duplication
6. Reconstruct 4 analytical populations (A, B, C, D) & assess selection bias
7. Audit complex survey design (weights, strata, PSUs)
8. Reconstruct crop-specific yields & agronomic plausibility flags
9. Reconstruct & benchmark seasonal instability metrics (decoupling yield vs area)
10. Export clean Parquet microdata, analytical cohorts, audit tables, and reports.
"""

import os
import sys
import time
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root and local packages to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / ".local_packages"))
sys.path.insert(0, str(project_root))

from phase2_data.src.data_loading import AASSDataLoader
from phase2_data.src.data_validation import DataValidator
from phase2_data.src.dataset_relationships import DatasetRelationshipManager
from phase2_data.src.crop_harmonisation import CropHarmoniser
from phase2_data.src.unit_conversion import UnitConverter
from phase2_data.src.sample_selection import SampleSelector
from phase2_data.src.survey_design import SurveyDesignAuditor
from phase2_data.src.yield_calculation import YieldCalculator
from phase2_data.src.volatility_metrics import InstabilityMetricReconstructor
from phase2_data.src.data_quality_reports import DataQualityReporter
from phase2_data.src.export_datasets import DatasetExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "phase2_data" / "phase2_execution.log", mode="w", encoding="utf-8")
    ]
)
logger = logging.getLogger("Phase2.MasterPipeline")


def run_phase2() -> None:
    start_time = time.time()
    logger.info("================================================================================")
    logger.info("STARTING PHASE 2 PIPELINE: TANZANIA AASS DATA VALIDATION & YIELD RECONSTRUCTION")
    logger.info("================================================================================")

    # 1. Initialize Components
    settings_file = project_root / "phase2_data" / "config" / "settings.yaml"
    loader = AASSDataLoader(settings_file)
    validator = DataValidator(settings_path=settings_file)
    rel_mgr = DatasetRelationshipManager(settings_file)
    harmoniser = CropHarmoniser(settings_file)
    converter = UnitConverter(settings_file)
    selector = SampleSelector(settings_file)
    survey_auditor = SurveyDesignAuditor(settings_file)
    yield_calc = YieldCalculator(settings_file)
    vol_calc = InstabilityMetricReconstructor(settings_file)
    reporter = DataQualityReporter(settings_file)
    exporter = DatasetExporter(settings_file)

    # 2. Data Ingestion & Smallholder Isolation
    logger.info("\n--- STEP 1: Ingesting Microdata & Filtering Smallholders ---")
    tables = loader.load_all_core_tables(smallholders_only=True)
    raw_master, _ = loader.load_table("AASS2025.dta", standardize_id=True)
    raw_master_len = len(raw_master)
    logger.info("Raw AASS2025: %d records -> Filtered Smallholders: %d records", raw_master_len, len(tables["master"]))

    # 3. Schema & Missingness Validation
    logger.info("\n--- STEP 2: Schema Validation & Missingness Audit ---")
    val_df = validator.audit_all_tables(tables)
    miss_df = validator.generate_missingness_audit(tables)

    # 4. Crop Harmonisation
    logger.info("\n--- STEP 3: Cross-Season Crop Harmonisation (119 Crops) ---")
    meta_m = loader.get_metadata("MASIKACROP.dta")
    meta_v = loader.get_metadata("VULICROP.dta")
    crop_dict_df = harmoniser.build_harmonisation_dictionary(meta_m, meta_v)

    masika_crop_clean = harmoniser.harmonise_crop_table(tables["masikacrop"], "masika", meta_m)
    vuli_crop_clean = harmoniser.harmonise_crop_table(tables["vulicrop"], "vuli", meta_v)

    # 5. Unit & Area Conversion
    logger.info("\n--- STEP 4: Harvest-Unit & Area Metric Harmonisation ---")
    masika_crop_clean = converter.standardize_production_kg(masika_crop_clean, "masika")
    vuli_crop_clean = converter.standardize_production_kg(vuli_crop_clean, "vuli")

    masika_plot_clean = converter.standardize_plot_area_ha(tables["masikaplot"], "masika")
    vuli_plot_clean = converter.standardize_plot_area_ha(tables["vuliplot"], "vuli")

    conv_audit_df, conv_report = converter.generate_conversion_audit(masika_crop_clean, vuli_crop_clean)

    # 6. Relational Joins & Cartesian Duplication Prevention
    logger.info("\n--- STEP 5: Relational Alignment & Merge Audit ---")
    masika_crop_aligned = rel_mgr.align_masika_crops_and_plots(masika_crop_clean, masika_plot_clean)
    
    # Audit merges
    master_plot_m, _ = rel_mgr.audit_merge(
        tables["master"], masika_plot_clean, "AASS2025", "MASIKAPLOT", on=["HHFARMID"], how="left", expected_relation="1:m"
    )
    master_crop_m, _ = rel_mgr.audit_merge(
        tables["master"], masika_crop_clean, "AASS2025", "MASIKACROP", on=["HHFARMID"], how="left", expected_relation="1:m"
    )
    # Relational join for Vuli plots and crops
    vuli_plot_sub = vuli_plot_clean[["HHFARMID", "FIELD__id", "VULIPLOT__id", "s4q03_Hectares", "area_ha"]].drop_duplicates(
        subset=["HHFARMID", "FIELD__id", "VULIPLOT__id"]
    )
    vuli_crop_aligned, _ = rel_mgr.audit_merge(
        vuli_crop_clean, vuli_plot_sub, "VULICROP", "VULIPLOT", on=["HHFARMID", "FIELD__id", "VULIPLOT__id"], how="left", expected_relation="m:1"
    )
    merge_audit_df = rel_mgr.save_merge_audit()

    # Calculate allocated crop areas
    masika_crop_aligned = yield_calc.calculate_plot_crop_allocated_area(masika_crop_aligned, "masika")
    vuli_crop_aligned = yield_calc.calculate_plot_crop_allocated_area(vuli_crop_aligned, "vuli")

    # 7. Analytical Sample Reconstruction & Selection Bias Audit
    logger.info("\n--- STEP 6: Analytical Sample Reconstruction (Populations A, B, C, D) ---")
    populations = selector.reconstruct_populations(
        tables["master"], masika_crop_aligned, vuli_crop_aligned, masika_plot_clean, vuli_plot_clean
    )
    sample_flow_df = selector.audit_sample_selection_flow(raw_master_len, populations)
    comp_sample_df, sample_rep = selector.conduct_selection_bias_assessment(
        populations["pop_d"], masika_plot_clean, tables["household"]
    )

    # 8. Survey Design & Weight Assessment
    logger.info("\n--- STEP 7: Complex Survey Design Audit (Weights, PSUs, Strata) ---")
    survey_inv_df = survey_auditor.audit_survey_variables(tables["master"])
    weight_assess_df, survey_rep = survey_auditor.audit_weights_across_populations(populations)

    # 9. Crop-Specific Yield Reconstruction
    logger.info("\n--- STEP 8: Crop-Specific Yield Rebuilding & Agronomic Outlier Diagnostics ---")
    yields_masika = yield_calc.compute_household_crop_yields(masika_crop_aligned, "masika")
    yields_vuli = yield_calc.compute_household_crop_yields(vuli_crop_aligned, "vuli")
    yields_all = pd.concat([yields_masika, yields_vuli], ignore_index=True)

    yield_summary_df, yield_flags_df, yield_rep = yield_calc.generate_yield_diagnostics(yields_all)

    # 10. Instability Metrics Reconstruction & Benchmarking
    logger.info("\n--- STEP 9: Reconstruct & Benchmark Seasonal Instability Metrics ---")
    instability_maize = vol_calc.compute_same_crop_instability(yields_all, target_crop="Maize")
    instability_comp_df, instab_rep = vol_calc.benchmark_instability_measures(instability_maize)

    # 11. Export Clean Parquet Microdata & Analytical Datasets
    logger.info("\n--- STEP 10: Exporting Verified Parquet Datasets & Reports ---")
    plots_clean_all = pd.concat([masika_plot_clean.assign(season="masika"), vuli_plot_clean.assign(season="vuli")], ignore_index=True)
    crops_clean_all = pd.concat([masika_crop_aligned.assign(season="masika"), vuli_crop_aligned.assign(season="vuli")], ignore_index=True)

    exporter.export_cleaned_microdata(tables["master"], tables["household"], plots_clean_all, crops_clean_all)
    exporter.export_analytical_cohorts(populations)

    # 12. Master Data Quality Synthesis Report
    logger.info("\n--- STEP 11: Generating Master Data Quality Report ---")
    master_quality_rep = reporter.generate_master_quality_report(val_df, merge_audit_df, miss_df, sample_flow_df)

    elapsed = round(time.time() - start_time, 2)
    logger.info("================================================================================")
    logger.info("PHASE 2 PIPELINE COMPLETED SUCCESSFULLY IN %.2f SECONDS!", elapsed)
    logger.info("All audit CSV tables, Parquet datasets, and Markdown reports are saved in phase2_data/outputs/")
    logger.info("================================================================================")


if __name__ == "__main__":
    run_phase2()
