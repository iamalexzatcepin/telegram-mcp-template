# Multiple Telegram accounts

Add each account with a local name:

```bash
telegram-mcp setup
telegram-mcp login --account work
telegram-mcp login --account personal
telegram-mcp storage --account work
```

The wizard records available names and a default. Every MCP operation also accepts `account`, for example `search_chat(chat="@example", query="contract", account="work")`.

Each account has a separate keyring record or encrypted fallback file and a separate cache database. Account identifiers are normalized and cannot escape the application directories.

Do not run concurrent mutations against the same account unless the calling workflow knows Telegram ordering semantics. If an account session may be compromised, revoke it in Telegram `Settings → Devices`, run `telegram-mcp logout --account <name> --confirm`, and log in again.
