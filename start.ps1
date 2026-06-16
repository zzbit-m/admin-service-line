# Admin Service Portal - Startup Script for PowerShell

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "       Admin Service Portal Starter      " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start Docker containers
Write-Host "[1/4] Starting Docker services (Postgres, Redis, MinIO, n8n)..." -ForegroundColor Yellow
docker compose up -d db redis minio n8n
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Failed to start docker services. Make sure Docker Desktop is running." -ForegroundColor Red
}

# 2. Run alembic migrations
Write-Host "[2/4] Running database migrations..." -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\alembic.exe") {
    & .\venv\Scripts\alembic.exe upgrade head
} elseif (Test-Path ".\venv\Scripts\alembic") {
    & .\venv\Scripts\alembic upgrade head
} else {
    Write-Host "WARNING: alembic not found in virtual environment. Skipping migrations." -ForegroundColor Red
}

# 3. Start python/uvicorn services in new windows
Write-Host "[3/4] Starting services in separate windows..." -ForegroundColor Yellow

# Start FastAPI Backend
Write-Host "  -> Starting FastAPI Backend on port 8001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'FastAPI Backend'; .\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001 --reload"

# Start ARQ Worker
Write-Host "  -> Starting ARQ Background Worker..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'ARQ Worker'; .\venv\Scripts\python.exe -m arq app.worker.WorkerSettings"

# Start Proxy Server
Write-Host "  -> Starting Local Proxy Server on port 3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Proxy Server'; .\venv\Scripts\python.exe scripts/proxy_server.py 3000"

# 4. Cloudflare Tunnel
Write-Host ""
$startTunnel = Read-Host "Do you want to start a Cloudflare tunnel? (y/N)"
$cfProcess = $null
if ($startTunnel -eq "y" -or $startTunnel -eq "Y") {
    Write-Host "[4/4] Starting Cloudflare tunnel and retrieving URL..." -ForegroundColor Yellow
    $logFile = Join-Path $PSScriptRoot "cloudflared.log"
    if (Test-Path $logFile) { Remove-Item $logFile -Force }

    $cfProcess = Start-Process cloudflared -ArgumentList "tunnel", "--url", "http://localhost:8001" -NoNewWindow -PassThru -RedirectStandardError $logFile

    # Wait for the tunnel URL to appear in the log (up to 15 seconds)
    $tunnelUrl = $null
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-Path $logFile) {
            $content = Get-Content $logFile -ErrorAction SilentlyContinue
            # Cloudflare quick tunnel URLs look like: https://xxxx.trycloudflare.com
            $match = $content | Select-String -Pattern "https://[a-zA-Z0-9-]+\.trycloudflare\.com"
            if ($match) {
                $tunnelUrl = $match.Matches[0].Value
                break
            }
        }
    }

    if ($tunnelUrl) {
        # Copy the LINE webhook URL directly to clipboard for convenience
        $webhookUrl = "$tunnelUrl/webhook/line"
        Set-Clipboard -Value $webhookUrl -ErrorAction SilentlyContinue

        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host "  CLOUDFLARE TUNNEL IS ACTIVE!" -ForegroundColor Green
        Write-Host "  Your public URL is: " -ForegroundColor Green -NoNewline
        Write-Host $tunnelUrl -ForegroundColor Cyan
        Write-Host "  Webhook URL for LINE: " -ForegroundColor Green -NoNewline
        Write-Host $webhookUrl -ForegroundColor Cyan
        Write-Host "  LIFF URL Endpoint:    " -ForegroundColor Green -NoNewline
        Write-Host "$tunnelUrl/liff-app.html" -ForegroundColor Cyan
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host "  [COPIED] Webhook URL has been copied to your clipboard!" -ForegroundColor Green
        Write-Host "  [TIP] DO NOT press Ctrl+C in this window (it closes the tunnel)." -ForegroundColor Yellow
        Write-Host "        Simply go to the LINE console and press Ctrl+V to paste." -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "WARNING: Failed to retrieve the tunnel URL automatically." -ForegroundColor Red
        Write-Host "Check 'cloudflared.log' to find the URL manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "[4/4] Skipping Cloudflare tunnel." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "All services started!" -ForegroundColor Green
if ($cfProcess) {
    Write-Host "Press any key to stop the Cloudflare tunnel and exit..." -ForegroundColor Yellow
} else {
    Write-Host "Press any key to exit..."
}

$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop the cloudflared process on exit
if ($cfProcess -and -not $cfProcess.HasExited) {
    Write-Host "Stopping Cloudflare tunnel..." -ForegroundColor Yellow
    Stop-Process -Id $cfProcess.Id -Force
}
