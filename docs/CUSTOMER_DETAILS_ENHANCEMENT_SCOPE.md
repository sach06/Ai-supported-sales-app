# Customer Details Enhancement - Project Scope & Analysis

## Executive Summary

This document outlines the comprehensive enhancement of the Customer Details page by integrating features from Axel Windbrake's salesai-da-app. The project will transform the current basic customer profile into a sophisticated analytics platform with deep-dive capabilities, market intelligence, project tracking, and cost analysis.

## Axel's Implementation Analysis

### Code Structure Identified
Based on analysis of `temp_repos/Streamlit_apps/salesai-da-app/`:

**Main Module**: `single_customer_analysis.py` (2,184 lines)
- Customer selection and portfolio analysis
- Intelligence generation via external APIs
- Historical performance tracking
- Export functionality (Excel/PDF/DOCX)

**Key Supporting Modules**:
1. `intelligence_service.py` - External data enrichment, market intel
2. `installed_base.py` - Equipment and asset management
3. `customer_stories.py` - Project case studies
4. `Fin_Data.py` - Financial analysis
5. `contract_analysis_handler.py` - Contract/cost analysis
6. `high_level_overview.py` - Dashboard and KPIs

### Features to Recreate

#### 1. Enhanced Customer Profile
- **Basic CRM Data**: Name, HQ, CEO, ownership, FTE, financials
- **Internet-Enriched Data**:
  - Company overview from web sources
  - Recent news mentions (last 12 months)
  - Ownership structure and history
  - Related projects and case studies
- **Provenance**: Every external field includes source URL

#### 2. Deep Dive Analytics
-  **KPI Dashboard**:
  - Revenue trends (YoY growth)
  - Project win rate
  - Customer lifetime value
  - Engagement score
- **Segmentation Analysis**:
  - Customer tier classification
  - Industry positioning
  - Geographic distribution
- **Historical Trends**:
  - Revenue by year/quarter
  - Project count evolution
  - Contract value trends
- **Relationship Mapping**:
  - Key contacts and their roles
  - Decision makers
  - Supplier/partner network

#### 3. Project Summary & Sub-Projects
- **Project Overview**:
  - Full descriptions with technical specs
  - Current status and phase
  - Start/end dates and milestones
  - Budget allocation
- **Sub-Project Hierarchy**:
  - Parent-child relationships
  - Dependencies and critical path
  - Resource allocation
- **Progress Tracking**:
  - Gantt chart visualization
  - Milestone completion %
  - Budget burn rate
- **Risk Management**:
  - Risk register with severity
  - Mitigation strategies
  - Issue tracking

#### 4. Market Intelligence
- **Market Analysis**:
  - Total addressable market size
  - Market growth rate
  - Customer's market share
- **Competitive Landscape**:
  - Key competitors list
  - Competitive positioning
  - Win/loss analysis vs competitors
- **Tender & Opportunities**:
  - Recent tenders (public sources)
  - Pipeline opportunities
  - Historical bid success rate
- **Regional Insights**:
  - Country-specific trends
  - Regulatory environment
  - Local partnerships
- **Trend Indicators**:
  - Industry trends affecting customer
  - Technology adoption patterns
  - Sustainability initiatives

#### 5. Cost Analysis
- **Cost Structure**:
  - Material costs
  - Labor costs
  - Overhead allocation
  - Margin analysis
- **Budget Management**:
  - Budget vs actual by project
  - Variance analysis with explanations
  - Forecast to completion
- **Historical Cost Trends**:
  - Cost evolution over time
  - Cost reduction initiatives
  - Efficiency gains
- **Scenario Analysis**:
  - Best/worst/expected case
  - Sensitivity analysis
  - What-if simulations

#### 6. Visualization Types (from Axel's Code)

**Revenue & Financial Charts**:
- Line chart: Revenue trends over time
- Area chart: Cumulative revenue
- Bar chart: Revenue by product/service
- Waterfall chart: Revenue breakdown

**Project Analytics**:
- Pie/Donut: Project distribution by status
- Gantt: Project timelines
- Burndown: Progress tracking
- Sankey: Resource allocation flow

**Geographic & Segmentation**:
- Choropleth map: Revenue by region
- Scatter: Customer segmentation
- Funnel: Sales pipeline stages
- Heatmap: Engagement matrix

**Performance Scorecards**:
- KPI cards with trend indicators
- Gauge charts for targets
- Comparison bars for benchmarking

### Data Sources & APIs

#### Internal Sources (CRM Database)
Schema to be mapped from existing `data_service.py`:
```
- unified_companies table
- bcg_installed_base table  
- company_mappings table
- (Additional tables to be identified)
```

#### External Sources (with URL Tracking)
1. **Company Information**:
   - Crunchbase API (https://data.crunchbase.com/)
   - Companies House UK (https://api.company-information.service.gov.uk/)
   - OpenCorporates (https://api.opencorporates.com/)

2. **News & Media**:
   - NewsAPI (https://newsapi.org/)
   - Google News RSS
   - Company press releases (web scraping)

3. **Financial Data**:
   - Yahoo Finance API
   - Alpha Vantage (https://www.alphavantage.co/)
   - Financial statements (if publicly traded)

4. **Tender & Procurement**:
   - TED (Tenders Electronic Daily - EU)
   - National procurement portals
   - Industry-specific tender platforms

5. **Market Intelligence**:
   - Industry report aggregators
   - Trade association data
   - Government statistics portals

### Technical Architecture

#### Service Layer Enhancements
```
app/services/
├── data_service.py (existing - enhance)
├── intelligence_service.py (new)
├── project_service.py (new)
├── financial_service.py (new)
├── market_intelligence_service.py (new)
├── web_scraping_service.py (new)
└── enhanced_export_service.py (new)
```

#### Export Strategy

**Remove**: Excel export option entirely

**DOCX Export** (using python-docx):
- Professional template with company branding
- Table of contents with hyperlinks
- Embedded charts as high-res images (via kaleido)
- Source URLs as clickable hyperlinks
- Sections: Profile, Deep Dive, Projects, Market Intel, Costs

**PDF Export** (using reportlab):
- Similar structure to DOCX
- Optimized for printing
- Embedded vector graphics where possible
- Professional typography
- Page numbering and headers/footers

#### Caching Strategy
```python
# In-memory cache for session
st.session_state.external_data_cache = {}

# Redis for persistent cache (optional future enhancement)
# - Cache TTL: 24 hours for company data
# - Cache TTL: 1 hour for news/tender data
```

### UI/UX Requirements

#### Remove All Emojis
Current code uses emojis extensively (💰, 📰, 📊, 🎯, ⚠️, etc.)
Replace with:
- Professional icons or
- Simple text labels with bold/color coding

#### Professional Styling
- Consistent color scheme (corporate blues/grays)
- Professional typography (sans-serif fonts)
- Clean layouts with proper spacing
- Loading indicators for async operations
- Error states with helpful messages

#### Responsive Design
- Must work on desktop (primary)
- Tablet support (nice to have)
- Print-friendly layouts

### Implementation Phases (12 Phases)

See `implementation_plan_customer_details_enhancement.md` for detailed breakdown.

**Timeline Estimate**: 2-3 weeks for full implementation
- Phase 1-2: 2 days (Analysis & Core Services)
- Phase 3-7: 8 days (Features Implementation)
- Phase 8-10: 4 days (Visualizations & Exports & UI)
- Phase 11-12: 2 days (CRM Section & Testing)

### Success Metrics

1. **Feature Parity**: 100% of Axel's key features recreated
2. **Data Enrichment**: ≥3 external sources for each customer
3. **URL Provenance**: 100% of external data points have source URLs
4. **Export Quality**: Professional DOCX/PDF with embedded charts
5. **Performance**: Page load <3s, export generation <5s
6. **No Emojis**: Zero emojis in production UI and exports
7. **Test Coverage**: ≥80% code coverage for new services

### Risks & Mitigation

**Risk**: External API rate limits
**Mitigation**: Implement caching, fallback to cached data, rate limiting

**Risk**: Data quality from web scraping
**Mitigation**: Multiple source verification, manual review queue

**Risk**: Export generation performance
**Mitigation**: Async generation, progress indicators, optimization

**Risk**: Scope creep
**Mitigation**: Phased delivery, MVP first, enhancements later

### Next Steps

1. ✅ Create feature branch
2. ✅ Document requirements and analysis
3. ⏳ Update requirements.txt with new libraries
4. ⏳ Begin Phase 2: Create enhanced services
5. ⏳ Implement Phase 3: Customer Profile Enhancement
6. ⏳ Continue through remaining phases

## Appendix

### Key Files from Axel's Implementation
- `single_customer_analysis.py`: Main analysis module (2184 lines)
- `intelligence_service.py`: External data integration
- `installed_base.py`: Equipment tracking
- `export_to_excel_enhanced()`: Export functionality (lines 160-650)
- `render_customer_analysis()`: Main UI (lines 1100-2184)

### Code Example (Export Structure from Axel)
```python
# Excel export with multiple tabs:
# - Tab 1: Customer Overview
# - Tab 2: Project Portfolio
# - Tab 3: Market Intelligence  
# - Tab 4: Historical Performance
# - Tab 5: Installed Base
# - Tab 6: Meeting Notes
```

This structure will be replicated but enhanced for DOCX/PDF exports.
