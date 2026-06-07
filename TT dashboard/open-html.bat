@echo off
REM open-html.bat
REM Opens the dashboard HTML file or the dev server URL.

REM Usage:
REM  - Double-click this file to open frontend\index.html
REM  - From cmd: open-html.bat dev   -> opens http://localhost:3000

if "%1"=="dev" (
  start "" "http://localhost:3000"
  exit /b 0
)

set "SCRIPT_DIR=%~dp0"
set "FILE=%SCRIPT_DIR%frontend\index.html"

if exist "%FILE%" (
  start "" "%FILE%"
) else (
  echo File not found: %FILE%
  echo If you run a frontend dev server, open the dev URL with:
  echo.
  echo    open-html.bat dev
)
