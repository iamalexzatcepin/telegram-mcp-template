# One-prompt installation for teammates

Send the following prompt to Codex or another trusted local coding agent. The user must personally complete Telegram credential and permission steps in the local terminal.

> Install `iamalexzatcepin/telegram-mcp-template` as a local Telegram MCP. Clone the repository into a normal user-owned development directory, read `docs/AGENT_SETUP.md` fully, and follow it one step at a time. Start with the read-only profile unless I explicitly choose another profile. Never ask me to paste `api_hash`, login code, 2FA password, session string, or encryption key into chat; pause while I enter them directly in the local terminal. Keep STDIO as the only transport. After setup, run permission inspection and diagnostics, register the server in my MCP client, start a fresh task, and verify only the tools allowed by my profile are visible.

The agent can automate cloning, dependency installation, configuration wiring, and diagnostics. The user must:

1. obtain their own Telegram `api_id` and `api_hash` at `my.telegram.org`;
2. select a permission profile or custom capabilities;
3. enter login code and optional 2FA locally;
4. explicitly confirm destructive operations when they are later requested.
