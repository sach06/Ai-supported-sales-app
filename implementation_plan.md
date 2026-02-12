# Implementation Plan - AI Supported Sales Application

## Goal Description
Develop a "Local-First" **AI Supported Sales Application** to increase sales hit rates. The app will ingest data from Excel/CSV exports (CRM, BCG, Installed Base), use **Predictive AI** to forecast sales probability, and **Generative AI** to compile a comprehensive **Customer Profile ("Steckbrief")** using internal data and internet sources.

## Architecture & Tech Stack

### High-Level Architecture
*(Simplified for Local Execution)*
```mermaid
graph TD
    User[Sales User] -->|Browses| UI[Streamlit Frontend]
    UI -->|Requests| Logic[Application Logic (Local Python)]
    
    subgraph "Data Layer (Local)"
        Files[Excel/CSV Inputs] --> Ingest[Data Ingestion]
        Ingest --> DB[(In-Memory/Local SQL)]
        Web[Internet Search] --> Enrich[Enrichment]
    end
    
    subgraph "AI Engine"
        Pred[Predictive Model (XGBoost)]
        LLM[Azure OpenAI (GPT-4o)]
    end
    
    Logic --> DB
    Logic --> Pred
    Logic --> LLM
    Logic --> Enrich
```

### Technology Stack
| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Frontend** | **Streamlit** | Interactive UI, runs locally in browser. |
| **Backend/Logic** | **Python (FastAPI optional)** | for modularity, we will structure code as a backend service but run it locally. |
| **Data Source** | **Pandas / Excel Files** | Direct ingestion of user-provided Excel sheets. |
| **Database** | **SQLite / DuckDB** | Lightweight local SQL for querying joined data without setup. |
| **Predictive AI** | **XGBoost** | Efficient tabular prediction for "Hit Rate". |
| **PDF/DOC Gen** | **python-docx / WeasyPrint** | For exporting the "Steckbrief" to downloadable formats. |

## Proposed Changes

### 1. Project Structure
```text
/
├── app/
│   ├── api/            # Logic for Predictions & Data Retrieval
│   ├── services/       # AI, Data Ingestion, & **Export Services**
│   ├── ui/             # Streamlit Pages & Components
│   ├── core/           # Config (Azure Keys, Paths)
│   └── main.py         # Entry point to run everything
├── data/               # Folder for User Excel Files
│   ├── crm_export.xlsx
│   ├── bcg_data.xlsx
│   └── installed_base.xlsx
├── notebooks/          # Experiments
└── requirements.txt
```

### 2. Data Ingestion & "Steckbrief" Logic
**Inputs**: Excel Files (CRM, BCG, Plant Data).
**Internet Enrichment**: Use a search API (e.g., Tavily/Bing) to fill gaps (e.g., "Company news", "ESG issues").

**Target "Steckbrief" Fields (as requested):**
*   **Basis Data**: Name, HQ Address, Owner, Management, FTE, Financials.
*   **Strategy/Risk**: Buying Center, Company Focus/Vision, Embargos/ESG, Frame Agreements.
*   **Locations**: Address, Installed Base (Plant type, EA, OEM...), Final Products, Tons/year.
*   **History**: Latest/Realized Projects, CRM Rating, Key Person, SMS Relationship/Contact, Latest Visits.
*   **Context**: End Customer identification.

### 3. AI Modules
#### Predictive Module (Sales Hit Rate)
*   **Goal**: Predict likelihood of a "Win".
*   **Features**: Company size, Region, Installed Base Age, Past Project Success, Market Sector.
*   **Output**: % Score + "Key Drivers".

#### Profile Generator (Generative)
*   **Process**: 
    1.  Flatten structured data (SQL/Excel) into text.
    2.  fetch "missing" info (e.g., "Company Vision") via Web Search.
    3.  Pass to LLM to format into the strict "Steckbrief" structure.

### 4. Frontend (Streamlit)
*   **Home/Dashboard**: Upload Excel files, View High-Level Table (Ranked by Prediction Score).
*   **Customer Detail View**:
    *   **Profile Tab**: The full "Steckbrief" (fields above).
        *   **Action**: "Edit Mode" toggle to manually correct AI output.
        *   **Action**: "Download Report" button (PDF/Word).
    *   **Installed Base Tab**: Detailed table of plants/equipment.
    *   **Analysis Tab**: Prediction details (Why is this score high/low?).

## User Review Required
> [!IMPORTANT]
> **API Keys**: We will need keys for **Azure OpenAI** and a Web Search provider (like **Bing Search API** or **Tavily**) to get the "Internet data" for the profile.

## Verification Plan
1.  **Data Loading**: Drop sample Excel files into `/data`, verify Streamlit loads them.
2.  **Profile Check**: Select a customer, verify all "Steckbrief" fields are populated (either from Excel or noted as "Not Found").
3.  **Local Run**: Command `streamlit run app/main.py` should launch the full app.
