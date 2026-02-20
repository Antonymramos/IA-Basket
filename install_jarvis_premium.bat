@echo off
echo ========================================
echo  JARVIS Premium - Setup Completo
echo ========================================
echo.

echo [PASSO 1] Ativando ambiente virtual...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo.
echo [PASSO 2] Instalando PyAudio (requer Visual C++ Build Tools)...
echo.
echo Se aparecer erro "Microsoft Visual C++ 14.0 required":
echo 1. Baixe: https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo 2. Instale "Desktop development with C++"
echo 3. Reinicie e execute este script novamente
echo.
pause
echo.

python -m pip install PyAudio

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️ PyAudio falhou no Python 3.14. Seguindo com modo offline premium.
)

echo.
echo [PASSO 3] Instalando dependencias premium...
python -m pip install SpeechRecognition pyttsx3 python-dotenv requests elevenlabs sounddevice numpy vosk

echo.
echo [PASSO 4] Configurando vozes premium (opcional)...
echo.
echo Para VOZ IGUAL AO FILME:
echo 1. Crie conta gratis em: https://elevenlabs.io/
echo 2. Copie sua API key
echo 3. Adicione ao arquivo .env:
echo    ELEVENLABS_API_KEY=sua-chave-aqui
echo.
echo Pressione ENTER para continuar (ou Ctrl+C para configurar depois)
pause > nul

echo.
echo ========================================
echo  Instalacao concluida!
echo ========================================
echo.
echo PRÓXIMO PASSO:
echo.
echo 1. [OPCIONAL] Configure voz premium editando .env
echo 2. Execute (recomendado): python jarvis_assistant_offline.py
echo 3. Se PyAudio funcionar no seu ambiente: python jarvis_assistant_premium.py
echo.
echo VOZES DISPONÍVEIS:
echo - ElevenLabs (melhor) - requer API key
echo - Azure TTS - requer conta Azure
echo - Google Cloud TTS - requer conta Google
echo - Windows (fallback) - já funciona
echo - Wake word offline com Vosk (sem compilacao)
echo.
pause
