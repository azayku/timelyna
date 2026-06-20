param(
    [switch]$NoBuild,
    [switch]$WithDevTools
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Tool {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is not installed or not available in PATH."
    }
}

function Wait-Url {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 120,
        [string]$Name = "service"
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                Write-Host "$Name is ready ($($response.StatusCode))" -ForegroundColor Green
                return
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }

    throw "Timeout waiting for $Name at $Url"
}

try {
    Write-Step "Checking prerequisites"
    Test-Tool -Name "docker"
    docker info *> $null

    if (-not (Test-Path "docker-compose.yml")) {
        throw "docker-compose.yml not found. Run this script from the project root."
    }

    if (-not (Test-Path "backend/.env")) {
        throw "backend/.env is missing. Create it before deploying."
    }

    if ($NoBuild) {
        Write-Step "Starting containers (without build)"
        if ($WithDevTools) {
            docker compose --profile dev up -d
        } else {
            docker compose up -d
        }
    } else {
        Write-Step "Building and starting containers"
        if ($WithDevTools) {
            docker compose --profile dev up -d --build
        } else {
            docker compose up -d --build
        }
    }

    Write-Step "Waiting for services"
    Wait-Url -Url "http://localhost:8000/health" -Name "backend"
    Wait-Url -Url "http://localhost" -Name "frontend"

    Write-Step "Compose status"
    docker compose ps

    Write-Host "`nDeployment completed successfully." -ForegroundColor Green
    Write-Host "Frontend : http://localhost"
    Write-Host "Backend  : http://localhost:8000"
    Write-Host "API docs : http://localhost:8000/docs"
    if ($WithDevTools) {
        Write-Host "Mailpit  : http://localhost:8025"
        Write-Host "pgAdmin  : http://localhost:5050"
    }
} catch {
    Write-Host "`nDeployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}