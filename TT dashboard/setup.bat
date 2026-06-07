@echo off
REM TT Dashboard Setup Script for Windows
REM Run this to check setup status and optionally install dependencies

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo   TT Dashboard Setup Check
echo ================================================================================
echo.

REM Check Node.js
echo [1/8] Checking Node.js...
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Install from https://nodejs.org/
) else (
    for /f "tokens=*" %%i in ('node -v') do echo ✅ Node.js %%i found
)

REM Check npm
echo [2/8] Checking npm...
npm -v >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm not found
) else (
    for /f "tokens=*" %%i in ('npm -v') do echo ✅ npm %%i found
)

REM Check backend folder
echo [3/8] Checking backend folder structure...
if exist "backend\server.js" (
    echo ✅ backend/server.js found
) else (
    echo ❌ backend/server.js missing
)

if exist "backend\db.js" (
    echo ✅ backend/db.js found
) else (
    echo ❌ backend/db.js missing
)

if exist "backend\routes" (
    echo ✅ backend/routes/ directory found
) else (
    echo ❌ backend/routes/ directory missing
)

REM Check backend .env
echo [4/8] Checking backend configuration...
if exist "backend\.env" (
    echo ✅ backend/.env exists
) else (
    echo ⚠️  backend/.env not found
    if exist "backend\.env.example" (
        echo    Copy from template: copy backend\.env.example backend\.env
    )
)

REM Check backend node_modules
echo [5/8] Checking backend dependencies...
if exist "backend\node_modules" (
    echo ✅ backend/node_modules found
) else (
    echo ⚠️  backend/node_modules not found
    echo    Run: cd backend ^&^& npm install
)

REM Check frontend folder
echo [6/8] Checking frontend folder structure...
if exist "frontend\index.html" (
    echo ✅ frontend/index.html found
) else (
    echo ❌ frontend/index.html missing
)

if exist "frontend\src" (
    echo ✅ frontend/src/ directory found
) else (
    echo ❌ frontend/src/ directory missing
)

REM Check frontend node_modules
echo [7/8] Checking frontend dependencies...
if exist "frontend\node_modules" (
    echo ✅ frontend/node_modules found
) else (
    echo ⚠️  frontend/node_modules not found
    echo    Run: cd frontend ^&^& npm install
)

REM Check PostgreSQL
echo [8/8] Checking PostgreSQL...
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  PostgreSQL client not found - verify PostgreSQL is running
) else (
    echo ✅ PostgreSQL client found
)

echo.
echo ================================================================================
echo   SETUP CHECK COMPLETE
echo ================================================================================
echo.
echo Next Steps:
echo   1. If dependencies are missing, run:
echo      - cd backend ^&^& npm install
echo      - cd frontend ^&^& npm install
echo.
echo   2. Configure backend/.env with your credentials
echo.
echo   3. Start the servers:
echo      Terminal 1: cd backend ^&^& npm run dev
echo      Terminal 2: cd frontend ^&^& npm run dev
echo.
echo   4. Open: http://localhost:3000
echo.
echo ================================================================================
echo.

pause
