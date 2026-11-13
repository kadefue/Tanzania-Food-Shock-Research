"""
Data Validation Module for Tanzania AASS 2024/2025.

Performs schema validation, identifier integrity, duplicate record detection,
and comprehensive missingness auditing across agricultural survey modules.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Union
import pandas as pd
import numpy as np
import yaml

logger = logging.getLogger("Phase2.DataValidation")


class DataValidator:
    """
    Validates schemas, primary keys, missingness patterns, and domain constraints.
    """

    def __init__(
        self,
        schema_dict_path: Union[str, Path] = "phase2_data/config/variable_dictionary.yaml",
        settings_path: Union[str, Path] = "phase2_data/config/settings.yaml"
    ) -> None:
        with open(schema_dict_path, "r", encoding="utf-8") as f:
            self.schema_config = yaml.safe_load(f)
        with open(settings_path, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)

        self.tables_config = self.schema_config.get("tables", {})
        self.output_dir = Path(self.settings.get("output_dirs", {}).get("audit", "phase2_data/outputs/audit"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def validate_dataset_schema(self, table_name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates schema requirements for a given DataFrame.
        """
        table_cfg = self.tables_config.get(table_name, {})
        expected_pk = table_cfg.get("primary_key", [])
        required_vars = [v["name"] for v in table_cfg.get("required_variables", [])]

        total_rows = len(df)
        total_cols = len(df.columns)

        missing_required = [v for v in required_vars if v not in df.columns]

        # Key validation
        pk_present = all(k in df.columns for k in expected_pk)
        if pk_present and len(expected_pk) > 0:
            duplicates_count = int(df.duplicated(subset=expected_pk).sum())
            pk_nulls = int(df[expected_pk].isna().any(axis=1).sum())
        else:
            duplicates_count = -1
            pk_nulls = -1

        result = {
            "table_name": table_name,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "primary_key": ":".join(expected_pk),
            "pk_present": pk_present,
            "pk_duplicate_rows": duplicates_count,
            "pk_null_rows": pk_nulls,
            "missing_required_variables": ",".join(missing_required) if missing_required else "None",
            "validation_status": "PASS" if (len(missing_required) == 0 and duplicates_count <= 0 and pk_nulls == 0) else "WARN"
        }
        return result

    def generate_missingness_audit(self, tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Computes detailed missingness metrics across all variables and datasets.
        """
        audit_rows = []
        for name, df in tables.items():
            if df.empty:
                continue
            total_n = len(df)
            for col in df.columns:
                null_count = int(df[col].isna().sum())
                null_pct = round(100.0 * null_count / total_n, 3)
                
                # Check for zero counts if numeric
                is_num = pd.api.types.is_numeric_dtype(df[col])
                zero_count = int((df[col] == 0).sum()) if is_num else 0
                zero_pct = round(100.0 * zero_count / total_n, 3) if is_num else 0.0

                audit_rows.append({
                    "table_name": name,
                    "variable": col,
                    "dtype": str(df[col].dtype),
                    "total_records": total_n,
                    "missing_count": null_count,
                    "missing_percent": null_pct,
                    "zero_count": zero_count,
                    "zero_percent": zero_pct
                })

        audit_df = pd.DataFrame(audit_rows)
        out_path = self.output_dir / "missingness_audit.csv"
        audit_df.to_csv(out_path, index=False)
        logger.info("Saved missingness audit to %s (%d variables)", out_path, len(audit_df))
        return audit_df

    def audit_all_tables(self, tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Runs validation across all provided tables and exports dataset_validation.csv.
        """
        results = []
        # Mapping table key to variable_dictionary key
        name_map = {
            "master": "AASS2025",
            "masikaplot": "MASIKAPLOT",
            "vuliplot": "VULIPLOT",
            "masikacrop": "MASIKACROP",
            "vulicrop": "VULICROP",
        }

        for key, df in tables.items():
            schema_key = name_map.get(key, key)
            val = self.validate_dataset_schema(schema_key, df)
            results.append(val)

        val_df = pd.DataFrame(results)
        out_path = self.output_dir / "dataset_validation.csv"
        val_df.to_csv(out_path, index=False)
        logger.info("Saved dataset validation audit to %s", out_path)
        return val_df
