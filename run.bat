@echo off
echo ========================================
echo AI Supported Sales Application
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Generate sample data if needed
if not exist "data\crm_export.xlsx" (
    echo.
    echo Generating sample data...
    python notebooks\generate_sample_data.py
)

REM Run the application
echo.
echo ========================================
echo Starting application...
echo ========================================
echo.
echo The application will open in your browser at:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

streamlit run app\main.py

pause
