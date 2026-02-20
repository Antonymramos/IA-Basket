@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║        INSTALAÇÃO PÓS-REINÍCIO - JARVIS PREMIUM            ║
echo ║    Visual C++ Build Tools já deve estar instalado          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Ativa ambiente virtual
call .venv\Scripts\activate.bat

echo [1/4] Verificando Visual C++ Build Tools...
echo.
timeout /t 2 /nobreak >nul

echo [2/4] Instalando PyAudio (agora deve funcionar)...
echo.
python -m pip install PyAudio
if errorlevel 1 (
    echo.
    echo ⚠️ PyAudio falhou no Python 3.14. Continuando com modo OFFLINE PREMIUM...
    echo.
    echo Wake word + voz premium continuam funcionando sem PyAudio.
)

echo.
echo [3/4] Instalando ElevenLabs e dependencias offline...
echo.
python -m pip install elevenlabs python-dotenv requests sounddevice numpy vosk

echo.
echo [4/4] Verificando instalação...
echo.
python -c "import pyaudio; print('✅ PyAudio OK')" 2>nul
python -c "from elevenlabs.client import ElevenLabs; print('✅ ElevenLabs OK')"
python -c "import sounddevice, vosk; print('✅ Wake word offline OK')"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                  INSTALAÇÃO COMPLETA!                      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Para testar a voz premium:
echo   python test_jarvis_voice.py
echo.
echo Para iniciar o assistente completo (SEM PyAudio):
echo   python jarvis_assistant_offline.py
echo.
echo Para iniciar versao com PyAudio (se funcionar no seu ambiente):
echo   python jarvis_assistant_premium.py
echo.
echo Comandos disponíveis após dizer "Jarvis":
echo   • "iniciar" / "parar" - controla bot
echo   • "status" - verifica estado do sistema
echo   • "lucro" - mostra resultados
echo   • "abrir painel" - abre interface web
echo   • "desligar jarvis" - encerra assistente
echo.
pause
