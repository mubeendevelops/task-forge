# Build and start the whole TaskForge stack, then wait until the app is healthy.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 1. Docker must be installed and its daemon running.
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed. See https://docs.docker.com/get-docker/"
}
docker info *> $null
if ($LASTEXITCODE -ne 0) { Write-Error "Docker daemon is not running. Start Docker and retry." }

# 2. Build and start everything in the background.
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Write-Error "docker compose failed." }

# 3. Wait (up to 60s) for /health to answer 200.
Write-Host -NoNewline "Waiting for the app to become healthy"
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri http://localhost:5000/health -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            Write-Host " - ready!"
            Write-Host ""
            Write-Host "  App:          http://localhost:5000"
            Write-Host "  Prometheus:   http://localhost:9090"
            Write-Host "  Grafana:      http://localhost:3000   (admin / admin)"
            Write-Host "  Alertmanager: http://localhost:9093"
            exit 0
        }
    } catch { }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 2
}
Write-Error "App did not become healthy. Check: docker compose logs app"
