#!/bin/bash

echo "========================================"
echo "AI Supported Sales Application"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Generate sample data if needed
if [ ! -f "data/crm_export.xlsx" ]; then
    echo ""
    echo "Generating sample data..."
    python notebooks/generate_sample_data.py
fi

# Run the application
echo ""
echo "========================================"
echo "Starting application..."
echo "========================================"
echo ""
echo "The application will open in your browser at:"
echo "http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run app/main.py
