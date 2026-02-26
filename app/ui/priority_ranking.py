"""
app/ui/priority_ranking.py
===========================
Priority Ranking page — enhanced with:
  - Country + Company search filters (in addition to Equipment Type)
  - Ranking explanation: 5 reasons per ranked item (why high / low)
  - Business opportunity type (OEM replacement, Modernisation, Maintenance, New Build)
  - Stale-model detection and retrain prompt
  - Improved charts
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

CURRENT_YEAR = 2026


# ── Ranking explanation helpers ───────────────────────────────────────────────

def _opportunity_type(row: pd.Series) -> str:
    """Classify the most likely business opportunity type from features."""
    age   = row.get("equipment_age", 0)
    is_oem = row.get("is_sms_oem", 0)
    crm_r  = row.get("crm_rating_num", 3)
    n_proj = row.get("crm_projects_count", 0)

    if is_oem and age >= 20:
        return "🔧 OEM Replacement / Major Upgrade"
    if is_oem and 10 <= age < 20:
        return "⚙️ Modernisation / Revamp"
    if is_oem and age < 10:
        return "🛠️ Maintenance / Spare Parts"
    if not is_oem and crm_r >= 4 and n_proj >= 2:
        return "🏗️ New Build (Strong CRM Relationship)"
    if not is_oem and age >= 25:
        return "🏗️ New Build / Greenfield"
    return "📞 Sales Development"


def _explain_rank(row: pd.Series, score: float, source: str) -> list[str]:
    """Return up to 5 plain-English reasons for this item's ranking."""
    reasons = []
    age   = float(row.get("equipment_age", 0))
    is_oem = int(row.get("is_sms_oem", 0))
    crm_r  = float(row.get("crm_rating_num", 3))
    n_proj = int(row.get("crm_projects_count", 0))
    fte   = float(row.get("log_fte", 0))

    # Equipment age
    if age >= 25:
        reasons.append(f"🕒 **Equipment age {age:.0f} yrs** — well past typical lifecycle → very high modernisation urgency")
    elif age >= 15:
        reasons.append(f"⏳ **Equipment age {age:.0f} yrs** — approaching end-of-life, upgrade discussion timely")
    elif age >= 8:
        reasons.append(f"📅 **Equipment age {age:.0f} yrs** — mid-life, maintenance & parts opportunity")
    else:
        reasons.append(f"🆕 **Equipment age {age:.0f} yrs** — relatively young, limited obsolescence urgency")

    # OEM flag
    if is_oem:
        reasons.append("✅ **SMS Group is the OEM** — incumbent advantage for replacement parts, upgrades & service")
    else:
        reasons.append("⚠️ **Third-party OEM** — no incumbent advantage; requires competitive positioning")

    # CRM rating
    rating_map = {5: "A (excellent)", 4: "B (good)", 3: "C / unknown", 2: "D (weak)", 1: "E (poor)"}
    r_label = rating_map.get(int(round(crm_r)), f"{crm_r:.1f}")
    if crm_r >= 4:
        reasons.append(f"⭐ **CRM Rating {r_label}** — strong existing customer relationship")
    elif crm_r == 3:
        reasons.append(f"❓ **CRM Rating {r_label}** — no CRM record found; relationship unknown")
    else:
        reasons.append(f"🔴 **CRM Rating {r_label}** — historically difficult relationship; approach with strategy")

    # Project history
    if n_proj >= 3:
        reasons.append(f"📁 **{n_proj} past projects** in CRM — deep engagement history with SMS Group")
    elif n_proj == 1:
        reasons.append(f"📁 **{n_proj} past project** in CRM — some history; relationship to develop")
    else:
        reasons.append("📭 **No project history** in CRM — cold contact or new prospect")

    # Company size
    actual_fte = int(round(np.expm1(fte))) if fte > 0 else 0
    if actual_fte >= 5000:
        reasons.append(f"🏢 **Large company (~{actual_fte:,} FTE)** — significant buying power and budget capacity")
    elif actual_fte >= 500:
        reasons.append(f"🏢 **Mid-size company (~{actual_fte:,} FTE)** — meaningful procurement capability")
    elif actual_fte > 0:
        reasons.append(f"🏢 **Smaller company (~{actual_fte:,} FTE)** — limited budget; prioritise ROI messaging")
    else:
        reasons.append("🏢 **Company size unknown** — verify FTE / revenue before outreach")

    return reasons[:5]


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.markdown("## 🎯 Priority Ranking — *Who should we call next?*")
    st.markdown(
        "Ranks customers and equipment by **SMS Group business potential**. "
        "Filters by Equipment Type, Country and Company. "
        "Click any row for a detailed **5-reason ranking explanation** and business opportunity type."
    )

    # ── Lazy-import the service ───────────────────────────────────────────────
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

        auc_valid = auc is not None and not (isinstance(auc, float) and auc != auc)

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.success("✅ Trained XGBoost model loaded")
        with col_b2:
            st.info(f"📅 Trained: {trained_at}")
        with col_b3:
            if auc_valid:
                st.metric("ROC-AUC (test)", f"{auc:.3f}")
            else:
                st.metric("ROC-AUC (test)", "NaN")

        if not auc_valid:
            st.warning(
                "⚠️ The loaded XGBoost model was trained on incomplete data (AUC = NaN). "
                "The data has since been updated with Axel's full dataset. "
                "**Please retrain the model** using the buttons below to get meaningful rankings."
            )
            col_train1, col_train2, col_train3 = st.columns(3)
            with col_train1:
                if st.button("📤 Step 1: Export training data to CSV", key="export_stale"):
                    _export_training_data()
            with col_train2:
                if st.button("🚀 Step 2: Train XGBoost from CSV", key="train_stale"):
                    _run_training_from_csv()
            with col_train3:
                if st.button("🔄 Switch to Heuristic (instant)", key="use_heuristic"):
                    from pathlib import Path as _P
                    from app.core.config import settings as _s
                    stale = _P(_s.XGB_MODEL_PATH)
                    stale_bak = stale.with_suffix(".pkl.bak")
                    if stale.exists():
                        stale.rename(stale_bak)
                        st.success("Model backed up. Switching to heuristic mode...")
                        ml_ranking_service._model = None
                        ml_ranking_service.clear_cache()
                        st.rerun()
    else:
        st.warning(
            "⚠️ No trained model found — showing **heuristic** ranking. "
            "Use the buttons below to export training data and train the XGBoost model."
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

    # ── Build filter options from feature dataframe (lazy load) ──────────────
    equipment_types = ml_ranking_service.get_equipment_types()
    countries       = ml_ranking_service.get_countries()
    companies       = ml_ranking_service.get_company_names()

    # ── Filter controls (3 rows) ──────────────────────────────────────────────
    st.markdown("### 🔍 Filters")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        eq_options = ["All Equipment Types"] + equipment_types
        selected_eq = st.selectbox("Equipment Type", eq_options, key="ranking_eq_type")
    with col2:
        country_options = ["All Countries"] + countries
        selected_country = st.selectbox("Country", country_options, key="ranking_country")
    with col3:
        top_k = st.number_input("Show top N", min_value=5, max_value=500, value=50, step=5)

    col4, col5, col6 = st.columns([3, 2, 1])
    with col4:
        company_search = st.text_input(
            "🔎 Search Company Name (partial match, case-insensitive)",
            placeholder="e.g. ArcelorMittal, Tata, POSCO …",
            key="ranking_company_search"
        )
    with col5:
        opp_types = [
            "All Opportunity Types",
            "🔧 OEM Replacement / Major Upgrade",
            "⚙️ Modernisation / Revamp",
            "🛠️ Maintenance / Spare Parts",
            "🏗️ New Build (Strong CRM Relationship)",
            "🏗️ New Build / Greenfield",
            "📞 Sales Development",
        ]
        selected_opp = st.selectbox("Opportunity Type", opp_types, key="ranking_opp_type")
    with col6:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh Rankings")

    eq_filter      = None if selected_eq      == "All Equipment Types" else selected_eq
    country_filter = None if selected_country == "All Countries"        else selected_country
    opp_filter     = None if selected_opp     == "All Opportunity Types" else selected_opp

    # ── Fetch rankings (clear cache on explicit refresh) ──────────────────────
    if refresh:
        ml_ranking_service.clear_cache()

    with st.spinner("Scoring equipment …"):
        ranked_df = ml_ranking_service.get_ranked_list(
            equipment_type=eq_filter,
            country=country_filter,
            top_k=int(top_k) * 5,   # fetch more before company / opp filter
        )

    if ranked_df.empty:
        st.info("No data available. Make sure data is loaded (sidebar → Load Data).")
        return

    # ── Apply company search filter ───────────────────────────────────────────
    if company_search.strip():
        mask = ranked_df["company"].str.contains(company_search.strip(), case=False, na=False)
        ranked_df = ranked_df[mask]

    # ── Compute opportunity type per row and optionally filter ────────────────
    # Get the full feature dataframe for explanation metadata
    feat_df = ml_ranking_service._get_features()

    if feat_df is not None and not feat_df.empty:
        # Build a map: company → first-match feature row
        feat_by_company: dict[str, pd.Series] = {}
        for _, frow in feat_df.iterrows():
            name = str(frow.get("_company", "")).strip()
            if name and name not in feat_by_company:
                feat_by_company[name] = frow

        def _opp_for_company(company):
            if company in feat_by_company:
                return _opportunity_type(feat_by_company[company])
            return "📞 Sales Development"

        ranked_df["opportunity_type"] = ranked_df["company"].map(_opp_for_company)
    else:
        ranked_df["opportunity_type"] = "📞 Sales Development"

    # Filter by opportunity type if requested
    if opp_filter:
        ranked_df = ranked_df[ranked_df["opportunity_type"] == opp_filter]

    # ── Enrich with site/location data from IB ───────────────────────────────
    if feat_df is not None and not feat_df.empty and "_company" in feat_df.columns:
        city_map = {}
        year_map = {}
        for _, fr in feat_df.iterrows():
            co = str(fr.get("_company", "")).strip()
            if co and co not in city_map:
                city_map[co] = str(fr.get("_site_city", "") or "")
                year_map[co] = fr.get("_last_startup", None)
        ranked_df["site_city"]    = ranked_df["company"].map(lambda c: city_map.get(c, ""))
        ranked_df["last_startup"] = ranked_df["company"].map(lambda c: year_map.get(c, None))
    else:
        ranked_df["site_city"]    = ""
        ranked_df["last_startup"] = None

    # Compute last_modernization as (current_year - last_startup)
    ranked_df["last_modernization"] = ranked_df["last_startup"].apply(
        lambda y: f"{y} ({2026 - int(y)} yrs ago)" if y and str(y).strip() and str(y) != "nan" else "—"
    )

    # Limit to top_k after all filters
    ranked_df = ranked_df.head(int(top_k)).reset_index(drop=True)
    ranked_df.index += 1

    if ranked_df.empty:
        st.info("No results match the current filters. Try broadening your search.")
        return

    source_label = "XGBoost" if model_available and not (
        auc is not None and not (isinstance(auc, float) and auc != auc)
        if model_available else True
    ) else "Heuristic"
    try:
        auc_ok = auc_valid if model_available else False
    except Exception:
        auc_ok = False
    source_label = "XGBoost" if (model_available and auc_ok) else "Heuristic"

    # ── Summary metrics ───────────────────────────────────────────────────────
    st.markdown("---")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Equipment Units", len(ranked_df))
    with m2:
        st.metric("Unique Companies", ranked_df["company"].nunique())
    with m3:
        st.metric("Countries", ranked_df["country"].nunique())
    with m4:
        st.metric(f"Avg {source_label} Score", f"{ranked_df['priority_score'].mean():.1f}")
    with m5:
        high_prio = (ranked_df["priority_score"] >= 50).sum()
        st.metric("High Priority (≥50)", high_prio)

    st.markdown("---")

    # ── Ranked table ──────────────────────────────────────────────────────────
    st.markdown(f"### 📋 Ranked List ({source_label} Score)")

    display_df = ranked_df[[
        "company", "site_city", "opportunity_type", "equipment_type",
        "country", "last_modernization", "equipment_age", "priority_score"
    ]].copy()
    display_df.insert(0, "rank", display_df.index + 1)
    display_df = display_df.rename(columns={
        "company": "Company",
        "site_city": "Site / City",
        "opportunity_type": "Opp. Type",
        "equipment_type": "Equipment",
        "country": "Country",
        "last_modernization": "Last Startup",
        "equipment_age": "Age (yrs)",
        "priority_score": "Score",
    })

    def _score_colour(s: float) -> str:
        if s >= 70: return "background-color: #d1fae5; color: #065f46"
        if s >= 50: return "background-color: #fef3c7; color: #92400e"
        return "background-color: #fee2e2; color: #991b1b"

    styled = (
        display_df.style
        .applymap(_score_colour, subset=["Score"])
        .format({"Score": "{:.1f}", "Age (yrs)": "{:.0f}"})
    )
    st.dataframe(styled, use_container_width=True, height=500)

    # Download
    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Download CSV",
        data=csv_bytes,
        file_name=f"priority_ranking_{eq_filter or 'all'}.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # ── Ranking Explanation Panel ─────────────────────────────────────────────
    st.markdown("### 🔍 Ranking Explanation — *Why does this company rank here?*")
    st.caption("Select a company from the dropdown to see the 5 key drivers of its score.")

    top_companies = display_df["Company"].unique().tolist()
    selected_explain = st.selectbox("Select company to explain:", top_companies, key="explain_company")

    if selected_explain and feat_df is not None:
        company_rows = ranked_df[ranked_df["company"] == selected_explain]
        if not company_rows.empty:
            crow = company_rows.iloc[0]
            score_val  = crow["priority_score"]
            country_val = crow["country"]
            eq_val      = crow["equipment_type"]
            age_val     = crow["equipment_age"]
            opp_val     = crow["opportunity_type"]

            # Get feature row for this company (for metadata)
            feat_row = feat_by_company.get(selected_explain, pd.Series()) if feat_df is not None else pd.Series()

            col_e1, col_e2 = st.columns([1, 2])
            with col_e1:
                city_val = crow.get("site_city", "")
                last_mod = crow.get("last_modernization", "—")
                st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e3a5f,#2e6ca4);border-radius:12px;padding:20px;color:white">
  <h3 style="margin:0 0 8px 0">{selected_explain}</h3>
  <p style="margin:4px 0">&#x1F4CD; {country_val}{(' — ' + city_val) if city_val else ''}</p>
  <p style="margin:4px 0">&#x2699;&#xFE0F; {eq_val}</p>
  <p style="margin:4px 0">&#x1F551; Age: {age_val:.0f} yrs | Last startup: {last_mod}</p>
  <p style="margin:4px 0">{opp_val}</p>
  <hr style="border-color:rgba(255,255,255,0.3)">
  <h2 style="margin:8px 0 0 0">Score: {score_val:.1f} / 100</h2>
  <p style="font-size:12px;margin:4px 0;opacity:0.8">({source_label} model)</p>
</div>""", unsafe_allow_html=True)

            with col_e2:
                reasons = _explain_rank(feat_row if not feat_row.empty else crow, score_val, source_label)
                st.markdown("**Top 5 Ranking Drivers:**")
                for i, r in enumerate(reasons, 1):
                    st.markdown(f"{i}. {r}")

                # Business recommendation
                st.markdown("**📌 Recommended Next Action:**")
                if "OEM Replacement" in opp_val:
                    st.info("Schedule technical visit to assess upgrade/replacement scope. Prepare lifecycle cost analysis.")
                elif "Modernisation" in opp_val:
                    st.info("Propose automation upgrade package. Reference recent revamp projects for similar equipment.")
                elif "Maintenance" in opp_val:
                    st.info("Reach out for frame agreement on spare parts and preventive maintenance contract.")
                elif "New Build" in opp_val:
                    st.info("Engage at strategic level. Prepare market entry or greenfield proposal with local partner.")
                else:
                    st.info("Identify key contacts and schedule introductory call/visit. Build relationship foundation.")

        all_rows = ranked_df[ranked_df["company"] == selected_explain]
        if len(all_rows) > 1:
            st.markdown("**All equipment units for this company:**")
            st.dataframe(all_rows[["equipment_type", "country", "equipment_age", "priority_score", "opportunity_type"]],
                         use_container_width=True)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown(f"**{source_label} Score Distribution**")
        fig_hist = px.histogram(
            ranked_df, x="priority_score", nbins=20,
            color_discrete_sequence=["#3b82f6"],
            labels={"priority_score": "Priority Score", "count": "# Equipment Units"},
        )
        fig_hist.add_vline(x=70, line_dash="dash", line_color="green", annotation_text="High priority (70)")
        fig_hist.add_vline(x=50, line_dash="dash", line_color="orange", annotation_text="Medium (50)")
        fig_hist.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_chart2:
        st.markdown("**Avg Score by Country**")
        country_avg = (
            ranked_df.groupby("country")["priority_score"]
            .mean().sort_values(ascending=True).tail(20)
        )
        fig_country = px.bar(
            country_avg.reset_index(),
            x="priority_score", y="country", orientation="h",
            color="priority_score", color_continuous_scale="Blues",
            labels={"priority_score": "Avg Score", "country": ""},
        )
        fig_country.update_layout(showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig_country, use_container_width=True)

    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.markdown("**Avg Score by Equipment Type**")
        if len(ranked_df["equipment_type"].unique()) > 1:
            eq_avg = (
                ranked_df.groupby("equipment_type")["priority_score"]
                .mean().sort_values(ascending=True).tail(15)
            )
            fig_bar = px.bar(
                eq_avg.reset_index(), x="priority_score", y="equipment_type", orientation="h",
                color="priority_score", color_continuous_scale="Blues",
                labels={"priority_score": "Avg Score", "equipment_type": ""},
            )
            fig_bar.update_layout(showlegend=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Filter to 'All Equipment Types' to see the breakdown chart.")

    with col_chart4:
        st.markdown("**Opportunity Type Breakdown**")
        opp_counts = ranked_df["opportunity_type"].value_counts().reset_index()
        opp_counts.columns = ["opportunity_type", "count"]
        fig_opp = px.pie(
            opp_counts, values="count", names="opportunity_type",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_opp.update_layout(showlegend=True, margin=dict(t=20, b=20))
        st.plotly_chart(fig_opp, use_container_width=True)

    # ── Feature Importance (XGBoost only) ────────────────────────────────────
    if model_available and auc_ok:
        fi = ml_ranking_service.get_feature_importance()
        if fi is not None and len(fi) > 0:
            st.markdown("---")
            st.markdown("### 🧠 Feature Importance (XGBoost)")
            fi_df = fi.reset_index()
            fi_df.columns = ["Feature", "Importance"]
            fig_fi = px.bar(
                fi_df.sort_values("Importance"),
                x="Importance", y="Feature", orientation="h",
                color="Importance", color_continuous_scale="Viridis",
            )
            fig_fi.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig_fi, use_container_width=True)

            with st.expander("📖 Feature Descriptions"):
                st.markdown("""
| Feature | Description |
|---|---|
| `equipment_age` | Years since installation/commission — older = higher modernisation urgency |
| `is_sms_oem` | 1 if SMS Group is the original equipment manufacturer — incumbent advantage |
| `equipment_type_enc` | Label-encoded equipment category (Blast Furnace, EAF, Rolling Mill, …) |
| `country_enc` | Label-encoded country — captures regional market dynamics |
| `crm_rating_num` | CRM relationship rating A=5 … E=1 (3 = no CRM record) |
| `log_fte` | log₁(1+employees) — proxy for company size and budget capacity |
| `crm_projects_count` | Number of past SMS Group projects — tracks historical business depth |
""")

    # ── Model Evaluation ──────────────────────────────────────────────────────
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


# ── Training helpers ──────────────────────────────────────────────────────────

_BCG_CSV = ROOT / "data" / "processed" / "bcg_export.csv"
_CRM_CSV = ROOT / "data" / "processed" / "crm_export.csv"


def _export_training_data():
    """Export BCG and CRM tables to CSV via the app's open DB connection."""
    try:
        from app.services.data_service import data_service
        import duckdb

        db_path = str(data_service.db_path) if hasattr(data_service, "db_path") else None
        if db_path is None:
            from app.core.config import settings
            db_path = str(settings.DATABASE_PATH)

        conn = duckdb.connect(db_path)
        _BCG_CSV.parent.mkdir(parents=True, exist_ok=True)

        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        # Prefer bcg_installed_base (normalised columns) over raw bcg_data dump
        bcg_table = next((t for t in ["bcg_installed_base", "bcg_data", "installed_base"] if t in tables), None)
        crm_table = next((t for t in ["crm_data", "crm", "customers", "unified_companies"] if t in tables), None)

        if bcg_table:
            conn.execute(f"COPY (SELECT * FROM {bcg_table}) TO '{_BCG_CSV}' (FORMAT CSV, HEADER)")
            n = conn.execute(f"SELECT COUNT(*) FROM {bcg_table}").fetchone()[0]
            st.success(f"✅ BCG data exported → `{_BCG_CSV.name}` ({n} rows)")
        else:
            st.error("No BCG table found in database.")
            conn.close()
            return

        if crm_table:
            conn.execute(f"COPY (SELECT * FROM {crm_table}) TO '{_CRM_CSV}' (FORMAT CSV, HEADER)")
            st.success(f"✅ CRM data exported → `{_CRM_CSV.name}`")
        else:
            st.warning("No CRM table found — labels will default to 0.")
            _CRM_CSV.write_text("company_name\n")

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
