# Setup for Windows (PowerShell)
# Usage: right-click -> Run with PowerShell, or:  powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> Creating venv (.venv)" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& ".venv\Scripts\python.exe" -m pip install --quiet "mcp>=1.0,<2" telethon python-dotenv

if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "!! No .env found. Copy the template:" -ForegroundColor Yellow
    Write-Host "    copy .env.example .env"
    Write-Host "  then fill TELEGRAM_API_ID and TELEGRAM_API_HASH (from https://my.telegram.org -> API development tools)"
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "==> Logging in to Telegram (first time only)" -ForegroundColor Cyan
Write-Host "    You will be asked for your phone number and the login code."
& ".venv\Scripts\python.exe" login.py

$py = (Resolve-Path ".venv\Scripts\python.exe").Path
$server = (Resolve-Path "telegram_mcp_server.py").Path

Write-Host ""
Write-Host "==> Done! Now connect the server:" -ForegroundColor Green
Write-Host ""
Write-Host "  ChatGPT Desktop:  Settings -> MCP servers -> Add server -> STDIO"
Write-Host "                   Command: $py"
Write-Host "                   Arguments: $server"
Write-Host ""
Write-Host "  Claude Desktop:   edit claude_desktop_config.json (see README, section Desktop)"
Write-Host "                   command:  $py"
Write-Host "                   args:     [$server]"
Write-Host ""
Write-Host "  Claude Code CLI:  claude mcp add telegram -- $py `"$server`""
Write-Host "  Codex CLI:        codex mcp add telegram -- $py `"$server`""
