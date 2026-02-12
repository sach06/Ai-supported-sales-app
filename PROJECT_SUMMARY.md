# AI Supported Sales Application - Project Summary

## 📋 Project Overview

**Status**: ✅ Complete and Ready to Use  
**Created**: January 19, 2026  
**Framework**: Streamlit + Python  
**Purpose**: AI-powered customer insights and sales predictions

---

## 🎯 What This Application Does

### Core Features
1. **Customer Data Management**
   - Import Excel/CSV files (CRM, BCG, Installed Base)
   - Unified database with DuckDB
   - Easy data loading via UI

2. **Sales Predictions**
   - AI-powered hit rate forecasting
   - Customer prioritization
   - Key driver identification

3. **Customer Profiles (Steckbrief)**
   - AI-generated comprehensive profiles
   - 30+ data fields covering:
     - Basic company data
     - Locations and installed equipment
     - Project history
     - Market context
   - Editable fields for manual refinement

4. **Export Capabilities**
   - Download profiles as DOCX files
   - Professional formatting
   - Ready for client meetings

5. **Analytics Dashboard**
   - Visual insights by region/industry
   - Opportunity segmentation
   - Top customer rankings

---

## 📁 Project Structure

```
Code/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration & settings
│   │   └── __init__.py
│   ├── services/
│   │   ├── data_service.py    # Excel import & database
│   │   ├── profile_generator.py  # AI profile generation
│   │   ├── prediction_service.py # Sales predictions
│   │   ├── export_service.py  # DOCX export
│   │   └── __init__.py
│   ├── ui/
│   │   ├── dashboard.py       # Main dashboard page
│   │   ├── customer_detail.py # Profile view/edit page
│   │   ├── analytics.py       # Analytics page
│   │   └── __init__.py
│   ├── main.py                # Application entry point
│   └── __init__.py
├── data/                      # Excel/CSV files go here
│   └── .keep
├── notebooks/
│   └── generate_sample_data.py  # Sample data generator
├── venv/                      # Virtual environment
├── .env.example               # API key template
├── .gitignore
├── requirements.txt
├── README.md
├── run.bat                    # Windows launcher
└── run.sh                     # Unix/Mac launcher
```

---

## 🚀 Quick Start Guide

### Option 1: Use the Launcher Script (Easiest)
**Windows:**
```bash
run.bat
```

**Mac/Linux:**
```bash
chmod +x run.sh
./run.sh
```

### Option 2: Manual Steps
1. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

2. **Install dependencies (if not done):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate sample data (optional):**
   ```bash
   python notebooks/generate_sample_data.py
   ```

4. **Run the application:**
   ```bash
   streamlit run app/main.py
   ```

5. **Open browser:**
   - Navigate to `http://localhost:8501`

---

## 🔑 API Configuration

To enable AI profile generation, configure API keys:

1. **Copy the example file:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` and add your keys:**
   ```
   # For Azure OpenAI (Recommended for Enterprise)
   AZURE_OPENAI_API_KEY=your_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4o
   
   # OR for Standard OpenAI
   OPENAI_API_KEY=your_key_here
   ```

**Note:** The app works without API keys, but profile generation will use basic data extraction instead of AI.

---

## 📊 Data Requirements

### Expected Excel Files

Place in the `data/` folder:

1. **crm_export.xlsx** - Customer data
   - Required columns: `name`, `industry`, `region`, `fte`, `rating`
   - Optional: `owner`, `management`, `revenue`, etc.

2. **bcg_data.xlsx** - Market data
   - Columns: `customer_id`, `market_share`, `growth_rate`, etc.

3. **installed_base.xlsx** - Equipment data
   - Columns: `customer_name`, `location`, `equipment`, `installation_year`

**Flexible Schema:** The app adapts to your column names (e.g., `name` or `customer_name`).

---

## 🎨 User Interface

### Pages

1. **🏠 Dashboard**
   - Customer overview table
   - Prediction scores
   - Filters (industry, region, hit rate)
   - Customer selection

2. **📋 Customer Details**
   - **Profile Tab**: AI-generated Steckbrief
   - **Installed Base Tab**: Equipment details
   - **Prediction Tab**: Hit rate analysis
   - **Edit Tab**: Manual profile editing

3. **📊 Analytics**
   - Hit rate distribution
   - Regional analysis
   - Industry insights
   - Top opportunities

---

## 🤖 AI Models

### 1. Sales Prediction
- **Current**: Heuristic model (rule-based)
- **Factors**: Company size, equipment age, past projects, CRM rating
- **Output**: 0-100% hit rate + key drivers

**Future Enhancement:** Train XGBoost on historical sales data

### 2. Profile Generation
- **Model**: GPT-4o (Azure OpenAI or OpenAI)
- **Method**: Structured JSON output
- **Fields**: 30+ comprehensive data points
- **Fallback**: Basic extraction if API unavailable

---

## 📝 Customer Profile Fields (Steckbrief)

### Basic Data
- Company name, HQ address, owner
- Management, employees (FTE)
- Financial status, buying center
- Company focus/vision/strategy
- Embargos/ESG concerns
- Frame agreements

### Locations
- Address
- Installed equipment details
- Final products
- Production capacity (tons/year)

### History
- Latest projects
- Realized projects
- CRM rating
- Key contact person
- SMS relationship
- Latest visits

### Context
- End customer information
- Market position and trends

---

## 🔧 Troubleshooting

### Issue: "No data showing"
**Solution:**
1. Ensure Excel files are in `data/` folder
2. Click "Load Data" in sidebar
3. Check console for errors

### Issue: "Profile generation fails"
**Solution:**
1. Verify API keys in `.env`
2. Check internet connection
3. Review error message in UI

### Issue: "ModuleNotFoundError"
**Solution:**
```bash
pip install -r requirements.txt
```

---

## 📈 Next Steps & Enhancements

### Immediate
- [ ] Add your real CRM/BCG data files
- [ ] Configure API keys for AI features
- [ ] Test with actual customer data

### Future Enhancements
- [ ] Train ML model on historical sales data
- [ ] Add web search for customer enrichment
- [ ] Implement PDF export (in addition to DOCX)
- [ ] Add user authentication
- [ ] Create Docker deployment
- [ ] Integrate with live CRM API

---

## 📞 Support

For questions or issues:
1. Check the README.md
2. Review error messages in the UI
3. Contact the development team

---

## ✅ Checklist for First Use

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Sample data generated (or real data added)
- [ ] `.env` file created (optional, for AI features)
- [ ] Application running (`streamlit run app/main.py`)
- [ ] Browser opened to `http://localhost:8501`
- [ ] Data loaded via sidebar
- [ ] Customer profile generated
- [ ] Profile exported to DOCX

---

**🎉 You're all set! Enjoy using the AI Supported Sales Application!**
