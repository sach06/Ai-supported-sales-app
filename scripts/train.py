#!/usr/bin/env python
"""
scripts/train.py
================
End-to-end training pipeline for the XGBoost priority-ranking model.

Usage
-----
    # From project root (with venv activated):
    python scripts/train.py

    # With explicit DB and model paths:
    python scripts/train.py --db data/sales_app.db --out models/xgb_priority_v1.pkl

    # Dry-run (feature engineering only, no model saved):
    python scripts/train.py --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# ── make src/ importable regardless of CWD ────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.features.feature_engineering import (
    build_labels,
    extract_equipment_features,
    load_raw_data,
)
from src.models.xgb_ranking_model import XGBPriorityModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train")


# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train XGBoost priority-ranking model")
    p.add_argument("--db",      default=str(ROOT / "data" / "sales_app.db"),
                   help="Path to DuckDB database")
    p.add_argument("--bcg-csv", default=None,
                   help="Path to BCG data CSV (use instead of --db when DB is locked)")
    p.add_argument("--crm-csv", default=None,
                   help="Path to CRM data CSV (use instead of --db when DB is locked)")
    p.add_argument("--export-csv-only", action="store_true",
                   help="Export BCG and CRM tables to CSV then exit (useful when DB is locked)")
    p.add_argument("--out",     default=str(ROOT / "models" / "xgb_priority_v1.pkl"),
                   help="Output path for model pickle")
    p.add_argument("--eval-split", type=float, default=0.2,
                   help="Fraction of data reserved for test evaluation")
    p.add_argument("--top-k",   type=int, default=20,
                   help="Number of top-ranked equipment to print per type")
    p.add_argument("--dry-run", action="store_true",
                   help="Run feature engineering only, skip training and saving")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    logger.info("=" * 60)
    logger.info("XGBoost Priority-Ranking – Training Pipeline")
    logger.info("Started at %s", datetime.now().isoformat())
    logger.info("Database   : %s", args.db)
    logger.info("Model out  : %s", args.out)
    logger.info("=" * 60)

    # ── 1. Load raw data ───────────────────────────────────────────────────────
    processed_dir = ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    if args.bcg_csv:
        # ── CSV mode: load from pre-exported files (avoids DB lock) ──────────
        logger.info("Step 1/5  Loading raw data from CSV files …")
        bcg_df = pd.read_csv(args.bcg_csv)
        crm_df = pd.read_csv(args.crm_csv) if args.crm_csv else pd.DataFrame()
        logger.info("BCG rows: %d  |  CRM rows: %d", len(bcg_df), len(crm_df))
    else:
        logger.info("Step 1/5  Loading raw data from DuckDB …")
        bcg_df, crm_df = load_raw_data(args.db)
        logger.info("BCG rows: %d  |  CRM rows: %d", len(bcg_df), len(crm_df))

        # ── Export-only mode (handy for unlocking then training later) ───────
        if args.export_csv_only:
            bcg_out = processed_dir / "bcg_export.csv"
            crm_out = processed_dir / "crm_export.csv"
            bcg_df.to_csv(bcg_out, index=False)
            crm_df.to_csv(crm_out, index=False)
            logger.info("Exported BCG → %s", bcg_out)
            logger.info("Exported CRM → %s", crm_out)
            logger.info("Now run: python scripts/train.py --bcg-csv %s --crm-csv %s", bcg_out, crm_out)
            return

    if bcg_df.empty:
        logger.error("BCG dataset is empty – nothing to train on. Aborting.")
        sys.exit(1)

    # ── 2. Labels ─────────────────────────────────────────────────────────────
    logger.info("Step 2/5  Building binary labels …")
    labels = build_labels(bcg_df, crm_df)

    if labels.sum() == 0:
        logger.warning("No positive labels found – label matching may have failed. "
                       "Check company name columns in BCG/CRM data.")

    # ── 3. Feature engineering ────────────────────────────────────────────────
    logger.info("Step 3/5  Extracting features …")
    feat_df, feat_meta = extract_equipment_features(bcg_df, crm_df)

    feature_cols = feat_meta["feature_columns"]
    logger.info("Feature columns: %s", feature_cols)

    # ── 4. Save processed dataset ──────────────────────────────────────────────
    processed_dir = ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    proc_path = processed_dir / f"features_{snapshot_id}.parquet"
    feat_df_with_labels = feat_df.copy()
    feat_df_with_labels["label"] = labels.values
    feat_df_with_labels.to_parquet(proc_path, index=False)
    logger.info("Processed dataset saved → %s (%d rows)", proc_path, len(feat_df_with_labels))

    if args.dry_run:
        logger.info("Dry-run mode – skipping model training.")
        return

    # ── 5. Train model ─────────────────────────────────────────────────────────
    logger.info("Step 4/5  Training XGBoost model …")
    model_wrapper = XGBPriorityModel(model_path=args.out)
    metrics = model_wrapper.train(
        X=feat_df,
        y=labels,
        feature_columns=feature_cols,
        eval_split=args.eval_split,
        data_snapshot_id=snapshot_id,
    )

    logger.info("─" * 40)
    logger.info("Training metrics:")
    for k, v in metrics.items():
        logger.info("  %-25s %s", k, v)

    # ── 5b. Per-equipment-type breakdown ───────────────────────────────────────
    logger.info("─" * 40)
    logger.info("Per-equipment-type ranking performance (Precision@10 / NDCG@10):")
    eq_metrics = model_wrapper.per_equipment_type_metrics(feat_df, labels, k=10)
    print(eq_metrics.to_string(index=False))

    # ── 5c. Feature importance ─────────────────────────────────────────────────
    logger.info("─" * 40)
    logger.info("Feature importances:")
    print(model_wrapper.feature_importances_.to_string())

    # ── 6. Persist ────────────────────────────────────────────────────────────
    logger.info("Step 5/5  Saving model artefacts …")
    meta_path = Path(args.out).with_suffix(".meta.json")
    mp, ap = model_wrapper.save(model_path=args.out, meta_path=meta_path)

    # ── 7. Export rankings per equipment type ──────────────────────────────────
    ranked_dir = ROOT / "data" / "processed"
    rankings_path = ranked_dir / f"rankings_{snapshot_id}.csv"

    logger.info("Generating global ranking …")
    global_ranked = model_wrapper.rank_by_equipment_type(feat_df)
    global_ranked.to_csv(rankings_path, index=False)
    logger.info("Global ranking exported → %s", rankings_path)

    logger.info("=" * 60)
    logger.info("✅  Training complete!")
    logger.info("    Model   : %s", mp)
    logger.info("    Metadata: %s", ap)
    logger.info("    Rankings: %s", rankings_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
