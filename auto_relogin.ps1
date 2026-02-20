$api = "http://localhost:8000"

Write-Host "Ativando modo relogin assistido (janelas visíveis)..." -ForegroundColor Cyan

$cfg = @{
  live_feed_headless = $false
  bet_headless = $false
  transmission_provider = "live_http"
  bet_provider = "bet365_playwright"
} | ConvertTo-Json

Invoke-RestMethod "$api/api/select" -Method POST -ContentType "application/json" -Body $cfg | Out-Null
Invoke-RestMethod "$api/api/control/start" -Method POST | Out-Null

Write-Host "Faça login manual na BLL e Bet365." -ForegroundColor Yellow
Write-Host "Quando terminar, pressione ENTER para validar." -ForegroundColor Yellow
Read-Host | Out-Null

$logs = Invoke-RestMethod "$api/api/logs?limit=40" -Method GET
$authErrors = $logs.items | Where-Object { $_.event -eq 'AUTH_REQUIRED' }

if ($authErrors.Count -gt 0) {
  Write-Host "Ainda há AUTH_REQUIRED nos logs recentes." -ForegroundColor Red
} else {
  Write-Host "Sem AUTH_REQUIRED recente. Sessão parece válida." -ForegroundColor Green
}

Invoke-RestMethod "$api/api/control/stop" -Method POST | Out-Null
Write-Host "Bot parado." -ForegroundColor Cyan
