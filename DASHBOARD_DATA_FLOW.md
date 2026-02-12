# Dashboard Data Flow Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                      (Streamlit Dashboard)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DASHBOARD CONTROLS                            │
│  ┌──────────────┬──────────────┬──────────────────────────┐    │
│  │   Country    │    Region    │    Equipment Type        │    │
│  │  Dropdown    │   Dropdown   │      Dropdown            │    │
│  └──────────────┴──────────────┴──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SERVICE LAYER                            │
│                  (app/services/data_service.py)                  │
│                                                                   │
│  Methods:                                                        │
│  • get_all_countries()                                          │
│  • get_detailed_plant_data(equipment, country, region)         │
│  • get_match_quality_stats()                                    │
│                                                                   │
│  Constants:                                                      │
│  • FIXED_EQUIPMENT_LIST (38 items)                              │
│  • REGION_OPTIONS (6 items)                                     │
│  • REGION_MAPPING (region to country mapping)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│                         (DuckDB)                                 │
│                                                                   │
│  Tables:                                                         │
│  • bcg_installed_base (all equipment records)                   │
│  • crm_data (customer relationship data)                        │
│  • company_mappings (BCG ↔ CRM name links)                      │
│  • unified_companies (aggregated view)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SOURCE DATA FILES                           │
│                                                                   │
│  • bcg_data.xlsx (41 sheets, ~10,000+ records)                  │
│  • crm_export.xlsx (customer data)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Data Flow

### 1. Data Loading Flow

```
┌──────────────┐
│ bcg_data.xlsx│
│ (41 sheets)  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ load_bcg_installed_base()                │
│                                          │
│ For each sheet:                          │
│  1. Read Excel sheet                     │
│  2. Add equipment_type column            │
│  3. Create internal mapping columns:     │
│     • company_internal                   │
│     • country_internal                   │
│     • latitude_internal                  │
│     • longitude_internal                 │
│     • start_year_internal                │
│     • capacity_internal                  │
│  4. Keep ALL original columns            │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ DuckDB: bcg_installed_base table         │
│                                          │
│ Columns:                                 │
│  • equipment_type                        │
│  • company_internal                      │
│  • country_internal                      │
│  • latitude_internal, longitude_internal │
│  • start_year_internal                   │
│  • capacity_internal                     │
│  • [All original columns from Excel]     │
└──────────────────────────────────────────┘
```

### 2. Company Matching Flow

```
┌──────────────┐     ┌──────────────┐
│ bcg_data.xlsx│     │crm_export.xlsx│
└──────┬───────┘     └──────┬────────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│ BCG companies│     │ CRM companies│
│ (from Col G) │     │ (name field) │
└──────┬───────┘     └──────┬────────┘
       │                    │
       └────────┬───────────┘
                ▼
┌────────────────────────────────────┐
│ Mapping Service                    │
│ (app/services/mapping_service.py)  │
│                                    │
│ 1. Fuzzy matching (thefuzz)        │
│    • Score ≥ 95: Auto-match        │
│    • Score 70-94: LLM verify       │
│    • Score < 70: No match          │
│                                    │
│ 2. LLM verification (optional)     │
│    • Azure OpenAI                  │
│    • Company name resolution       │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ DuckDB: company_mappings table     │
│                                    │
│ Columns:                           │
│  • crm_name                        │
│  • bcg_name                        │
│                                    │
│ Used for:                          │
│  • Joining BCG ↔ CRM data          │
│  • Match quality statistics        │
└────────────────────────────────────┘
```

### 3. Dashboard Query Flow

```
User selects filters:
  • Country: "Germany"
  • Region: "Europe"
  • Equipment: "Continuous Annealing Line"
         │
         ▼
┌────────────────────────────────────────────────┐
│ get_detailed_plant_data()                      │
│                                                │
│ SQL Query:                                     │
│   SELECT b.*, c.company_ceo, c.fte_count, ...  │
│   FROM bcg_installed_base b                    │
│   LEFT JOIN company_mappings m                 │
│     ON b.company_internal = m.bcg_name         │
│   LEFT JOIN crm_data c                         │
│     ON COALESCE(m.crm_name, b.company_internal)│
│        = c.name                                │
│   WHERE equipment_type = 'Cont. Annealing...' │
│     AND country_internal = 'Germany'           │
│                                                │
│ Python filter:                                 │
│   • Region filter (mapping logic)              │
└────────┬───────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ Result DataFrame                               │
│                                                │
│ Contains:                                      │
│  • All BCG columns (original + internal)       │
│  • CRM columns (CEO, FTE)                      │
│  • Mapping info (crm_name)                     │
└────────┬───────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ Dashboard Processing                           │
│                                                │
│ 1. Map Data:                                   │
│    • Filter for valid lat/lon                  │
│    • Extract Nominal Capacity                  │
│    • Create heatmap visualization              │
│                                                │
│ 2. Match Stats:                                │
│    • Query company_mappings                    │
│    • Calculate fuzzy scores                    │
│    • Categorize: excellent/good/okay/poor      │
│                                                │
│ 3. Table Data:                                 │
│    • Add default columns                       │
│    • Calculate Hit Rate %                      │
│    • Add equipment-specific columns            │
│    • Format missing data as "—"                │
└────────┬───────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ Rendered Dashboard                             │
│                                                │
│  • Interactive map with heatmap                │
│  • Match quality metrics                       │
│  • Sortable/filterable table                   │
│  • CSV export button                           │
└────────────────────────────────────────────────┘
```

## Column Flow for Equipment-Specific Fields

### Example: Continuous Annealing Line

```
bcg_data.xlsx
  Sheet: "Continuous Annealing Line"
    │
    ├─ Default columns:
    │   • DB-Plant-No.
    │   • Type of Plant
    │   • Country
    │   • Company
    │   • City
    │   • State
    │   • Region
    │   • ...
    │
    └─ Equipment-specific columns:
        • Process/type Of Plant
        • Strip Width Min.
        • Strip Width Max.
        • Strip Thickness Min.
        • Strip Thickness Max.
        • Entry: Number Of Pay-off Reels
        • Entry: Coil Weight Max.
        • Annealing: Strip Cleaning
        • Annealing: Heat Cycle
        • ... (20+ more)
         │
         ▼
┌────────────────────────────────────────┐
│ load_bcg_installed_base()              │
│                                        │
│ • Reads ALL columns from sheet         │
│ • Adds equipment_type = sheet name     │
│ • Creates internal mapping columns     │
│ • Preserves all original columns       │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ DuckDB: bcg_installed_base             │
│                                        │
│ Row for each CAL plant contains:       │
│  • equipment_type = "Cont. Ann. Line"  │
│  • All default columns                 │
│  • All CAL-specific columns            │
│  • Internal mapping columns            │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Dashboard: Equipment filter selected   │
│                                        │
│ IF equipment == "Continuous Ann. Line":│
│   1. Get all columns from result       │
│   2. Exclude default columns           │
│   3. Exclude internal columns          │
│   4. Filter for non-null columns       │
│   5. Result: CAL-specific columns      │
│                                        │
│ Display order:                         │
│   [Default cols] + [Hit Rate] + [CAL]  │
└────────────────────────────────────────┘
```

## Match Quality Statistics Flow

```
┌────────────────────────────────────────┐
│ get_match_quality_stats()              │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Query: SELECT crm_name, bcg_name       │
│        FROM company_mappings           │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ For each mapping:                      │
│   score = fuzz.token_sort_ratio(       │
│     crm_name, bcg_name                 │
│   )                                    │
│                                        │
│   IF score == 100:                     │
│     excellent_count++                  │
│   ELIF score >= 80:                    │
│     good_count++                       │
│   ELIF score >= 50:                    │
│     okay_count++                       │
│   ELSE:                                │
│     poor_count++                       │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Return percentages:                    │
│   {                                    │
│     "excellent": 45.2%,                │
│     "good": 32.1%,                     │
│     "okay": 18.5%,                     │
│     "poor": 4.2%                       │
│   }                                    │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Dashboard displays 4 metric cards      │
└────────────────────────────────────────┘
```

## Hit Rate Calculation Flow

```
For each plant in filtered results:
         │
         ▼
┌────────────────────────────────────────┐
│ Check if CRM match exists              │
│   (crm_name field is not null)         │
└────────┬───────────────────────────────┘
         │
         ├─ YES ──────────────────────────┐
         │                                │
         │                                ▼
         │                    ┌───────────────────────┐
         │                    │ Get start_year_internal│
         │                    └───────┬───────────────┘
         │                            │
         │                            ▼
         │                    ┌───────────────────────┐
         │                    │ Calculate age:        │
         │                    │   age = 2026 - year   │
         │                    └───────┬───────────────┘
         │                            │
         │                            ▼
         │                    ┌───────────────────────┐
         │                    │ IF age > 20: 85%      │
         │                    │ ELIF age > 15: 70%    │
         │                    │ ELIF age > 10: 55%    │
         │                    │ ELSE: 40%             │
         │                    │                       │
         │                    │ IF no age: 60%        │
         │                    └───────┬───────────────┘
         │                            │
         └────────────────────────────┤
                                      │
         ┌────────────────────────────┘
         │
         └─ NO ──────────────────────────┐
                                         │
                                         ▼
                                 ┌───────────────┐
                                 │ Hit Rate = NA │
                                 └───────────────┘
```

## Region Filtering Logic

```
User selects Region: "Europe"
         │
         ▼
┌────────────────────────────────────────┐
│ REGION_MAPPING lookup:                 │
│   "Europe" → [                         │
│     "Europe",                          │
│     "EU",                              │
│     "Western Europe",                  │
│     "Eastern Europe",                  │
│     "Central Europe",                  │
│     "Nordics"                          │
│   ]                                    │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Filter DataFrame:                      │
│   df = df[                             │
│     df['Region'].apply(                │
│       lambda x: any(                   │
│         r.lower() in str(x).lower()    │
│         for r in allowed_regions       │
│       ) or str(x) == region            │
│     )                                  │
│   ]                                    │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Result: Plants with Region field       │
│ matching any of the allowed variations │
└────────────────────────────────────────┘
```

## Performance Considerations

### Optimizations Implemented

1. **Database Indexing**
   - DuckDB automatically optimizes queries
   - Filters applied at SQL level when possible

2. **Lazy Loading**
   - Data only loaded when "Load Data" clicked
   - Queries only run when filters change

3. **Efficient Filtering**
   - Country/Equipment: SQL WHERE clause
   - Region: Python filter (complex mapping logic)

4. **Hit Rate Calculation**
   - Simple heuristic (fast)
   - No ML inference per row
   - Vectorized operations where possible

5. **Map Rendering**
   - Log scale for marker sizes (better distribution)
   - Filters invalid coordinates before plotting
   - Uses Plotly's optimized rendering

### Scalability Limits

| Component | Current Limit | Recommendation |
|-----------|--------------|----------------|
| Plants in map | ~10,000 | Use clustering for >5,000 |
| Table rows | ~50,000 | Pagination for >10,000 |
| Hit rate calc | ~100,000 | Pre-calculate for >50,000 |
| Match quality | ~10,000 | Cache results for >5,000 |

## Error Handling Flow

```
User action
    │
    ▼
┌───────────────────────────────────┐
│ Try: Execute query/operation      │
└───────┬───────────────────────────┘
        │
        ├─ SUCCESS ──────────────────┐
        │                            │
        │                            ▼
        │                    ┌───────────────┐
        │                    │ Render results│
        │                    └───────────────┘
        │
        └─ ERROR ───────────────────┐
                                    │
                                    ▼
                            ┌───────────────────┐
                            │ Catch exception   │
                            └───────┬───────────┘
                                    │
                                    ▼
                            ┌───────────────────┐
                            │ st.error(message) │
                            │ st.exception(e)   │
                            └───────────────────┘
```

## Summary

This architecture provides:
- ✅ **Separation of concerns**: UI, business logic, data access
- ✅ **Flexibility**: Easy to add new equipment types or columns
- ✅ **Performance**: SQL-level filtering, efficient queries
- ✅ **Maintainability**: Clear data flow, documented processes
- ✅ **Extensibility**: Can add ML models, caching, etc.
