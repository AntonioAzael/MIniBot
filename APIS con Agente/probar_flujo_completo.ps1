# Script para probar el flujo completo: MinIO + OCR + Base de Datos

Write-Host "1. Verificando conexion con el backend FastAPI..." -ForegroundColor Cyan
try {
    $saludo = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method Get
    Write-Host "Backend en linea: $($saludo.app)" -ForegroundColor Green
} catch {
    Write-Host "Error: El backend no esta corriendo. Inicialo con:" -ForegroundColor Red
    Write-Host "uvicorn main:app --reload --port 8000" -ForegroundColor Yellow
    exit
}

Write-Host "`n2. Sembrando usuario y refrigerador demo..." -ForegroundColor Cyan
$demo = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/refrigerators/seed-demo" -Method Post
Write-Host "User ID: $($demo.user_id)" -ForegroundColor Green
Write-Host "Refrigerator ID: $($demo.refrigerator_id)" -ForegroundColor Green

Write-Host "`n3. Subiendo ticket y procesando OCR en MinIO..." -ForegroundColor Cyan
$rutaTicket = "C:\Users\bauti\Downloads\Mercadona-2025A-captura_400900.jpg"

if (-not (Test-Path $rutaTicket)) {
    Write-Host "Error: No se encontro el archivo en $rutaTicket" -ForegroundColor Red
    exit
}

$jsonRaw = & curl.exe -s -F "user_id=$($demo.user_id)" -F "refrigerator_id=$($demo.refrigerator_id)" -F "store_name=Mercadona" -F "archivo=@$rutaTicket" http://127.0.0.1:8000/api/v1/tickets/upload
$subida = $jsonRaw | ConvertFrom-Json

Write-Host "`n================ RESULTADOS GENERADOS ================" -ForegroundColor Yellow
Write-Host "Ticket ID:        $($subida.ticket_id)" -ForegroundColor Green
Write-Host "URL en MinIO:     $($subida.image_url)" -ForegroundColor Cyan
Write-Host "Texto detectado:`n$($subida.ocr_preview)" -ForegroundColor White
Write-Host "======================================================`n" -ForegroundColor Yellow

Write-Host "4. Consultando lista de todos los tickets guardados con sus URLs:" -ForegroundColor Cyan
$tickets = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/tickets/" -Method Get
$tickets | Format-Table id, store_name, ticket_image_url, created_at
