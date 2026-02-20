@echo off
echo ========================================
echo  JARVIS - Instalacao SEM PyAudio
echo ========================================
echo.

REM Ativa ambiente virtual
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo [1/2] Instalando bibliotecas sem compilacao...
python -m pip install sounddevice numpy vosk pyttsx3 python-dotenv requests

echo.
echo [2/2] Baixando modelo de voz offline PT-BR (50MB)...
echo.
python -c "import urllib.request, zipfile, os; url='https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip'; urllib.request.urlretrieve(url, 'model.zip'); zipfile.ZipFile('model.zip').extractall('.'); os.remove('model.zip'); print('Modelo instalado!')"

echo.
echo ========================================
echo  Instalacao concluida!
echo ========================================
echo.
echo Execute: python jarvis_assistant_offline.py
echo.
pause
