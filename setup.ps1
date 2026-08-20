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
& $venvPython -m pip install --quiet -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "A local .env file was created." -ForegroundColor Yellow
    Write-Host "Open it and fill TELEGRAM_API_ID and TELEGRAM_API_HASH from https://my.telegram.org."
    Write-Host "Do not paste API_HASH into an AI chat. Then run setup.ps1 again."
    exit 2
}

$envText = Get-Content ".env" -Raw
if ($envText -notmatch '(?m)^TELEGRAM_API_ID=\d+\s*$' -or
    $envText -notmatch '(?m)^TELEGRAM_API_HASH=[0-9A-Fa-f]{32}\s*$') {
    throw "The .env file does not contain a valid TELEGRAM_API_ID and TELEGRAM_API_HASH. Edit it locally; secret values will not be printed."
}

Write-Host ""
Write-Host "==> Logging in to Telegram (first time only)" -ForegroundColor Cyan
Write-Host "    You will be asked for your phone number and the login code."
& $venvPython login.py --account default

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
