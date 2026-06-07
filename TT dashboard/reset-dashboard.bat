@echo off
REM reset-dashboard.bat - Reset the dashboard database schema and seed sample data

pushd "%~dp0"


echo Running DB reset script (Node)...

node backend\scripts\reset_db.js

if %ERRORLEVEL% EQU 0 (
  echo Database reset successful.
) else (
  echo Database reset failed. See errors above.
)

popd
