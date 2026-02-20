@echo off
chcp 65001 >nul

REM Ajustes de microfone para este setup (kofire)
set JARVIS_MIC_DEVICE=1
set JARVIS_MIC_GAIN=2.0

echo [JARVIS] MIC_DEVICE=%JARVIS_MIC_DEVICE%
echo [JARVIS] MIC_GAIN=%JARVIS_MIC_GAIN%
echo.

call .venv\Scripts\activate.bat
python jarvis_assistant_offline.py
