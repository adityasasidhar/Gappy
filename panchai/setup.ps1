$ErrorActionPreference = "Stop"

Write-Host "🏛️ PANCHAI Setup" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Check lemma CLI
if (!(Get-Command lemma -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Lemma CLI not found. Install with: npm install -g @lemma/cli" -ForegroundColor Red
    exit 1
}

# Import the pod
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "📦 Importing pod from $ScriptDir..." -ForegroundColor Yellow
lemma pods import "$ScriptDir"

Write-Host ""
Write-Host "✅ Pod imported successfully!" -ForegroundColor Green
Write-Host ""

# Ask about seed data
$LoadSeed = Read-Host "Load demo seed data (YesMadam & Binocs scenarios)? (y/N)"
if ($LoadSeed -match '^[Yy]') {
    Write-Host "🌱 Loading seed data..." -ForegroundColor Yellow
    & "$ScriptDir\seed\seed.ps1"
}

Write-Host ""
Write-Host "🚀 Opening PANCHAI App..." -ForegroundColor Yellow
try {
    lemma apps open panchai
} catch {
    Write-Host "Run: lemma apps open panchai" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Setup complete! The PANCHAI multi-agent deliberation engine is ready." -ForegroundColor Green
