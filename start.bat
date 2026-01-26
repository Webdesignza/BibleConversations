@echo off
echo ======================================================================
echo Bible Conversations - Multi-Translation Bible Study System
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

echo [2/2] Starting Bible Conversations server...
echo.
echo ======================================================================
echo Server starting at: http://127.0.0.1:8009
echo.
echo Available Pages:
echo   - Bible Widget Demo:  http://127.0.0.1:8009/static/bibleconversation.html
echo   - Admin Panel:        http://127.0.0.1:8009/admin
echo   - Chat Interface:     http://127.0.0.1:8009/chat
echo   - API Documentation:  http://127.0.0.1:8009/docs
echo.
echo Translation Management:
echo   1. Create translations in Admin Panel
echo   2. Upload Bible text files to each translation
echo   3. Select translation in the widget dropdown
echo ======================================================================
echo.
echo Press CTRL+C to stop the server
echo.

REM Start the server on port 8009
py -m uvicorn app.main:app --reload --port 8009

REM If the server stops, pause so user can see any error messages
pause