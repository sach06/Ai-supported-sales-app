# Dashboard UI Layout - Visual Guide

## Page Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Customer Intelligence Dashboard                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  #### Filters                                                        │
│  ┌──────────────┬──────────────┬──────────────────────────────┐    │
│  │   Country    │    Region    │      Equipment Type          │    │
│  │  [Dropdown]  │  [Dropdown]  │        [Dropdown]            │    │
│  │              │              │                              │    │
│  │  • All       │  • All       │  • All                       │    │
│  │  • Germany   │  • Americas  │  • AC-Electric Arc Furnace   │    │
│  │  • USA       │  • APAC&MEA  │  • Batch Annealing Plant     │    │
│  │  • China     │  • China     │  • Continuous Annealing Line │    │
│  │  • ...       │  • Europe    │  • ... (38 total)            │    │
│  │              │  • ...       │                              │    │
│  └──────────────┴──────────────┴──────────────────────────────┘    │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  #### Geographic Distribution                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                               │   │
│  │         [Interactive World Map - 650px height]               │   │
│  │                                                               │   │
│  │  • Country borders: Light gray                               │   │
│  │  • Markers: Sized by capacity (log scale)                    │   │
│  │  • Colors: Yellow → Orange → Red (capacity heatmap)          │   │
│  │  • Hover: Company, Equipment, Country, City, Capacity        │   │
│  │  • Legend: "Nominal Capacity" (right side)                   │   │
│  │  • Responsive: Fits container width                          │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  #### Company Matching Quality                                       │
│  ┌──────────┬──────────┬──────────┬──────────┐                     │
│  │Excellent │   Good   │   Okay   │   Poor   │                     │
│  │  (100%)  │ (80-99%) │ (50-79%) │  (<50%)  │                     │
│  │          │          │          │          │                     │
│  │  45.2%   │  32.1%   │  18.5%   │   4.2%   │                     │
│  │          │          │          │          │                     │
│  └──────────┴──────────┴──────────┴──────────┘                     │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  #### Complete Plant Inventory                                       │
│                                                                       │
│  ℹ️ Displaying 42 columns: 17 default + 1 hit rate + 24 equipment   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Type of │Country│Parent  │Company│City │...│Hit Rate│Strip  │   │
│  │  Plant  │       │Company │       │     │   │   %    │Width  │   │
│  ├─────────┼───────┼────────┼───────┼─────┼───┼────────┼───────┤   │
│  │Cont.    │Germany│Thyssen │TKSE   │Duis.│...│  85.0% │1,200  │   │
│  │Annealing│       │Krupp   │       │     │   │        │       │   │
│  ├─────────┼───────┼────────┼───────┼─────┼───┼────────┼───────┤   │
│  │Cont.    │USA    │USS     │US     │Gary │...│  70.0% │1,500  │   │
│  │Annealing│       │        │Steel  │     │   │        │       │   │
│  ├─────────┼───────┼────────┼───────┼─────┼───┼────────┼───────┤   │
│  │  ...    │  ...  │  ...   │  ...  │ ... │...│  ...   │  ...  │   │
│  │         │       │        │       │     │   │        │       │   │
│  └─────────┴───────┴────────┴───────┴─────┴───┴────────┴───────┘   │
│                                                                       │
│  [Height: 600px, Sortable columns, Filterable]                      │
│                                                                       │
│  ┌─────────────────────────────────────┐                            │
│  │ 📥 Export current view to CSV       │                            │
│  └─────────────────────────────────────┘                            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Filter Behavior

### Country Dropdown
- **Source**: All unique countries from `bcg_data.xlsx`
- **Example values**: 
  - All
  - Germany
  - United States
  - China
  - India
  - Brazil
  - (... all countries in dataset)

### Region Dropdown
- **Fixed options** (exactly 6):
  1. All
  2. Americas
  3. APAC & MEA
  4. China
  5. Commonwealth
  6. Europe
  7. Not assigned

### Equipment Dropdown
- **Fixed options** (exactly 38 equipment types):
  1. All
  2. AC-Electric Arc Furnace
  3. Batch Annealing Plant
  4. Billet-/heavy Bar Mill
  5. Blast Furnace
  6. ... (34 more)

## Map Visualization

### Visual Characteristics
```
┌────────────────────────────────────────────────────┐
│ Plant Capacity Heatmap                             │
├────────────────────────────────────────────────────┤
│                                                     │
│    [World map with country borders]                │
│                                                     │
│    Markers:                                        │
│    🔴 Large red circle = High capacity            │
│    🟠 Medium orange circle = Medium capacity      │
│    🟡 Small yellow circle = Low capacity          │
│                                                     │
│    Hover tooltip:                                  │
│    ┌─────────────────────────┐                    │
│    │ ThyssenKrupp Steel      │                    │
│    │ Equipment: Cont. Ann... │                    │
│    │ Country: Germany        │                    │
│    │ City: Duisburg          │                    │
│    │ Nominal Capacity: 1,200 │                    │
│    └─────────────────────────┘                    │
│                                                     │
└────────────────────────────────────────────────────┘
                                            │
                                            │ Nominal
                                            │ Capacity
                                            │
                                            ▼
                                         ┌────┐
                                         │████│ 2000
                                         │████│
                                         │████│ 1500
                                         │▓▓▓▓│
                                         │▒▒▒▒│ 1000
                                         │▒▒▒▒│
                                         │░░░░│ 500
                                         │░░░░│
                                         └────┘ 0
```

## Table Columns

### Default Columns (Always Visible)
1. **Type of Plant** - Equipment type
2. **Country** - Plant location country
3. **Parent Company** - Corporate parent
4. **Company** - Operating company
5. **City** - Plant city
6. **State** - State/province
7. **Region** - Geographic region
8. **Value Chain Step** - Position in value chain
9. **Plant No.** - Plant identifier
10. **Last Update** - Last modification date
11. **Status of the Plant** - Operational status
12. **Year Of Start Up** - Initial commissioning year
13. **Year Of Modernizing** - Last modernization year
14. **Nominal Capacity** - Production capacity
15. **CEO** - Company CEO (from CRM)
16. **Number of Full time employees** - FTE count (from CRM)
17. **Hit Rate %** - Sales opportunity probability

### Equipment-Specific Columns (Example: Continuous Annealing Line)
When "Continuous Annealing Line" is selected, these additional columns appear:

18. Process/type Of Plant
19. Strip Width Min.
20. Strip Width Max.
21. Strip Thickness Min.
22. Strip Thickness Max.
23. Entry: Number Of Pay-off Reels
24. Entry: Coil Weight Max.
25. Entry: Pay-off Speed Max.
26. Entry: Type Of Strip Accumulator
27. Entry: Capacity Of Accumulator
28. Annealing: Strip Cleaning
29. Annealing: Heat Cycle
30. Annealing: Type Of Furnace Heating
31. Annealing: Cooling Cycle
32. Annealing: Proc. Speed Min.
33. Annealing: Proc. Speed Max.
34. Exit: Number Of Tension Reels
35. Exit: Coil Weight Max.
36. Exit: Coiling Speed Max.
37. Exit: Type Of Strip Accumulator
38. Exit: Capacity Of Accumulator Max.
39. Processed Strip Grades A)
40. Processed Strip Grades B)
41. Additional Inline Equipment
42. Additional Information

**Note**: Different equipment types will have different specific columns based on what's available in the dataset.

## Match Quality Metrics

### Visual Display
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Excellent   │     Good     │     Okay     │     Poor     │
│   (100%)     │   (80-99%)   │   (50-79%)   │    (<50%)    │
├──────────────┼──────────────┼──────────────┼──────────────┤
│              │              │              │              │
│    45.2%     │    32.1%     │    18.5%     │     4.2%     │
│              │              │              │              │
│ Perfect      │ High conf.   │ Moderate     │ Low conf.    │
│ matches      │ matches      │ confidence   │ or no match  │
│              │              │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### Interpretation
- **Excellent (100%)**: Company names match exactly (e.g., "SMS group" = "SMS group")
- **Good (80-99%)**: Very similar names (e.g., "ThyssenKrupp AG" = "ThyssenKrupp")
- **Okay (50-79%)**: Recognizable match (e.g., "TK Steel" = "ThyssenKrupp Steel")
- **Poor (<50%)**: Weak or no match found

## Data Indicators

### Missing Data Display
- **Symbol**: "—" (em dash)
- **Example**:
  ```
  CEO: John Smith
  FTE: 5,000
  Strip Width Min.: —
  Strip Width Max.: —
  ```

### Hit Rate Calculation
Based on equipment age:
- **Age > 20 years**: 85.0%
- **Age 15-20 years**: 70.0%
- **Age 10-15 years**: 55.0%
- **Age < 10 years**: 40.0%
- **No age data**: 60.0%
- **No CRM match**: — (not displayed)

## Responsive Behavior

### Desktop (>1200px)
- Map: Full width, 650px height
- Table: Full width, 600px height
- Filters: 3 columns side-by-side
- Metrics: 4 columns side-by-side

### Tablet (768px - 1200px)
- Map: Full width, 650px height
- Table: Full width, scrollable horizontally
- Filters: 3 columns (may wrap)
- Metrics: 2x2 grid

### Mobile (<768px)
- Map: Full width, 650px height
- Table: Full width, scrollable horizontally
- Filters: Stacked vertically
- Metrics: Stacked vertically

## Color Scheme

### Map
- **Land**: `rgb(243, 243, 243)` - Light gray
- **Ocean**: `rgb(230, 245, 255)` - Light blue
- **Country borders**: `LightGray`
- **Coastlines**: `Gray`
- **Heatmap**: Yellow → Orange → Red (YlOrRd scale)

### Table
- **Header**: Streamlit default (dark gray)
- **Rows**: Alternating white/light gray
- **Missing data**: "—" in default text color

### Metrics
- **Background**: Light blue (Streamlit metric default)
- **Text**: Dark gray
- **Values**: Large, bold

## Interactive Features

### Map Interactions
- **Zoom**: Scroll wheel or pinch
- **Pan**: Click and drag
- **Hover**: Shows tooltip with plant details
- **Click**: (Currently no action, could be enhanced)

### Table Interactions
- **Sort**: Click column header to sort ascending/descending
- **Scroll**: Vertical scroll for rows, horizontal for columns
- **Select**: Click row to highlight (Streamlit default)
- **Copy**: Select cells and copy to clipboard

### Filter Interactions
- **Dropdown**: Click to expand, select option
- **Cascading**: Filters apply immediately on selection
- **Reset**: Select "All" to clear filter

## Export Format

### CSV Structure
```
Type of Plant,Country,Parent Company,Company,...,Hit Rate %
Continuous Annealing Line,Germany,ThyssenKrupp,TKSE,...,85.0
Blast Furnace,USA,USS,US Steel,...,70.0
...
```

- **Encoding**: UTF-8
- **Delimiter**: Comma (,)
- **Headers**: First row
- **Missing values**: "—"
- **Filename**: `dashboard_export.csv`
