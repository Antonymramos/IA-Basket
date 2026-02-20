# Comandos para Testar a API

## 1. Iniciar o servidor

```powershell
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Iniciar servidor
uvicorn backend.main:app --reload
```

Servidor rodando em: **http://localhost:8000**

---

## 2. Testar via Navegador

### Opção mais fácil:

1. Abra: **http://localhost:8000** (interface visual)
2. Ou: **http://localhost:8000/docs** (testar API diretamente)

---

## 3. Comandos PowerShell (copiar e colar)

### Ver status
```powershell
Invoke-RestMethod http://localhost:8000/api/status -Method GET | ConvertTo-Json
```

### Configurar jogo
```powershell
$body = @{
    selected_game = "Lakers x Warriors"
    transmission_provider = "simulated_feed"
    bet_provider = "bet_mock"
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8000/api/select -Method POST -ContentType "application/json" -Body $body
```

### Iniciar análise
```powershell
Invoke-RestMethod http://localhost:8000/api/control/start -Method POST
```

### Ligar auto-bet
```powershell
$body = @{enabled = $true} | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/control/auto-bet -Method POST -ContentType "application/json" -Body $body
```

### Ver logs (verificar se está analisando)
```powershell
Invoke-RestMethod "http://localhost:8000/api/logs?limit=20" -Method GET | ConvertTo-Json -Depth 5
```

### Ver relatório
```powershell
Invoke-RestMethod http://localhost:8000/api/report -Method GET | ConvertTo-Json
```

### Parar
```powershell
Invoke-RestMethod http://localhost:8000/api/control/stop -Method POST
```

---

## 4. Teste completo (copiar tudo de uma vez)

```powershell
# Status inicial
Write-Host "Status:" -ForegroundColor Cyan
Invoke-RestMethod http://localhost:8000/api/status -Method GET | Select-Object running, mode | Format-List

# Configurar
Write-Host "`nConfigurando jogo..." -ForegroundColor Cyan
$config = @{selected_game = "Lakers x Warriors"; transmission_provider = "simulated_feed"; bet_provider = "bet_mock"} | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/select -Method POST -ContentType "application/json" -Body $config | Out-Null

# Auto-bet ON
Write-Host "Ativando auto-bet..." -ForegroundColor Cyan
$autobet = @{enabled = $true} | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/control/auto-bet -Method POST -ContentType "application/json" -Body $autobet | Out-Null

# Iniciar
Write-Host "Iniciando..." -ForegroundColor Cyan
Invoke-RestMethod http://localhost:8000/api/control/start -Method POST | Out-Null

# Aguardar
Write-Host "Aguardando 5 segundos..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Ver logs
Write-Host "`nLogs:" -ForegroundColor Cyan
$logs = Invoke-RestMethod "http://localhost:8000/api/logs?limit=10" -Method GET
$logs.items | ForEach-Object { Write-Host "[$($_.event)]" -ForegroundColor Green }

# Relatório
Write-Host "`nRelatório:" -ForegroundColor Cyan
Invoke-RestMethod http://localhost:8000/api/report -Method GET | Format-List

# Parar
Write-Host "`nParando..." -ForegroundColor Cyan
Invoke-RestMethod http://localhost:8000/api/control/stop -Method POST | Out-Null
Write-Host "Concluído!" -ForegroundColor Green
```

---

## O que esperar nos logs

Se estiver funcionando, você verá:
- **TICK** = Bot capturando dados (aparece a cada 0.5s)
- **DETECTADO** = Discrepância de 2/3 pontos encontrada
- **APOSTOU** = Aposta executada (se auto-bet ligado)
- **BLOQUEADO** = Aposta bloqueada por algum filtro

---

## Problemas comuns

| Erro | Solução |
|------|---------|
| Servidor não inicia | Verificar se porta 8000 está livre |
| Nenhum log aparece | Rodar `/api/control/start` |
| Só aparecem BLOQUEADOS | Ligar auto-bet com `/api/control/auto-bet` |
| GEMINI_ERROR | Chave API inválida (normal se não configurou) |
