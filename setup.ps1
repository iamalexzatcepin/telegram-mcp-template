# Safe local setup for Windows PowerShell.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Test-SupportedPython {
    param([string]$Command, [string[]]$PrefixArgs)
    try {
        & $Command @PrefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

$pythonCommand = $null
$pythonPrefixArgs = @()
$candidates = @(
    @{ Command = "python"; Prefix = @() },
    @{ Command = "py"; Prefix = @("-3.13") },
    @{ Command = "py"; Prefix = @("-3.12") },
    @{ Command = "py"; Prefix = @("-3.11") },
    @{ Command = "py"; Prefix = @("-3.10") }
)

foreach ($candidate in $candidates) {
    if (Test-SupportedPython -Command $candidate.Command -PrefixArgs $candidate.Prefix) {
        $pythonCommand = $candidate.Command
        $pythonPrefixArgs = $candidate.Prefix
        break
    }
}

if (-not $pythonCommand) {
    throw "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ and run setup.ps1 again."
}

$pythonVersion = & $pythonCommand @pythonPrefixArgs --version
Write-Host "==> Using $pythonVersion" -ForegroundColor Cyan

Write-Host "==> Creating venv (.venv)" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    & $pythonCommand @pythonPrefixArgs -m venv .venv
}

$venvPython = ".venv\Scripts\python.exe"
& $venvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "The existing .venv uses an unsupported Python version. Rename or remove .venv, then run setup.ps1 again."
}

& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -e .

Write-Host ""
Write-Host "==> Choosing permissions" -ForegroundColor Cyan
& ".venv\Scripts\telegram-mcp.exe" setup

Write-Host ""
Write-Host "==> Logging in locally" -ForegroundColor Cyan
Write-Host "    API hash, login code, and 2FA are entered only in this terminal."
& ".venv\Scripts\telegram-mcp.exe" login

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
Write-Host "  Claude Code CLI:  claude mcp add --transport stdio --scope user telegram -- `"$py`" `"$server`""
Write-Host "  Codex CLI:        codex mcp add telegram -- $py `"$server`""
Write-Host ""
Write-Host "Inspect exact permissions: .venv\Scripts\telegram-mcp.exe permissions"
