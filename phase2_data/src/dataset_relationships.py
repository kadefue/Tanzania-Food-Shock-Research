"""
Dataset Relationships and Merge Audit Module for Tanzania AASS 2024/2025.

Validates relational integrity across households, plots, crops, inputs, and seasons.
Ensures zero Cartesian duplication of crop production and generates a detailed merge audit.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple
import pandas as pd
import numpy as np
import yaml

logger = logging.getLogger("Phase2.DatasetRelationships")


class DatasetRelationshipManager:
    """
    Manages and audits relational joins between hierarchical AASS tables.
    """

    def __init__(self, settings_path: Union[str, Path] = "phase2_data/config/settings.yaml") -> None:
        with open(settings_path, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)
        self.output_dir = Path(self.settings.get("output_dirs", {}).get("audit", "phase2_data/outputs/audit"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.merge_logs: List[Dict[str, Any]] = []

    def audit_merge(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        left_name: str,
        right_name: str,
        on: List[str],
        how: str = "left",
        expected_relation: str = "1:m"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes a relational merge with rigorous before-and-after record auditing.
        Detects unmatched records and verifies that no accidental duplicate rows are introduced.
        """
        n_left_pre = len(left_df)
        n_right_pre = len(right_df)

        merged = pd.merge(left_df, right_df, on=on, how=how, indicator=True)
        n_merged = len(merged)

        both_count = int((merged["_merge"] == "both").sum())
        left_only = int((merged["_merge"] == "left_only").sum())
        right_only = int((merged["_merge"] == "right_only").sum()) if how in ["right", "outer"] else 0

        # Check for unintended duplication: if 1:1 or m:1 was expected, n_merged should equal n_left_pre
        if expected_relation in ["1:1", "m:1"]:
            cartesian_expansion = n_merged - n_left_pre
        else:
            cartesian_expansion = 0

        merged = merged.drop(columns=["_merge"])

        log_entry = {
            "left_table": left_name,
            "right_table": right_name,
            "join_keys": ":".join(on),
            "join_type": how,
            "expected_relation": expected_relation,
            "left_records_pre": n_left_pre,
            "right_records_pre": n_right_pre,
            "merged_records_post": n_merged,
            "matched_records": both_count,
            "left_unmatched": left_only,
            "right_unmatched": right_only,
            "cartesian_duplicates": cartesian_expansion,
            "status": "PASS" if cartesian_expansion == 0 else "FAIL_DUPLICATION"
        }
        self.merge_logs.append(log_entry)
        logger.info(
            "Audited merge %s [%s] %s on %s: %d pre -> %d post (Unmatched: %d, Dupes: %d)",
            left_name, how, right_name, on, n_left_pre, n_merged, left_only, cartesian_expansion
        )
        return merged, log_entry

    def align_masika_crops_and_plots(
        self,
        masika_crops: pd.DataFrame,
        masika_plots: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Aligns MASIKACROP records with MASIKAPLOT records.
        
        Critical domain insight from Phase 1 Audit:
        NBS omitted FIELD__id from MASIKACROP, causing naive merges on (HHFARMID, MASIKAPLOT__id)
        to trigger massive Cartesian duplication for multi-field holdings.
        
        This alignment reconstructs the true sequential plot order:
        Each plot in MASIKAPLOT is uniquely identified by (HHFARMID, FIELD__id, MASIKAPLOT__id).
        Within each holding, crops in MASIKACROP are allocated in sequential plot order,
        ensuring total harvest production remains exactly preserved without duplication.
        """
        pre_harvest_total = masika_crops["harvest_ton"].sum()

        # Step 1: Assign sequential plot rank in MASIKAPLOT
        p_df = masika_plots.sort_values(["HHFARMID", "FIELD__id", "MASIKAPLOT__id"]).copy()
        p_df["plot_rank"] = p_df.groupby("HHFARMID").cumcount() + 1
        p_lookup = p_df[["HHFARMID", "FIELD__id", "MASIKAPLOT__id", "s6q03_Hectares", "plot_rank"]].copy()

        # Step 2: Determine plot transitions in MASIKACROP vectorially
        c_df = masika_crops.copy()
        c_df["is_new_plot"] = (c_df["MASIKAPLOT__id"] != c_df.groupby("HHFARMID")["MASIKAPLOT__id"].shift(1))
        c_df["plot_rank"] = c_df.groupby("HHFARMID")["is_new_plot"].cumsum()

        # Merge with plot lookup on (HHFARMID, plot_rank)
        aligned = pd.merge(
            c_df,
            p_lookup,
            on=["HHFARMID", "plot_rank"],
            how="left",
            suffixes=("", "_plot")
        )

        # Fallback for plots exceeding plot_rank: match on (HHFARMID, MASIKAPLOT__id)
        missing_area = aligned["s6q03_Hectares"].isna()
        if missing_area.any():
            avg_plot_area = p_df.groupby(["HHFARMID", "MASIKAPLOT__id"])["s6q03_Hectares"].first()
            fallback_vals = aligned[missing_area].set_index(["HHFARMID", "MASIKAPLOT__id"]).index.map(avg_plot_area).values
            aligned.loc[missing_area, "s6q03_Hectares"] = fallback_vals

        post_harvest_total = aligned["harvest_ton"].sum()
        production_diff = abs(post_harvest_total - pre_harvest_total)
        assert production_diff < 1e-4, f"Crop production was altered during alignment! Diff: {production_diff}"

        logger.info(
            "MASIKACROP and MASIKAPLOT aligned successfully: %d records, 0 kg production lost or duplicated.",
            len(aligned)
        )
        return aligned

    def save_merge_audit(self) -> pd.DataFrame:
        """
        Exports the merge audit log to CSV.
        """
        audit_df = pd.DataFrame(self.merge_logs)
        out_path = self.output_dir / "merge_audit.csv"
        audit_df.to_csv(out_path, index=False)
        logger.info("Saved merge audit to %s (%d joins audited)", out_path, len(audit_df))
        return audit_df
