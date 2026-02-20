@echo off
echo ========================================
echo  Instalacao JARVIS Desktop Assistant
echo ========================================
echo.

REM Ativa ambiente virtual se existir
if exist .venv\Scripts\activate.bat (
    echo [1/4] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
) else (
    echo [AVISO] Ambiente virtual nao encontrado. Usando Python global.
)

echo.
echo [2/4] Instalando dependencias base...
python -m pip install --upgrade pip
python -m pip install SpeechRecognition pyttsx3 python-dotenv openai pywhatkit requests

echo.
echo [3/4] Instalando PyAudio (requer pipwin)...
python -m pip install pipwin
python -m pipwin install pyaudio

echo.
echo [4/4] Configurando variavel de ambiente...
if not exist .env (
    echo # JARVIS Desktop Assistant > .env
    echo OPENAI_API_KEY=sua-chave-aqui >> .env
    echo [CRIADO] Arquivo .env criado. Edite e adicione sua chave OpenAI.
) else (
    echo [OK] Arquivo .env ja existe.
)

echo.
echo ========================================
echo  Instalacao concluida!
echo ========================================
echo.
echo PROXIMO PASSO:
echo 1. Edite o arquivo .env e adicione sua OPENAI_API_KEY
echo 2. Certifique-se que o sistema Hoops Jarvis esta rodando: python -m uvicorn backend.main:app --reload
echo 3. Execute: python jarvis_assistant.py
echo.
pause
