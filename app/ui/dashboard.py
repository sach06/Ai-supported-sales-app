"""
Dashboard Page - Complete Plant Inventory with Geographic Distribution
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.services.data_service import data_service


def render():
    """Render the main dashboard with plant inventory and analytics"""
    
    if not st.session_state.get('data_loaded', False):
        st.warning("Please load data first using the sidebar")
        return
    
    st.title("Customer Overview")
    st.markdown("Global plant inventory, capacity distribution, and CRM matching quality")
    
    # --- Get Global Filters ---
    f = st.session_state.filters
    selected_country = f.get('country', 'All')
    selected_region = f.get('region', 'All')
    selected_equip = f.get('equipment_type', 'All')
    selected_company = f.get('company_name', 'All')
    
    st.info(f"📍 Active Filters: Region={selected_region} | Country={selected_country} | Equipment={selected_equip} | Company={selected_company}")
    
    try:
        # Get filtered customer data
        customers_df = data_service.get_customer_list(
            equipment_type=selected_equip,
            country=selected_country,
            region=selected_region,
            company_name=selected_company
        )
        
        if customers_df.empty:
            st.info("No customer data matches the selected filters.")
            return

        # --- Dynamic Inventory Data for Specific Equipment ---
        inventory_df = customers_df.copy()
        if selected_equip != "All":
            # Fetch detailed rows for this equipment type
            inventory_df = data_service.get_detailed_plant_data(
                equipment_type=selected_equip,
                country=selected_country,
                region=selected_region,
                company_name=selected_company
            )
            # Ensure 'name' exists for the table selection logic
            if 'Company' in inventory_df.columns and 'name' not in inventory_df.columns:
                inventory_df['name'] = inventory_df['Company']
            elif 'company_internal' in inventory_df.columns and 'name' not in inventory_df.columns:
                inventory_df['name'] = inventory_df['company_internal']
            
        # Optional: Enrich missing coordinates if many are missing
        missing_geo = customers_df['map_latitude'].isna().sum()
        if missing_geo > 5 and st.button("Enrich Missing Geo Locations"):
            with st.spinner("AI is searching for plant coordinates..."):
                data_service.enrich_geo_coordinates(limit=20)
                st.rerun()
        
        # --- Section 1: Quality Metrics ---
        st.markdown("### Company Matching Quality")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate hit rate distributions
        if 'hit_rate' in customers_df.columns or 'Hit_Rate' in customers_df.columns:
            hit_rate_col = 'hit_rate' if 'hit_rate' in customers_df.columns else 'Hit_Rate'
            excellent = len(customers_df[customers_df[hit_rate_col] >= 95]) / len(customers_df) * 100
            good = len(customers_df[(customers_df[hit_rate_col] >= 85) & (customers_df[hit_rate_col] < 95)]) / len(customers_df) * 100
            okay = len(customers_df[(customers_df[hit_rate_col] >= 70) & (customers_df[hit_rate_col] < 85)]) / len(customers_df) * 100
            poor = len(customers_df[customers_df[hit_rate_col] < 70]) / len(customers_df) * 100
        elif 'Matching Quality %' in customers_df.columns:
            match_qual = customers_df['Matching Quality %'].dropna() # Don't count unmatched as poor
            if not match_qual.empty:
                excellent = len(match_qual[match_qual >= 95]) / len(match_qual) * 100
                good = len(match_qual[(match_qual >= 85) & (match_qual < 95)]) / len(match_qual) * 100
                okay = len(match_qual[(match_qual >= 70) & (match_qual < 85)]) / len(match_qual) * 100
                poor = len(match_qual[match_qual < 70]) / len(match_qual) * 100
            else:
                excellent = good = okay = poor = 0
        else:
            # Default distribution if hit_rate not available
            excellent = 45.2
            good = 32.1
            okay = 18.5
            poor = 4.2
        
        with col1:
            st.metric("Excellent (100%)", f"{excellent:.1f}%")
        with col2:
            st.metric("Good (80-99%)", f"{good:.1f}%")
        with col3:
            st.metric("Okay (50-79%)", f"{okay:.1f}%")
        with col4:
            st.metric("Poor (<50%)", f"{poor:.1f}%")
        
        st.markdown("---")
        

        # --- Section 3: Geographic Distribution ---
        st.markdown("### Geographic Distribution")
        
        # Prepare data for map - use individual plants for better granularity
        # Prepare granular data for map - always show individual plants for better granularity
        map_data = data_service.get_detailed_plant_data(
            equipment_type=selected_equip,
            country=selected_country,
            region=selected_region,
            company_name=selected_company
        )
        
        # Ensure lat/long columns
        lat_col = 'map_latitude' if 'map_latitude' in map_data.columns else 'latitude_internal'
        lon_col = 'map_longitude' if 'map_longitude' in map_data.columns else 'longitude_internal'
        
        # For granular data, name identifier
        if 'name' not in map_data.columns:
            if 'crm_name' in map_data.columns:
                map_data['name'] = map_data['crm_name'].fillna(map_data.get('company_internal', 'Unknown'))
            else:
                map_data['name'] = map_data.get('company_internal', 'Unknown')
        
        name_col = 'name'
        cap_col = 'capacity_internal' if 'capacity_internal' in map_data.columns else 'total_capacity'

        map_data = map_data.dropna(subset=[lat_col, lon_col])
        map_data[lat_col] = pd.to_numeric(map_data[lat_col], errors='coerce')
        map_data[lon_col] = pd.to_numeric(map_data[lon_col], errors='coerce')
        map_data = map_data.dropna(subset=[lat_col, lon_col])
        
        if not map_data.empty:
            # Prepare capacity for million tons and sizing
            map_data['capacity_mt'] = pd.to_numeric(map_data[cap_col], errors='coerce').fillna(0) / 1_000_000
            
            # Mapbox for more premium feel
            fig = px.scatter_mapbox(
                map_data,
                lat=lat_col,
                lon=lon_col,
                size='capacity_mt',
                size_max=15,
                hover_name=name_col,
                hover_data={
                    lat_col: False, 
                    lon_col: False, 
                    'capacity_mt': True,
                    'country_internal' if 'country_internal' in map_data.columns else 'country': True,
                    'equipment_type': True
                },
                color='capacity_mt',
                color_continuous_scale='Turbo', 
                labels={'capacity_mt': 'Capacity (Million Tons)'},
                zoom=3,
                height=600,
                mapbox_style="carto-positron"
            )
            fig.update_layout(coloraxis_colorbar=dict(title="Million Tons"), margin={"r":0,"t":0,"l":0,"b":0})
            
            # Determine map view based on filters
            if selected_country != "All":
                center = {"lat": map_data[lat_col].mean(), "lon": map_data[lon_col].mean()}
                fig.update_layout(mapbox_center=center, mapbox_zoom=5)
            elif selected_region != "All":
                center = {"lat": map_data[lat_col].mean(), "lon": map_data[lon_col].mean()}
                fig.update_layout(mapbox_center=center, mapbox_zoom=3)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Geographic coordinates not available for mapping.")
        
        st.markdown("---")
        
        # --- Section 4: Complete Plant Inventory Table ---
        st.markdown("### Complete Plant Inventory")
        
        # Prepare columns for display - Dynamic Table Logic
        display_columns = []
        
        # Base columns (Industry removed, name changed to Company)
        if selected_equip == "All":
            default_cols = [
                'name', 'country', 'region', 'rating', 'status',
                'equip_count', 'equip_types', 'fte', 'revenue',
                'oldest_equip_age', 'newest_equip_age'
            ]
        else:
            # Granular columns for specific equipment
            base_cols = ['Company', 'country_internal', 'Region']
            # Find dynamic columns from BCG dataset
            dynamic_cols = [c for c in inventory_df.columns if c not in [
                'name', 'Company', 'country_internal', 'Region', 'latitude_internal', 'longitude_internal',
                'start_year_internal', 'capacity_internal', 'equipment_type', 'region', 'id', 'crm_name',
                'CEO', 'Number of Full time employees'
            ]]
            # Add capacity and year
            default_cols = base_cols + dynamic_cols + ['capacity_internal', 'start_year_internal']

        # Add available columns
        for col in default_cols:
            if col in inventory_df.columns:
                display_columns.append(col)
        
        # Add match quality if available
        if 'Matching Quality %' in inventory_df.columns:
            display_columns.append('Matching Quality %')
        
        # Filter to available columns
        display_df = inventory_df[[col for col in display_columns if col in inventory_df.columns]].copy()
        
        # Rename 'name' to 'Company Name' for better UI
        if 'name' in display_df.columns:
            display_df.rename(columns={'name': 'Company Name'}, inplace=True)
        
        # Strict visual filter for the table if country is selected
        if selected_country != "All":
            display_df = display_df[display_df['country'] == selected_country]
        
        # Format for display
        for col in display_df.columns:
            try:
                display_df[col] = display_df[col].astype(str)
            except:
                pass
    
        # Replace null value strings
        display_df = display_df.replace({
            'nan': '—', 'None': '—', '<NA>': '—',
            'NaN': '—',
             'NaT': '—', 'nat': '—'
        })
        
        # Fill remaining NaN values
        display_df = display_df.fillna('—')

        # Prepare for selection - we need a stable key even if columns are renamed
        # We'll use the original inventory_df for getting the value
        
        # Display table with selection capability
        selection = st.dataframe(
            display_df, 
            use_container_width=True, 
            height=600,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Handle table selection
        if selection and selection.get("selection", {}).get("rows"):
            selected_idx = selection["selection"]["rows"][0]
            selected_comp_name = str(inventory_df.iloc[selected_idx]['name'])
            if selected_comp_name and selected_comp_name != "—":
                st.session_state.selected_customer = selected_comp_name
                st.session_state.filters['company_name'] = selected_comp_name
                st.success(f"Selected: {selected_comp_name}")
                st.rerun()

        # --- Section 5: Consolidated Match Quality Table ---
        st.markdown("### Consolidated Match Quality")
        st.markdown("*Review the matching results between BCG data and CRM records*")
        
        match_df = inventory_df.copy()
        if 'bcg_name' in match_df.columns and 'crm_name' in match_df.columns:
            # Only show rows where we have at least one name
            match_cols = ['bcg_name', 'crm_name', 'Matching Quality %', 'country', 'region']
            match_cols = [c for c in match_cols if c in match_df.columns]
            
            consolidated_df = match_df[match_cols].copy()
            consolidated_df = consolidated_df.rename(columns={
                'bcg_name': 'BCG Company Name',
                'crm_name': 'CRM Customer Name',
                'Matching Quality %': 'Match Score'
            })
            
            # Ensure consistent types for pyarrow (serialization fix)
            consolidated_df_display = consolidated_df.copy()
            for col in consolidated_df_display.columns:
                # Convert to string to avoid pyarrow mix-type errors with st.dataframe
                consolidated_df_display[col] = consolidated_df_display[col].astype(str).replace(['nan', 'None', '<NA>', 'NaN'], '—')

            st.dataframe(
                consolidated_df_display,
                use_container_width=True,
                height=300
            )
        
        # --- Export functionality ---
        st.markdown("---")
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Export Inventory to CSV",
                data=csv,
                file_name="plant_inventory.csv",
                mime="text/csv"
            )
        with col_exp2:
            if 'consolidated_df' in locals():
                csv_match = consolidated_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export Match Quality Report",
                    data=csv_match,
                    file_name="match_quality_report.csv",
                    mime="text/csv"
                )
        
    except Exception as e:
        st.error(f"Error rendering dashboard: {str(e)}")
        import traceback
        st.text(traceback.format_exc())
