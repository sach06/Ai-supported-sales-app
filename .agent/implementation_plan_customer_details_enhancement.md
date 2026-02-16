# Customer Details Enhancement - Implementation Plan

## Objective
Recreate and improve Axel Windbrake's customer analysis functionality from the salesai-da-app, integrating it into our existing AI-supported sales application.

## Analysis of Axel's Work

### Key Files Identified
1. **single_customer_analysis.py** (2184 lines) - Main customer analysis module
2. **intelligence_service.py** - External data enrichment and market intelligence
3. **installed_base.py** - Equipment and asset tracking
4. **customer_stories.py** - Project and case study management
5. **Fin_Data.py** - Financial data analysis
6. **contract_analysis_handler.py** - Contract and cost analysis

### Required Libraries (from Axel's code)
- **Visualization**: plotly (express & graph_objects) - already used
- **Data Processing**: pandas, numpy
- **Web scraping**: BeautifulSoup, requests
- **Export**: openpyxl (DOCX/PDF export via reportlab or python-docx)

## Implementation Phases

### Phase 1: Analysis & Data Mapping (Current)
- [x] Create feature branch
- [ ] Map Axel's data sources to our CRM schema
- [ ] Document all features from Axel's implementation
- [ ] Identify external data sources and APIs used

### Phase 2: Core Services Enhancement
- [ ] Enhance `intelligence_service.py` with web scraping for company data
- [ ] Create `financial_data_service.py` for cost/budget analysis
- [ ] Create `project_service.py` for project tracking
- [ ] Add URL provenance tracking for all external data

### Phase 3: Customer Profile Enhancement
- [ ] Expand customer profile with all CRM fields from Axel's system
- [ ] Add internet-enriched fields (company overview, news, ownership)
- [ ] Implement real-time data fetching with caching
- [ ] Add source URL display for each external field

### Phase 4: Deep Dive Analytics
- [ ] KPI dashboard with key metrics
- [ ] Segmentation analysis
- [ ] Historical trend analysis
- [ ] Project timeline visualization
- [ ] Contract history and supplier links

### Phase 5: Project Analysis
- [ ] Project summary with descriptions, status, timelines
- [ ] Sub-project hierarchy and dependencies
- [ ] Budget tracking and variance analysis
- [ ] Risk indicators
- [ ] Progress visualization (Gantt charts, burndown)

### Phase 6: Market Intelligence
- [ ] Market size and share analysis
- [ ] Competitor tracking
- [ ] Recent tenders and opportunities
- [ ] Regional insights
- [ ] Trend indicators with sources

### Phase 7: Cost Analysis
- [ ] Load client-specific cost data
- [ ] Cost breakdown by category
- [ ] Historical cost trends
- [ ] Budget variance analysis
- [ ] Scenario comparison

### Phase 8: Visualization Enhancement
- [ ] Install visualization libraries
- [ ] Recreate all of Axel's graphs:
  - Revenue trends (line charts)
  - Project distribution (pie/donut charts)
  - Timeline views (Gantt charts)
  - Geographic distribution (maps)
  - KPI scorecards
  - Comparison charts
- [ ] Add interactivity (hover, drill-down, filters)
- [ ] Ensure export compatibility

### Phase 9: Export Enhancement
- [ ] Remove Excel export option
- [ ] Enhance DOCX export:
  - Full customer profile
  - All analysis sections
  - Embedded charts as images
  - Source URLs as hyperlinks
- [ ] Enhance PDF export:
  - Professional formatting
  - Charts as high-res images
  - Table of contents
  - Source citations

### Phase 10: UI Polish
- [ ] Remove all emojis from UI
- [ ] Professional styling and layout
- [ ] Consistent typography
- [ ] Loading states and error handling
- [ ] Responsive design

### Phase 11: CRM Customers Section
- [ ] Customer list with advanced filtering
- [ ] Segmentation with cohort analysis
- [ ] Churn/retention indicators
- [ ] Per-customer mini analytics
- [ ] Bulk actions and exports

### Phase 12: Testing & QA
- [ ] Unit tests for all services
- [ ] Integration tests for data flows
- [ ] UI/UX testing
- [ ] Performance testing (large datasets)
- [ ] Export validation (DOCX/PDF quality)
- [ ] Source URL validation

## Data Requirements

### CRM Schema Mapping
Need to document:
- Customer/Company fields
- Contact information
- Financial data structure
- Project/Order structure
- Meeting notes format
- Contract data model

### External Data Sources
To be integrated with URL tracking:
1. Company registries (e.g., Crunchbase, Companies House)
2. News APIs (e.g., NewsAPI, Google News)
3. Financial data (e.g., Yahoo Finance, Alpha Vantage)
4. Tender databases
5. Industry reports

## Technical Decisions

### Architecture
- Service layer pattern (already established)
- Caching for external API calls (Redis or in-memory)
- Async data fetching where possible
- Error handling and fallbacks

### Export Format
- **DOCX**: python-docx library
- **PDF**: reportlab or weasyprint
- **Charts**: Save plotly charts as static images (kaleido)

### Visualization Strategy
- Primary: Plotly (already in use)
- Chart types needed:
  - Line/Area charts (trends)
  - Bar/Column charts (comparisons)
  - Pie/Donut charts (distributions)
  - Scatter plots (correlations)
  - Gantt charts (timelines)
  - Maps (geographic data)
  - Sankey diagrams (flows)
  - Scorecard/KPI cards

## Next Steps
1. Complete analysis of Axel's single_customer_analysis.py
2. Map data sources and create schema documentation
3. Begin Phase 2 implementation
4. Incremental commits and testing

## Success Criteria
- ✅ All features from Axel's app recreated
- ✅ Additional depth in analysis
- ✅ URL provenance for all external data
- ✅ Professional UI without emojis  
- ✅ High-quality DOCX/PDF exports with charts
- ✅ No Excel export option
- ✅ Comprehensive test coverage
- ✅ Performance benchmarks met
