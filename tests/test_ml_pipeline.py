"""
tests/test_ml_pipeline.py
==========================
Unit tests for the XGBoost priority-ranking pipeline.

Run:
    pytest tests/test_ml_pipeline.py -v
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── make src/ importable ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.features.feature_engineering import (
    _normalise_name,
    _rating_num,
    build_labels,
    extract_equipment_features,
)
from src.models.xgb_ranking_model import XGBPriorityModel, ndcg_at_k, precision_at_k


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_bcg_df() -> pd.DataFrame:
    """BCG installed-base dataframe large enough for 5-fold stratified CV."""
    n = 30
    rng = np.random.default_rng(42)
    companies = (
        ["Alpha Steel GmbH"] * 8
        + ["Gamma Corp"] * 7
        + ["Delta Inc"] * 5
        + ["Beta Iron Ltd"] * 5
        + ["Zeta Works"] * 5
    )
    eq_types = ["Blast Furnace", "Rolling Mill", "EAF", "Caster", "Ladle Furnace"]
    oems = ["SMS Group", "Danieli", "Tenova", "Primetals", "SMS Group"]
    countries = ["Germany", "Italy", "USA", "China", "India"]
    return pd.DataFrame({
        "company_name": companies[:n],
        "equipment_type": [eq_types[i % len(eq_types)] for i in range(n)],
        "start_year": [rng.integers(1990, 2022) for _ in range(n)],
        "supplier": [oems[i % len(oems)] for i in range(n)],
        "country": [countries[i % len(countries)] for i in range(n)],
    })


@pytest.fixture
def sample_crm_df() -> pd.DataFrame:
    """CRM dataframe – contains Alpha Steel, Gamma Corp, Delta Inc (positives)."""
    return pd.DataFrame({
        "company_name": ["Alpha Steel GmbH", "Gamma Corp", "Delta Inc"],
        "crm_rating":   ["A", "B", "C"],
        "fte":          [5000, 3000, 800],
        "project_count": [12, 7, 3],
    })


# ─────────────────────────────────────────────────────────────────────────────
# Feature Engineering
# ─────────────────────────────────────────────────────────────────────────────

class TestNormaliseName:
    def test_removes_gmbh(self):
        assert "alpha steel" == _normalise_name("Alpha Steel GmbH")

    def test_lowercase(self):
        result = _normalise_name("BETA Iron")
        assert result == result.lower()

    def test_strips_punctuation(self):
        result = _normalise_name("Acme & Co., Inc.")
        assert "&" not in result and "," not in result


class TestRatingNum:
    def test_a_is_5(self):   assert _rating_num("A") == 5
    def test_e_is_1(self):   assert _rating_num("E") == 1
    def test_unknown_is_3(self): assert _rating_num("Z") == 3


class TestBuildLabels:
    def test_positive_match(self, sample_bcg_df, sample_crm_df):
        labels = build_labels(sample_bcg_df, sample_crm_df)
        # Alpha Steel GmbH and Gamma Corp are in CRM → label 1
        for company in ["Alpha Steel GmbH", "Gamma Corp", "Delta Inc"]:
            mask = sample_bcg_df["company_name"] == company
            assert (labels[mask] == 1).all(), f"{company} should be label 1"

    def test_negative_match(self, sample_bcg_df, sample_crm_df):
        labels = build_labels(sample_bcg_df, sample_crm_df)
        # Beta Iron Ltd and Zeta Works are NOT in the CRM → label 0
        for company in ["Beta Iron Ltd", "Zeta Works"]:
            mask = sample_bcg_df["company_name"] == company
            assert (labels[mask] == 0).all(), f"{company} should be label 0"

    def test_empty_crm_all_zero(self, sample_bcg_df):
        labels = build_labels(sample_bcg_df, pd.DataFrame())
        assert (labels == 0).all()


class TestExtractEquipmentFeatures:
    def test_shape(self, sample_bcg_df, sample_crm_df):
        feat_df, meta = extract_equipment_features(sample_bcg_df, sample_crm_df)
        assert len(feat_df) == len(sample_bcg_df)

    def test_equipment_age_positive(self, sample_bcg_df, sample_crm_df):
        feat_df, _ = extract_equipment_features(sample_bcg_df, sample_crm_df)
        assert (feat_df["equipment_age"] >= 0).all()

    def test_sms_oem_flag(self, sample_bcg_df, sample_crm_df):
        feat_df, _ = extract_equipment_features(sample_bcg_df, sample_crm_df)
        # Alpha (SMS) and Gamma (SMS) → 1; Beta (Danieli) and Delta (Tenova) → 0
        assert feat_df["is_sms_oem"].iloc[0] == 1
        assert feat_df["is_sms_oem"].iloc[1] == 0

    def test_feature_columns_in_meta(self, sample_bcg_df, sample_crm_df):
        feat_df, meta = extract_equipment_features(sample_bcg_df, sample_crm_df)
        for col in meta["feature_columns"]:
            assert col in feat_df.columns, f"Missing feature column: {col}"

    def test_no_nans_in_features(self, sample_bcg_df, sample_crm_df):
        feat_df, meta = extract_equipment_features(sample_bcg_df, sample_crm_df)
        assert not feat_df[meta["feature_columns"]].isnull().any().any()


# ─────────────────────────────────────────────────────────────────────────────
# Metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestMetrics:
    def test_precision_at_k_perfect(self):
        y = np.array([1, 1, 1, 0, 0])
        s = np.array([0.9, 0.8, 0.7, 0.3, 0.1])
        assert precision_at_k(y, s, k=3) == 1.0

    def test_precision_at_k_zero(self):
        y = np.array([0, 0, 0, 1, 1])
        s = np.array([0.9, 0.8, 0.7, 0.3, 0.1])
        assert precision_at_k(y, s, k=3) == 0.0

    def test_ndcg_at_k_perfect(self):
        y = np.array([1, 1, 0, 0])
        s = np.array([0.9, 0.8, 0.4, 0.2])
        assert ndcg_at_k(y, s, k=2) == pytest.approx(1.0)

    def test_ndcg_at_k_range(self):
        y = np.array([1, 0, 1, 0])
        s = np.random.rand(4)
        v = ndcg_at_k(y, s, k=4)
        assert 0.0 <= v <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Model training and persistence
# ─────────────────────────────────────────────────────────────────────────────

class TestXGBPriorityModel:

    @pytest.fixture
    def trained_model(self, sample_bcg_df, sample_crm_df):
        feat_df, meta = extract_equipment_features(sample_bcg_df, sample_crm_df)
        labels = build_labels(sample_bcg_df, sample_crm_df)
        m = XGBPriorityModel()
        m.train(
            X=feat_df,
            y=labels,
            feature_columns=meta["feature_columns"],
            eval_split=0.2,
            data_snapshot_id="test",
        )
        return m, feat_df, labels

    def test_predict_proba_range(self, trained_model):
        m, feat_df, _ = trained_model
        probs = m.predict_proba(feat_df)
        assert probs.min() >= 0.0
        assert probs.max() <= 1.0

    def test_rank_returns_dataframe(self, trained_model):
        m, feat_df, _ = trained_model
        ranked = m.rank_by_equipment_type(feat_df)
        assert isinstance(ranked, pd.DataFrame)
        assert "priority_score" in ranked.columns
        assert "rank" in ranked.columns

    def test_rank_sorted_descending(self, trained_model):
        m, feat_df, _ = trained_model
        ranked = m.rank_by_equipment_type(feat_df)
        scores = ranked["priority_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_rank_filter_by_equipment_type(self, trained_model):
        m, feat_df, _ = trained_model
        ranked = m.rank_by_equipment_type(feat_df, equipment_type="Blast")
        assert (ranked["equipment_type"].str.contains("Blast", case=False)).all()

    def test_save_and_load(self, trained_model, tmp_path):
        m, feat_df, _ = trained_model
        pkl_path = tmp_path / "test_model.pkl"
        m.save(model_path=pkl_path, meta_path=pkl_path.with_suffix(".json"))

        m2 = XGBPriorityModel()
        m2.load(pkl_path)
        # Predictions should be identical
        orig  = m.predict_proba(feat_df)
        loaded = m2.predict_proba(feat_df)
        np.testing.assert_allclose(orig, loaded, rtol=1e-5)

    def test_metadata_json(self, trained_model, tmp_path):
        m, feat_df, _ = trained_model
        pkl_path  = tmp_path / "model.pkl"
        meta_path = tmp_path / "model.json"
        m.save(pkl_path, meta_path)

        meta = json.loads(meta_path.read_text())
        assert "metrics" in meta
        assert "feature_columns" in meta
        assert "trained_at" in meta

    def test_per_equipment_type_metrics(self, trained_model):
        m, feat_df, labels = trained_model
        df = m.per_equipment_type_metrics(feat_df, labels, k=2)
        assert "equipment_type" in df.columns
        assert "precision_at_2" in df.columns
