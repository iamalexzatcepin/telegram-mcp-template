# Safe setup protocol for a local AI agent

Follow this file sequentially. Do not read secret files or ask the user to paste secrets into chat.

1. Confirm the repository is a user-owned local checkout and Python is at least 3.10.
2. Read `SECURITY.md`. Keep STDIO as the only transport; do not add a tunnel, HTTP, SSE, or shared host.
3. Run the operating-system setup script. If dependencies cannot be downloaded, request normal network approval rather than changing package sources.
4. Let the user operate `telegram-mcp setup` in the terminal. Recommend `read-only`; explain additions before selecting `assistant`, `power-user`, or custom capabilities.
5. Run `telegram-mcp permissions` and show only the profile, capabilities, and exposed tool names.
6. Direct the user to `my.telegram.org` for their personal `api_id` and `api_hash`. Run `telegram-mcp login --account <name>` in a user-visible terminal and pause while the user privately enters API hash, phone, login code, 2FA, and any fallback master key.
7. Never open `.env`, OS keyring entries, encrypted session files, config encryption keys, or raw cache databases. Secret-free `storage` and `diagnostics` commands are allowed.
8. Register `telegram_mcp_server.py` with the requested client as a local STDIO process using absolute paths.
9. Restart the MCP client or start a fresh Codex task. List tools and compare them with `telegram-mcp permissions`; a forbidden tool appearing is a failed installation.
10. Verify a harmless read such as `list_chats(limit=5)`. Do not test writes or destructive actions unless the user explicitly requests the real operation.

Changing capabilities requires rerunning setup, restarting the MCP process, and starting a fresh task because tool exposure is fixed at process startup.
