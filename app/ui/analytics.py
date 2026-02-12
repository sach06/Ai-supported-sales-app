"""
Analytics page - Visualizations and insights
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.services import data_service, prediction_service


def render():
    """Render the analytics page"""
    
    if not st.session_state.get('data_loaded', False):
        st.warning("Please load data first using the sidebar")
        return
    
    st.markdown("### Sales Analytics and Insights")
    
    # --- 1. Use Global Filters ---
    f = st.session_state.filters
    selected_country = f.get('country', 'All')
    selected_region = f.get('region', 'All')
    selected_equip = f.get('equipment_type', 'All')
    selected_company = f.get('company_name', 'All')

    st.info(f"Active Filters: Region={selected_region} | Country={selected_country} | Equipment={selected_equip} | Company={selected_company}")
    
    try:
        customers_df = data_service.get_customer_list(
            equipment_type=selected_equip,
            country=selected_country,
            region=selected_region,
            company_name=selected_company
        )
        
        if customers_df.empty:
            st.info("No customer data matches the selected filters.")
            return
        
        # Calculate predictions for all customers
        with st.spinner("Analyzing customer data..."):
            predictions = []
            
            for idx, row in customers_df.head(100).iterrows():
                customer_data = {'crm': row.to_dict()}
                score, drivers = prediction_service.predict_hit_rate(customer_data)
                
                predictions.append({
                    'Customer': row.get('name', f'Customer {idx}'),
                    'Hit_Rate': score,
                    'Industry': row.get('industry', 'Unknown'),
                    'Region': row.get('region', row.get('country', 'Unknown')),
                    'Employees': row.get('fte', row.get('employees', 0)),
                    'Rating': row.get('rating', 'C')
                })
            
            pred_df = pd.DataFrame(predictions)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_score = pred_df['Hit_Rate'].mean()
            st.metric("Average Hit Rate", f"{avg_score:.1f}%")
        
        with col2:
            high_potential = len(pred_df[pred_df['Hit_Rate'] >= 70])
            st.metric("High Potential", high_potential)
        
        with col3:
            medium_potential = len(pred_df[(pred_df['Hit_Rate'] >= 50) & (pred_df['Hit_Rate'] < 70)])
            st.metric("Medium Potential", medium_potential)
        
        with col4:
            low_potential = len(pred_df[pred_df['Hit_Rate'] < 50])
            st.metric("Low Potential", low_potential)
        
        st.markdown("---")
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Hit Rate Distribution")
            
            # Histogram
            fig = px.histogram(
                pred_df,
                x='Hit_Rate',
                nbins=20,
                title='Distribution of Sales Hit Rates',
                labels={'Hit_Rate': 'Hit Rate (%)', 'count': 'Number of Customers'},
                color_discrete_sequence=['#667eea']
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.markdown("#### Opportunity Segments")
            
            # Pie chart
            segments = pd.DataFrame({
                'Segment': ['High (>=70%)', 'Medium (50-70%)', 'Low (<50%)'],
                'Count': [high_potential, medium_potential, low_potential]
            })
            
            fig = px.pie(
                segments,
                values='Count',
                names='Segment',
                title='Customer Segmentation by Hit Rate',
                color_discrete_sequence=['#28a745', '#ffc107', '#dc3545']
            )
            st.plotly_chart(fig, width='stretch')
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Hit Rate by Region")
            
            region_avg = pred_df.groupby('Region')['Hit_Rate'].mean().reset_index()
            region_avg = region_avg.sort_values('Hit_Rate', ascending=False)
            
            fig = px.bar(
                region_avg,
                x='Region',
                y='Hit_Rate',
                title='Average Hit Rate by Region',
                labels={'Hit_Rate': 'Average Hit Rate (%)'},
                color='Hit_Rate',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.markdown("#### Hit Rate by Industry")
            
            industry_avg = pred_df.groupby('Industry')['Hit_Rate'].mean().reset_index()
            industry_avg = industry_avg.sort_values('Hit_Rate', ascending=False).head(10)
            
            fig = px.bar(
                industry_avg,
                x='Industry',
                y='Hit_Rate',
                title='Top 10 Industries by Hit Rate',
                labels={'Hit_Rate': 'Average Hit Rate (%)'},
                color='Hit_Rate',
                color_continuous_scale='Viridis'
            )
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, width='stretch')
        
        st.markdown("---")
        
        # Geographic Map
        st.markdown("#### Geographic Distribution of Equipment")
        
        try:
            # Try to load BCG installed base data with geolocation
            # Optimize: Only process Europe for now as requested
            bcg_query = """
                SELECT Company as company, equipment_type, Country as country, latitude_internal as latitude, longitude_internal as longitude, start_year_internal as start_year
                FROM bcg_installed_base
                WHERE latitude_internal IS NOT NULL AND longitude_internal IS NOT NULL
                AND (LOWER(Region) LIKE '%europe%' OR LOWER(Region) LIKE '%oceania%' OR LOWER(Region) LIKE '%australia%' OR LOWER(Country) LIKE '%australia%')
            """
            
            geo_df = data_service.conn.execute(bcg_query).df()
            
            if not geo_df.empty and 'latitude' in geo_df.columns and 'longitude' in geo_df.columns:
                # Calculate hit rates for equipment on the map
                equipment_with_scores = []
                
                # Limit to 500 for better performance with map markers
                for idx, row in geo_df.head(500).iterrows():
                    equipment_data = row.to_dict()
                    score, _ = prediction_service.predict_equipment_hit_rate(equipment_data, {})
                    
                    equipment_with_scores.append({
                        'company': row.get('company', 'Unknown'),
                        'equipment_type': row.get('equipment_type', 'Unknown'),
                        'country': row.get('country', 'Unknown'),
                        'latitude': float(row['latitude']),
                        'longitude': float(row['longitude']),
                        'hit_rate': float(score),
                        'age': 2026 - int(row.get('start_year', 2020)) if pd.notna(row.get('start_year')) else 0
                    })
                
                map_df = pd.DataFrame(equipment_with_scores)
                
                # Create map with color-coded markers
                fig = px.scatter_mapbox(
                    map_df,
                    lat='latitude',
                    lon='longitude',
                    color='hit_rate',
                    size='age',
                    hover_name='company',
                    hover_data={
                        'equipment_type': True,
                        'country': True,
                        'hit_rate': ':.1f',
                        'age': True,
                        'latitude': False,
                        'longitude': False
                    },
                    color_continuous_scale='RdYlGn',
                    size_max=15,
                    zoom=3,
                    title='Europe & Australia Equipment Distribution (Size = Age, Color = Hit Rate %)'
                )
                
                fig.update_layout(
                    mapbox_style="open-street-map",
                    height=600,
                    margin={"r":0,"t":40,"l":0,"b":0}
                )
                
                st.plotly_chart(fig, width="stretch")
                
                # Map statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Locations", len(map_df))
                
                with col2:
                    unique_countries = map_df['country'].nunique()
                    st.metric("Countries", unique_countries)
                
                with col3:
                    high_priority_locations = len(map_df[map_df['hit_rate'] >= 70])
                    st.metric("High Priority Sites", high_priority_locations)
                
                with col4:
                    avg_equipment_age = map_df['age'].mean()
                    st.metric("Avg Equipment Age", f"{avg_equipment_age:.1f} years")
                
            else:
                st.info("Geographic data not available for Europe.")
        
        except Exception as e:
            st.info(f"Geographic map not available: {str(e)}")
        
        st.markdown("---")
        
        # Top opportunities table
        st.markdown("#### Top 20 Opportunities (Europe & Australia)")
        
        top_customers = pred_df.nlargest(20, 'Hit_Rate')[['Customer', 'Hit_Rate', 'Industry', 'Region', 'Rating']].copy()
        top_customers['Rank'] = range(1, len(top_customers) + 1)
        top_customers = top_customers[['Rank', 'Customer', 'Hit_Rate', 'Industry', 'Region', 'Rating']]
        
        # Fix Pyarrow serialization errors by ensuring consistent types
        top_customers_display = top_customers.copy()
        for col in top_customers_display.columns:
            if col != 'Hit_Rate':
                # Use astype(object) first to avoid TypeError with Int32/masked types
                top_customers_display[col] = top_customers_display[col].astype(object).fillna("N/A").astype(str)
            else:
                top_customers_display[col] = pd.to_numeric(top_customers_display[col], errors='coerce')

        st.dataframe(
            top_customers_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Hit_Rate": st.column_config.NumberColumn(format="%.1f%%")
            }
        )
        
    except Exception as e:
        st.error(f"Error generating analytics: {e}")
        st.exception(e)
