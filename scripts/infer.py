#!/usr/bin/env python
"""
scripts/infer.py
================
Inference script: score new (or all) equipment and produce ranked lists.

Usage
-----
    # Rank ALL equipment globally:
    python scripts/infer.py

    # Rank within a specific equipment type:
    python scripts/infer.py --equipment-type "Blast Furnace"

    # Top-20 only:
    python scripts/infer.py --top-k 20

    # Export to JSON instead of CSV:
    python scripts/infer.py --format json

    # Use a non-default model or database:
    python scripts/infer.py --model models/xgb_priority_v1.pkl --db data/sales_app.db
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.features.feature_engineering import extract_equipment_features, load_raw_data
from src.models.xgb_ranking_model import XGBPriorityModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("infer")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run inference with persisted XGBoost model")
    p.add_argument("--model",          default=str(ROOT / "models" / "xgb_priority_v1.pkl"))
    p.add_argument("--db",             default=str(ROOT / "data" / "sales_app.db"))
    p.add_argument("--equipment-type", default=None,
                   help="Filter ranking to this equipment type (substring match)")
    p.add_argument("--top-k",          type=int, default=None,
                   help="Return only the top-K ranked items")
    p.add_argument("--format",         choices=["csv", "json", "print"],
                   default="print", help="Output format")
    p.add_argument("--out",            default=None,
                   help="Output file path (default: auto-named in data/processed/)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    logger.info("XGBoost Priority-Ranking – Inference")
    logger.info("Model  : %s", args.model)
    logger.info("DB     : %s", args.db)

    # ── Load model ─────────────────────────────────────────────────────────────
    model_wrapper = XGBPriorityModel()
    model_wrapper.load(args.model)
    logger.info("Features used: %s", model_wrapper.feature_columns)

    # ── Load & engineer features ───────────────────────────────────────────────
    bcg_df, crm_df = load_raw_data(args.db)
    if bcg_df.empty:
        logger.error("No BCG data found – nothing to score. Aborting.")
        sys.exit(1)

    feat_df, _ = extract_equipment_features(bcg_df, crm_df)

    # ── Score & rank ───────────────────────────────────────────────────────────
    ranked = model_wrapper.rank_by_equipment_type(
        feat_df,
        equipment_type=args.equipment_type,
        top_k=args.top_k,
    )
    logger.info("Scored %d equipment units", len(ranked))

    # ── Output ────────────────────────────────────────────────────────────────
    if args.format == "print":
        print("\n" + "=" * 70)
        print(f"  Priority Ranking — {args.equipment_type or 'ALL EQUIPMENT TYPES'}")
        print("=" * 70)
        print(ranked.to_string(index=False))

    elif args.format == "csv":
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = Path(args.out) if args.out else (
            ROOT / "data" / "processed" / f"ranking_{ts}.csv"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        ranked.to_csv(out_path, index=False)
        logger.info("CSV saved → %s", out_path)

    elif args.format == "json":
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = Path(args.out) if args.out else (
            ROOT / "data" / "processed" / f"ranking_{ts}.json"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(ranked.to_json(orient="records", indent=2))
        logger.info("JSON saved → %s", out_path)


if __name__ == "__main__":
    main()
