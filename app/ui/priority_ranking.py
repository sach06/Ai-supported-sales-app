"""
app/ui/priority_ranking.py
===========================
Priority Ranking page for the Streamlit app.

Shows XGBoost-ranked customer / equipment lists, per-equipment-type breakdown,
feature-importance bar chart, and model metadata.  Falls back gracefully to
the heuristic scorer if no trained model is found.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def render():
    st.markdown("## 🎯 Priority Ranking — *Who should we call next?*")
    st.markdown(
        "Ranks customers and equipment by the **XGBoost probability** of doing "
        "business with SMS Group. Where no trained model exists, a transparent "
        "heuristic score is shown instead."
    )

    # ── Lazy-import the service (avoids top-level import issues on first load) ──
    try:
        from app.services.ml_ranking_service import ml_ranking_service
    except Exception as e:
        st.error(f"Could not load ML Ranking Service: {e}")
        return

    # ── Model status banner ───────────────────────────────────────────────────
    model_available = ml_ranking_service.is_model_available()

    if model_available:
        meta = ml_ranking_service.get_model_metadata()
        trained_at = meta.get("trained_at", "unknown")[:16].replace("T", " ")
        auc = meta.get("metrics", {}).get("auc_test", None)
        p10 = meta.get("metrics", {}).get("precision_at_10", None)

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.success(f"✅ Trained XGBoost model loaded")
        with col_b2:
            st.info(f"📅 Trained: {trained_at}")
        with col_b3:
            if auc is not None:
                st.metric("ROC-AUC (test)", f"{auc:.3f}")
    else:
        st.warning(
            "⚠️ No trained model found at `models/xgb_priority_v1.pkl`. "
            "Showing **heuristic** ranking. "
            "Use the button below to export training data and train the XGBoost model."
        )
        st.markdown(
            "**Note:** Because the app holds the database open while running on Windows, "
            "training exports the BCG and CRM tables to CSV first, then trains from those."
        )
        col_train1, col_train2 = st.columns(2)
        with col_train1:
            if st.button("📤 Step 1: Export training data to CSV"):
                _export_training_data()
        with col_train2:
            if st.button("🚀 Step 2: Train XGBoost model from CSV"):
                _run_training_from_csv()

    st.markdown("---")

    # ── Controls ──────────────────────────────────────────────────────────────
    equipment_types = ml_ranking_service.get_equipment_types()

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        eq_options = ["All Equipment Types"] + equipment_types
        selected_eq = st.selectbox(
            "Equipment Type",
            eq_options,
            key="ranking_eq_type",
        )
    with col2:
        top_k = st.number_input("Show top N", min_value=5, max_value=500, value=50, step=5)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh Rankings")

    eq_filter = None if selected_eq == "All Equipment Types" else selected_eq

    # ── Fetch rankings ────────────────────────────────────────────────────────
    with st.spinner("Scoring equipment …"):
        ranked_df = ml_ranking_service.get_ranked_list(
            equipment_type=eq_filter,
            top_k=int(top_k),
        )

    if ranked_df.empty:
        st.info("No data available. Make sure data is loaded (sidebar → Load Data).")
        return

    source_label = "XGBoost" if model_available else "Heuristic"

    # ── Summary metrics ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Equipment Units Shown", len(ranked_df))
    with m2:
        st.metric("Unique Companies", ranked_df["company"].nunique())
    with m3:
        st.metric(f"Avg {source_label} Score", f"{ranked_df['priority_score'].mean():.1f}")
    with m4:
        high_prio = (ranked_df["priority_score"] >= 70).sum()
        st.metric("High Priority (≥70)", high_prio)

    st.markdown("---")

    # ── Ranked table ──────────────────────────────────────────────────────────
    st.markdown(f"### 📋 Ranked List ({source_label} Score)")

    # Score colour helper
    def _score_colour(s: float) -> str:
        if s >= 70:  return "background-color: #d1fae5; color: #065f46"
        if s >= 50:  return "background-color: #fef3c7; color: #92400e"
        return "background-color: #fee2e2; color: #991b1b"

    styled = (
        ranked_df.style
        .applymap(_score_colour, subset=["priority_score"])
        .format({"priority_score": "{:.1f}", "equipment_age": "{:.0f}"})
    )
    st.dataframe(styled, use_container_width=True, height=480)

    # Download button
    csv_bytes = ranked_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Download CSV",
        data=csv_bytes,
        file_name=f"priority_ranking_{eq_filter or 'all'}.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # ── Score Distribution Chart ──────────────────────────────────────────────
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown(f"**{source_label} Score Distribution**")
        fig_hist = px.histogram(
            ranked_df,
            x="priority_score",
            nbins=20,
            color_discrete_sequence=["#3b82f6"],
            labels={"priority_score": "Priority Score", "count": "# Equipment Units"},
        )
        fig_hist.add_vline(x=70, line_dash="dash", line_color="green",
                           annotation_text="High priority (70)")
        fig_hist.add_vline(x=50, line_dash="dash", line_color="orange",
                           annotation_text="Medium (50)")
        fig_hist.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_chart2:
        st.markdown("**Average Score by Equipment Type**")
        if len(ranked_df["equipment_type"].unique()) > 1:
            eq_avg = (
                ranked_df.groupby("equipment_type")["priority_score"]
                .mean()
                .sort_values(ascending=True)
                .tail(15)
            )
            fig_bar = px.bar(
                eq_avg.reset_index(),
                x="priority_score",
                y="equipment_type",
                orientation="h",
                color="priority_score",
                color_continuous_scale="Blues",
                labels={"priority_score": "Avg Score", "equipment_type": ""},
            )
            fig_bar.update_layout(showlegend=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Filter to 'All Equipment Types' to see the breakdown chart.")

    # ── Feature Importance (only shown when XGBoost model exists) ────────────
    if model_available:
        fi = ml_ranking_service.get_feature_importance()
        if fi is not None and len(fi) > 0:
            st.markdown("---")
            st.markdown("### 🧠 Feature Importance (XGBoost)")
            fi_df = fi.reset_index()
            fi_df.columns = ["Feature", "Importance"]
            fig_fi = px.bar(
                fi_df.sort_values("Importance"),
                x="Importance",
                y="Feature",
                orientation="h",
                color="Importance",
                color_continuous_scale="Viridis",
            )
            fig_fi.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig_fi, use_container_width=True)

            with st.expander("📖 Feature Descriptions"):
                st.markdown("""
| Feature | Description |
|---|---|
| `equipment_age` | Years since installation/commission — older = higher modernisation urgency |
| `is_sms_oem` | 1 if SMS Group is the original equipment manufacturer — existing relationship advantage |
| `equipment_type_enc` | Label-encoded equipment category (Blast Furnace, EAF, Rolling Mill, …) |
| `country_enc` | Label-encoded country — captures regional market dynamics |
| `crm_rating_num` | CRM relationship rating A=5 … E=1 (3 = no CRM record) |
| `log_fte` | log₁(1+employees) — proxy for company size and budget capacity |
| `crm_projects_count` | Number of past SMS Group projects — tracks historical business depth |
""")

    # ── Per-equipment-type model report (from metadata JSON) ──────────────────
    if model_available:
        meta = ml_ranking_service.get_model_metadata()
        metrics = meta.get("metrics", {})
        if metrics:
            st.markdown("---")
            st.markdown("### 📊 Model Evaluation Summary")
            m_cols = st.columns(5)
            kv_pairs = [
                ("AUC-CV (mean)", f"{metrics.get('auc_cv_mean', 0):.3f}"),
                ("AUC-CV (std)",  f"±{metrics.get('auc_cv_std', 0):.3f}"),
                ("AUC Test",      f"{metrics.get('auc_test', 0):.3f}"),
                ("Precision@10",  f"{metrics.get('precision_at_10', 0):.3f}"),
                ("NDCG@10",       f"{metrics.get('ndcg_at_10', 0):.3f}"),
            ]
            for col, (label, val) in zip(m_cols, kv_pairs):
                col.metric(label, val)


# ── Training helpers ─────────────────────────────────────────────────────────

_BCG_CSV = ROOT / "data" / "processed" / "bcg_export.csv"
_CRM_CSV = ROOT / "data" / "processed" / "crm_export.csv"


def _export_training_data():
    """Export BCG and CRM tables to CSV via the app's open DB connection."""
    try:
        from app.services.data_service import data_service
        import duckdb

        db_path = str(data_service.db_path) if hasattr(data_service, "db_path") else None
        if db_path is None:
            # Fall back: look for the DB from config
            from app.core.config import settings
            db_path = str(settings.DATABASE_PATH)

        conn = duckdb.connect(db_path)   # app already has it open; same process is fine
        _BCG_CSV.parent.mkdir(parents=True, exist_ok=True)

        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        bcg_table = next((t for t in ["bcg_data", "bcg_installed_base", "installed_base"] if t in tables), None)
        crm_table = next((t for t in ["crm_data", "crm", "customers", "unified_companies"] if t in tables), None)

        if bcg_table:
            conn.execute(f"COPY (SELECT * FROM {bcg_table}) TO '{_BCG_CSV}' (FORMAT CSV, HEADER)")
            st.success(f"✅ BCG data exported → `{_BCG_CSV.name}` ({conn.execute(f'SELECT COUNT(*) FROM {bcg_table}').fetchone()[0]} rows)")
        else:
            st.error("No BCG table found in database.")
            conn.close()
            return

        if crm_table:
            conn.execute(f"COPY (SELECT * FROM {crm_table}) TO '{_CRM_CSV}' (FORMAT CSV, HEADER)")
            st.success(f"✅ CRM data exported → `{_CRM_CSV.name}`")
        else:
            st.warning("No CRM table found — labels will default to 0.")
            _CRM_CSV.write_text("company_name\n")  # empty CRM CSV

        conn.close()
        st.info("📤 Export complete! Now click **Step 2** to train the model.")
    except Exception as e:
        st.error(f"Export failed: {e}")
        import traceback
        with st.expander("Traceback"):
            st.code(traceback.format_exc())


def _run_training_from_csv():
    """Train from the previously exported CSV files (avoids DB lock)."""
    import subprocess, sys
    if not _BCG_CSV.exists():
        st.error(f"BCG CSV not found at `{_BCG_CSV}`. Run Step 1 first.")
        return

    train_script = ROOT / "scripts" / "train.py"
    cmd = [
        sys.executable, str(train_script),
        "--bcg-csv", str(_BCG_CSV),
        "--crm-csv", str(_CRM_CSV) if _CRM_CSV.exists() else "",
    ]
    with st.spinner("Training XGBoost model … (this may take 1-3 minutes)"):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))

    if result.returncode == 0:
        st.success("✅ Training complete! Refresh the page to load the new model.")
        with st.expander("Training log"):
            out = result.stdout + result.stderr
            st.text(out[-4000:] if len(out) > 4000 else out)
    else:
        st.error("Training failed. See log below.")
        with st.expander("Error log"):
            st.text(result.stderr[-4000:])

