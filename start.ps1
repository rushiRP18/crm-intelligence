#!/usr/bin/env pwsh
# ============================================================
# CRM Intelligence Platform — Quick Start Script (PowerShell)
# Run from: crm-intelligence/
# Usage:    .\start.ps1
# ============================================================

param(
    [switch]$SkipSeed,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

function Write-Step($msg) {
    Write-Host "`n>> $msg" -ForegroundColor Cyan
}

function Write-OK($msg) {
    Write-Host "   [OK] $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host "   [!!] $msg" -ForegroundColor Yellow
}

function Write-Err($msg) {
    Write-Host "   [ERROR] $msg" -ForegroundColor Red
}

# ── Header ──────────────────────────────────────────────────
Write-Host ""
Write-Host "  =====================================================" -ForegroundColor Magenta
Write-Host "   CRM Intelligence Platform — Startup" -ForegroundColor Magenta
Write-Host "   AI-Powered Email Triage (LangGraph + RAG + React)" -ForegroundColor Magenta
Write-Host "  =====================================================" -ForegroundColor Magenta
Write-Host ""

# ── Check .env ──────────────────────────────────────────────
Write-Step "Checking environment configuration..."
$EnvFile = Join-Path $Root ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Err ".env file not found!"
    Write-Host "   Copy .env.example to .env and fill in your API keys:" -ForegroundColor Yellow
    Write-Host "   HUGGINGFACE_API_KEY=hf_..." -ForegroundColor Yellow
    Write-Host "   LANGCHAIN_API_KEY=lsv2_..." -ForegroundColor Yellow
    exit 1
}
$EnvContent = Get-Content $EnvFile -Raw
if ($EnvContent -match "hf_your_key_here") {
    Write-Warn "HUGGINGFACE_API_KEY not set in .env! AI processing will fail."
    Write-Warn "Edit .env and replace 'hf_your_key_here' with your actual key."
} else {
    Write-OK ".env file configured"
}

if (-not $FrontendOnly) {
    # ── Check Python ─────────────────────────────────────────
    Write-Step "Checking Python..."
    try {
        $pyVer = python --version 2>&1
        Write-OK "Python: $pyVer"
    } catch {
        Write-Err "Python not found. Install Python 3.10+ from python.org"
        exit 1
    }

    # ── Install backend dependencies ─────────────────────────
    Write-Step "Checking Python packages..."
    $chromaInstalled = python -c "import chromadb; print('ok')" 2>&1
    if ($chromaInstalled -ne "ok") {
        Write-Warn "Some packages missing. Installing requirements..."
        Push-Location $Backend
        python -m pip install -r requirements.txt
        Pop-Location
        Write-OK "Packages installed"
    } else {
        Write-OK "Python packages already installed"
    }

    # ── Seed RAG ─────────────────────────────────────────────
    if (-not $SkipSeed) {
        $ChromaDir = Join-Path $Backend "chroma_db"
        if (-not (Test-Path $ChromaDir)) {
            Write-Step "Seeding RAG knowledge base (first-time setup)..."
            Write-Host "   This will download the embedding model (~90MB) — please wait..." -ForegroundColor Yellow
            Push-Location $Backend
            python -m scripts.seed_rag
            Pop-Location
            Write-OK "RAG knowledge base ready"
        } else {
            Write-OK "RAG knowledge base already seeded (chroma_db/ exists)"
        }
    }

    # ── Start backend ─────────────────────────────────────────
    Write-Step "Starting FastAPI backend on port 8000..."
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Backend'; uvicorn app.main:app --reload --port 8000" -WindowStyle Normal
    Start-Sleep -Seconds 3

    try {
        $health = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 10
        Write-OK "Backend running: http://localhost:8000"
        Write-OK "API docs: http://localhost:8000/api/docs"
    } catch {
        Write-Warn "Backend may still be starting. Check the backend window."
    }
}

if (-not $BackendOnly) {
    # ── Check Node ───────────────────────────────────────────
    Write-Step "Checking Node.js..."
    try {
        $nodeVer = node --version 2>&1
        Write-OK "Node.js: $nodeVer"
    } catch {
        Write-Err "Node.js not found. Install Node 18+ from nodejs.org"
        exit 1
    }

    # ── Install frontend deps ─────────────────────────────────
    $nodeModules = Join-Path $Frontend "node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-Step "Installing frontend dependencies..."
        Push-Location $Frontend
        npm install
        Pop-Location
        Write-OK "Frontend dependencies installed"
    } else {
        Write-OK "Frontend dependencies already installed"
    }

    # ── Start frontend ────────────────────────────────────────
    Write-Step "Starting React frontend on port 3000..."
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Frontend'; npm run dev" -WindowStyle Normal
    Start-Sleep -Seconds 3

    Write-OK "Frontend starting: http://localhost:3000"
}

# ── Summary ──────────────────────────────────────────────────
Write-Host ""
Write-Host "  =====================================================" -ForegroundColor Green
Write-Host "   STARTUP COMPLETE!" -ForegroundColor Green
Write-Host "  =====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   Dashboard:   http://localhost:3000" -ForegroundColor White
Write-Host "   API Docs:    http://localhost:8000/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "   To ingest emails, open a new terminal and run:" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor Yellow
Write-Host "   python -m scripts.replay_emails --batch" -ForegroundColor Yellow
Write-Host ""
