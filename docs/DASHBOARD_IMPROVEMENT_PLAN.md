# Dashboard (Overview Page) Improvement Plan

## Executive Summary

Transform the current "Customer Overview" dashboard from a basic plant inventory view into a comprehensive **Sales & Operations Intelligence Dashboard** that combines:
- Your existing BCG plant inventory data and CRM matching
- Axel's sales pipeline analytics (OI, LOI, Hot Projects, Priority Projects)
- Advanced KPIs, trends, and AI-powered insights

**Goal**: Create a premium, executive-level dashboard that provides instant business intelligence at a glance.

---

## Current State Analysis

### Your Current Dashboard (Strengths to Keep)
✅ **Geographic Distribution Map** - Interactive plant locations with capacity visualization  
✅ **Complete Plant Inventory Table** - Detailed equipment data with dynamic columns  
✅ **CRM Matching Quality Metrics** - Excellent/Good/Okay/Poor distribution  
✅ **Filter Integration** - Global filters (Region, Country, Equipment, Company)  
✅ **Clean Professional Layout** - No emojis, good use of space  

### Axel's Dashboard (Features to Adopt)
✅ **Sales Pipeline Tracking** - OI, LOI, Hot Projects, Priority Projects  
✅ **Top 20 Account Analysis** - Concentration metrics and percentages  
✅ **AI-Generated Insights** - GPT-powered business recommendations  
✅ **Expected vs Raw Values** - Probability-adjusted forecasting  
✅ **Multi-Tab Data Views** - Data / AI Insights / Reporting Gaps  
✅ **European Number Formatting** - Millions with proper separators  

---

## Proposed New Dashboard Structure

### **Section 1: Executive Summary (NEW - Top of Page)**
**Purpose**: Instant business health snapshot

**Components**:
1. **Hero Metrics (4-column layout)**
   - Total Pipeline Value (€ XXX M)
   - Active Opportunities (count)
   - Win Rate (%)
   - Average Deal Size (€ XXX M)

2. **Quick Trend Indicators**
   - Month-over-month pipeline growth
   - Quarter-to-date bookings
   - Forecast accuracy

3. **Alert Panel** (if applicable)
   - At-risk deals (closing soon, low probability)
   - Stalled opportunities (no activity in 30 days)
   - High-value wins (recent OIs)

---

### **Section 2: Sales Pipeline Overview (NEW - Inspired by Axel)**
**Purpose**: Comprehensive sales funnel analysis

**Layout**: 2x2 Grid (4 cards)

#### **Card 1: Order Intake (OI)** 
- **Metrics**:
  - Total OI Value (all accounts)
  - Top 20 Accounts Value
  - Top 20 Concentration %
- **Visualization**: Horizontal bar chart (Top 10 accounts)
- **Tabs**:
  - Data: Top 20 accounts table (Account, Country, GM%, Value)
  - AI Insights: GPT-generated portfolio analysis
  - Trends: Month-over-month OI progression

#### **Card 2: Letters of Intent (LOI)**
- **Metrics**:
  - Expected OI from LOIs
  - Top 20 Accounts Value
  - Pipeline Health Score
- **Visualization**: Funnel chart (LOI → Expected OI)
- **Tabs**:
  - Data: Top 20 LOI opportunities
  - AI Insights: Conversion potential analysis
  - Trends: LOI aging analysis

#### **Card 3: Hot Projects**
- **Metrics**:
  - Total Project Values (raw)
  - Expected OI (probability-adjusted)
  - Average Win Probability
- **Visualization**: Scatter plot (Value vs Probability)
- **Tabs**:
  - Data: Top 20 hot projects
  - AI Insights: Resource allocation recommendations
  - Trends: Hot project velocity

#### **Card 4: Priority Projects**
- **Metrics**:
  - Total Expected Value
  - Number of Opportunities
  - Conversion Potential
- **Visualization**: Pie chart (by region/CoE)
- **Tabs**:
  - Data: Top 20 priority projects
  - AI Insights: Development recommendations
  - Trends: Priority → Hot conversion rate

---

### **Section 3: Geographic Intelligence (ENHANCED - Your Existing)**
**Purpose**: Spatial distribution and capacity analysis

**Enhancements**:
1. **Map Improvements**:
   - Add cluster mode for dense regions
   - Color code by CRM rating (A/B/C)
   - Add heat map overlay for revenue concentration
   - Click-to-filter: Select region on map to filter tables

2. **Regional Performance Cards** (NEW):
   - Top 3 regions by:
     - Total capacity
     - Number of opportunities
     - Pipeline value
     - Win rate

3. **Country Comparison** (NEW):
   - Side-by-side comparison table
   - Sparkline trends for each country
   - Market penetration % (your equipment vs total market)

---

### **Section 4: Customer Intelligence (ENHANCED)**
**Purpose**: Deep dive into customer portfolio

**Layout**: Tabbed Interface

#### **Tab 1: Complete Plant Inventory** (Your existing - keep as is)
- Dynamic table with equipment-specific columns
- Selection to navigate to Customer Details
- Export to CSV

#### **Tab 2: Customer Segmentation** (NEW)
- **Strategic Accounts** (Top 20 by revenue)
  - Table with: Account, Total Value, # Projects, Win Rate, Last Activity
  - Visual: Bubble chart (Revenue vs # Projects, sized by Win Rate)

- **Growth Opportunities** (High potential, underserved)
  - Customers with equipment but no recent projects
  - Large capacity but low engagement
  - Visual: Opportunity matrix (Capacity vs Engagement)

- **At-Risk Customers** (Declining engagement)
  - No activity in 6+ months
  - Lost recent opportunities
  - Visual: Timeline of last interactions

#### **Tab 3: CRM Matching Quality** (Your existing - enhanced)
- Keep existing Excellent/Good/Okay/Poor metrics
- Add:
  - Unmatched BCG companies (need CRM entry)
  - Unmatched CRM customers (need BCG data)
  - Suggested matches (AI-powered fuzzy matching)
  - Bulk match approval interface

---

### **Section 5: Analytics & Insights (NEW)**
**Purpose**: AI-powered business intelligence

**Components**:

1. **Trend Analysis**:
   - Revenue trends (last 12 months)
   - Pipeline velocity (time from LOI → OI)
   - Win rate by region/CoE/equipment type
   - Seasonal patterns

2. **Predictive Analytics**:
   - Forecast next quarter bookings
   - Churn risk prediction (customers likely to go inactive)
   - Cross-sell opportunities (customers with 1 equipment type, potential for others)

3. **AI Insights Panel**:
   - Weekly summary of key changes
   - Anomaly detection (unusual spikes/drops)
   - Recommended actions (prioritized list)

---

## Implementation Checklist

### **Phase 1: Data Integration (Week 1)**
- [ ] Integrate Axel's CRM data structure (account_name, cp_status_hot, sp_expected_value_eur)
- [ ] Map your BCG data to Axel's pipeline statuses
- [ ] Create unified data model (BCG + CRM + Pipeline)
- [ ] Implement probability calculations (Go & Get probabilities)
- [ ] Add European number formatting utilities

### **Phase 2: Executive Summary (Week 1)**
- [ ] Create hero metrics calculations
- [ ] Implement trend indicators (MoM, QTD)
- [ ] Build alert detection logic
- [ ] Design premium metric cards with icons
- [ ] Add drill-down capability

### **Phase 3: Sales Pipeline Cards (Week 2)**
- [ ] Implement OI card with metrics and visualizations
- [ ] Implement LOI card with funnel chart
- [ ] Implement Hot Projects card with scatter plot
- [ ] Implement Priority Projects card with pie chart
- [ ] Add AI insights integration (GPT API)
- [ ] Create tabbed interface for each card

### **Phase 4: Geographic Enhancements (Week 2)**
- [ ] Add map clustering for dense regions
- [ ] Implement color coding by CRM rating
- [ ] Add heat map overlay
- [ ] Create regional performance cards
- [ ] Build country comparison table with sparklines

### **Phase 5: Customer Intelligence (Week 3)**
- [ ] Enhance plant inventory table
- [ ] Create customer segmentation logic
- [ ] Build growth opportunity matrix
- [ ] Implement at-risk customer detection
- [ ] Enhance CRM matching interface with AI suggestions

### **Phase 6: Analytics & Insights (Week 3)**
- [ ] Build trend analysis charts (12-month revenue, pipeline velocity)
- [ ] Implement predictive models (forecast, churn risk)
- [ ] Create cross-sell opportunity detection
- [ ] Build AI insights panel with GPT integration
- [ ] Add anomaly detection

### **Phase 7: Polish & Optimization (Week 4)**
- [ ] Implement caching for expensive calculations
- [ ] Add loading indicators for AI insights
- [ ] Optimize map rendering performance
- [ ] Create responsive layouts for different screen sizes
- [ ] Add export functionality (PDF dashboard report)
- [ ] Implement user preferences (save favorite views)

---

## Technical Implementation Details

### **New Services Required**

1. **`pipeline_service.py`**
   ```python
   - calculate_oi_metrics(df) → OI totals, top 20, concentration
   - calculate_loi_metrics(df) → LOI pipeline, conversion rates
   - calculate_hot_projects(df) → Hot project analysis
   - calculate_priority_projects(df) → Priority project metrics
   - apply_probabilities(df) → Go & Get probability adjustments
   ```

2. **`analytics_service.py`**
   ```python
   - calculate_trends(df, period) → MoM, QTD, YTD trends
   - forecast_pipeline(df, periods) → Predictive forecasting
   - detect_anomalies(df) → Unusual patterns
   - calculate_win_rates(df, groupby) → Win rate analysis
   - identify_cross_sell(df) → Cross-sell opportunities
   ```

3. **`insights_service.py`**
   ```python
   - generate_oi_insights(df, metrics) → GPT-powered OI analysis
   - generate_loi_insights(df, metrics) → GPT-powered LOI analysis
   - generate_hot_insights(df, metrics) → GPT-powered hot project analysis
   - generate_weekly_summary(df) → Weekly business summary
   - generate_recommendations(df) → Actionable recommendations
   ```

4. **`formatting_service.py`**
   ```python
   - to_millions(value, european=True) → Format to millions
   - format_percentage(value) → European percentage format
   - format_currency(value, currency='EUR') → Currency formatting
   - format_number(value, european=True) → Number formatting
   ```

### **Enhanced Visualizations**

1. **Sales Pipeline Visualizations**:
   - Horizontal bar charts for Top 20 accounts
   - Funnel charts for LOI → OI conversion
   - Scatter plots for Value vs Probability
   - Pie charts for regional distribution

2. **Trend Visualizations**:
   - Line charts with trend lines
   - Sparklines for quick trends
   - Heat maps for regional performance
   - Waterfall charts for pipeline changes

3. **Geographic Visualizations**:
   - Clustered map markers
   - Heat map overlays
   - Choropleth maps for country-level metrics
   - 3D globe view (optional premium feature)

### **AI Integration**

1. **GPT-4 Insights**:
   - Portfolio concentration analysis
   - Risk assessment
   - Strategic recommendations
   - Anomaly explanations
   - Predictive insights

2. **Prompt Templates**:
   ```python
   OI_INSIGHT_PROMPT = """
   Analyze the following Order Intake data:
   - Total OI: €{total} M
   - Top 20 Concentration: {concentration}%
   - Top Account: {account} (€{value} M)
   
   Provide:
   1. Portfolio concentration risk
   2. Key business insights
   3. Strategic recommendations
   
   Max 150 words, executive-level language.
   """
   ```

---

## Design Specifications

### **Color Palette** (Professional, Premium)
```python
PRIMARY_COLORS = {
    'success': '#10b981',  # Green for positive metrics
    'warning': '#f59e0b',  # Amber for warnings
    'danger': '#ef4444',   # Red for risks
    'info': '#3b82f6',     # Blue for information
    'neutral': '#6b7280'   # Gray for neutral
}

CHART_COLORS = {
    'oi': '#059669',       # Dark green
    'loi': '#0891b2',      # Cyan
    'hot': '#dc2626',      # Red
    'priority': '#7c3aed', # Purple
    'pipeline': '#2563eb' # Blue
}
```

### **Typography**
- **Headers**: Bold, 24-32px
- **Metrics**: Bold, 36-48px for values, 14px for labels
- **Body**: Regular, 14-16px
- **Captions**: Regular, 12px

### **Spacing**
- **Section gaps**: 48px
- **Card padding**: 24px
- **Metric spacing**: 16px
- **Element spacing**: 8px

### **Card Design**
- **Border**: 1px solid #e5e7eb
- **Border radius**: 8px
- **Shadow**: 0 1px 3px rgba(0,0,0,0.1)
- **Hover**: Slight elevation increase

---

## Success Metrics

### **User Experience**
- ✅ Dashboard loads in < 3 seconds
- ✅ All charts interactive (hover, click, zoom)
- ✅ Mobile-responsive (works on tablets)
- ✅ Accessible (WCAG 2.1 AA compliant)

### **Business Value**
- ✅ Executives can understand pipeline health in < 30 seconds
- ✅ Sales managers can identify top opportunities instantly
- ✅ AI insights provide actionable recommendations
- ✅ Trend analysis reveals patterns not visible in raw data

### **Technical Quality**
- ✅ All calculations cached for performance
- ✅ Error handling for missing/invalid data
- ✅ Graceful degradation when AI unavailable
- ✅ Export functionality for all key reports

---

## Estimated Effort

| Phase | Effort | Priority |
|-------|--------|----------|
| Data Integration | 2 days | HIGH |
| Executive Summary | 1 day | HIGH |
| Sales Pipeline Cards | 3 days | HIGH |
| Geographic Enhancements | 2 days | MEDIUM |
| Customer Intelligence | 2 days | MEDIUM |
| Analytics & Insights | 3 days | MEDIUM |
| Polish & Optimization | 2 days | LOW |
| **TOTAL** | **15 days** | |

**Recommended Approach**: Implement in phases, deploy incrementally, gather feedback, iterate.

---

## Next Steps

1. **Review & Approve**: Review this plan and approve scope
2. **Data Audit**: Verify all required data fields are available
3. **API Setup**: Ensure OpenAI API access for insights
4. **Mockups** (Optional): Create visual mockups for key sections
5. **Implementation**: Start with Phase 1 (Data Integration)

---

## Questions to Answer Before Starting

1. **Data Availability**:
   - Do you have access to Axel's CRM data (cp_status_hot, sp_expected_value_eur, etc.)?
   - Are Go & Get probabilities available in your data?
   - Do you have historical data for trend analysis?

2. **AI Integration**:
   - Do you have OpenAI API access?
   - What's your preferred model (GPT-4, GPT-3.5)?
   - Any budget constraints for API calls?

3. **User Preferences**:
   - Who are the primary users (executives, sales managers, analysts)?
   - What are the most important metrics to highlight?
   - Any specific visualizations you prefer?

4. **Technical Constraints**:
   - Any performance requirements (max load time)?
   - Browser compatibility requirements?
   - Mobile/tablet support needed?

---

**End of Plan**
