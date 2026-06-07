@echo off
echo ========================================
echo  Pushing TT Wallet V1 to VPS
echo ========================================
echo.

set KEY=%USERPROFILE%\.ssh\LightsailDefaultKey.pem
set VPS=ubuntu@43.205.116.126
set SRC=c:\Users\gopij\OneDrive\Synced\Python\TT Wallet\Wallet V1

where rsync >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [1/2] rsync found — pushing only changed files...
    rsync -avz --progress -e "ssh -i %KEY% -o StrictHostKeyChecking=no" "%SRC%/" "%VPS%:~/tt-wallet/Wallet V1/"
) else (
    echo [1/2] rsync not found — falling back to scp (all files)...
    echo     Install rsync for delta transfers ^(Git Bash includes it^)
    scp -i "%KEY%" -o StrictHostKeyChecking=no "%SRC%\tt_integrated_automation.py" "%VPS%:~/tt-wallet/Wallet V1/"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "%SRC%\cookie_refresh.py" "%VPS%:~/tt-wallet/Wallet V1/"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "%SRC%\requirements.txt" "%VPS%:~/tt-wallet/Wallet V1/"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "%SRC%\.env" "%VPS%:~/tt-wallet/Wallet V1/"
)

echo.
echo [2/2] Verifying files on VPS...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "ls -la ~/tt-wallet/Wallet\ V1/"

echo.
echo ========================================
echo  Done! TT Wallet V1 updated on VPS
echo ========================================
pause
