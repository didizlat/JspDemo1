# PowerShell Database Reset Script
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Database Reset Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will delete all data and reset the database to clean state." -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Type 'YES' to continue or anything else to cancel"

if ($confirm -ne "YES") {
    Write-Host "Operation cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "[1/2] Stopping Spring Boot server..." -ForegroundColor Green
Get-Process | Where-Object {$_.ProcessName -match "java"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "[2/2] Deleting database files..." -ForegroundColor Green
$deleted = $false

if (Test-Path "data\jspdemo.mv.db") {
    Remove-Item "data\jspdemo.mv.db" -Force
    Write-Host "  - Deleted: data\jspdemo.mv.db" -ForegroundColor Gray
    $deleted = $true
}

if (Test-Path "data\jspdemo.trace.db") {
    Remove-Item "data\jspdemo.trace.db" -Force
    Write-Host "  - Deleted: data\jspdemo.trace.db" -ForegroundColor Gray
    $deleted = $true
}

Get-ChildItem -Path "data" -Filter "*.lock.db" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  - Deleted: $($_.Name)" -ForegroundColor Gray
    $deleted = $true
}

if (-not $deleted) {
    Write-Host "  - No database files found (already clean)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Database reset complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The database will be recreated on next server start."
Write-Host "Tables will be empty with fresh schema."
Write-Host ""
Write-Host "To start the server:" -ForegroundColor Yellow
Write-Host "  .\mvnw.cmd spring-boot:run"
Write-Host ""
Read-Host "Press Enter to exit"

