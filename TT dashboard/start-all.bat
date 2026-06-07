@echo off
REM TT Dashboard Startup Script for Windows
REM Launches both backend and frontend servers

title TT Dashboard

echo.
echo ================================================================================
echo   TT Dashboard - Starting both servers
echo ================================================================================
echo.

REM Check if backend/node_modules exists
if not exist "backend\node_modules" (
    echo ❌ Backend dependencies not installed!
    echo    Run: cd backend ^&^& npm install
    pause
    exit /b 1
)

REM Check if frontend/node_modules exists
if not exist "frontend\node_modules" (
    echo ❌ Frontend dependencies not installed!
    echo    Run: cd frontend ^&^& npm install
    pause
    exit /b 1
)

echo Starting backend on port 5000...
start "Backend API" cmd /k "cd backend && npm run dev"

timeout /t 2 /nobreak

echo Starting frontend on port 3000...
start "Frontend React" cmd /k "cd frontend && npm run dev"

echo.
echo ================================================================================
echo.
echo ✅ Both servers starting:
echo.
echo   Dashboard:    http://localhost:3000
echo   API Backend:  http://localhost:5000/api/health
echo.
echo   Close this window when done
echo.
echo ================================================================================
echo.

pause
