"""
Main Streamlit Application Entry Point
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir.parent))

from app.services import data_service

# Page configuration
st.set_page_config(
    page_title="Sales App",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f4788;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: 600;
    }
    .stButton>button:hover {
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'selected_customer' not in st.session_state:
    st.session_state.selected_customer = None
if 'filters' not in st.session_state:
    st.session_state.filters = {
        'country': 'All',
        'region': 'All',
        'equipment_type': 'All',
        'company_name': 'All'
    }

# Sidebar
with st.sidebar:
    # Logo in sidebar
    try:
        st.image("assets/logo.png", use_container_width=True)
    except:
        pass
            
    st.markdown("### Navigation")
    page = st.radio(
        "Select Page",
        ["Overview", "Customer Details", "Analytics"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # GLOBAL FILERS
    st.markdown("### Global Filters")
    if st.session_state.data_loaded:
        # Load filter options
        countries = ["All"] + data_service.get_all_countries()
        
        reg_opts = ["All"] + data_service.REGION_OPTIONS
        st.session_state.filters['region'] = st.selectbox(
            "Region", 
            reg_opts,
            index=reg_opts.index(st.session_state.filters['region']) if st.session_state.filters['region'] in reg_opts else 0
        )
        
        st.session_state.filters['country'] = st.selectbox(
            "Country", 
            countries,
            index=countries.index(st.session_state.filters['country']) if st.session_state.filters['country'] in countries else 0
        )
        
        eq_opts = ["All"] + data_service.FIXED_EQUIPMENT_LIST
        st.session_state.filters['equipment_type'] = st.selectbox(
            "Equipment Type", 
            eq_opts,
            index=eq_opts.index(st.session_state.filters['equipment_type']) if st.session_state.filters['equipment_type'] in eq_opts else 0
        )

        # 4. Company Name Filter (Dependent on above)
        filtered_customers = data_service.get_customer_list(
            equipment_type=st.session_state.filters['equipment_type'],
            country=st.session_state.filters['country'],
            region=st.session_state.filters['region']
        )
        
        # Robust column check
        if not filtered_customers.empty and 'name' in filtered_customers.columns:
            comp_opts = ["All"] + sorted([str(n) for n in filtered_customers['name'].unique() if pd.notna(n)])
        else:
            comp_opts = ["All"]
            
        st.session_state.filters['company_name'] = st.selectbox(
            "Company Name",
            comp_opts,
            index=comp_opts.index(st.session_state.filters['company_name']) if st.session_state.filters['company_name'] in comp_opts else 0,
            help="Deep dive into a specific customer"
        )
        
        # Sync selected_customer for Customer Details page
        if st.session_state.filters['company_name'] != "All":
            st.session_state.selected_customer = st.session_state.filters['company_name']
    else:
        st.info("Load data to enable filters")

    st.markdown("---")
    st.markdown("### Settings")
    
    # Data loading section
    st.markdown("#### Data Management")
    
    available_files = data_service.list_available_files()
    
    if available_files:
        st.success(f"{len(available_files)} file(s) found in data folder")
        
        if st.button("Load Data", width="stretch"):
            data_service.clear_logs()
            with st.spinner("Loading data..."):
                try:
                    data_service.initialize_database()
                    
                    # Try to load each type of file
                    for file in available_files:
                        if 'crm' in file.lower():
                            data_service.load_crm_data(file)
                        elif 'bcg' in file.lower():
                            # Use the multi-sheet loader for BCG installed base
                            data_service.load_bcg_installed_base(file)
                        elif 'install' in file.lower() or 'base' in file.lower():
                            data_service.load_installed_base(file)
                    
                    # Create the unified "Smart Joint" view
                    data_service.create_unified_view()
                    
                    st.session_state.data_loaded = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading data: {e}")
    else:
        st.warning("No Excel/CSV files found in data folder")
        st.info("Please add your data files to the `data/` directory")
    
    if st.session_state.data_loaded:
        st.success("Data is loaded")
        
    # Log Console in Sidebar
    if data_service.get_logs():
        st.markdown("---")
        with st.expander("System Logs", expanded=True):
            for log in data_service.get_logs():
                st.caption(log)

# Main content
st.markdown('<div class="main-header" style="text-align: center;">AI Supported Sales Application</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header" style="text-align: center;">Intelligent Customer Insights and Sales Predictions</div>', unsafe_allow_html=True)

try:
    if page == "Overview":
        from app.ui import dashboard
        dashboard.render()
    elif page == "Customer Details":
        from app.ui import customer_detail
        customer_detail.render()
    elif page == "Analytics":
        from app.ui import analytics
        analytics.render()
    else:
        st.error(f"Unknown page: {page}")
except Exception as e:
    st.error(f"Critical error loading page '{page}': {e}")
    import traceback
    st.expander("Full Traceback").text(traceback.format_exc())
