@echo off
title Flash Loan Arbitrage System - Final Launcher
echo ================================================================
echo 🚀 FLASH LOAN ARBITRAGE SYSTEM - FINAL UNIFIED LAUNCHER
echo ================================================================
echo.
echo 🎯 This REPLACES all scattered startup scripts:
echo    • working_revenue_bot.py
echo    • windows_revenue_bot.py  
echo    • start_revenue_generation.bat
echo    • All scripts/*.bat files
echo    • Multiple test bots
echo.
echo ✅ Features:
echo    • Realistic profit calculations
echo    • Conservative cost analysis
echo    • Market efficiency awareness  
echo    • Single consolidated entry point
echo.
echo ================================================================
echo Starting unified system launcher...
echo ================================================================
echo.

cd /d "%~dp0"

REM Try Python first
python FINAL_LAUNCHER.py
if not errorlevel 1 goto :end

REM Try python3 if python failed
echo Trying alternative Python command...
python3 FINAL_LAUNCHER.py
if not errorlevel 1 goto :end

REM Try py if python3 failed
echo Trying py command...
py FINAL_LAUNCHER.py
if not errorlevel 1 goto :end

REM If all failed
echo.
echo ❌ ERROR: Python not found or error occurred
echo.
echo Please ensure Python 3.7+ is installed and in PATH
echo You can download Python from: https://python.org
echo.
echo Alternative: Run "python FINAL_LAUNCHER.py" manually
echo.
pause
goto :end

:end
echo.
echo 👋 System launcher completed
pause
