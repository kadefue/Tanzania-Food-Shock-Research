# Phase 2 Reproducible Data Pipeline: Tanzania AASS

This directory contains the standalone, reproducible data-cleaning, validation, harmonisation, sample reconstruction, and yield instability measurement pipeline for the Tanzania Agricultural Annual Sample Survey (AASS) 2024/2025 (Catalog 69).

## Structure

```text
phase2_data/
├── config/
│   ├── settings.yaml              # Pipeline execution parameters and agronomic bounds
│   └── variable_dictionary.yaml   # Survey table schemas, primary keys, and required fields
├── src/
│   ├── data_loading.py            # Robust loading of Stata .dta tables with pyreadstat
│   ├── data_validation.py         # Schema, key uniqueness, and missingness validation
│   ├── dataset_relationships.py   # Relational merges and join-duplication audit
│   ├── crop_harmonisation.py      # Cross-season crop name harmonisation (Masika vs Vuli)
│   ├── unit_conversion.py         # Area and production unit audit and conversion
│   ├── sample_selection.py        # Analytical populations (A, B, C, D) reconstruction
│   ├── survey_design.py           # Sampling weights, strata, and PSU variance audit
│   ├── yield_calculation.py       # Plot-weighted crop yields and agronomic outlier flags
│   ├── volatility_metrics.py      # Benchmarking legacy Y_vol against defensible alternatives
│   ├── data_quality_reports.py    # Automated scientific audit and markdown generation
│   └── export_datasets.py         # Verified Parquet and CSV dataset exporter
├── tests/
│   ├── test_data_loading.py
│   ├── test_data_validation.py
│   ├── test_dataset_relationships.py
│   ├── test_crop_harmonisation.py
│   ├── test_unit_conversion.py
│   ├── test_sample_selection.py
│   ├── test_yield_calculation.py
│   └── test_volatility_metrics.py
├── outputs/
│   ├── audit/                     # Verification CSV tables
│   ├── cleaned_data/              # Cleaned microdata tables (Parquet)
│   ├── analytical_data/           # Reconstructed analytical cohorts (Parquet)
│   ├── diagnostics/               # Distribution summaries and outlier logs
│   └── reports/                   # Detailed scientific markdown reports
├── run_phase2.py                  # Master CLI pipeline orchestrator
├── requirements.txt               # Required Python packages
└── README.md                      # This overview
```

## Execution

To execute the entire Phase 2 pipeline end-to-end:
```bash
PYTHONPATH=.local_packages python3 phase2_data/run_phase2.py
```

To execute the automated test suite:
```bash
PYTHONPATH=.local_packages pytest phase2_data/tests/ -v
```
