# Run Oracle NBA API Server
# Mode: PowerShell

Write-Host "🚀 Iniciando Oracle NBA API..." -ForegroundColor Green
Write-Host "Servidor em: http://127.0.0.1:8001" -ForegroundColor Cyan
Write-Host "OpenAPI: http://127.0.0.1:8001/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para parar: Ctrl+C" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
