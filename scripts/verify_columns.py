"""Verify column aliases resolve correctly against bcg_installed_base."""
import sys, pathlib, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(".").resolve()))

import pandas as pd

# Read from CSV export instead (not locked by Streamlit)
REPO = pathlib.Path("temp_repos/work_apps/templates")
ib = pd.read_excel(REPO / "ib_list.xlsx")
# Simulate what sync_axel_data.py produces
ib["company_internal"]   = ib["ib_customer"].astype(str)
ib["country_internal"]   = ib["ib_customer_country"].astype(str)
ib["equipment_type"]     = ib["pbs_plant_type"].fillna("Unknown").astype(str)
ib["start_year_internal"]= pd.to_datetime(ib["ib_startup"], errors="coerce").dt.year
ib["OEM"]                = "SMS"

_YEAR_COLS    = ["start_year_internal","start_year","year","installation_year","commission_year","Startup Year"]
_OEM_COLS     = ["OEM","supplier","oem","manufacturer"]
_EQ_TYPE_COLS = ["equipment_type","Equipment Type","equipment","type"]
_COMPANY_COLS = ["company_internal","company_name","Company Name","name","customer_name","ib_customer"]
_COUNTRY_COLS = ["country_internal","country","Country","ib_customer_country","region","location"]

def first(df, lst):
    for c in lst:
        if c in df.columns: return c
    return None

print("year_col     ->", first(ib, _YEAR_COLS))
print("oem_col      ->", first(ib, _OEM_COLS))
print("eq_type_col  ->", first(ib, _EQ_TYPE_COLS))
print("company_col  ->", first(ib, _COMPANY_COLS))
print("country_col  ->", first(ib, _COUNTRY_COLS))
print()
print("Sample company_internal:", ib["company_internal"].head(3).tolist())
print("Sample country_internal:", ib["country_internal"].head(3).tolist())
print("Sample equipment_type:  ", ib["equipment_type"].head(3).tolist())
print("Sample start_year_int:  ", ib["start_year_internal"].head(3).tolist())
print("Sample OEM:             ", ib["OEM"].head(3).tolist())
print()
print("Unique equipment types:", ib["equipment_type"].nunique())
print("Unique countries:      ", ib["country_internal"].nunique())
print("Unique companies:      ", ib["company_internal"].nunique())
