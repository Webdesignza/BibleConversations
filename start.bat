@echo off
echo ======================================================================
echo RAG FastAPI System - Startup Script
echo ======================================================================
echo.

REM Change to the script's directory
cd /d "%~dp0"

REM Check if venv exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run the setup first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/2] Activating virtual environment...
call venv\Scripts\activate

REM Check if activation was successful
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo [2/2] Starting FastAPI server...
echo.
echo ======================================================================
echo Server will start at: http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo Admin Panel: http://127.0.0.1:8000/admin
echo Chat Interface: http://127.0.0.1:8000/chat
echo ======================================================================
echo.
echo Press CTRL+C to stop the server
echo.

REM Start the server using run.py
python run.py

REM If the server stops, pause so user can see any error messages
pause