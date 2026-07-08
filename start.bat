@echo off
cd /d "%~dp0"
title Mutual Income Protection

echo.
echo  Mutual Income Protection
echo  ==================================
echo.

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe run.py
) else (
    python run.py
)

if errorlevel 1 (
    echo.
    echo  Something went wrong. See the error above.
    pause
)