# 🎯 ML Priority Scoring System - Implementation Guide

## Overview

The ML Priority Scoring System uses machine learning to predict equipment modernization, OEM replacement, and maintenance service probabilities for steel industry customers. This system helps sales teams prioritize their efforts by identifying high-value opportunities.

## 🏗️ Architecture

### Components

1. **`ml_priority_service.py`** - Core ML service with model training and prediction logic
2. **`priority_list.py`** - Streamlit UI for viewing and filtering priorities
3. **`ml_priority_training.ipynb`** - Jupyter notebook for interactive model training and evaluation
4. **`models/`** - Directory storing trained model files

### Data Flow

```
DuckDB (BCG + CRM Data)
    ↓
Feature Engineering
    ↓
Label Generation (Semi-Supervised)
    ↓
Model Training (RF, XGBoost, LightGBM)
    ↓
Priority Predictions
    ↓
Streamlit UI / Export
```

## 📊 Features Engineered

### Equipment-Level Features
- **Equipment Age** - Years since startup
- **Age Category** - very_new, new, mature, old, very_old
- **Equipment Type** - Categorical encoding
- **Is Critical Equipment** - Binary flag for high-priority equipment types
- **Capacity** - Production capacity (tons/year)

### Company-Level Features
- **FTE Count** - Number of employees
- **FTE Category** - micro, small, medium, large, enterprise
- **Revenue** - Annual revenue
- **CRM Rating** - A/B/C/D/E converted to numeric
- **Match Quality** - Data quality indicator from Smart Joint

### Aggregated Features
- **Company Avg Equipment Age** - Average age of all equipment
- **Company Max Equipment Age** - Oldest equipment age
- **Company Total Equipment** - Total equipment count
- **Company Critical Equipment Count** - Count of critical equipment

## 🏷️ Label Generation Strategy

Since we don't have explicit historical labels for "modernization needed", we use a **semi-supervised approach**:

### Modernization Target
- Equipment > 15 years old
- OR critical equipment > 10 years old

### OEM Target (Total Replacement)
- Equipment > 25 years old
- OR critical equipment > 20 years old

### Maintenance Service Target
- Equipment between 5-15 years old
- (Not too new, not ready for replacement)

### Label Noise
- 10% random label flipping to simulate real-world uncertainty
- Helps models generalize better

## 🤖 Models Trained

### 1. Random Forest
- **Purpose**: Baseline model, highly interpretable
- **Hyperparameters**:
  - n_estimators: 100
  - max_depth: 10
  - min_samples_split: 20
  - min_samples_leaf: 10

### 2. XGBoost
- **Purpose**: Gradient boosting, handles missing data well
- **Hyperparameters**:
  - n_estimators: 100
  - max_depth: 6
  - learning_rate: 0.1
  - subsample: 0.8
  - colsample_bytree: 0.8

### 3. LightGBM
- **Purpose**: Fast, efficient for large datasets
- **Hyperparameters**:
  - n_estimators: 100
  - max_depth: 6
  - learning_rate: 0.1
  - subsample: 0.8
  - colsample_bytree: 0.8

## 📈 Evaluation Metrics

For each model, we calculate:

- **AUC-ROC** - Area under ROC curve (overall discrimination)
- **AUC-PR** - Area under Precision-Recall curve (performance on imbalanced data)
- **Accuracy** - Overall classification accuracy
- **Precision** - Proportion of positive predictions that are correct
- **Recall** - Proportion of actual positives that are identified

## 🚀 Usage

### Option 1: Jupyter Notebook (Recommended for First Time)

```bash
cd notebooks
jupyter notebook ml_priority_training.ipynb
```

Run all cells to:
1. Extract data from DuckDB
2. Engineer features
3. Generate labels
4. Train all models
5. Evaluate performance
6. Generate priority list
7. Export results

### Option 2: Streamlit UI

1. Start the Streamlit app:
```bash
streamlit run app/main.py
```

2. Navigate to **Priority List** page

3. Click **"Train ML Models Now"** button

4. View results in the UI

### Option 3: Python Script

```python
from app.services.ml_priority_service import ml_priority_service
from app.services.data_service import data_service
import duckdb

# Connect to database
conn = duckdb.connect("data/sales_data.db")
ml_priority_service.db_conn = conn

# Train all models
ml_priority_service.train_all_models()

# Generate predictions
df = ml_priority_service.extract_training_data()
priority_df = ml_priority_service.predict_priorities(df)

# View top priorities
print(priority_df.head(20))
```

## 📋 Output Format

The priority list includes:

| Column | Description |
|--------|-------------|
| `company_internal` | Company name |
| `equipment_type_clean` | Equipment type |
| `equipment_age` | Age in years |
| `modernization_score` | Probability (0-100%) |
| `oem_score` | Probability (0-100%) |
| `maintenance_score` | Probability (0-100%) |
| `priority_rank` | Rank (1 = highest priority) |

## 🎨 UI Features

### Priority Table
- Color-coded scores (Red: ≥75%, Yellow: 50-74%, Green: <50%)
- Sortable columns
- Downloadable as CSV

### Filters
- Minimum modernization score threshold
- Equipment type
- Country

### Visualizations
- Score distribution histograms
- Company-level rankings
- Geographic distribution
- Equipment type breakdown

## 🔧 Customization

### Adjusting Label Generation Rules

Edit `ml_priority_service.py`, method `generate_labels()`:

```python
# Example: Make modernization threshold stricter
df['modernization_target'] = (
    (df['equipment_age'] > 20) |  # Changed from 15
    ((df['is_critical_equipment'] == 1) & (df['equipment_age'] > 15))  # Changed from 10
).astype(int)
```

### Adding New Features

Edit `ml_priority_service.py`, method `_engineer_features()`:

```python
# Example: Add geographic risk factor
df['high_risk_region'] = df['region_clean'].isin(['Eastern Europe', 'Middle East']).astype(int)
```

Then add to `prepare_features()`:

```python
numerical_features = [
    # ... existing features ...
    'high_risk_region'
]
```

### Tuning Hyperparameters

Edit `ml_priority_service.py`, method `train_models()`:

```python
# Example: Increase XGBoost depth
xgb_model = xgb.XGBClassifier(
    n_estimators=200,  # More trees
    max_depth=8,       # Deeper trees
    learning_rate=0.05,  # Slower learning
    # ...
)
```

## 📊 Expected Performance

Based on the semi-supervised labeling approach:

- **AUC-ROC**: 0.75 - 0.85 (Good discrimination)
- **AUC-PR**: 0.70 - 0.80 (Good precision-recall balance)
- **Accuracy**: 70% - 80%

**Note**: Performance will improve with:
1. More historical project data
2. Explicit labels from sales team feedback
3. Additional features (maintenance history, financial data)

## 🔄 Retraining Models

Models should be retrained:
- **Monthly** - As new equipment data is added
- **Quarterly** - With updated CRM ratings
- **After major data updates** - New BCG data releases

To retrain:
```python
ml_priority_service.train_all_models()
```

Models are automatically saved with timestamps in `models/` directory.

## 🐛 Troubleshooting

### Issue: "No module named 'xgboost'"
**Solution**: Install ML dependencies
```bash
pip install scikit-learn xgboost lightgbm
```

### Issue: "Database connection required"
**Solution**: Initialize database first
```python
from app.services.data_service import data_service
data_service.initialize_database()
ml_priority_service.db_conn = data_service.conn
```

### Issue: Low model performance
**Solution**: Check data quality
- Verify BCG data has `start_year_internal` populated
- Ensure CRM data is joined correctly
- Review label distribution (should be 30-50% positive)

## 📚 Further Reading

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [SHAP for Model Interpretability](https://shap.readthedocs.io/)

## 🤝 Contributing

To improve the ML system:

1. **Add more features** - Domain expertise is valuable
2. **Collect feedback** - Sales team input on predictions
3. **Tune hyperparameters** - Use grid search or Bayesian optimization
4. **Implement SHAP** - For better model explainability

## 📞 Support

For questions or issues:
- Check the Jupyter notebook for detailed examples
- Review the code comments in `ml_priority_service.py`
- Test with the Streamlit UI for quick iterations
