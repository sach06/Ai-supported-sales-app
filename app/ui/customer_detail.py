"""
app/ui/customer_detail.py
==========================
Enhanced Customer Detail Page.

Tabs
----
1. Profile          – AI-generated profile + external enrichment + basic data
2. Historical       – Year-by-year CRM project performance (from Axel's data)
3. Deep Dive        – KPIs, engagement score, trends
4. Projects         – CRM project table with filters
5. Market Intel     – Financial health, market position, strategic outlook
6. Installed Base   – IB equipment table enriched from Axel's ib_list.xlsx
7. Prediction       – Hit-rate prediction
8. Edit             – Manual corrections
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from app.services.data_service import data_service
from app.services import (
    profile_generator,
    prediction_service,
    web_enrichment_service,
    market_intelligence_service,
    project_service,
    financial_service,
    enhanced_export_service,
    visualization_service,
)
from app.services.historical_service import (
    get_yearly_performance,
    get_ib_summary,
    get_crm_projects_for_company,
)

CURRENT_YEAR = 2026


# ── Page entry point ─────────────────────────────────────────────────────────

def render():
    """Render the enhanced customer detail page."""

    if not st.session_state.get("data_loaded", False):
        st.warning("Please load data first using the sidebar")
        return

    st.markdown("### Customer Analysis Dashboard")

    # --- Global Filters ---
    f = st.session_state.filters
    selected_country     = f.get("country", "All")
    selected_region      = f.get("region", "All")
    selected_equip       = f.get("equipment_type", "All")
    selected_company_glob = f.get("company_name", "All")

    st.info(
        f"Active Filters: Region={selected_region} | Country={selected_country} "
        f"| Equipment={selected_equip} | Company={selected_company_glob}"
    )

    customers_df = data_service.get_customer_list(
        equipment_type=selected_equip,
        country=selected_country,
        region=selected_region,
        company_name=selected_company_glob,
    )

    if customers_df.empty:
        st.info("No customers match the active global filters.")
        return

    customer_names = sorted([str(n) for n in customers_df["name"].unique() if pd.notna(n)])

    default_idx = 0
    target_customer = (
        selected_company_glob if selected_company_glob != "All"
        else st.session_state.get("selected_customer")
    )
    if target_customer:
        try:
            default_idx = customer_names.index(target_customer)
        except ValueError:
            pass

    selected_customer = st.selectbox("Select Customer", customer_names, index=default_idx)

    if not selected_customer:
        return

    customer_data = data_service.get_customer_detail(selected_customer, equipment_type=selected_equip)

    if not customer_data:
        st.warning(f"No data found for {selected_customer}")
        return

    # --- Tabs ---
    # Profile is LAST — it is the culmination of the full workflow
    tabs = st.tabs([
        "Historical",
        "Deep Dive",
        "Projects",
        "Market Intelligence",
        "Installed Base",
        "Prediction",
        "Edit",
        "Profile",
    ])

    with tabs[0]:
        render_historical_tab(selected_customer, customer_data)
    with tabs[1]:
        render_deep_dive_tab(selected_customer, customer_data)
    with tabs[2]:
        render_projects_tab(selected_customer, customer_data)
    with tabs[3]:
        render_market_intelligence_tab(selected_customer, customer_data)
    with tabs[4]:
        render_installed_base_tab(selected_customer, customer_data)
    with tabs[5]:
        render_prediction_tab(selected_customer, customer_data)
    with tabs[6]:
        render_edit_tab(selected_customer)
    with tabs[7]:
        render_profile_tab(selected_customer, customer_data)


# ── Tab 1: Profile ────────────────────────────────────────────────────────────

def render_profile_tab(selected_customer: str, customer_data: dict):
    """AI-generated Customer Profile — the comprehensive consolidated output."""
    st.markdown("#### Customer Profile")
    st.caption(
        "This is the **culminating output** of the full analysis workflow — a consolidated "
        "intelligence dossier drawing on CRM data, BCG market data, Priority Ranking results, "
        "Financial details, Market Intelligence, Projects, Installed Base, and Country-level insights."
    )

    col1, col2 = st.columns([2, 2])

    with col2:
        sub_col1, sub_col2, sub_col3 = st.columns(3)

        with sub_col1:
            if st.button("Generate Profile", type="primary", use_container_width=True):
                with st.spinner("Gathering all available intelligence and generating comprehensive profile..."):
                    # ── 1. Company overview + news ────────────────────────────
                    company_name = customer_data.get("crm", {}).get(
                        "name", customer_data.get("crm", {}).get("customer_name", selected_customer)
                    )
                    try:
                        overview = web_enrichment_service.get_company_overview(company_name)
                    except Exception as e:
                        overview = {}
                        st.warning(f"Company overview not retrieved: {e}")

                    try:
                        # Depending on the method signature in web_enrichment_service
                        company_news = web_enrichment_service.get_recent_news(company_name, limit=5)
                    except Exception as e2:
                        company_news = []
                        st.warning(f"Company news not retrieved: {e2}")

                    # ── 2. Country-level steel intelligence ───────────────────
                    country = (
                        customer_data.get("crm", {}).get("country")
                        or st.session_state.filters.get("country", "")
                        or ""
                    )
                    try:
                        country_intel = web_enrichment_service.get_country_intelligence(country)
                    except Exception as e:
                        country_intel = {}
                        st.warning(f"Country intelligence not retrieved: {e}")

                    # ── 3. Priority ranking ────────────────────────────────────
                    priority_ranking = None
                    try:
                        from app.services.ml_ranking_service import ml_ranking_service as _mls
                        ranked = _mls.get_ranked_customers()
                        if not ranked.empty:
                            # Find this customer in the ranking
                            name_col = "name" if "name" in ranked.columns else ranked.columns[0]
                            match = ranked[
                                ranked[name_col].astype(str).str.lower() == selected_customer.lower()
                            ]
                            if not match.empty:
                                row = match.iloc[0]
                                priority_ranking = {
                                    "rank": int(match.index[0]) + 1,
                                    "total_customers": len(ranked),
                                    "score": float(row.get("score", row.get("ml_score", 0))),
                                    "raw_data": row.to_dict(),
                                }
                    except Exception as e:
                        st.info(f"Priority ranking data not available: {e}")

                    # ── 4. Financial details ────────────────────────────────────
                    financial_details = None
                    try:
                        from app.services import financial_service as _fs
                        financial_details = _fs.get_financial_summary(customer_data)
                    except Exception:
                        pass

                    # ── 5. CRM history (Axel's data) ─────────────────────────
                    crm_history = None
                    try:
                        crm_history = get_yearly_performance(selected_customer)
                    except Exception:
                        pass

                    # ── 6. Installed base summary ─────────────────────────────
                    ib_data = None
                    try:
                        ib_data = get_ib_summary(selected_customer)
                    except Exception:
                        pass

                    # ── 7. Market intelligence from LLM ──────────────────────
                    try:
                        # Build a minimal profile skeleton so market_intel can run
                        _tmp_profile = {"basic_data": {"name": company_name}}
                        market_intel = market_intelligence_service.generate_market_intelligence(
                            customer_data, _tmp_profile
                        )
                    except Exception as e:
                        market_intel = {}
                        st.warning(f"Market intelligence not generated: {e}")

                    # ── 8. Generate the full profile ──────────────────────────
                    extra_ctx = {
                        "priority_ranking": priority_ranking,
                        "financial_details": financial_details,
                        "crm_history": crm_history,
                        "ib_summary": ib_data,
                        "country_intelligence": country_intel,
                        "company_news": company_news,
                    }
                    profile = profile_generator.generate_profile(
                        customer_data, extra_context=extra_ctx
                    )
                    # Attach enriched data to profile
                    if overview:
                        profile["company_overview"] = overview
                    if company_news:
                        profile["recent_news"] = company_news
                    if market_intel:
                        profile["market_intelligence"] = market_intel
                    if country_intel:
                        profile["_country_intelligence_raw"] = country_intel
                    if priority_ranking:
                        profile["_priority_ranking_raw"] = priority_ranking

                    st.session_state[f"profile_{selected_customer}"] = profile
                    st.session_state[f"enriched_{selected_customer}"] = True
                    st.success("Comprehensive profile generated with all available intelligence!")
                    st.rerun()

        if f"profile_{selected_customer}" in st.session_state:
            profile = st.session_state[f"profile_{selected_customer}"]
            
            # --- Build chart dictionary for exports ---
            export_charts = {}
            if True:
                _crm_hist = get_yearly_performance(selected_customer)
                if _crm_hist and not _crm_hist.get("yearly_df", pd.DataFrame()).empty:
                    fig_pipeline = px.bar(
                        _crm_hist["yearly_df"], x="Year", y="Total Value (EUR)",
                        color_discrete_sequence=["#3b82f6"],
                        title="Annual Pipeline Value (EUR)",
                    )
                    export_charts['pipeline_history'] = fig_pipeline

                projects = customer_data.get("projects", [])
                if projects:
                    rev_by_year = {}
                    for p in projects:
                        sd = str(p.get("start_date", ""))
                        year = sd.split("-")[0] if "-" in sd else sd[:4]
                        if year:
                            rev_by_year[year] = rev_by_year.get(year, 0) + p.get("value", 0)
                    if rev_by_year:
                        years_sorted = sorted(rev_by_year.keys())
                        fig_rev = visualization_service.create_revenue_trend(
                            years=years_sorted, revenues=[rev_by_year[y] for y in years_sorted],
                            title=f"Revenue Trend - {selected_customer}",
                        )
                        export_charts['revenue_trend'] = fig_rev

                installed_base = customer_data.get("installed_base", [])
                if installed_base:
                    eq_types = {}
                    for eq in installed_base:
                        et = eq.get("equipment", eq.get("equipment_type", "Unknown"))
                        eq_types[et] = eq_types.get(et, 0) + 1
                    fig_eq = visualization_service.create_equipment_distribution(
                        equipment_types=eq_types, title="Equipment Distribution"
                    )
                    export_charts['equipment_distribution'] = fig_eq

                _ib_data = get_ib_summary(selected_customer)
                if _ib_data and _ib_data.get("df") is not None and not _ib_data["df"].empty:
                    df_ib = _ib_data["df"]
                    if "_age" in df_ib.columns and df_ib["_age"].notna().any():
                        fig_age = px.histogram(
                            df_ib.dropna(subset=["_age"]), x="_age", nbins=15,
                            labels={"_age": "Equipment Age (years)", "count": "#"},
                            color_discrete_sequence=["#3b82f6"], title="Age Distribution (IB)"
                        )
                        export_charts['ib_age_dist'] = fig_age
                    prod_col = _ib_data.get("prod_col")
                    if prod_col and prod_col in df_ib.columns:
                        eq_counts = df_ib[prod_col].value_counts().reset_index()
                        eq_counts.columns = ["Type", "Count"]
                        fig_type = px.bar(
                            eq_counts.head(15), x="Count", y="Type", orientation="h",
                            color_discrete_sequence=["#6366f1"], title="Equipment Type Breakdown (IB)"
                        )
                        export_charts['ib_type_dist'] = fig_type

            with sub_col2:
                try:
                    market_intel = profile.get("market_intelligence", {})
                    projects = customer_data.get("projects", [])
                    _crm_hist = get_yearly_performance(selected_customer)
                    _ib_data  = get_ib_summary(selected_customer)
                    docx_buffer = enhanced_export_service.generate_comprehensive_docx(
                        selected_customer, profile, customer_data,
                        market_intel=market_intel, projects=projects, charts=export_charts,
                        crm_history=_crm_hist if _crm_hist else None,
                        ib_data=_ib_data if _ib_data and _ib_data.get("n_units", 0) > 0 else None,
                    )
                    filename = enhanced_export_service.generate_filename(selected_customer, "docx")
                    st.download_button(
                        "DOCX Export", data=docx_buffer, file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Export error: {e}")

            with sub_col3:
                try:
                    market_intel = profile.get("market_intelligence", {})
                    _crm_hist = get_yearly_performance(selected_customer)
                    _ib_data  = get_ib_summary(selected_customer)
                    pdf_buffer = enhanced_export_service.generate_comprehensive_pdf(
                        selected_customer, profile, customer_data,
                        market_intel=market_intel, projects=customer_data.get("projects", []),
                        crm_history=_crm_hist if _crm_hist else None,
                        ib_data=_ib_data if _ib_data and _ib_data.get("n_units", 0) > 0 else None,
                        charts=export_charts,
                    )
                    pdf_filename = enhanced_export_service.generate_filename(selected_customer, "pdf")
                    st.download_button(
                        "PDF Export", data=pdf_buffer, file_name=pdf_filename,
                        mime="application/pdf", use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"PDF error: {e}")

    # ── Display profile ────────────────────────────────────────────────────────
    if f"profile_{selected_customer}" in st.session_state:
        profile = st.session_state[f"profile_{selected_customer}"]

        # ── Basic Information ──────────────────────────────────────────────────
        st.markdown("##### Basic Information")
        basic_data = profile.get("basic_data", {})
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Company Name",      basic_data.get("name", "N/A"),           disabled=True)
            st.text_input("Owner/Parent",       basic_data.get("owner", "N/A"),          disabled=True)
            st.text_input("Employees (FTE)",    basic_data.get("fte", "N/A"),            disabled=True)
            st.text_input("CEO",                basic_data.get("ceo", "N/A"),            disabled=True)
            st.text_input("Buying Center",      basic_data.get("buying_center", "N/A"),  disabled=True)
        with col2:
            st.text_input("HQ Address",         basic_data.get("hq_address", "N/A"),     disabled=True)
            st.text_input("Management",         basic_data.get("management", "N/A"),     disabled=True)
            st.text_input("Financial Status",   basic_data.get("financials", "N/A"),     disabled=True)
            lat = basic_data.get("latitude", "N/A")
            lon = basic_data.get("longitude", "N/A")
            st.text_input("Coordinates",        f"{lat}, {lon}",                         disabled=True)
            st.text_input("Frame Agreements",   basic_data.get("frame_agreements", "N/A"), disabled=True)

        st.text_area("Ownership History",        basic_data.get("ownership_history", "N/A"), height=80,  disabled=True)
        st.text_area("Recent News & Facts",      basic_data.get("recent_facts", "N/A"),      height=80,  disabled=True)
        st.text_area("Company Focus/Vision",     basic_data.get("company_focus", "N/A"),     height=80,  disabled=True)
        st.text_area("Embargos/ESG Concerns",    basic_data.get("embargos_esg", "N/A"),      height=60,  disabled=True)

        # ── External Company Information ────────────────────────────────────
        if "company_overview" in profile:
            st.markdown("##### External Company Information")
            overview = profile["company_overview"]
            if overview.get("description"):
                st.info(overview["description"])
            if overview.get("source_url"):
                st.markdown(f"**Source:** [{overview['source_url']}]({overview['source_url']})")
            if overview.get("last_updated"):
                st.caption(f"Retrieved: {overview['last_updated']}")

        # ── Recent Company News ─────────────────────────────────────────────
        if "recent_news" in profile and profile["recent_news"]:
            st.markdown("##### Recent Company News & Developments")
            for idx, news in enumerate(profile["recent_news"], 1):
                with st.expander(f"{idx}. {news.get('title','No title')} ({news.get('published_date','Unknown date')})"):
                    if news.get("description"):
                        st.write(news["description"])
                    if news.get("url"):
                        st.markdown(f"**Source:** [{news['url']}]({news['url']})")

        # ── Priority Analysis ──────────────────────────────────────────────
        priority_analysis = profile.get("priority_analysis", {})
        if priority_analysis:
            st.markdown("##### Priority Ranking Analysis")
            pa_col1, pa_col2 = st.columns([1, 2])
            with pa_col1:
                score_val = priority_analysis.get("priority_score", "N/A")
                rank_val  = priority_analysis.get("priority_rank", "N/A")
                st.metric("Priority Score", score_val)
                st.metric("Customer Rank",  rank_val)
            with pa_col2:
                st.text_area(
                    "Key Opportunity Drivers",
                    priority_analysis.get("key_opportunity_drivers", "N/A"),
                    height=80, disabled=True, key=f"pa_drivers_{selected_customer}",
                )
                st.text_area(
                    "Engagement Recommendation",
                    priority_analysis.get("engagement_recommendation", "N/A"),
                    height=60, disabled=True, key=f"pa_rec_{selected_customer}",
                )

        # ── Financial History Chart ────────────────────────────────────────
        financial_history = profile.get("financial_history", [])
        if financial_history:
            st.markdown("##### Financial History")
            try:
                fh_df = pd.DataFrame(financial_history)
                if "year" in fh_df.columns and "revenue_m_eur" in fh_df.columns:
                    fh_df = fh_df.sort_values("year")
                    fig_fh = go.Figure()
                    fig_fh.add_bar(
                        x=fh_df["year"].astype(str),
                        y=fh_df["revenue_m_eur"],
                        name="Revenue (M EUR)",
                        marker_color="#3b82f6",
                    )
                    if "ebitda_m_eur" in fh_df.columns:
                        fig_fh.add_bar(
                            x=fh_df["year"].astype(str),
                            y=fh_df["ebitda_m_eur"],
                            name="EBITDA (M EUR)",
                            marker_color="#22c55e",
                        )
                    fig_fh.update_layout(
                        barmode="group",
                        xaxis_title="Year",
                        yaxis_title="M EUR",
                        height=320,
                        margin=dict(t=10, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    )
                    st.plotly_chart(fig_fh, use_container_width=True)
            except Exception as e:
                st.info(f"Financial history chart could not be rendered: {e}")

        # ── Locations and Installed Base ───────────────────────────────────
        st.markdown("##### Locations and Installed Base")
        locations = profile.get("locations", [])
        if locations:
            for i, loc in enumerate(locations, 1):
                with st.expander(f"Location {i}: {loc.get('address','Unknown')}"):
                    st.text_input("Address", loc.get("address", "N/A"),
                                  key=f"loc_addr_{i}_{selected_customer}", disabled=True)
                    st.markdown("**Installed Equipment:**")
                    eq_data = loc.get("installed_base")
                    if isinstance(eq_data, list) and eq_data:
                        eq_df = pd.DataFrame(eq_data)
                        eq_df.columns = [c.replace("_", " ").title() for c in eq_df.columns]
                        st.dataframe(eq_df, use_container_width=True)
                    else:
                        st.info(str(eq_data) if eq_data else "No equipment data")
                    st.text_input("Final Products",       loc.get("final_products", "N/A"),
                                  key=f"loc_prod_{i}_{selected_customer}", disabled=True)
                    st.text_input("Production Capacity",  loc.get("tons_per_year", "N/A"),
                                  key=f"loc_cap_{i}_{selected_customer}",  disabled=True)
        else:
            st.info("No location data available")

        # ── Project History and Relationship ───────────────────────────────
        st.markdown("##### Project History and Relationship")
        history = profile.get("history", {})
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("Latest Projects",   history.get("latest_projects", "N/A"),   disabled=True)
            st.text_input("CRM Rating",        history.get("crm_rating", "N/A"),        disabled=True)
            st.text_input("SMS Relationship",  history.get("sms_relationship", "N/A"),  disabled=True)
        with col2:
            st.text_area("Realized Projects", history.get("realized_projects", "N/A"), disabled=True)
            st.text_input("Key Contact Person", history.get("key_person", "N/A"),       disabled=True)
            st.text_input("Latest Visits",      history.get("latest_visits", "N/A"),    disabled=True)
        h_col1, h_col2, h_col3 = st.columns(3)
        h_col1.metric("Total Won Value (EUR)", history.get("total_won_value_eur", "N/A"))
        h_col2.metric("Win Rate",              history.get("win_rate_pct", "N/A"))
        h_col3.metric("Total Projects Tracked", history.get("n_projects", "N/A"))

        # ── Market Context ─────────────────────────────────────────────────
        st.markdown("##### Market Context")
        context = profile.get("context", {})
        st.text_area("End Customer",    context.get("end_customer", "N/A"),    disabled=True)
        st.text_area("Market Position", context.get("market_position", "N/A"), disabled=True)

        # ── Country Intelligence ────────────────────────────────────────────
        ci = profile.get("country_intelligence", {})
        raw_ci = profile.get("_country_intelligence_raw", {})
        if ci or raw_ci:
            st.markdown("##### Country-Level Intelligence")
            ci_col1, ci_col2 = st.columns(2)
            with ci_col1:
                st.text_area(
                    "Steel Market Summary",
                    ci.get("steel_market_summary", "N/A"),
                    height=100, disabled=True, key=f"ci_steel_{selected_customer}",
                )
                st.text_area(
                    "Economic Context",
                    ci.get("economic_context", "N/A"),
                    height=100, disabled=True, key=f"ci_econ_{selected_customer}",
                )
                st.text_area(
                    "Trade & Tariff Context",
                    ci.get("trade_tariff_context", "N/A"),
                    height=80, disabled=True, key=f"ci_tariff_{selected_customer}",
                )
            with ci_col2:
                st.text_area(
                    "Automotive Sector Trends",
                    ci.get("automotive_sector", "N/A"),
                    height=100, disabled=True, key=f"ci_auto_{selected_customer}",
                )
                st.text_area(
                    "Investment Drivers",
                    ci.get("investment_drivers", "N/A"),
                    height=100, disabled=True, key=f"ci_invest_{selected_customer}",
                )
                st.text_area(
                    "SMS Group Positioning",
                    ci.get("sms_positioning", "N/A"),
                    height=80, disabled=True, key=f"ci_sms_{selected_customer}",
                )
            # Show raw news headlines
            if raw_ci.get("steel_news"):
                st.markdown("###### Recent Steel Industry News")
                for idx, item in enumerate(raw_ci["steel_news"][:5], 1):
                    with st.expander(f"{idx}. {item.get('title', 'No title')}"):
                        if item.get("description"):
                            st.write(item["description"])
                        if item.get("url"):
                            st.markdown(f"[Read more]({item['url']})")

        # ── Market Intelligence (AI) ────────────────────────────────────────
        if "market_intelligence" in profile:
            intel = profile["market_intelligence"]
            if intel:
                st.markdown("##### Market Intelligence")
                st.info(intel.get("financial_health", "N/A"))
                mi_col1, mi_col2 = st.columns(2)
                with mi_col1:
                    st.markdown("**Recent Developments**")
                    st.write(intel.get("recent_developments", "N/A"))
                    st.markdown("**Market Position**")
                    st.info(intel.get("market_position", "N/A"))
                with mi_col2:
                    st.markdown("**Strategic Outlook**")
                    st.write(intel.get("strategic_outlook", "N/A"))
                    st.markdown("**Risk Assessment**")
                    st.warning(intel.get("risk_assessment", "N/A"))

        # ── Metallurgical & Technical Insights ──────────────────────────────
        st.markdown("##### Metallurgical & Technical Insights")
        meta = profile.get("metallurgical_insights", {})
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.text_area("Process Efficiency",         meta.get("process_efficiency", "N/A"),        disabled=True, key=f"eff_{selected_customer}")
            st.text_area("Carbon Footprint (Green Steel)", meta.get("carbon_footprint_strategy", "N/A"), disabled=True, key=f"co2_{selected_customer}")
        with col_m2:
            st.text_area("Modernization Potential",    meta.get("modernization_potential", "N/A"),   disabled=True, key=f"mod_{selected_customer}")
            st.text_area("Technical Bottlenecks",      meta.get("technical_bottlenecks", "N/A"),     disabled=True, key=f"bottle_{selected_customer}")

        # ── Strategic Sales Pitch ───────────────────────────────────────────
        st.markdown("##### Strategic Sales Pitch")
        strat = profile.get("sales_strategy", {})
        st.success(f"Recommended Portfolio: {strat.get('recommended_portfolio', 'N/A')}")
        st.info(f"Value Proposition: {strat.get('value_proposition', 'N/A')}")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.text_area("Competitive Landscape",  strat.get("competitive_landscape", "N/A"),  disabled=True, key=f"comp_{selected_customer}")
        with col_s2:
            st.text_area("Suggested Next Steps",   strat.get("suggested_next_steps", "N/A"),   disabled=True, key=f"steps_{selected_customer}")
    else:
        st.info(
            "Click **'Generate Profile'** to create a comprehensive AI-powered Customer Profile "
            "consolidating all available intelligence: BCG data, CRM history, Priority Ranking, "
            "Financial details, Market Intelligence, Installed Base, Country-level steel market news, "
            "and company-specific external data."
        )


# ── Tab 2: Historical Performance ─────────────────────────────────────────────

def render_historical_tab(selected_customer: str, customer_data: dict):
    """Year-by-year business performance loaded from Axel's CRM export."""
    st.markdown("#### Historical Performance (CRM Data)")

    # Load from Axel's repo
    hist = get_yearly_performance(selected_customer)

    if not hist:
        st.info(
            "No CRM project history found for this company in Axel's data. "
            "The fuzzy match may not find a match if the company name differs. "
            "Try the **Projects** tab to browse the full CRM project list."
        )
        _show_raw_crm_search(selected_customer)
        return

    st.caption(f"📂 {hist.get('source', 'Axel CRM export')}")

    metrics = hist.get("metrics", {})
    yearly_df = hist.get("yearly_df", pd.DataFrame())

    # ── Summary KPIs ──────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        won_val = metrics.get("total_won_value", 0)
        st.metric("Total Won Value", f"€ {won_val:,.0f}" if won_val else "N/A")
    with m2:
        st.metric("Total Projects", metrics.get("n_projects", 0))
    with m3:
        st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
    with m4:
        st.metric("Years of Data", metrics.get("time_span", 0))

    st.markdown("---")

    # ── Yearly bar chart ──────────────────────────────────────────────────────
    if not yearly_df.empty and "Year" in yearly_df.columns:
        st.markdown("##### Annual Project Value (Total vs Won)")
        fig = go.Figure()
        fig.add_bar(
            x=yearly_df["Year"].astype(str),
            y=yearly_df["Total Value (EUR)"],
            name="Total Pipeline Value",
            marker_color="#93c5fd",
        )
        fig.add_bar(
            x=yearly_df["Year"].astype(str),
            y=yearly_df["Won Value (EUR)"],
            name="Won Value",
            marker_color="#16a34a",
        )
        fig.update_layout(
            barmode="overlay",
            xaxis_title="Year",
            yaxis_title="Value (EUR)",
            height=380,
            margin=dict(t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Win rate line
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("##### Win Rate by Year (%)")
            fig_wr = px.line(
                yearly_df, x="Year", y="Win Rate %",
                markers=True, color_discrete_sequence=["#f59e0b"],
            )
            fig_wr.update_layout(height=280, margin=dict(t=10, b=10))
            st.plotly_chart(fig_wr, use_container_width=True)

        with col_right:
            st.markdown("##### Projects per Year")
            fig_n = px.bar(
                yearly_df, x="Year", y="Projects",
                color_discrete_sequence=["#6366f1"],
            )
            fig_n.update_layout(height=280, margin=dict(t=10, b=10))
            st.plotly_chart(fig_n, use_container_width=True)

        st.markdown("##### Yearly Summary Table")
        st.dataframe(
            yearly_df.style.format({
                "Total Value (€)": "€ {:,.0f}",
                "Won Value (€)": "€ {:,.0f}",
                "Win Rate %": "{:.1f}%",
            }),
            use_container_width=True,
        )

    # ── Won projects detail ───────────────────────────────────────────────────
    won_list = hist.get("won_list", pd.DataFrame())
    if not won_list.empty:
        st.markdown("---")
        st.markdown(f"##### Won Projects ({len(won_list)} records)")
        show_cols = [c for c in [
            "account_name", "codeword_sales", "customer_project",
            "cp_expected_value_eur", "sp_expected_value_eur", "_year",
            "cp_status_hot", "sp_custom_status", "account_country", "sp_coe",
        ] if c in won_list.columns]
        if show_cols:
            st.dataframe(
                won_list[show_cols].rename(columns={
                    "account_name": "Account",
                    "codeword_sales": "Codeword",
                    "customer_project": "Project",
                    "cp_expected_value_eur": "CP Value (€)",
                    "sp_expected_value_eur": "SP Value (€)",
                    "_year": "Year",
                    "cp_status_hot": "Status",
                    "sp_custom_status": "SP Status",
                    "account_country": "Country",
                    "sp_coe": "CoE",
                }),
                use_container_width=True,
                height=300,
            )

    # ── All projects raw ──────────────────────────────────────────────────────
    with st.expander("📋 Show all CRM Projects (raw)"):
        raw = hist.get("raw_projects", pd.DataFrame())
        if not raw.empty:
            st.dataframe(raw, use_container_width=True, height=400)
        else:
            st.info("No raw project data available.")


def _show_raw_crm_search(company: str):
    """Allow user to manually search a company name in the CRM data."""
    st.markdown("##### Manual CRM Search")
    search_term = st.text_input(
        "Search CRM by company name (try partial name):",
        value=company[:10],
        key=f"hist_search_{company}",
    )
    if search_term and len(search_term) >= 3:
        from app.services.historical_service import _load_crm
        crm = _load_crm()
        if not crm.empty:
            col = "account_name" if "account_name" in crm.columns else crm.columns[0]
            mask = crm[col].astype(str).str.contains(search_term, case=False, na=False)
            results = crm[mask]
            st.info(f"Found {len(results)} rows matching '{search_term}'")
            if not results.empty:
                show_cols = [c for c in ["account_name", "codeword_sales", "customer_project",
                                          "cp_expected_value_eur", "_year", "cp_status_hot",
                                          "account_country"] if c in results.columns]
                st.dataframe(results[show_cols] if show_cols else results,
                             use_container_width=True, height=300)


# ── Tab 3: Deep Dive ──────────────────────────────────────────────────────────

def render_deep_dive_tab(selected_customer: str, customer_data: dict):
    """Deep-dive KPIs, engagement score, revenue trends."""
    st.markdown("#### Deep Dive Analytics")

    projects       = customer_data.get("projects", [])
    installed_base = customer_data.get("installed_base", [])
    crm            = customer_data.get("crm", {})

    total_revenue  = sum(p.get("value", 0) for p in projects)
    total_equipment = len(installed_base)

    def _safe_year(eq):
        try:
            return int(eq.get("start_year", CURRENT_YEAR))
        except (ValueError, TypeError):
            return CURRENT_YEAR

    valid_eq    = [eq for eq in installed_base if eq.get("start_year") is not None]
    avg_eq_age  = sum(CURRENT_YEAR - _safe_year(eq) for eq in valid_eq) / max(len(valid_eq), 1)
    active_proj = len([p for p in projects if p.get("status") in ["Active", "In Progress"]])

    # Engagement score
    ef = []
    if total_revenue > 1_000_000: ef.append(30)
    elif total_revenue > 500_000:  ef.append(20)
    elif total_revenue > 100_000:  ef.append(10)
    if total_equipment > 10: ef.append(25)
    elif total_equipment > 5: ef.append(15)
    elif total_equipment > 0: ef.append(5)
    if active_proj > 3: ef.append(25)
    elif active_proj > 1: ef.append(15)
    elif active_proj > 0: ef.append(10)
    crm_rating = crm.get("rating", "C")
    if crm_rating == "A": ef.append(20)
    elif crm_rating == "B": ef.append(10)
    engagement_score = min(100, sum(ef))
    churn_risk  = max(0, 100 - engagement_score - 20)
    years_active = len({str(p.get("start_date", "")).split("-")[0] for p in projects if p.get("start_date")})
    clv = total_revenue * max(1, years_active / 3)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue",            f"€ {total_revenue:,.0f}")
    col2.metric("Customer Lifetime Value", f"€ {clv:,.0f}")
    col3.metric("Engagement Score",         f"{engagement_score}/100")
    risk_status = "Low" if churn_risk < 30 else "Medium" if churn_risk < 60 else "High"
    col4.metric("Churn Risk",               risk_status)

    st.markdown("---")

    # Revenue trend
    if projects:
        st.markdown("##### Revenue Trends Over Time")
        rev_by_year = {}
        for p in projects:
            sd = str(p.get("start_date", ""))
            year = sd.split("-")[0] if "-" in sd else sd[:4]
            if year:
                rev_by_year[year] = rev_by_year.get(year, 0) + p.get("value", 0)
        if rev_by_year:
            years_sorted = sorted(rev_by_year.keys())
            fig = visualization_service.create_revenue_trend(
                years=years_sorted,
                revenues=[rev_by_year[y] for y in years_sorted],
                title=f"Revenue Trend - {selected_customer}",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No dated projects for trend analysis.")
    else:
        st.info("No project data available for revenue trends.")

    # Also show CRM historical trend from Axel's data
    hist = get_yearly_performance(selected_customer)
    if hist and not hist.get("yearly_df", pd.DataFrame()).empty:
        st.markdown("---")
        st.markdown("##### CRM Pipeline History (Axel's data)")
        st.caption(f"📂 {hist.get('source', '')}")
        yd = hist["yearly_df"]
        fig2 = px.bar(
            yd, x="Year", y="Total Value (EUR)",
            color_discrete_sequence=["#3b82f6"],
            title="Annual Pipeline Value (€)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Equipment Portfolio")
        if installed_base:
            eq_types = {}
            for eq in installed_base:
                et = eq.get("equipment", eq.get("equipment_type", "Unknown"))
                eq_types[et] = eq_types.get(et, 0) + 1
            fig = visualization_service.create_equipment_distribution(
                equipment_types=eq_types, title="Equipment Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.metric("Total Equipment",  total_equipment)
            st.metric("Average Age",      f"{avg_eq_age:.1f} years")
        else:
            st.info("No equipment data available.")

    with col2:
        st.markdown("##### Project Status Distribution")
        if projects:
            status_counts = {}
            for p in projects:
                s = p.get("status", "Unknown")
                status_counts[s] = status_counts.get(s, 0) + 1
            fig = visualization_service.create_project_distribution(
                statuses=list(status_counts.keys()),
                counts=list(status_counts.values()),
                title="Project Status Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.metric("Total Projects",  len(projects))
            st.metric("Active Projects", active_proj)
        else:
            st.info("No project data available.")


# ── Tab 4: Projects ───────────────────────────────────────────────────────────

def render_projects_tab(selected_customer: str, customer_data: dict):
    """Project table — internal data PLUS Axel's CRM export."""
    st.markdown("#### Project Analysis")

    # ── Internal projects ─────────────────────────────────────────────────────
    projects = customer_data.get("projects", [])
    if projects:
        summary = project_service.get_project_summary(customer_data)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Projects",     summary["total_projects"])
        col2.metric("Active Projects",    summary["active_projects"])
        col3.metric("Completed Projects", summary["completed_projects"])
        col4.metric("Total Value",        f"€ {summary['total_value']:,.0f}")

        st.markdown("---")
        st.markdown("##### Project Details")
        for project in projects:
            health = project_service.calculate_project_health(project)
            label  = {"On Track": "✅", "At Risk": "⚠️", "Delayed": "🔴"}.get(health, "❓")
            with st.expander(f"{label} {project.get('name','Unnamed Project')} — {health}"):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Status:** {project.get('status','Unknown')}")
                c1.write(f"**Start:**  {project.get('start_date','N/A')}")
                c1.write(f"**End:**    {project.get('end_date','N/A')}")
                c2.write(f"**Budget:** € {project.get('budget',0):,.2f}")
                c2.write(f"**Spent:**  € {project.get('spent',0):,.2f}")
                c2.write(f"**Progress:** {project.get('progress',0)}%")
                c3.write(f"**Type:**   {project.get('type','N/A')}")
                c3.write(f"**Value:**  € {project.get('value',0):,.2f}")
                risks = project_service.get_project_risks(project)
                if risks:
                    st.markdown("**Identified Risks:**")
                    for risk in risks:
                        if risk["severity"] == "High":
                            st.error(f"{risk['risk']}: {risk['mitigation']}")
                        elif risk["severity"] == "Medium":
                            st.warning(f"{risk['risk']}: {risk['mitigation']}")
                        else:
                            st.info(f"{risk['risk']}: {risk['mitigation']}")
    else:
        st.info("No internal project data available for this customer.")

    # ── Axel's CRM projects ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### CRM Projects (Axel's Export)")
    crm_proj = get_crm_projects_for_company(selected_customer)
    if not crm_proj.empty:
        from app.services.historical_service import CRM_SOURCE_LINK
        st.caption(f"📂 {CRM_SOURCE_LINK}  — {len(crm_proj)} rows")

        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            statuses  = ["All"] + sorted(crm_proj["cp_status_hot"].dropna().unique().tolist()) if "cp_status_hot" in crm_proj.columns else ["All"]
            sel_status = st.selectbox("Filter by Status", statuses, key=f"crm_status_{selected_customer}")
        with col_f2:
            coes = ["All"] + sorted(crm_proj["sp_coe"].dropna().unique().tolist()) if "sp_coe" in crm_proj.columns else ["All"]
            sel_coe = st.selectbox("Filter by CoE", coes, key=f"crm_coe_{selected_customer}")

        filtered = crm_proj.copy()
        if sel_status != "All" and "cp_status_hot" in filtered.columns:
            filtered = filtered[filtered["cp_status_hot"] == sel_status]
        if sel_coe != "All" and "sp_coe" in filtered.columns:
            filtered = filtered[filtered["sp_coe"] == sel_coe]

        show_cols = [c for c in [
            "account_name", "codeword_sales", "customer_project",
            "cp_expected_value_eur", "sp_expected_value_eur",
            "cp_status_hot", "sales_phase", "sp_coe",
            "account_country", "cp_close_date", "latest_notes",
        ] if c in filtered.columns]

        st.dataframe(
            filtered[show_cols].rename(columns={
                "account_name": "Account",
                "codeword_sales": "Codeword",
                "customer_project": "Project",
                "cp_expected_value_eur": "CP Value (€)",
                "sp_expected_value_eur": "SP Value (€)",
                "cp_status_hot": "Status",
                "sales_phase": "Phase",
                "sp_coe": "CoE",
                "account_country": "Country",
                "cp_close_date": "Close Date",
                "latest_notes": "Notes",
            }) if show_cols else filtered,
            use_container_width=True,
            height=400,
        )

        # Download
        csv = (filtered[show_cols] if show_cols else filtered).to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download CRM Projects CSV", data=csv,
                           file_name=f"{selected_customer}_crm_projects.csv", mime="text/csv")
    else:
        st.info("No matching CRM projects found in Axel's export. Use the manual search in the Historical tab.")


# ── Tab 5: Market Intelligence ─────────────────────────────────────────────────

def render_market_intelligence_tab(selected_customer: str, customer_data: dict):
    """Market intelligence from AI profile generation."""
    st.markdown("#### Market Intelligence")

    if f"profile_{selected_customer}" in st.session_state:
        profile = st.session_state[f"profile_{selected_customer}"]
        intel   = profile.get("market_intelligence", {})

        if intel:
            st.markdown("##### Financial Health")
            st.info(intel.get("financial_health", "N/A"))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### Recent Developments")
                st.write(intel.get("recent_developments", "N/A"))
                st.markdown("##### Market Position")
                st.info(intel.get("market_position", "N/A"))
            with col2:
                st.markdown("##### Strategic Outlook")
                st.write(intel.get("strategic_outlook", "N/A"))
                st.markdown("##### Risk Assessment")
                st.warning(intel.get("risk_assessment", "N/A"))

            if intel.get("competitors"):
                st.markdown("##### Key Competitors")
                for c in intel["competitors"]:
                    st.write(f"- {c}")

            if intel.get("sources"):
                st.markdown("##### Data Sources")
                for src in intel["sources"]:
                    st.caption(src)
        else:
            st.info("Generate a profile first (Profile tab → Generate Profile) to see market intelligence.")
    else:
        st.info("Generate a profile first (Profile tab → Generate Profile) to see market intelligence.")


# ── Tab 6: Installed Base ─────────────────────────────────────────────────────

def render_installed_base_tab(selected_customer: str, customer_data: dict):
    """Installed base — internal data + Axel's IB list enrichment."""
    st.markdown("#### Installed Base Details with Equipment-Level Predictions")

    # ── Section A: internal data + hit-rate ───────────────────────────────────
    if customer_data.get("installed_base"):
        equipment_list = []
        for idx, equipment in enumerate(customer_data["installed_base"]):
            score, drivers = prediction_service.predict_equipment_hit_rate(
                equipment, customer_data.get("crm", {})
            )
            equipment_list.append({
                "Equipment ID":       str(equipment.get("equipment_id", f"EQ-{idx+1}")),
                "Location":           equipment.get("location", "N/A"),
                "Equipment Type":     equipment.get("equipment", equipment.get("equipment_type", "N/A")),
                "Installation Year":  equipment.get("start_year", equipment.get("installation_year", "N/A")),
                "OEM":                equipment.get("oem", equipment.get("manufacturer", "N/A")),
                "Hit Rate %":         score,
                "Age (years)":        CURRENT_YEAR - int(equipment.get("start_year", CURRENT_YEAR))
                                      if pd.notna(equipment.get("start_year")) else 0,
            })

        eq_df = pd.DataFrame(equipment_list).sort_values("Hit Rate %", ascending=False)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Equipment",      len(eq_df))
        col2.metric("High Priority (≥70%)", len(eq_df[eq_df["Hit Rate %"] >= 70]))
        col3.metric("Avg Equipment Age",    f"{eq_df['Age (years)'].mean():.1f} years")
        col4.metric("Avg Hit Rate",         f"{eq_df['Hit Rate %'].mean():.1f}%")

        eq_df_display = eq_df.copy()
        for col in eq_df_display.columns:
            if col not in ["Hit Rate %", "Age (years)"]:
                eq_df_display[col] = eq_df_display[col].astype(object).fillna("—").astype(str)
            else:
                eq_df_display[col] = pd.to_numeric(eq_df_display[col], errors="coerce")

        st.dataframe(
            eq_df_display, use_container_width=True, height=400,
            column_config={"Hit Rate %": st.column_config.NumberColumn(format="%.1f%%")},
        )

        # Equipment detail view
        st.markdown("---")
        st.markdown("##### Equipment Detail Analysis")
        selected_eq = st.selectbox(
            "Select equipment for detailed analysis",
            eq_df["Equipment ID"].tolist(),
            key=f"eq_selector_{selected_customer}",
        )
        if selected_eq:
            eq_idx = next((i for i, eq in enumerate(equipment_list) if eq["Equipment ID"] == selected_eq), 0)
            raw_eq = customer_data["installed_base"][eq_idx]
            score, drivers = prediction_service.predict_equipment_hit_rate(raw_eq, customer_data.get("crm", {}))
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Equipment Hit Rate", f"{score}%")
                colour = "green" if score >= 70 else "orange" if score >= 50 else "red"
                st.markdown(f"""
<div style="background:#f0f0f0;border-radius:10px;padding:5px">
  <div style="background:{colour};width:{score}%;height:30px;border-radius:8px;
              display:flex;align-items:center;justify-content:center;color:white;font-weight:bold">
    {score}%
  </div>
</div>""", unsafe_allow_html=True)
            with col2:
                st.markdown("**Key Drivers:**")
                for d in drivers.get("positive", []):
                    st.success(f"Positive: {d}")
                for d in drivers.get("negative", []):
                    st.warning(f"Risk: {d}")
                for d in drivers.get("neutral", []):
                    st.info(f"Neutral: {d}")
    else:
        st.info("No internal installed-base data available for this customer.")

    # ── Section B: Axel's IB list ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Axel's Installed Base Data")

    ib_info = get_ib_summary(selected_customer)
    if ib_info["n_units"] == 0:
        st.info("No matching records found in Axel's IB list (ib_list.xlsx). Try the manual search below.")
        _ib_manual_search(selected_customer)
        return

    st.caption(f"📂 {ib_info.get('source', '')}  — {ib_info['n_units']} records found")

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Equipment Units",   ib_info["n_units"])
    col2.metric("Average Age (yrs)", ib_info["avg_age"])
    col3.metric("Equipment Types",   len(ib_info["equipment_types"]))
    col4.metric("Countries",         len(ib_info["countries"]))

    df_ib = ib_info["df"].copy()

    # Age histogram
    if "_age" in df_ib.columns and df_ib["_age"].notna().any():
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("##### Age Distribution")
            fig_age = px.histogram(
                df_ib.dropna(subset=["_age"]), x="_age", nbins=15,
                labels={"_age": "Equipment Age (years)", "count": "#"},
                color_discrete_sequence=["#3b82f6"],
            )
            fig_age.update_layout(height=280, margin=dict(t=10, b=10))
            st.plotly_chart(fig_age, use_container_width=True)

        with col_right:
            prod_col = ib_info.get("prod_col")
            if prod_col and prod_col in df_ib.columns:
                st.markdown("##### Equipment Type Breakdown")
                eq_counts = df_ib[prod_col].value_counts().reset_index()
                eq_counts.columns = ["Type", "Count"]
                fig_eq = px.bar(
                    eq_counts.head(15), x="Count", y="Type", orientation="h",
                    color_discrete_sequence=["#6366f1"],
                )
                fig_eq.update_layout(height=280, margin=dict(t=10, b=10))
                st.plotly_chart(fig_eq, use_container_width=True)

    # Full IB table
    st.markdown("##### IB Equipment Records")
    display_cols = [c for c in [
        "ib_machine", "ib_description", "ib_product",
        "ib_city", "ib_customer_country", "ib_country",
        "ib_startup", "_age", "ib_status",
        "pbs_coe", "key_account", "sub_region",
        "ib_region", "ib_responsible",
    ] if c in df_ib.columns]

    st.dataframe(
        df_ib[display_cols].rename(columns={
            "ib_machine": "Machine", "ib_description": "Description",
            "ib_product": "Product", "ib_city": "City",
            "ib_customer_country": "Country",
            "ib_startup": "Start Year", "_age": "Age (yrs)",
            "ib_status": "Status", "pbs_coe": "CoE",
            "key_account": "Key Account", "sub_region": "Sub-Region",
            "ib_region": "Region", "ib_responsible": "Responsible",
        }) if display_cols else df_ib,
        use_container_width=True, height=400,
    )

    csv_ib = (df_ib[display_cols] if display_cols else df_ib).to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download IB CSV", data=csv_ib,
                       file_name=f"{selected_customer}_installed_base.csv", mime="text/csv")


def _ib_manual_search(company: str):
    """Manual search in Axel's IB list."""
    st.markdown("##### Manual IB Search")
    search_term = st.text_input(
        "Search IB by customer name (partial):",
        value=company[:10],
        key=f"ib_search_{company}",
    )
    if search_term and len(search_term) >= 3:
        from app.services.historical_service import _load_ib
        ib = _load_ib()
        if not ib.empty:
            col = "ib_customer" if "ib_customer" in ib.columns else ib.columns[0]
            mask = ib[col].astype(str).str.contains(search_term, case=False, na=False)
            results = ib[mask]
            st.info(f"Found {len(results)} rows matching '{search_term}'")
            if not results.empty:
                st.dataframe(results, use_container_width=True, height=300)


# ── Tab 7: Prediction ─────────────────────────────────────────────────────────

def render_prediction_tab(selected_customer: str, customer_data: dict):
    """Sales hit-rate prediction."""
    st.markdown("#### Sales Hit Rate Prediction")

    score, drivers = prediction_service.predict_hit_rate(customer_data)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.metric("Predicted Hit Rate", f"{score}%")
        colour = "green" if score >= 70 else "orange" if score >= 50 else "red"
        st.markdown(f"""
<div style="background:#f0f0f0;border-radius:10px;padding:5px">
  <div style="background:{colour};width:{score}%;height:30px;border-radius:8px;
              display:flex;align-items:center;justify-content:center;color:white;font-weight:bold">
    {score}%
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Positive Factors")
        for d in drivers.get("positive", []):
            st.success(f"* {d}")
        if not drivers.get("positive"):
            st.info("No significant positive factors identified.")
    with col2:
        st.markdown("##### Risk Factors")
        for d in drivers.get("negative", []):
            st.warning(f"* {d}")
        if not drivers.get("negative"):
            st.info("No significant risk factors identified.")


# ── Tab 8: Edit ───────────────────────────────────────────────────────────────

def render_edit_tab(selected_customer: str):
    """Manual corrections to the generated profile."""
    st.markdown("#### Edit Profile")
    st.info("Allows manual corrections to the profile data")

    if f"profile_{selected_customer}" not in st.session_state:
        st.warning("Generate a profile first before editing")
        return

    profile = st.session_state[f"profile_{selected_customer}"]
    ep = {k: (v.copy() if isinstance(v, dict) else v) for k, v in profile.items()}

    # Basic Data
    st.markdown("##### Basic Data")
    bd = dict(ep.get("basic_data", {}))
    col1, col2 = st.columns(2)
    with col1:
        bd["name"]           = st.text_input("Company Name",       bd.get("name",""),           key=f"edit_name_{selected_customer}")
        bd["owner"]          = st.text_input("Owner / Parent",      bd.get("owner",""),          key=f"edit_owner_{selected_customer}")
        bd["fte"]            = st.text_input("Employees (FTE)",     bd.get("fte",""),            key=f"edit_fte_{selected_customer}")
        bd["ceo"]            = st.text_input("CEO",                 bd.get("ceo",""),            key=f"edit_ceo_{selected_customer}")
        bd["buying_center"] = st.text_input("Buying Center",       bd.get("buying_center",""),  key=f"edit_bc_{selected_customer}")
    with col2:
        bd["hq_address"]     = st.text_input("HQ Address",          bd.get("hq_address",""),    key=f"edit_hq_{selected_customer}")
        bd["management"]     = st.text_input("Management",           bd.get("management",""),   key=f"edit_mgmt_{selected_customer}")
        bd["financials"]     = st.text_input("Financial Status",     bd.get("financials",""),   key=f"edit_fin_{selected_customer}")
        lat = bd.get("latitude",""); lon = bd.get("longitude","")
        coords = st.text_input("Coordinates (lat, lon)",             f"{lat}, {lon}" if lat else "", key=f"edit_coords_{selected_customer}")
        bd["frame_agreements"] = st.text_input("Frame Agreements",   bd.get("frame_agreements",""), key=f"edit_fa_{selected_customer}")
    bd["ownership_history"] = st.text_area("Ownership History",    bd.get("ownership_history",""), height=80,  key=f"edit_ownhist_{selected_customer}")
    bd["recent_facts"]      = st.text_area("Recent News & Facts",   bd.get("recent_facts",""),      height=80,  key=f"edit_facts_{selected_customer}")
    bd["company_focus"]     = st.text_area("Company Focus / Vision",bd.get("company_focus",""),     height=80,  key=f"edit_focus_{selected_customer}")
    bd["embargos_esg"]      = st.text_area("Embargos / ESG",        bd.get("embargos_esg",""),      height=60,  key=f"edit_esg_{selected_customer}")
    ep["basic_data"] = bd

    st.markdown("---")

    # History
    st.markdown("##### Project History & Relationship")
    hist = dict(ep.get("history", {}))
    col1, col2 = st.columns(2)
    with col1:
        hist["latest_projects"]   = st.text_area("Latest Projects",   hist.get("latest_projects",""),  height=100, key=f"edit_latproj_{selected_customer}")
        hist["crm_rating"]        = st.text_input("CRM Rating",        hist.get("crm_rating",""),                  key=f"edit_crmr_{selected_customer}")
        hist["sms_relationship"]  = st.text_input("SMS Relationship",  hist.get("sms_relationship",""),            key=f"edit_smsrel_{selected_customer}")
    with col2:
        hist["realized_projects"] = st.text_area("Realized Projects",  hist.get("realized_projects",""), height=100, key=f"edit_realproj_{selected_customer}")
        hist["key_person"]        = st.text_input("Key Contact Person", hist.get("key_person",""),                  key=f"edit_kp_{selected_customer}")
        hist["latest_visits"]     = st.text_input("Latest Visits",      hist.get("latest_visits",""),               key=f"edit_lv_{selected_customer}")
    ep["history"] = hist

    st.markdown("---")

    # Market Context
    st.markdown("##### Market Context")
    ctx = dict(ep.get("context", {}))
    ctx["end_customer"]    = st.text_area("End Customer",    ctx.get("end_customer",""),    height=80, key=f"edit_ec_{selected_customer}")
    ctx["market_position"] = st.text_area("Market Position", ctx.get("market_position",""), height=80, key=f"edit_mp_{selected_customer}")
    ep["context"] = ctx

    st.markdown("---")

    # Metallurgical
    st.markdown("##### Metallurgical & Technical Insights")
    meta = dict(ep.get("metallurgical_insights", {}))
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        meta["process_efficiency"]        = st.text_area("Process Efficiency",           meta.get("process_efficiency",""),        height=100, key=f"edit_eff_{selected_customer}")
        meta["carbon_footprint_strategy"] = st.text_area("Carbon Footprint / Green Steel",meta.get("carbon_footprint_strategy",""), height=100, key=f"edit_co2_{selected_customer}")
    with col_m2:
        meta["modernization_potential"]   = st.text_area("Modernization Potential",      meta.get("modernization_potential",""),   height=100, key=f"edit_mod_{selected_customer}")
        meta["technical_bottlenecks"]     = st.text_area("Technical Bottlenecks",        meta.get("technical_bottlenecks",""),     height=100, key=f"edit_bottle_{selected_customer}")
    ep["metallurgical_insights"] = meta

    st.markdown("---")

    # Sales Strategy
    st.markdown("##### Strategic Sales Pitch")
    strat = dict(ep.get("sales_strategy", {}))
    strat["recommended_portfolio"] = st.text_input("Recommended Portfolio", strat.get("recommended_portfolio",""), key=f"edit_rp_{selected_customer}")
    strat["value_proposition"]     = st.text_area("Value Proposition",      strat.get("value_proposition",""),     height=80, key=f"edit_vp_{selected_customer}")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        strat["competitive_landscape"] = st.text_area("Competitive Landscape", strat.get("competitive_landscape",""), height=100, key=f"edit_cl_{selected_customer}")
    with col_s2:
        strat["suggested_next_steps"]  = st.text_area("Suggested Next Steps",  strat.get("suggested_next_steps",""),  height=100, key=f"edit_ns_{selected_customer}")
    ep["sales_strategy"] = strat

    st.markdown("---")

    if st.button("Save Changes", type="primary", key=f"save_{selected_customer}"):
        st.session_state[f"profile_{selected_customer}"] = ep
        st.success("Changes saved! Switch to the Profile tab to see the updated data.")
        st.rerun()

