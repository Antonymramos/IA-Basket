@echo off
echo ========================================
echo  Instalador PyAudio para Windows
echo ========================================
echo.

REM Ativa ambiente virtual se existir
if exist .venv\Scripts\activate.bat (
    echo [1/2] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
) else (
    echo [AVISO] Ambiente virtual nao encontrado.
)

echo.
echo [2/2] Executando instalador automatico...
python install_pyaudio.py

echo.
pause
