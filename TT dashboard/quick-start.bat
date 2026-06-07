@echo off
REM Quick Start - Just runs the dashboard immediately
REM Double-click this to start everything

cd /d "%~dp0"

echo.
echo ================================================================================
echo   TT Dashboard - Quick Start
echo ================================================================================
echo.

REM Check if dependencies exist
if not exist "backend\node_modules" (
    echo ❌ Backend dependencies not installed!
    echo    Please run: dashboard.bat ^> Option 2
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo ❌ Frontend dependencies not installed!
    echo    Please run: dashboard.bat ^> Option 2
    pause
    exit /b 1
)

if not exist "backend\.env" (
    echo ❌ backend/.env not configured!
    echo    Please run: dashboard.bat ^> Option 6
    pause
    exit /b 1
)

echo Starting Backend (Port 5000)...
start "Backend API" cmd /k "cd backend && npm run dev"

timeout /t 3 /nobreak

echo Starting Frontend (Port 3000)...
start "Frontend Dashboard" cmd /k "cd frontend && npm run dev"

echo.
echo ================================================================================
echo ✅ Dashboard started!
echo.
echo   Open in browser: http://localhost:3000
echo.
echo   Close the new terminal windows to stop
echo ================================================================================
echo.
pause
