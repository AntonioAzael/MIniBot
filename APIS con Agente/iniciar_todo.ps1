# Script para iniciar todo el ecosistema en un solo comando con pestanas

$Dir = $PSScriptRoot

Write-Host "1. Levantando contenedores de MinIO y PostgreSQL..." -ForegroundColor Cyan
docker-compose up -d

$HasWT = Get-Command wt.exe -ErrorAction SilentlyContinue

function Abrir-Pestana {
    param(
        [string]$Titulo,
        [string]$Script
    )
    if ($HasWT) {
        Start-Process wt.exe -ArgumentList "-w", "0", "nt", "-d", "`"$Dir`"", "--title", "`"$Titulo`"", "powershell.exe", "-NoExit", "-Command", $Script
    } else {
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $Script
    }
}

Write-Host "2. Abriendo pestana para el Backend FastAPI..." -ForegroundColor Cyan
$BackendScript = @"
cd '$Dir'
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
"@
Abrir-Pestana -Titulo "FastAPI Backend" -Script $BackendScript

Start-Sleep -Milliseconds 600

Write-Host "3. Abriendo pestana para el Agente de Discord..." -ForegroundColor Cyan
$DiscordScript = @"
cd '$Dir'
.\venv\Scripts\Activate.ps1
python discord_agent.py
"@
Abrir-Pestana -Titulo "Agente Discord" -Script $DiscordScript

Start-Sleep -Milliseconds 600

Write-Host "4. Abriendo pestana de consola para pruebas..." -ForegroundColor Cyan
$ClientScript = @"
cd '$Dir'
.\venv\Scripts\Activate.ps1
Write-Host 'Entorno virtual activado y listo para pruebas' -ForegroundColor Green
"@
Abrir-Pestana -Titulo "Consola Cliente" -Script $ClientScript

Write-Host "`nServicios iniciados con exito en pestanas" -ForegroundColor Green
Write-Host "Consola MinIO: http://localhost:9001" -ForegroundColor Yellow
Write-Host "Swagger Docs:  http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "Agente: Conectado a Discord y listo" -ForegroundColor Yellow
