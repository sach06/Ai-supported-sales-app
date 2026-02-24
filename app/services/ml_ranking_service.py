"""
app/services/ml_ranking_service.py
====================================
Streamlit-friendly wrapper around the XGBoost priority-ranking model.

Responsibilities
----------------
* Load the persisted model once at startup (with graceful heuristic fallback)
* Expose `get_ranked_list(equipment_type, top_k)` for the UI
* Expose `score_customer(bcg_rows, crm_row)` for the customer-detail page
* Provide `is_model_available()` so the UI can show a "train model" prompt
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MLRankingService:
    """
    High-level service that bridges the Streamlit app and the XGBoost model.

    The model is loaded lazily on first use.  If the model file does not exist
    the service falls back to the heuristic scoring already implemented in
    PredictionService, so the app never breaks.
    """

    def __init__(self, db_path: str | Path, model_path: Optional[str | Path] = None):
        from app.core.config import settings
        self._db_path    = Path(db_path)
        self._model_path = Path(model_path) if model_path else Path(settings.XGB_MODEL_PATH)
        self._model      = None    # lazy
        self._feat_df    = None    # cached feature matrix
        self._labels     = None    # cached labels (if available)

    # ── Public API ────────────────────────────────────────────────────────────

    def is_model_available(self) -> bool:
        return self._model_path.exists()

    def clear_cache(self) -> None:
        """Invalidate the cached feature matrix (call after data is reloaded)."""
        self._feat_df = None
        self._labels  = None

    def load_model(self) -> bool:
        """Load model from disk. Returns True on success."""
        if not self.is_model_available():
            logger.info("No trained model found at %s", self._model_path)
            return False
        try:
            from src.models.xgb_ranking_model import XGBPriorityModel
            self._model = XGBPriorityModel()
            self._model.load(self._model_path)
            logger.info("XGBoost model loaded from %s", self._model_path)
            return True
        except Exception as e:
            logger.warning("Could not load XGBoost model: %s", e)
            self._model = None
            return False

    def get_ranked_list(
        self,
        equipment_type: Optional[str] = None,
        top_k: Optional[int] = 50,
        force_heuristic: bool = False,
    ) -> pd.DataFrame:
        """
        Return a ranked DataFrame of equipment units.

        Columns: rank, company, equipment_type, country, equipment_age, priority_score

        Falls back to the heuristic model if XGBoost model is unavailable.
        """
        if self._model is None and not force_heuristic:
            self.load_model()

        if self._model is not None:
            feat_df = self._get_features()
            if feat_df is not None and not feat_df.empty:
                try:
                    return self._model.rank_by_equipment_type(
                        feat_df, equipment_type=equipment_type, top_k=top_k
                    )
                except Exception as e:
                    logger.warning("XGBoost ranking failed, falling back: %s", e)

        # ── Heuristic fallback ────────────────────────────────────────────────
        return self._heuristic_ranked_list(equipment_type, top_k)

    def score_customer(
        self,
        company_name: str,
        equipment_type: Optional[str] = None,
    ) -> Tuple[float, str]:
        """
        Return (priority_score [0-100], source) for a single company.
        source is "xgboost" or "heuristic".
        """
        ranked = self.get_ranked_list(equipment_type=equipment_type)
        if ranked.empty:
            return 50.0, "heuristic"

        mask = ranked["company"].str.lower().str.contains(
            company_name.lower()[:8], na=False
        )
        if mask.any():
            row = ranked[mask].iloc[0]
            source = "xgboost" if self._model is not None else "heuristic"
            return float(row["priority_score"]), source

        return 50.0, "heuristic"

    def get_equipment_types(self) -> List[str]:
        """Return sorted list of unique EquipmentType values from BCG data."""
        feat_df = self._get_features()
        if feat_df is not None and "_equipment_type" in feat_df.columns:
            return sorted(feat_df["_equipment_type"].dropna().unique().tolist())
        return []

    def get_model_metadata(self) -> Dict:
        """Return the metadata JSON stored alongside the model file."""
        meta_path = self._model_path.with_suffix(".meta.json")
        if meta_path.exists():
            import json
            try:
                return json.loads(meta_path.read_text())
            except Exception:
                pass
        return {}

    def get_feature_importance(self) -> Optional[pd.Series]:
        """Return feature importances as a pd.Series, or None."""
        if self._model and hasattr(self._model, "feature_importances_"):
            return self._model.feature_importances_
        return None

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_features(self) -> Optional[pd.DataFrame]:
        """Lazily extract and cache the feature matrix, reusing the app's open DB connection."""
        if self._feat_df is not None:
            return self._feat_df
        try:
            from src.features.feature_engineering import (
                extract_equipment_features,
                load_raw_data,
                load_raw_data_from_conn,
            )

            # ── Preferred path: reuse the already-open data_service connection ──
            # data_service holds an exclusive Windows lock on the DB file, so
            # opening a second connection would fail. Borrowing its connection
            # avoids that entirely.
            bcg_df = crm_df = None
            try:
                from app.services.data_service import data_service as _ds
                conn = _ds.get_conn()
                if conn is not None:
                    bcg_df, crm_df = load_raw_data_from_conn(conn)
            except Exception as shared_err:
                logger.debug("Shared-conn load failed (%s), falling back to file open", shared_err)

            # ── Fallback: open the file directly (works when no Streamlit lock) ─
            if bcg_df is None:
                bcg_df, crm_df = load_raw_data(self._db_path)

            if bcg_df is None or bcg_df.empty:
                return None

            self._feat_df, _ = extract_equipment_features(bcg_df, crm_df)
            return self._feat_df
        except Exception as e:
            logger.warning("Feature extraction failed: %s", e)
            return None


    def _heuristic_ranked_list(
        self,
        equipment_type: Optional[str],
        top_k: Optional[int],
    ) -> pd.DataFrame:
        """
        Build a heuristic ranking directly from BCG data.
        Score = age × 3 + sms_oem × 15 + crm_rating × 2  (capped at 100).
        """
        from src.features.feature_engineering import (
            extract_equipment_features,
            load_raw_data,
            load_raw_data_from_conn,
        )
        _empty = pd.DataFrame(columns=["rank", "company", "equipment_type",
                                        "country", "equipment_age", "priority_score"])
        try:
            bcg_df = crm_df = None
            try:
                from app.services.data_service import data_service as _ds
                conn = _ds.get_conn()
                if conn is not None:
                    bcg_df, crm_df = load_raw_data_from_conn(conn)
            except Exception:
                pass

            if bcg_df is None:
                bcg_df, crm_df = load_raw_data(self._db_path)

            feat_df, _ = extract_equipment_features(bcg_df, crm_df)
        except Exception as e:
            logger.warning("Heuristic fallback data load failed: %s", e)
            return _empty

        df = feat_df.copy()
        df["priority_score"] = (
            df["equipment_age"].clip(0, 30) * 3.0
            + df["is_sms_oem"] * 15.0
            + df["crm_rating_num"] * 2.0
        ).clip(0, 100).round(1)

        if equipment_type:
            df = df[df["_equipment_type"].str.contains(equipment_type, case=False, na=False)]

        df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
        df.index += 1

        out = df[["_company", "_equipment_type", "_country", "_equipment_age", "priority_score"]].copy()
        out.columns = ["company", "equipment_type", "country", "equipment_age", "priority_score"]
        out.insert(0, "rank", out.index)

        if top_k:
            out = out.head(top_k)
        return out



# Singleton (uses settings.DB_PATH automatically)
def _make_service() -> MLRankingService:
    try:
        from app.core.config import settings
        return MLRankingService(db_path=settings.DB_PATH)
    except Exception:
        return MLRankingService(db_path=Path(__file__).parent.parent.parent / "data" / "sales_app.db")


ml_ranking_service = _make_service()
