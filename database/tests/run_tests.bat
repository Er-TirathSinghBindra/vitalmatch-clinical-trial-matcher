@echo off
REM ============================================================================
REM VitalMatch Clinical Trial Matcher - Database Schema Validation Test Runner
REM Task 2.2: Write database schema validation tests (Windows)
REM ============================================================================

echo ==========================================
echo VitalMatch Database Schema Validation Tests
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Load environment variables from .env file if it exists
if exist .env (
    echo Loading environment variables from .env file...
    for /f "usebackq tokens=*" %%a in (".env") do (
        set "%%a"
    )
)

REM Set default values if not provided
if not defined DB_HOST set DB_HOST=localhost
if not defined DB_PORT set DB_PORT=5432
if not defined DB_NAME set DB_NAME=trials_db
if not defined DB_USER set DB_USER=vitalmatch_admin

REM Check if password is set
if not defined DB_PASSWORD (
    echo Warning: DB_PASSWORD environment variable is not set
    echo Please set it before running tests:
    echo   set DB_PASSWORD=your_password
    echo.
)

echo Database Configuration:
echo   Host: %DB_HOST%
echo   Port: %DB_PORT%
echo   Database: %DB_NAME%
echo   User: %DB_USER%
echo.

REM Check if pytest is installed
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo Installing test dependencies...
    pip install -r requirements.txt
    echo.
)

REM Run tests
echo Running database schema validation tests...
echo.

REM Run pytest with verbose output
python -m pytest test_schema_validation.py -v --tb=short

REM Check exit code
if errorlevel 1 (
    echo.
    echo ==========================================
    echo X Some tests failed. Please review the output above.
    echo ==========================================
    exit /b 1
) else (
    echo.
    echo ==========================================
    echo √ All tests passed successfully!
    echo ==========================================
    exit /b 0
)
