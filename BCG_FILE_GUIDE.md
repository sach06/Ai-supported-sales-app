# BCG Installed Base File - Usage Guide

## 📊 File Structure

Your BCG installed base file has a **multi-sheet structure** where:
- **Each sheet** = Different equipment type (e.g., "Continuous Annealing Line", "Blast Furnace", "Pickling Plant")
- **Column G** = Company names (your clients)
- **Geolocation data** = Latitude/Longitude for mapping

---

## 🔄 How the App Processes This File

### 1. Multi-Sheet Loading
The app automatically:
- Reads **ALL sheets** from the Excel file
- Extracts equipment type from the sheet name
- Combines all sheets into a unified database

### 2. Column Mapping
The app recognizes these column variations:

| Your Column | Mapped To | Purpose |
|-------------|-----------|---------|
| Company / Customer | `company` | Client name |
| Plant | `plant_name` | Plant identifier |
| Location | `location` | Site location |
| Country | `country` | Geographic region |
| Latitude | `latitude` | For mapping |
| Longitude | `longitude` | For mapping |
| Year of Start Up / Start Up | `start_year` | Installation year |
| Last Update | `last_update` | Last service date |
| Capacity | `capacity` | Production capacity |
| OEM / Supplier | `oem` | Equipment manufacturer |

### 3. Equipment-Level Analysis
For each equipment record, the app calculates:
- **Hit Rate %** - Probability of modernization/service opportunity
- **Age** - Years since installation
- **Priority** - Based on age, type, OEM, maintenance

---

## 🗺️ Geographic Visualization

### Requirements
Your BCG file must have:
- `Latitude` column (numeric)
- `Longitude` column (numeric)

### What You'll See
1. **Interactive World Map** with:
   - Color-coded markers (green = high hit rate, red = low)
   - Size = equipment age (bigger = older)
   - Hover info: Company, equipment type, country, hit rate, age, OEM

2. **Map Statistics**:
   - Total locations
   - Number of countries
   - High-priority sites (≥70% hit rate)
   - Average equipment age

---

## 📋 Expected Data Format

### Example Row from BCG File:
```
Sheet: Continuous Annealing Line
Row 5:
- Column A: Plant ID
- Column B: Plant Name
- Column G: ThyssenKrupp Steel  ← Company
- Column H: Germany  ← Country
- Column I: 51.4556  ← Latitude
- Column J: 7.0116   ← Longitude
- Column K: 1998     ← Year of Start Up
- Column L: SMS group ← OEM
```

---

## 🎯 How to Use

### Step 1: Prepare Your File
1. Ensure your BCG file has multiple sheets for different equipment types
2. Verify Column G contains company names
3. Check that latitude/longitude columns exist (for mapping)

### Step 2: Load into App
1. Place file in `data/` folder (name it with "bcg" in the filename, e.g., `bcg_installed_base.xlsx`)
2. Click **"Load Data"** in sidebar
3. Watch the console output:
   ```
   📊 Loading BCG Installed Base from 12 sheets...
     ✓ Continuous Annealing Line: 45 records
     ✓ Blast Furnace: 32 records
     ✓ Pickling Plant: 28 records
     ...
   ✓ BCG Installed Base loaded: 387 total equipment records
   ```

### Step 3: View Results

#### Dashboard
- See customer-level aggregated hit rates
- Filter by region, industry, minimum hit rate

#### Customer Details → Installed Base Tab
- View ALL equipment for selected customer
- See equipment-level hit rates (sorted by priority)
- Select individual equipment for detailed analysis

#### Analytics → Geographic Map
- See global distribution of equipment
- Identify high-priority regions
- Filter by equipment type, age, OEM

---

## 🔍 Equipment-Level Predictions

### Scoring Factors
Each piece of equipment is scored based on:

1. **Age** (Primary Factor):
   - 20+ years: +35% (Very high priority)
   - 15-20 years: +25% (High priority)
   - 10-15 years: +15% (Medium priority)
   - <5 years: -10% (Low priority)

2. **Equipment Type**:
   - Critical types (Furnace, Blast, Arc, Casting, Rolling): +10%

3. **OEM**:
   - SMS equipment: +10% (existing relationship)

4. **Maintenance**:
   - No service 24+ months: +10%
   - No service 12-24 months: +5%

5. **Customer Rating**:
   - A/B tier: +10%
   - D/E tier: -10%

### Example Output
```
Equipment: Blast Furnace #3
Location: Duisburg, Germany
Age: 28 years
OEM: SMS group
Hit Rate: 90%

Drivers:
✅ Very old equipment (28 years) - high modernization priority
✅ Critical equipment type - high business impact
✅ SMS equipment - existing relationship advantage
✅ No recent maintenance (36 months) - potential reliability issues
```

---

## 📊 Analytics Features

### 1. Equipment Distribution Map
- **What**: Interactive world map showing all equipment locations
- **Color**: Hit rate (green = high opportunity, red = low)
- **Size**: Equipment age (bigger circles = older equipment)
- **Hover**: Company, equipment type, country, hit rate, age, OEM

### 2. Regional Analysis
- Hit rates by country/region
- Equipment concentration by area
- High-priority locations

### 3. Equipment Type Analysis
- Which equipment types have highest hit rates
- Age distribution by equipment type
- OEM market share by equipment type

---

## 🚀 ML Approach (Future Enhancement)

Based on your requirements, here's the planned ML implementation:

### 1. Data Preprocessing
- ✅ Handle missing values (currently using defaults)
- ✅ Feature engineering (age calculation, categorical encoding)
- ⏳ Normalization/standardization (to be added)

### 2. Model Selection
- **Current**: Heuristic rule-based model
- **Planned**: XGBoost classifier
- **Target**: Predict modernization/OEM sales/maintenance probability

### 3. Features for ML Model
- Equipment age
- Equipment type (one-hot encoded)
- OEM (SMS vs. competitor)
- Country/region
- Capacity
- Last maintenance date
- Customer rating
- Historical project count

### 4. Training Data
Will need historical data with labels:
- `modernization_occurred` (0/1)
- `service_contract_signed` (0/1)
- `oem_sale_made` (0/1)

---

## 💡 Tips for Best Results

1. **Complete Data**: Ensure latitude/longitude are filled for mapping
2. **Consistent Naming**: Use consistent company names across sheets
3. **Update Dates**: Include "Last Update" or maintenance dates
4. **OEM Field**: Specify equipment manufacturer (especially SMS vs. others)
5. **Multiple Files**: You can have separate CRM file + BCG file

---

## 🔧 Troubleshooting

### Map Not Showing?
- Check if `Latitude` and `Longitude` columns exist
- Verify values are numeric (not text)
- Ensure at least some rows have non-null coordinates

### Equipment Not Loading?
- Check sheet names (avoid special characters)
- Verify Column G has company names
- Check console for error messages

### Hit Rates Seem Off?
- The current model is heuristic (rule-based)
- Scores will improve with ML model training
- Adjust weights in `prediction_service.py` if needed

---

## 📁 File Naming Convention

For automatic detection:
- BCG file: `bcg_*.xlsx` or `*_bcg.xlsx`
- CRM file: `crm_*.xlsx` or `*_crm.xlsx`
- Other installed base: `installed_base.xlsx` or `*_base.xlsx`

---

**Ready to load your BCG file!** 🎉

Place it in the `data/` folder and click "Load Data" to see:
- Multi-sheet equipment analysis
- Geographic distribution map
- Equipment-level hit rate predictions
