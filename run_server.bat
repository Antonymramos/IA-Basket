@echo off
REM Run Oracle NBA API Server
REM Mode: Command Prompt (CMD)

echo.
echo 🚀 Iniciando Oracle NBA API...
echo Servidor em: http://127.0.0.1:8001
echo OpenAPI: http://127.0.0.1:8001/docs
echo.
echo Para parar: Ctrl+C
echo.

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
