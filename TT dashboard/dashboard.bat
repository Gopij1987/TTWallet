@echo off
REM ============================================================================
REM TT Dashboard Master Script - Run this to manage everything!
REM Just double-click this file or run: dashboard.bat
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

:menu
cls
echo.
echo ================================================================================
echo   TT Dashboard - Control Center
echo ================================================================================
echo.
echo   What would you like to do?
echo.
echo   [1] Check Setup Status (Recommended First)
echo   [2] Install Dependencies (if not installed)
echo   [3] Start Dashboard (Backend + Frontend)
echo   [4] Start Backend Only (Port 5000)
echo   [5] Start Frontend Only (Port 3000)
echo   [6] Open .env file for editing
echo   [7] Exit
echo.
echo ================================================================================
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto check_status
if "%choice%"=="2" goto install_deps
if "%choice%"=="3" goto start_both
if "%choice%"=="4" goto start_backend
if "%choice%"=="5" goto start_frontend
if "%choice%"=="6" goto edit_env
if "%choice%"=="7" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

REM ============================================================================
REM Check Setup Status
REM ============================================================================
:check_status
cls
echo.
echo ================================================================================
echo   CHECKING SETUP STATUS
echo ================================================================================
echo.

echo [1/8] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo   Node.js not found. Install from https://nodejs.org/
) else (
    for /f %%i in ('node -v') do echo   Node.js %%i found
)

echo [2/8] Checking npm...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo   npm not found
) else (
    for /f %%i in ('npm -v') do echo   npm %%i found
)

echo [3/8] Checking backend structure...
if exist "backend\server.js" (
    echo   ✅ backend/server.js found
) else (
    echo   ❌ backend/server.js missing
)

echo [4/8] Checking backend .env...
if exist "backend\.env" (
    echo   ✅ backend/.env exists
) else (
    echo   ⚠️  backend/.env NOT FOUND
    echo      Run option [6] to create it
)

echo [5/8] Checking backend dependencies...
if exist "backend\node_modules" (
    echo   ✅ backend/node_modules found
) else (
    echo   ⚠️  backend/node_modules not found - Run option [2]
)

echo [6/8] Checking frontend structure...
if exist "frontend\index.html" (
    echo   ✅ frontend/index.html found
) else (
    echo   ❌ frontend/index.html missing
)

echo [7/8] Checking frontend dependencies...
if exist "frontend\node_modules" (
    echo   ✅ frontend/node_modules found
) else (
    echo   ⚠️  frontend/node_modules not found - Run option [2]
)

echo [8/8] Checking PostgreSQL...
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   ⚠️  PostgreSQL client not found (may still be running)
) else (
    echo   ✅ PostgreSQL client found
)

echo.
echo ================================================================================
echo.
pause
goto menu

REM ============================================================================
REM Install Dependencies
REM ============================================================================
:install_deps
cls
echo.
echo ================================================================================
echo   INSTALLING DEPENDENCIES
echo ================================================================================
echo.

echo Checking if npm is installed...
npm -v >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm not found! Install Node.js from https://nodejs.org/
    pause
    goto menu
)

echo.
echo Installing backend dependencies...
cd backend
call npm install
cd ..

echo.
echo Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo ================================================================================
echo ✅ Dependencies installed successfully!
echo ================================================================================
echo.
pause
goto menu

REM ============================================================================
REM Start Both Servers
REM ============================================================================
:start_both
cls
echo.
echo ================================================================================
echo   STARTING TT DASHBOARD (Backend + Frontend)
echo ================================================================================
echo.

REM Check dependencies first
if not exist "backend\node_modules" (
    echo Backend dependencies not installed!
    echo    Run option [2] first to install dependencies
    pause
    goto menu
)

if not exist "frontend\node_modules" (
    echo Frontend dependencies not installed!
    echo    Run option [2] first to install dependencies
    pause
    goto menu
)

if not exist "backend\.env" (
    echo backend/.env not found!
    echo    Run option [6] to create and edit .env
    pause
    goto menu
)

echo Starting backend server (Port 5000)...
start "Backend - TT Dashboard API" cmd /k "cd backend && npm run dev"

timeout /t 3 /nobreak

echo Starting frontend server (Port 3000)...
start "Frontend - TT Dashboard React" cmd /k "cd frontend && npm run dev"

echo.
echo ================================================================================
echo ✅ Both servers are starting!
echo.
echo   🌐 Dashboard:     http://localhost:3000
echo   🔌 API Backend:   http://localhost:5000/api/health
echo.
echo   Close the terminal windows to stop the servers
echo ================================================================================
echo.
pause
goto menu

REM ============================================================================
REM Start Backend Only
REM ============================================================================
:start_backend
cls
echo.
echo Starting backend only (Port 5000)...
echo Close this window to stop the server
echo.
cd backend
npm run dev
pause
goto menu

REM ============================================================================
REM Start Frontend Only
REM ============================================================================
:start_frontend
cls
echo.
echo Starting frontend only (Port 3000)...
echo Close this window to stop the server
echo.
cd frontend
npm run dev
pause
goto menu

REM ============================================================================
REM Edit .env File
REM ============================================================================
:edit_env
cls
echo.
echo Creating .env from template (if not exists)...
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo ✅ Created backend/.env from template
    ) else (
        echo ❌ .env.example not found!
        pause
        goto menu
    )
)

echo.
echo Opening backend/.env in Notepad...
echo.
echo IMPORTANT: Fill in these values:
echo   - DB_HOST: localhost
echo   - DB_PORT: 5432
echo   - DB_NAME: alphametrix
echo   - DB_USER: postgres
echo   - DB_PASSWORD: your_password
echo   - TT_COOKIES_B64_GOPI: your_cookies
echo   - TT_COOKIES_B64_RAMKI: your_cookies
echo   - TT_COOKIES_B64_CAPITAL: your_cookies
echo.
timeout /t 3 /nobreak

notepad "backend\.env"

echo.
echo ================================================================================
echo ✅ .env file updated!
echo ================================================================================
echo.
pause
goto menu

REM ============================================================================
REM Exit
REM ============================================================================
:end
cls
echo.
echo ================================================================================
echo   Goodbye!
echo ================================================================================
echo.
echo   Dashboard files located in: !cd!
echo.
echo   To run again, just double-click: dashboard.bat
echo.
pause
exit /b 0
