# AI Supported Sales Application

An intelligent sales application that uses AI to analyze customer data, predict sales opportunities, and generate comprehensive customer profiles (Steckbrief).

## 🚀 Features

- **📊 Customer Dashboard**: Overview of all customers with AI-powered sales predictions
- **🎯 Sales Predictions**: ML-based hit rate forecasting for prioritizing opportunities
- **📋 Customer Profiles**: AI-generated comprehensive customer profiles (Steckbrief)
- **✏️ Editable Profiles**: Manually edit and refine AI-generated content
- **📥 Export to DOCX**: Download customer profiles as Word documents
- **📈 Analytics**: Visual insights into sales opportunities by region, industry, and more

## 📁 Project Structure

```
Code/
├── app/
│   ├── core/           # Configuration and settings
│   ├── services/       # Business logic (data, AI, export)
│   ├── ui/             # Streamlit pages
│   └── main.py         # Application entry point
├── data/               # Excel/CSV data files (add your files here)
├── notebooks/          # Jupyter notebooks for analysis
├── requirements.txt    # Python dependencies
└── .env               # Environment variables (create from .env.example)
```

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Azure OpenAI (Recommended for Enterprise)
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# OR Standard OpenAI
OPENAI_API_KEY=your_key_here
```

### 3. Add Your Data

Place your Excel/CSV files in the `data/` folder:

- `crm_export.xlsx` - CRM customer data
- `bcg_data.xlsx` - BCG market data  
- `installed_base.xlsx` - Equipment installation data

**Expected columns** (flexible - the app will adapt):

**CRM Data:**
- `name` or `customer_name` - Customer name
- `industry` - Industry sector
- `region` or `country` - Geographic location
- `fte` or `employees` - Number of employees
- `rating` or `crm_rating` - Customer rating (A/B/C/D/E)

**Installed Base:**
- `customer_id` or `customer_name` - Link to customer
- `location` - Installation location
- `equipment` - Equipment type/details
- `installation_year` or `year` - Year installed

### 4. Run the Application

```bash
streamlit run app/main.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### Step 1: Load Data
1. Click **Load Data** in the sidebar
2. Wait for the data to be imported into the database

### Step 2: Explore Dashboard
1. View the customer overview with predicted hit rates
2. Filter by industry, region, or minimum hit rate
3. Select a customer to view details

### Step 3: Generate Customer Profile
1. Go to **Customer Details** page
2. Select a customer
3. Click **Generate Profile** to create AI-powered Steckbrief
4. Review the comprehensive profile with all fields

### Step 4: Edit & Export
1. Use the **Edit** tab to manually refine the profile
2. Click **Download DOCX** to export the profile as a Word document

### Step 5: Analyze Insights
1. Go to **Analytics** page
2. View visualizations of sales opportunities
3. Identify trends by region and industry

## 🎯 Customer Profile Fields (Steckbrief)

The AI generates a comprehensive profile including:

**Basic Data:**
- Company name, HQ address, owner
- Management, employees (FTE)
- Financial status, buying center
- Company focus/vision/strategy
- Embargos/ESG concerns
- Frame agreements

**Locations:**
- Address, installed equipment
- Final products, production capacity

**History:**
- Latest and realized projects
- CRM rating, key contacts
- SMS relationship, latest visits

**Context:**
- End customer information
- Market position and trends

## 🤖 AI Models

### Prediction Model
- **Current**: Heuristic-based scoring (placeholder)
- **Future**: XGBoost trained on historical sales data
- **Features**: Company size, industry, installed base age, past projects, CRM rating

### Profile Generator
- **Model**: GPT-4o (Azure OpenAI or OpenAI)
- **Method**: Structured JSON output with comprehensive fields
- **Fallback**: Basic extraction if API unavailable

## 🔧 Troubleshooting

### No data showing?
- Ensure Excel files are in the `data/` folder
- Click "Load Data" in the sidebar
- Check file format matches expected columns

### Profile generation fails?
- Verify API keys in `.env` file
- Check internet connection
- Review error messages in the UI

### Export not working?
- Ensure `python-docx` is installed
- Generate a profile first before exporting

## 📝 Development

### Adding New Features
1. Services go in `app/services/`
2. UI pages go in `app/ui/`
3. Update `app/main.py` for new navigation items

### Testing
```bash
pytest
```

## 📄 License

Internal SMS Group project - All rights reserved

## 👥 Support

For questions or issues, contact the development team.
