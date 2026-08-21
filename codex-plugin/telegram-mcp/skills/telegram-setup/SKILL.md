---
name: telegram-setup
description: Configure the local Telegram MCP, choose a permission profile or custom capabilities, add named accounts, and diagnose installation without exposing secrets.
---

# Telegram Setup

Guide the user through local setup one decision at a time.

1. Install project dependencies, then run `telegram-mcp setup`. Recommend `read-only` unless the user names a need for write or management capabilities.
2. Explain the selected profile and show `telegram-mcp permissions` before login.
3. The user must obtain their own `api_id` and `api_hash` from `my.telegram.org` and enter credentials, login code, and 2FA only in the local terminal during `telegram-mcp login --account <name>`.
4. Never ask the user to paste secrets into Codex. Do not inspect `.env`, encrypted session files, keyring entries, or master-key values.
5. Use `telegram-mcp diagnostics` or the MCP diagnostics tool for secret-free checks. Start a fresh Codex task after changing plugin installation or capabilities so the MCP tool schema is reloaded.
6. For Claude or another MCP client, register `telegram_mcp_server.py` or `telegram-mcp serve` as a local STDIO server; do not enable HTTP/SSE.
