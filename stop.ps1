# Admin Service Portal - Shutdown Script for PowerShell

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "       Admin Service Portal Stopper      " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Stop Docker containers
Write-Host "[1/3] Stopping Docker services..." -ForegroundColor Yellow
docker compose down

# 2. Stop running python / uvicorn processes
Write-Host "[2/3] Terminating any running python and uvicorn processes..." -ForegroundColor Yellow
Stop-Process -Name python,uvicorn -ErrorAction SilentlyContinue

# 3. Stop running cloudflared processes
Write-Host "[3/3] Terminating any running cloudflared processes..." -ForegroundColor Yellow
Stop-Process -Name cloudflared -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "All services stopped successfully!" -ForegroundColor Green
