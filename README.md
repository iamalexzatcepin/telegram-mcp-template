# Telegram MCP v2

Production-oriented local Telegram access for Codex, Claude, and any STDIO-compatible MCP client. The user chooses capabilities; the server physically registers only tools allowed by the active configuration. Missing configuration means `read-only`.

## Profiles

| Profile | Intended use | Capabilities |
|---|---|---|
| `read-only` | safest default | dialogs, messages, unread, context, live search, local activity analysis |
| `assistant` | daily personal assistant | read-only plus cache, send/reply, forward, reactions, read-state, drafts, scheduling, media, polls |
| `power-user` | full local Telegram control | every capability, including edit/delete and group/channel management |
| `custom` | least-privilege workflows | exact capabilities selected by the user |

Profiles are convenience presets. `capabilities` and `denied_capabilities` provide per-capability overrides. Diagnostics are always available and secret-free.

## What is included

- Read, unread, context, per-chat search, global search, and deterministic activity statistics.
- Optional account-scoped SQLite cache with fail-closed SQLCipher mode.
- Send, reply, edit, delete, forward, reactions, mark-as-read, pin/unpin, drafts, scheduled messages, media, and polls.
- Basic group/channel creation, invitations, title changes, member removal, and leaving.
- Exact-target confirmation guard for destructive calls.
- OS-keyring-first Telethon `StringSession` storage with encrypted atomic owner-only fallback.
- Multiple named accounts across every tool.
- Setup wizard, permission inspection, diagnostics, generic STDIO entrypoint, and Codex plugin skills.

## Quick install

Requirements: Python 3.10+, Git, and a Telegram user account. Installing the self-contained Codex plugin bundle directly also requires `uv`.

macOS/Linux:

```bash
git clone https://github.com/iamalexzatcepin/telegram-mcp-template.git ~/telegram-mcp
cd ~/telegram-mcp
bash setup.sh
```

Windows PowerShell:

```powershell
git clone https://github.com/iamalexzatcepin/telegram-mcp-template.git "$env:USERPROFILE\telegram-mcp"
Set-Location "$env:USERPROFILE\telegram-mcp"
powershell -ExecutionPolicy Bypass -File setup.ps1
```

The setup script installs an isolated environment, opens the profile wizard, and runs local Telegram login. Obtain your own `api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org). Enter API hash, login code, 2FA password, session material, and encryption keys only in the local terminal—never in an AI chat.

For AI-guided installation, copy the prompt in [docs/INSTALL_WITH_AI.md](docs/INSTALL_WITH_AI.md).

## Inspect before connecting

```bash
.venv/bin/telegram-mcp permissions
.venv/bin/telegram-mcp diagnostics
```

On Windows use `.venv\Scripts\telegram-mcp.exe`.

Changing the profile changes the MCP schema. Restart the server and start a fresh agent task after every capability change.

Individual permissions can be changed without resetting the selected profile, accounts, or session:

```bash
telegram-mcp capabilities enable schedule
telegram-mcp capabilities disable schedule
```

The change is written atomically to the owner-only config. A fresh agent task is still required because MCP clients cache the exposed tool schema.

Every operation that transmits content to another Telegram user — immediate send, reply, forward, scheduled message, media, or poll — requires fresh runtime confirmation bound to the exact destination and content. Enabling a capability alone never authorizes a send. Draft creation remains non-transmitting and does not require confirmation.

## Generic MCP clients

The compatibility entrypoint remains `telegram_mcp_server.py` and always uses STDIO:

```bash
codex mcp add telegram -- "$PWD/.venv/bin/python" "$PWD/telegram_mcp_server.py"
claude mcp add --transport stdio --scope user telegram -- "$PWD/.venv/bin/python" "$PWD/telegram_mcp_server.py"
```

Equivalent JSON:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/telegram_mcp_server.py"]
    }
  }
}
```

The project does not support HTTP, SSE, tunnels, or hosted/shared operation.

## Codex plugin

The bundle is in `codex-plugin/telegram-mcp`. It adds native routing through `@Telegram` and explicit skill-style commands with Russian UI labels:

- `$telegram-mcp:telegram`
- `$telegram-mcp:telegram-chtenie`
- `$telegram-mcp:telegram-otpravka`
- `$telegram-mcp:telegram-upravlenie`
- `$telegram-mcp:telegram-nastroika`

The technical command identifiers use Latin characters for Codex compatibility. Their visible names, descriptions, icons, and starter prompts are in Russian. See [the Russian command guide](codex-plugin/telegram-mcp/docs/commands-ru.md) for when to use each command.

The bundle contains the canonical Python runtime and does not bypass its capability registry. Install it from a local/team marketplace or package it with a release; start a fresh Codex task after installation. The bundle uses `uv` to create an isolated runtime from its own `mcp_server` directory, so it remains self-contained when copied out of this repository.

## Configuration and accounts

Default config: `~/.config/telegram-mcp-v2/config.json` (or `%APPDATA%\telegram-mcp-v2\config.json` on Windows). Override with `TELEGRAM_MCP_CONFIG` or `TELEGRAM_MCP_CONFIG_DIR`.

```bash
telegram-mcp setup
telegram-mcp login --account work
telegram-mcp login --account personal
telegram-mcp storage --account work
telegram-mcp logout --account work --confirm
```

Existing v1 users can retain their authorization without another Telegram login:

```bash
telegram-mcp migrate-v1 --repo ~/telegram-mcp --account default
```

The command restricts the old session to owner-only access, stores a converted session through the v2 keyring/encrypted backend, and retains the source file for rollback.

Every Telegram tool accepts `account`. Account names are normalized before any path or keyring lookup.

## Storage and cache

Session storage tries the operating-system keyring first. When no usable keyring exists, set `TELEGRAM_MCP_MASTER_KEY` locally before login and before starting MCP; the encrypted fallback is never written plaintext.

Cache is disabled by default. Enable it through setup. Encrypted cache additionally requires the `encrypted-cache` extra, a working SQLCipher build, and `TELEGRAM_MCP_CACHE_KEY`. If any encryption dependency is missing, the server refuses to open the cache instead of downgrading.

Media uploads require `TELEGRAM_MCP_UPLOAD_DIR`; arbitrary filesystem paths are rejected. Downloads use `TELEGRAM_MCP_DOWNLOAD_DIR` or the private application config directory.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```

Architecture and audit: [docs/AUDIT_AND_ARCHITECTURE_V2.md](docs/AUDIT_AND_ARCHITECTURE_V2.md). Security model: [SECURITY.md](SECURITY.md).
