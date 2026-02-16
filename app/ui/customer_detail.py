"""
Enhanced Customer Detail Page - Professional UI with comprehensive analytics
NO EMOJIS - Professional formatting only
Integrates: web enrichment, market intelligence, projects, financial analysis, visualizations
"""
import streamlit as st
import json
import pandas as pd
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
    visualization_service
)


def render():
    """Render the enhanced customer detail page"""
    
    if not st.session_state.get('data_loaded', False):
        st.warning("Please load data first using the sidebar")
        return
    
    st.markdown("### Customer Analysis Dashboard")
    
    # --- 1. Use Global Filters ---
    f = st.session_state.filters
    selected_country = f.get('country', 'All')
    selected_region = f.get('region', 'All')
    selected_equip = f.get('equipment_type', 'All')
    selected_company_glob = f.get('company_name', 'All')

    st.info(f"Active Filters: Region={selected_region} | Country={selected_country} | Equipment={selected_equip} | Company={selected_company_glob}")

    # Customer selection with filters
    customers_df = data_service.get_customer_list(
        equipment_type=selected_equip,
        country=selected_country,
        region=selected_region,
        company_name=selected_company_glob
    )
    
    if customers_df.empty:
        st.info("No customers match the active global filters.")
        return
    
    # Get customer names
    customer_names = sorted([str(n) for n in customers_df['name'].unique() if pd.notna(n)])
    
    # Pre-select based on global filter or dashboard navigation
    default_idx = 0
    target_customer = selected_company_glob if selected_company_glob != "All" else st.session_state.get('selected_customer')
    
    if target_customer:
        try:
            default_idx = customer_names.index(target_customer)
        except ValueError:
            pass
    
    selected_customer = st.selectbox(
        "Select Customer",
        customer_names,
        index=default_idx
    )
    
    if not selected_customer:
        return
    
    # Get customer data
    customer_data = data_service.get_customer_detail(selected_customer, equipment_type=selected_equip)
    
    if not customer_data:
        st.warning(f"No data found for {selected_customer}")
        return
    
    # Enhanced tabs with new sections
    tabs = st.tabs([
        "Profile", 
        "Deep Dive",
        "Projects",
        "Market Intelligence",
        "Cost Analysis",
        "Installed Base", 
        "Prediction",
        "Edit"
    ])
    
    # --- TAB 1: ENHANCED PROFILE ---
    with tabs[0]:
        render_profile_tab(selected_customer, customer_data)
    
    # --- TAB 2: DEEP DIVE ANALYTICS ---
    with tabs[1]:
        render_deep_dive_tab(selected_customer, customer_data)
    
    # --- TAB 3: PROJECT ANALYSIS ---
    with tabs[2]:
        render_projects_tab(selected_customer, customer_data)
    
    # --- TAB 4: MARKET INTELLIGENCE ---
    with tabs[3]:
        render_market_intelligence_tab(selected_customer, customer_data)
    
    # --- TAB 5: COST ANALYSIS ---
    with tabs[4]:
        render_cost_analysis_tab(selected_customer, customer_data)
    
    # --- TAB 6: INSTALLED BASE (Existing, keep functionality) ---
    with tabs[5]:
        render_installed_base_tab(selected_customer, customer_data)
    
    # --- TAB 7: PREDICTION (Existing, keep functionality) ---
    with tabs[6]:
        render_prediction_tab(selected_customer, customer_data)
    
    # --- TAB 8: EDIT (Existing, keep functionality) ---
    with tabs[7]:
        render_edit_tab(selected_customer)


def render_profile_tab(selected_customer: str, customer_data: dict):
    """Render enhanced profile tab with external data enrichment"""
    st.markdown("#### Customer Profile")
    
    col1, col2 = st.columns([2, 2])
    
    with col2:
        sub_col1, sub_col2, sub_col3 = st.columns(3)
        
        with sub_col1:
            if st.button("Generate Profile", type="primary", use_container_width=True):
                with st.spinner("Generating comprehensive profile with external data..."):
                    # Generate profile
                    profile = profile_generator.generate_profile(customer_data)
                    
                    # Enrich with external data
                    company_name = profile.get('basic_data', {}).get('name', selected_customer)
                    
                    try:
                        # Get company overview from Wikipedia
                        overview = web_enrichment_service.get_company_overview(company_name)
                        profile['company_overview'] = overview
                        
                        # Get recent news
                        news = web_enrichment_service.get_recent_news(company_name, max_results=5)
                        profile['recent_news'] = news
                        
                        # Get market intelligence
                        market_intel = market_intelligence_service.generate_market_intelligence(
                            customer_data,
                            profile
                        )
                        profile['market_intelligence'] = market_intel
                        
                    except Exception as e:
                        st.warning(f"Some external data could not be retrieved: {e}")
                    
                    st.session_state[f'profile_{selected_customer}'] = profile
                    st.session_state[f'enriched_{selected_customer}'] = True
                    st.success("Profile generated with external data!")
                    st.rerun()
        
        # Export buttons (NO EXCEL - only DOCX and PDF)
        if f'profile_{selected_customer}' in st.session_state:
            profile = st.session_state[f'profile_{selected_customer}']
            
            with sub_col2:
                try:
                    # Get additional data for comprehensive export
                    market_intel = profile.get('market_intelligence', {})
                    projects = customer_data.get('projects', [])
                    
                    # Generate charts for export
                    charts = {}
                    # TODO: Add chart generation here when needed
                    
                    docx_buffer = enhanced_export_service.generate_comprehensive_docx(
                        selected_customer,
                        profile,
                        customer_data,
                        market_intel=market_intel,
                        projects=projects,
                        charts=charts
                    )
                    
                    filename = enhanced_export_service.generate_filename(selected_customer, 'docx')
                    
                    st.download_button(
                        label="DOCX Export",
                        data=docx_buffer,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Export error: {e}")
            
            with sub_col3:
                st.button(
                    "PDF Export",
                    use_container_width=True,
                    disabled=True,
                    help="PDF export coming soon"
                )
    
    # Display profile
    if f'profile_{selected_customer}' in st.session_state:
        profile = st.session_state[f'profile_{selected_customer}']
        
        # Basic Data
        st.markdown("##### Basic Information")
        basic_data = profile.get('basic_data', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Company Name", basic_data.get('name', 'N/A'), disabled=True)
            st.text_input("Owner/Parent", basic_data.get('owner', 'N/A'), disabled=True)
            st.text_input("Employees (FTE)", basic_data.get('fte', 'N/A'), disabled=True)
            st.text_input("CEO", basic_data.get('ceo', 'N/A'), disabled=True)
            st.text_input("Buying Center", basic_data.get('buying_center', 'N/A'), disabled=True)
        
        with col2:
            st.text_input("HQ Address", basic_data.get('hq_address', 'N/A'), disabled=True)
            st.text_input("Management", basic_data.get('management', 'N/A'), disabled=True)
            st.text_input("Financial Status", basic_data.get('financials', 'N/A'), disabled=True)
            st.text_input("Coordinates", f"{basic_data.get('latitude', 'N/A')}, {basic_data.get('longitude', 'N/A')}", disabled=True)
            st.text_input("Frame Agreements", basic_data.get('frame_agreements', 'N/A'), disabled=True)
        
        st.text_area("Ownership History", basic_data.get('ownership_history', 'N/A'), height=100, disabled=True)
        st.text_area("Recent News & Facts", basic_data.get('recent_facts', 'N/A'), height=100, disabled=True)
        st.text_area("Company Focus/Vision", basic_data.get('company_focus', 'N/A'), height=100, disabled=True)
        st.text_area("Embargos/ESG Concerns", basic_data.get('embargos_esg', 'N/A'), height=80, disabled=True)
        
        # External Company Overview (if enriched)
        if 'company_overview' in profile:
            st.markdown("##### External Company Information")
            overview = profile['company_overview']
            
            if overview.get('description'):
                st.info(overview['description'])
            
            if overview.get('source_url'):
                st.markdown(f"**Source:** [{overview['source_url']}]({overview['source_url']})")
            
            if overview.get('last_updated'):
                st.caption(f"Retrieved: {overview['last_updated']}")
        
        # Recent News from External Sources
        if 'recent_news' in profile and profile['recent_news']:
            st.markdown("##### Recent News & Developments")
            
            news_items = profile['recent_news']
            for idx, news in enumerate(news_items, 1):
                with st.expander(f"{idx}. {news.get('title', 'No title')} ({news.get('published_date', 'Unknown date')})"):
                    if news.get('description'):
                        st.write(news['description'])
                    if news.get('url'):
                        st.markdown(f"**Source:** [{news['url']}]({news['url']})")
        
        # Locations
        st.markdown("##### Locations and Installed Base")
        locations = profile.get('locations', [])
        
        if locations:
            for i, loc in enumerate(locations, 1):
                with st.expander(f"Location {i}: {loc.get('address', 'Unknown')}"):
                    st.text_input("Address", loc.get('address', 'N/A'), key=f'loc_addr_{i}_{selected_customer}', disabled=True)
                    
                    st.markdown("**Installed Equipment:**")
                    eq_data = loc.get('installed_base')
                    if isinstance(eq_data, list) and eq_data:
                        eq_df = pd.DataFrame(eq_data)
                        eq_df.columns = [c.replace('_', ' ').title() for c in eq_df.columns]
                        st.dataframe(eq_df, use_container_width=True)
                    else:
                        st.info(str(eq_data) if eq_data else "No equipment data")
                        
                    st.text_input("Final Products", loc.get('final_products', 'N/A'), key=f'loc_prod_{i}_{selected_customer}', disabled=True)
                    st.text_input("Production Capacity", loc.get('tons_per_year', 'N/A'), key=f'loc_cap_{i}_{selected_customer}', disabled=True)
        else:
            st.info("No location data available")
        
        # History
        st.markdown("##### Project History and Relationship")
        history = profile.get('history', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("Latest Projects", history.get('latest_projects', 'N/A'), disabled=True)
            st.text_input("CRM Rating", history.get('crm_rating', 'N/A'), disabled=True)
            st.text_input("SMS Relationship", history.get('sms_relationship', 'N/A'), disabled=True)
        
        with col2:
            st.text_area("Realized Projects", history.get('realized_projects', 'N/A'), disabled=True)
            st.text_input("Key Contact Person", history.get('key_person', 'N/A'), disabled=True)
            st.text_input("Latest Visits", history.get('latest_visits', 'N/A'), disabled=True)
        
        # Context
        st.markdown("##### Market Context")
        context = profile.get('context', {})
        
        st.text_area("End Customer", context.get('end_customer', 'N/A'), disabled=True)
        st.text_area("Market Position", context.get('market_position', 'N/A'), disabled=True)

        # Metallurgical Insights
        st.markdown("##### Metallurgical & Technical Insights")
        meta = profile.get('metallurgical_insights', {})
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.text_area("Process Efficiency", meta.get('process_efficiency', 'N/A'), disabled=True, key=f'eff_{selected_customer}')
            st.text_area("Carbon Footprint (Green Steel)", meta.get('carbon_footprint_strategy', 'N/A'), disabled=True, key=f'co2_{selected_customer}')
        with col_m2:
            st.text_area("Modernization Potential", meta.get('modernization_potential', 'N/A'), disabled=True, key=f'mod_{selected_customer}')
            st.text_area("Technical Bottlenecks", meta.get('technical_bottlenecks', 'N/A'), disabled=True, key=f'bottle_{selected_customer}')

        # Sales Strategy
        st.markdown("##### Strategic Sales Pitch")
        strat = profile.get('sales_strategy', {})
        
        st.success(f"Recommended Portfolio: {strat.get('recommended_portfolio', 'N/A')}")
        st.info(f"Value Proposition: {strat.get('value_proposition', 'N/A')}")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.text_area("Competitive Landscape", strat.get('competitive_landscape', 'N/A'), disabled=True, key=f'comp_{selected_customer}')
        with col_s2:
            st.text_area("Suggested Next Steps", strat.get('suggested_next_steps', 'N/A'), disabled=True, key=f'steps_{selected_customer}')
    
    else:
        st.info("Click 'Generate Profile' to create an AI-powered customer profile with external data enrichment")


def render_deep_dive_tab(selected_customer: str, customer_data: dict):
    """Render deep dive analytics tab with comprehensive KPIs and charts"""
    st.markdown("#### Deep Dive Analytics")
    
    # Get projects and installed base for analysis
    projects = customer_data.get('projects', [])
    installed_base = customer_data.get('installed_base', [])
    crm = customer_data.get('crm', {})
    
    # Calculate comprehensive KPIs
    total_revenue = sum([p.get('value', 0) for p in projects])
    total_equipment = len(installed_base)
    avg_equipment_age = sum([2026 - eq.get('start_year', 2020) for eq in installed_base if eq.get('start_year') is not None]) / max(len([eq for eq in installed_base if eq.get('start_year') is not None]), 1)
    active_projects_count = len([p for p in projects if p.get('status') in ['Active', 'In Progress']])
    
    # Engagement score (0-100 based on multiple factors)
    engagement_factors = []
    if total_revenue > 1000000:
        engagement_factors.append(30)
    elif total_revenue > 500000:
        engagement_factors.append(20)
    elif total_revenue > 100000:
        engagement_factors.append(10)
    
    if total_equipment > 10:
        engagement_factors.append(25)
    elif total_equipment > 5:
        engagement_factors.append(15)
    elif total_equipment > 0:
        engagement_factors.append(5)
    
    if active_projects_count > 3:
        engagement_factors.append(25)
    elif active_projects_count > 1:
        engagement_factors.append(15)
    elif active_projects_count > 0:
        engagement_factors.append(10)
    
    crm_rating = crm.get('rating', 'C')
    if crm_rating == 'A':
        engagement_factors.append(20)
    elif crm_rating == 'B':
        engagement_factors.append(10)
    
    engagement_score = min(100, sum(engagement_factors))
    
    # Churn risk calculation (inverted engagement score)
    churn_risk = max(0, 100 - engagement_score - 20)  # Baseline lower risk
    
    # Customer Lifetime Value (simplified)
    years_active = len(set([p.get('start_date', '').split('-')[0] for p in projects if p.get('start_date')]))
    clv = total_revenue * max(1, years_active / 3)  # Simplified CLV formula
    
    # Top row: Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Revenue", f"${total_revenue:,.0f}", delta=None)
    with col2:
        st.metric("Customer Lifetime Value", f"${clv:,.0f}")
    with col3:
        st.metric("Engagement Score", f"{engagement_score}/100", 
                 delta=f"{engagement_score - 60}" if engagement_score >= 60 else f"{engagement_score - 60}")
    with col4:
        risk_status = "Low" if churn_risk < 30 else "Medium" if churn_risk < 60 else "High"
        st.metric("Churn Risk", risk_status, delta=None, 
                 delta_color="inverse" if churn_risk > 50 else "normal")
    
    st.markdown("---")
    
    # Revenue trends chart
    if projects:
        st.markdown("##### Revenue Trends Over Time")
        
        # Create revenue by year data
        revenue_by_year = {}
        for project in projects:
            start_date = project.get('start_date', '')
            if start_date:
                # Convert to string first to handle both string and non-string dates
                start_date_str = str(start_date)
                year = start_date_str.split('-')[0] if '-' in start_date_str else start_date_str[:4]
                revenue_by_year[year] = revenue_by_year.get(year, 0) + project.get('value', 0)
        
        if revenue_by_year:
            # Prepare data for visualization
            years = sorted(revenue_by_year.keys())
            revenues = [revenue_by_year[y] for y in years]
            
            # Create chart using visualization_service
            fig = visualization_service.create_revenue_trend(
                years=years,
                revenues=revenues,
                title=f"Revenue Trend - {selected_customer}"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No dated projects available for trend analysis")
    else:
        st.info("No project data available for revenue trends")
    
    st.markdown("---")
    
    # Equipment and Projects Overview  
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Equipment Portfolio")
        if installed_base:
            equipment_types = {}
            for eq in installed_base:
                eq_type = eq.get('equipment', eq.get('equipment_type', 'Unknown'))
                equipment_types[eq_type] = equipment_types.get(eq_type, 0) + 1
            
            # Create pie chart
            fig = visualization_service.create_equipment_distribution(
                equipment_types=equipment_types,
                title="Equipment Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("Total Equipment", total_equipment)
            st.metric("Average Age", f"{avg_equipment_age:.1f} years")
        else:
            st.info("No equipment data available")
    
    with col2:
        st.markdown("##### Project Status Distribution")
        if projects:
            status_counts = {}
            for project in projects:
                status = project.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Create pie chart
            fig = visualization_service.create_project_distribution(
                statuses=list(status_counts.keys()),
                counts=list(status_counts.values()),
                title="Project Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("Total Projects", len(projects))
            st.metric("Active Projects", active_projects_count)
        else:
            st.info("No project data available")
    
    st.markdown("---")
    
    # Historical Activity
    st.markdown("##### Historical Activity Timeline")
    if projects:
        # Create timeline data
        activity_timeline = []
        for project in projects:
            start_date = project.get('start_date')
            if start_date:
                activity_timeline.append({
                    'Date': start_date,
                    'Event': f"Project: {project.get('name', 'Unnamed')}",
                    'Value': project.get('value', 0),
                    'Status': project.get('status', 'Unknown')
                })
        
        if activity_timeline:
            # Sort by date
            activity_timeline.sort(key=lambda x: x['Date'])
            
            # Display as table
            st.dataframe(
                pd.DataFrame(activity_timeline),
                use_container_width=True,
                height=300
            )
        else:
            st.info("No dated activities to display")
    else:
        st.info("No historical activity data available")


def render_projects_tab(selected_customer: str, customer_data: dict):
    """Render project analysis tab"""
    st.markdown("#### Project Analysis")
    
    projects = customer_data.get('projects', [])
    
    if not projects:
        st.info("No project data available for this customer")
        return
    
    # Get project summary
    summary = project_service.get_project_summary (customer_data)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Projects", summary['total_projects'])
    with col2:
        st.metric("Active Projects", summary['active_projects'])
    with col3:
        st.metric("Completed Projects", summary['completed_projects'])
    with col4:
        st.metric("Total Value", f"${summary['total_value']:,.0f}")
    
    st.markdown("---")
    
    # Project details
    st.markdown("##### Project Details")
    
    for project in projects:
        health = project_service.calculate_project_health(project)
        
        # Status label (no emojis)
        if health == "On Track":
            status_label = "[ON TRACK]"
        elif health == "At Risk":
            status_label = "[AT RISK]"
        elif health == "Delayed":
            status_label = "[DELAYED]"
        else:
            status_label = "[UNKNOWN]"
        
        with st.expander(f"{status_label} {project.get('name', 'Unnamed Project')} - {health}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Status:** {project.get('status', 'Unknown')}")
                st.write(f"**Start:** {project.get('start_date', 'N/A')}")
                st.write(f"**End:** {project.get('end_date', 'N/A')}")
            
            with col2:
                st.write(f"**Budget:** ${project.get('budget', 0):,.2f}")
                st.write(f"**Spent:** ${project.get('spent', 0):,.2f}")
                st.write(f"**Progress:** {project.get('progress', 0)}%")
            
            with col3:
                st.write(f"**Type:** {project.get('type', 'N/A')}")
                st.write(f"**Value:** ${project.get('value', 0):,.2f}")
            
            # Project risks
            risks = project_service.get_project_risks(project)
            if risks:
                st.markdown("**Identified Risks:**")
                for risk in risks:
                    if risk['severity'] == 'High':
                        st.error(f"{risk['risk']}: {risk['mitigation']}")
                    elif risk['severity'] == 'Medium':
                        st.warning(f"{risk['risk']}: {risk['mitigation']}")
                    else:
                        st.info(f"{risk['risk']}: {risk['mitigation']}")


def render_market_intelligence_tab(selected_customer: str, customer_data: dict):
    """Render market intelligence tab"""
    st.markdown("#### Market Intelligence")
    
    # Generate or retrieve market intelligence
    if f'profile_{selected_customer}' in st.session_state:
        profile = st.session_state[f'profile_{selected_customer}']
        intel = profile.get('market_intelligence', {})
        
        if intel:
            # Financial Health
            st.markdown("##### Financial Health")
            st.info(intel.get('financial_health', 'N/A'))
            
            # Two-column layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Recent Developments")
                st.write(intel.get('recent_developments', 'N/A'))
                
                st.markdown("##### Market Position")
                st.info(intel.get('market_position', 'N/A'))
            
            with col2:
                st.markdown("##### Strategic Outlook")
                st.write(intel.get('strategic_outlook', 'N/A'))
                
                st.markdown("##### Risk Assessment")
                st.warning(intel.get('risk_assessment', 'N/A'))
            
            # Competitors
            if intel.get('competitors'):
                st.markdown("##### Key Competitors")
                for competitor in intel['competitors']:
                    st.write(f"- {competitor}")
            
            # Source citations
            if intel.get('sources'):
                st.markdown("##### Data Sources")
                for source in intel['sources']:
                    st.caption(source)
        else:
            st.info("Generate a profile first to see market intelligence")
    else:
        st.info("Generate a profile first to see market intelligence")


def render_cost_analysis_tab(selected_customer: str, customer_data: dict):
    """Render comprehensive cost analysis tab with financial tracking"""
    st.markdown("#### Cost Analysis & Financial Tracking")
    
    projects = customer_data.get('projects', [])
    
    if not projects:
        st.info("No project data available for cost analysis")
        return
    
    # Calculate financial metrics using financial_service
    cost_breakdown = financial_service.calculate_cost_breakdown(customer_data)
    budget_variance = financial_service.calculate_budget_variance(customer_data)
    
    # Top-level financial metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_budget = sum([p.get('budget', 0) for p in projects])
    total_spent = sum([p.get('spent', 0) for p in projects])
    total_value = sum([p.get('value', 0) for p in projects])
    
    with col1:
        st.metric("Total Budget", f"${total_budget:,.0f}")
    with col2:
        st.metric("Total Spent", f"${total_spent:,.0f}", 
                 delta=f"${total_spent - total_budget:,.0f}" if total_budget > 0 else None,
                 delta_color="inverse")
    with col3:
        variance_pct = ((total_spent - total_budget) / total_budget * 100) if total_budget > 0 else 0
        st.metric("Budget Variance", f"{variance_pct:.1f}%",
                 delta_color="inverse" if variance_pct > 0 else "normal")
    with col4:
        roi = ((total_value - total_spent) / total_spent * 100) if total_spent > 0 else 0
        st.metric("ROI", f"{roi:.1f}%",
                 delta_color="normal" if roi > 0 else "inverse")
    
    st.markdown("---")
    
    # Cost Breakdown by Category
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Cost Breakdown by Project")
        
        if cost_breakdown:
            # Create bar chart
            project_names = [item['category'] for item in cost_breakdown]
            costs = [item['cost'] for item in cost_breakdown]
            
            fig = visualization_service.create_cost_breakdown(
                categories=project_names,
                costs=costs,
                title="Cost Distribution by Project"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No cost breakdown data available")
    
    with col2:
        st.markdown("##### Budget vs Actual Spending")
        
        if projects:
            # Prepare data for budget variance chart
            project_names = [p.get('name', f"Project {i+1}") for i, p in enumerate(projects)]
            budgets = [p.get('budget', 0) for p in projects]
            actuals = [p.get('spent', 0) for p in projects]
            
            fig = visualization_service.create_budget_variance(
                projects=project_names,
                budgets=budgets,
                actuals=actuals,
                title="Budget vs Actual by Project"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Cost Forecasting
    st.markdown("##### Cost Forecasting & Projections")
    
    try:
        forecast = financial_service.forecast_costs(customer_data, periods=6)
        
        if forecast:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Create forecast chart
                periods = list(range(1, len(forecast) + 1))
                forecasted_costs = forecast
                
                fig = visualization_service.create_cost_forecast(
                    periods=periods,
                    forecasts=forecasted_costs,
                    title="6-Month Cost Forecast"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Forecast Summary**")
                st.metric("Next Period", f"${forecast[0]:,.0f}")
                st.metric("6-Month Total", f"${sum(forecast):,.0f}")
                avg_monthly = sum(forecast) / len(forecast)
                st.metric("Avg Monthly", f"${avg_monthly:,.0f}")
        else:
            st.info("Insufficient data for cost forecasting")
    except Exception as e:
        st.warning(f"Cost forecasting unavailable: {e}")
    
    st.markdown("---")
    
    # Scenario Analysis
    st.markdown("##### Scenario Analysis")
    
    try:
        scenarios = financial_service.calculate_scenario_analysis(customer_data)
        
        if scenarios:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Best Case**")
                st.success(f"Revenue: ${scenarios['best_case']['revenue']:,.0f}")
                st.write(f"Cost: ${scenarios['best_case']['cost']:,.0f}")
                st.write(f"Profit: ${scenarios['best_case']['profit']:,.0f}")
            
            with col2:
                st.markdown("**Expected Case**")
                st.info(f"Revenue: ${scenarios['expected']['revenue']:,.0f}")
                st.write(f"Cost: ${scenarios['expected']['cost']:,.0f}")
                st.write(f"Profit: ${scenarios['expected']['profit']:,.0f}")
            
            with col3:
                st.markdown("**Worst Case**")
                st.warning(f"Revenue: ${scenarios['worst_case']['revenue']:,.0f}")
                st.write(f"Cost: ${scenarios['worst_case']['cost']:,.0f}")
                st.write(f"Profit: ${scenarios['worst_case']['profit']:,.0f}")
        else:
            st.info("Insufficient data for scenario analysis")
    except Exception as e:
        st.warning(f"Scenario analysis unavailable: {e}")
    
    st.markdown("---")
    
    # Detailed Project Cost Table
    st.markdown("##### Detailed Project Costs")
    
    project_costs = []
    for project in projects:
        budget = project.get('budget', 0)
        spent = project.get('spent', 0)
        variance = spent - budget
        variance_pct = (variance / budget * 100) if budget > 0 else 0
        
        project_costs.append({
            'Project': project.get('name', 'Unnamed'),
            'Budget': f"${budget:,.0f}",
            'Spent': f"${spent:,.0f}",
            'Variance': f"${variance:,.0f}",
            'Variance %': f"{variance_pct:.1f}%",
            'Status': project.get('status', 'Unknown'),
            'Progress': f"{project.get('progress', 0)}%"
        })
    
    if project_costs:
        st.dataframe(
            pd.DataFrame(project_costs),
            use_container_width=True,
            height=300
        )


def render_installed_base_tab(selected_customer: str, customer_data: dict):
    """Render installed base tab (existing functionality)"""
    st.markdown("#### Installed Base Details with Equipment-Level Predictions")
    
    if 'installed_base' in customer_data and customer_data['installed_base']:
        
        # Calculate predictions for each equipment
        equipment_list = []
        for idx, equipment in enumerate(customer_data['installed_base']):
            score, drivers = prediction_service.predict_equipment_hit_rate(
                equipment, 
                customer_data.get('crm', {})
            )
            
            # Build equipment row
            eq_row = {
                'Equipment ID': str(equipment.get('equipment_id', f'EQ-{idx+1}')),
                'Location': equipment.get('location', 'N/A'),
                'Equipment Type': equipment.get('equipment', equipment.get('equipment_type', 'N/A')),
                'Installation Year': equipment.get('start_year', equipment.get('installation_year', 'N/A')),
                'OEM': equipment.get('oem', equipment.get('manufacturer', 'N/A')),
                'Hit Rate %': score,
                'Age (years)': 2026 - int(equipment.get('start_year', 2020)) if pd.notna(equipment.get('start_year')) else 0
            }
            equipment_list.append(eq_row)
        
        equipment_df = pd.DataFrame(equipment_list)
        equipment_df = equipment_df.sort_values('Hit Rate %', ascending=False)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Equipment", len(equipment_df))
        
        with col2:
            high_priority = len(equipment_df[equipment_df['Hit Rate %'] >= 70])
            st.metric("High Priority (>=70%)", high_priority)
        
        with col3:
            avg_age = equipment_df['Age (years)'].mean()
            st.metric("Avg Equipment Age", f"{avg_age:.1f} years")
        
        with col4:
            avg_hit_rate = equipment_df['Hit Rate %'].mean()
            st.metric("Avg Hit Rate", f"{avg_hit_rate:.1f}%")
        
        st.markdown("---")
        
        # Fix Pyarrow serialization errors
        equipment_df_display = equipment_df.copy()
        for col in equipment_df_display.columns:
            if col not in ['Hit Rate %', 'Age (years)']:
                equipment_df_display[col] = equipment_df_display[col].astype(object).fillna("—").astype(str)
            else:
                equipment_df_display[col] = pd.to_numeric(equipment_df_display[col], errors='coerce')
        
        st.dataframe(
            equipment_df_display, 
            use_container_width=True, 
            height=400,
            column_config={
                "Hit Rate %": st.column_config.NumberColumn(format="%.1f%%")
            }
        )
        
        # Equipment detail view
        st.markdown("---")
        st.markdown("##### Equipment Detail Analysis")
        
        selected_eq = st.selectbox(
            "Select equipment for detailed analysis",
            equipment_df['Equipment ID'].tolist(),
            key=f'eq_selector_{selected_customer}'
        )
        
        if selected_eq:
            eq_idx = next((i for i, eq in enumerate(equipment_list) if eq['Equipment ID'] == selected_eq), 0)
            raw_eq_data = customer_data['installed_base'][eq_idx]
            
            score, drivers = prediction_service.predict_equipment_hit_rate(
                raw_eq_data,
                customer_data.get('crm', {})
            )
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric("Equipment Hit Rate", f"{score}%")
                
                if score >= 70:
                    status_color = "green"
                elif score >= 50:
                    status_color = "orange"
                else:
                    status_color = "red"
                
                st.markdown(f"""
                <div style="background-color: #f0f0f0; border-radius: 10px; padding: 5px;">
                    <div style="background-color: {status_color}; width: {score}%; height: 30px; border-radius: 8px; 
                                display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                        {score}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Key Drivers:**")
                for driver in drivers.get('positive', []):
                    st.success(f"Positive: {driver}")
                for driver in drivers.get('negative', []):
                    st.warning(f"Risk: {driver}")
                for driver in drivers.get('neutral', []):
                    st.info(f"Neutral: {driver}")
    else:
        st.info("No installed base data available for this customer")


def render_prediction_tab(selected_customer: str, customer_data: dict):
    """Render prediction tab (existing functionality)"""
    st.markdown("#### Sales Hit Rate Prediction")
    
    score, drivers = prediction_service.predict_hit_rate(customer_data)
    
    # Display score
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.metric("Predicted Hit Rate", f"{score}%")
        
        if score >= 70:
            status_color = "green"
        elif score >= 50:
            status_color = "orange"
        else:
            status_color = "red"
        
        st.markdown(f"""
        <div style="background-color: #f0f0f0; border-radius: 10px; padding: 5px;">
            <div style="background-color: {status_color}; width: {score}%; height: 30px; border-radius: 8px; 
                        display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                {score}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display drivers
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Positive Factors")
        for driver in drivers.get('positive', []):
            st.success(f"* {driver}")
        
        if not drivers.get('positive'):
            st.info("No significant positive factors identified")
    
    with col2:
        st.markdown("##### Risk Factors")
        for driver in drivers.get('negative', []):
            st.warning(f"* {driver}")
        
        if not drivers.get('negative'):
            st.info("No significant risk factors identified")


def render_edit_tab(selected_customer: str):
    """Render edit tab (existing functionality)"""
    st.markdown("#### Edit Profile")
    st.info("Allows manual corrections to the profile data")
    
    if f'profile_{selected_customer}' in st.session_state:
        profile = st.session_state[f'profile_{selected_customer}']
        
        st.markdown("##### Edit Basic Data")
        
        edited_profile = profile.copy()
        basic_data = edited_profile.get('basic_data', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            basic_data['name'] = st.text_input("Company Name", basic_data.get('name', ''), key=f'edit_name_{selected_customer}')
            basic_data['owner'] = st.text_input("Owner/Parent", basic_data.get('owner', ''), key=f'edit_owner_{selected_customer}')
            basic_data['fte'] = st.text_input("Employees (FTE)", basic_data.get('fte', ''), key=f'edit_fte_{selected_customer}')
        
        with col2:
            basic_data['hq_address'] = st.text_input("HQ Address", basic_data.get('hq_address', ''), key=f'edit_hq_{selected_customer}')
            basic_data['management'] = st.text_input("Management", basic_data.get('management', ''), key=f'edit_mgmt_{selected_customer}')
            basic_data['financials'] = st.text_input("Financial Status", basic_data.get('financials', ''), key=f'edit_fin_{selected_customer}')
        
        basic_data['company_focus'] = st.text_area("Company Focus/Vision", basic_data.get('company_focus', ''), key=f'edit_focus_{selected_customer}')
        
        edited_profile['basic_data'] = basic_data
        
        if st.button("Save Changes", type="primary", key=f'save_{selected_customer}'):
            st.session_state[f'profile_{selected_customer}'] = edited_profile
            st.success("Changes saved!")
            st.rerun()
    
    else:
        st.warning("Generate a profile first before editing")
