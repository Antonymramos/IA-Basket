# Teste Rápido - Hoops Jarvis
# Execute: .\teste.ps1

$API = "http://localhost:8000"

Write-Host "`n=== TESTE HOOPS JARVIS ===" -ForegroundColor Magenta

# 1. Status
Write-Host "`n1. Status" -ForegroundColor Cyan
Invoke-RestMethod "$API/api/status" -Method GET | Select-Object running, mode | Format-List

# 2. Configurar
Write-Host "2. Configurando jogo..." -ForegroundColor Cyan
$config = @{
    selected_game         = "Lakers x Warriors"
    transmission_provider = "simulated_feed"
    bet_provider          = "bet_mock"
} | ConvertTo-Json
Invoke-RestMethod "$API/api/select" -Method POST -ContentType "application/json" -Body $config | Out-Null

# 3. Auto-bet ON
Write-Host "3. Auto-bet ON" -ForegroundColor Cyan
$autobet = @{enabled = $true } | ConvertTo-Json
Invoke-RestMethod "$API/api/control/auto-bet" -Method POST -ContentType "application/json" -Body $autobet | Out-Null

# 4. Iniciar
Write-Host "4. Iniciando..." -ForegroundColor Cyan
Invoke-RestMethod "$API/api/control/start" -Method POST | Out-Null

# 5. Aguardar
Write-Host "5. Aguardando 5s..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 6. Logs
Write-Host "`n6. LOGS:" -ForegroundColor Cyan
$logs = Invoke-RestMethod "$API/api/logs?limit=15" -Method GET
$logs.items | ForEach-Object { 
    $color = if ($_.event -eq "APOSTOU") { "Green" } elseif ($_.event -eq "DETECTADO") { "Cyan" } else { "Gray" }
    Write-Host "  [$($_.event)] $($_.timestamp)" -ForegroundColor $color
}

# 7. Relatório
Write-Host "`n7. RELATÓRIO:" -ForegroundColor Cyan
Invoke-RestMethod "$API/api/report" -Method GET | Format-List

# 8. Parar
Write-Host "`n8. Parando..." -ForegroundColor Cyan
Invoke-RestMethod "$API/api/control/stop" -Method POST | Out-Null

Write-Host "`n=== CONCLUÍDO ===" -ForegroundColor Green
