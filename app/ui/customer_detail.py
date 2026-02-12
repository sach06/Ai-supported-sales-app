"""
Customer Detail page - Detailed profile view with AI-generated Steckbrief
"""
import streamlit as st
import json
from app.services import data_service, profile_generator, prediction_service, export_service
import pandas as pd


def render():
    """Render the customer detail page"""
    
    if not st.session_state.get('data_loaded', False):
        st.warning("Please load data first using the sidebar")
        return
    
    st.markdown("### Customer Profile (Steckbrief)")
    
    # --- 1. Use Global Filters ---
    f = st.session_state.filters
    selected_country = f.get('country', 'All')
    selected_region = f.get('region', 'All')
    selected_equip = f.get('equipment_type', 'All')
    selected_company_glob = f.get('company_name', 'All')

    st.info(f"📍 Active Filters: Region={selected_region} | Country={selected_country} | Equipment={selected_equip} | Company={selected_company_glob}")

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
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Profile", "Installed Base", "Prediction", "Edit"])
    
    # Tab 1: Profile
    with tab1:
        st.markdown("#### AI-Generated Customer Profile")
        
        col1, col2 = st.columns([2, 2])
        
        with col2:
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                if st.button("Generate Profile", type="primary", use_container_width=True):
                    with st.spinner("Generating comprehensive profile..."):
                        
                        profile = profile_generator.generate_profile(customer_data)
                        st.session_state[f'profile_{selected_customer}'] = profile
                        st.success("Profile generated!")
                        st.rerun()
            
            # Export buttons
            if f'profile_{selected_customer}' in st.session_state:
                profile = st.session_state[f'profile_{selected_customer}']
                
                with sub_col2:
                    docx_buffer = export_service.generate_docx(profile, selected_customer)
                    st.download_button(
                        label="📄 DOCX",
                        data=docx_buffer,
                        file_name=export_service.generate_filename(selected_customer, 'docx'),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                with sub_col3:
                    pdf_buffer = export_service.generate_pdf(profile, selected_customer)
                    st.download_button(
                        label="📕 PDF",
                        data=pdf_buffer,
                        file_name=export_service.generate_filename(selected_customer, 'pdf'),
                        mime="application/pdf",
                        use_container_width=True
                    )
        
        # Display profile
        if f'profile_{selected_customer}' in st.session_state:
            profile = st.session_state[f'profile_{selected_customer}']
            
            # Basic Data
            st.markdown("##### Basic Data")
            basic_data = profile.get('basic_data', {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Company Name", basic_data.get('name', 'N/A'), disabled=True, key=f'name_{selected_customer}')
                st.text_input("Owner/Parent", basic_data.get('owner', 'N/A'), disabled=True, key=f'owner_{selected_customer}')
                st.text_input("Employees (FTE)", basic_data.get('fte', 'N/A'), disabled=True, key=f'fte_{selected_customer}')
                st.text_input("CEO", basic_data.get('ceo', 'N/A'), disabled=True, key=f'ceo_{selected_customer}')
                st.text_input("Buying Center", basic_data.get('buying_center', 'N/A'), disabled=True, key=f'bc_{selected_customer}')
            
            with col2:
                st.text_input("HQ Address", basic_data.get('hq_address', 'N/A'), disabled=True, key=f'hq_{selected_customer}')
                st.text_input("Management", basic_data.get('management', 'N/A'), disabled=True, key=f'mgmt_{selected_customer}')
                st.text_input("Financial Status", basic_data.get('financials', 'N/A'), disabled=True, key=f'fin_{selected_customer}')
                st.text_input("Coordinates", f"{basic_data.get('latitude', 'N/A')}, {basic_data.get('longitude', 'N/A')}", disabled=True, key=f'coords_{selected_customer}')
                st.text_input("Frame Agreements", basic_data.get('frame_agreements', 'N/A'), disabled=True, key=f'fa_{selected_customer}')
            
            st.text_area("Ownership History", basic_data.get('ownership_history', 'N/A'), height=100, disabled=True, key=f'history_{selected_customer}')
            st.text_area("Recent News & Facts", basic_data.get('recent_facts', 'N/A'), height=100, disabled=True, key=f'facts_{selected_customer}')
            st.text_area("Company Focus/Vision", basic_data.get('company_focus', 'N/A'), height=100, disabled=True, key=f'focus_{selected_customer}')
            st.text_area("Embargos/ESG Concerns", basic_data.get('embargos_esg', 'N/A'), height=80, disabled=True, key=f'esg_{selected_customer}')
            
            # Locations
            st.markdown("##### Locations and Installed Base")
            locations = profile.get('locations', [])
            
            if locations:
                for i, loc in enumerate(locations, 1):
                    with st.expander(f"Location {i}: {loc.get('address', 'Unknown')}"):
                        st.text_input("Address", loc.get('address', 'N/A'), key=f'loc_addr_{i}_{selected_customer}', disabled=True)
                        
                        # CLEAN TABLE DISPLAY FOR EQUIPMENT
                        st.markdown("**Installed Equipment:**")
                        eq_data = loc.get('installed_base')
                        if isinstance(eq_data, list) and eq_data:
                            eq_df = pd.DataFrame(eq_data)
                            # Clean column names for display
                            eq_df.columns = [c.replace('_', ' ').title() for c in eq_df.columns]
                            st.dataframe(eq_df, width="stretch")
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
                st.text_area("Latest Projects", history.get('latest_projects', 'N/A'), disabled=True, key=f'latest_{selected_customer}')
                st.text_input("CRM Rating", history.get('crm_rating', 'N/A'), disabled=True, key=f'rating_{selected_customer}')
                st.text_input("SMS Relationship", history.get('sms_relationship', 'N/A'), disabled=True, key=f'sms_rel_{selected_customer}')
            
            with col2:
                st.text_area("Realized Projects", history.get('realized_projects', 'N/A'), disabled=True, key=f'realized_{selected_customer}')
                st.text_input("Key Contact Person", history.get('key_person', 'N/A'), disabled=True, key=f'contact_{selected_customer}')
                st.text_input("Latest Visits", history.get('latest_visits', 'N/A'), disabled=True, key=f'visits_{selected_customer}')
            
            # Context
            st.markdown("##### Market Context")
            context = profile.get('context', {})
            
            st.text_area("End Customer", context.get('end_customer', 'N/A'), disabled=True, key=f'end_cust_{selected_customer}')
            st.text_area("Market Position", context.get('market_position', 'N/A'), disabled=True, key=f'market_pos_{selected_customer}')

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
            st.info("Click 'Generate Profile' to create an AI-powered customer profile")
    
    # Tab 2: Installed Base
    with tab2:
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
            
            # Fix Pyarrow serialization errors by ensuring consistent types
            equipment_df_display = equipment_df.copy()
            for col in equipment_df_display.columns:
                if col not in ['Hit Rate %', 'Age (years)']:
                    # Convert everything else to clean strings
                    equipment_df_display[col] = equipment_df_display[col].astype(object).fillna("—").astype(str)
                else:
                    # Keep as numeric for st.column_config
                    equipment_df_display[col] = pd.to_numeric(equipment_df_display[col], errors='coerce')
            
            st.dataframe(
                equipment_df_display, 
                width="stretch", 
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
                # Find the equipment data
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
    
    # Tab 3: Prediction
    with tab3:
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
    
    # Tab 4: Edit
    with tab4:
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
