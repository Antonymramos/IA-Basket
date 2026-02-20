$api = "http://localhost:8000"

$cfg = @{
    selected_game           = "NBA - Auto"
    transmission_provider   = "live_http"
    bet_provider            = "bet365_playwright"
    live_feed_ws_url        = "https://bllsport.com/view/6995df33a6240d963bb2785a?view=clean"
    bet_url                 = "https://www.bet365.bet.br/#/IP/EV151899729285C18"
    live_feed_headless      = $false
    live_feed_user_data_dir = "C:/Users/anton/OneDrive/Desktop/IA Basket/IA-Basket/.profiles/live_feed"
    bet_headless            = $false
    bet_user_data_dir       = "C:/Users/anton/OneDrive/Desktop/IA Basket/IA-Basket/.profiles/bet365"
} | ConvertTo-Json

Invoke-RestMethod "$api/api/select" -Method POST -ContentType "application/json" -Body $cfg | Out-Null
Invoke-RestMethod "$api/api/control/start" -Method POST | Out-Null

Write-Host "Bot iniciado. Faça login nas janelas abertas e acompanhe os logs." -ForegroundColor Cyan

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    $logs = Invoke-RestMethod "$api/api/logs?limit=12" -Method GET
    Clear-Host
    Write-Host "--- LOGS RECENTES ---" -ForegroundColor Yellow
    $logs.items | ForEach-Object {
        $msg = "[$($_.event)] $($_.timestamp)"
        Write-Host $msg
    }
}

Write-Host "Parando bot..." -ForegroundColor Yellow
Invoke-RestMethod "$api/api/control/stop" -Method POST | Out-Null
Write-Host "Concluído." -ForegroundColor Green
