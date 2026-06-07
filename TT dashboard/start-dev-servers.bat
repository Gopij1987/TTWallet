@echo off
REM start-dev-servers.bat - Launch backend & frontend dev servers and open browser

setlocal
set "ROOT=%~dp0"

echo Starting TT Dashboard servers (backend + frontend)...

REM Launch the existing start-all.bat in a new cmd window
start "TT Dashboard Starter" cmd /k "cd /d "%ROOT%" && call start-all.bat"

REM Give servers a couple seconds to start, then open browser
timeout /t 4 /nobreak >nul
start "" "http://localhost:3000"

endlocal
