# Telegram MCP v2: audit and target architecture

## Confirmed v1 state

- One module statically registers exactly three tools: `list_chats`, `read_chat`, and `search_chat`.
- The server is local STDIO-only and the contract test prevents Telegram write methods from entering the two runtime modules.
- Named accounts are supported by mapping a sanitized account name to a Telethon SQLite `.session` file.
- Session files are local, but they are not encrypted and are not stored in the OS credential store.
- There is no runtime configuration schema, capability model, cache, diagnostics tool, setup profile, or Codex plugin bundle.
- Tests cover the three-tool contract, STDIO transport, basic path confinement, and MCP startup. They do not cover storage backends, write gating, destructive confirmation, or per-profile exposure.

## Reference findings

`bchewy/codex-telegram-plugin` demonstrates useful domain separation, a broad Telethon tool set, a local cache, Codex skills, keyring-first session storage, encrypted-file fallback, and a second destructive-action switch. Its server registers the full tool set statically and its session store uses one fixed account, so those parts are not adopted as-is.

## Security invariants

1. STDIO is the only server transport shipped and documented.
2. `read-only` is the setup and missing-config default.
3. A tool is registered only when its capability is resolved as allowed. Runtime denial is not a substitute for schema-level absence.
4. Diagnostic and permission-inspection tools reveal no Telegram secret or message content.
5. Destructive tools require both their capability and an explicit per-call confirmation guard.
6. Telegram session material uses an OS keyring first. The fallback is encrypted, written atomically, and owner-only.
7. Every stateful path is account-scoped and every account identifier is normalized before path or keyring use.
8. Cache encryption is opt-in and fail-closed: requesting encryption without SQLCipher never creates a plaintext cache.
9. Plugin skills guide invocation but do not weaken MCP permissions or generic MCP compatibility.

## Runtime flow

```text
config file / setup wizard
        |
        v
profile + custom capability overrides
        |
        v
resolved capability set
        |
        +--> permission inspection / diagnostics (always local, secret-free)
        |
        v
tool registry filters definitions
        |
        v
FastMCP exposes only allowed tools over STDIO
        |
        v
account-scoped Telethon client
        |
        +--> OS keyring
        `--> encrypted owner-only file fallback
```

## Capability groups

- `read`: dialogs, message history, unread items, and message context.
- `search`: per-chat and global live search.
- `analysis`: deterministic local statistics; narrative analysis stays with the calling agent.
- `cache`: optional local sync, search, status, and aggregate operations.
- `write`: sending and replying.
- `edit`, `delete`, `forward`, `reactions`, `read-state`, `pin`, `drafts`, `schedule`, `media`, and `polls`.
- `groups` and `channels`: basic creation and membership/title operations.

Profiles are cumulative convenience presets, not hard-coded roles: `read-only`, `assistant`, `power-user`, and `custom`. Custom overrides can add or remove individual capabilities.

## Package boundaries

- `config.py`: profiles, validation, permission resolution, and atomic config writes.
- `capabilities.py`: canonical capability names and tool-to-capability registry metadata.
- `server.py`: filtered registration and STDIO startup.
- `session_store.py`: keyring-first multi-account storage and encrypted fallback.
- `client.py`: authorized account-scoped Telethon client lifecycle.
- `tools/`: domain operations with no implicit registration.
- `cache.py`: account-scoped SQLite/SQLCipher storage.
- `cli.py`: setup wizard, login/logout, permissions, storage, diagnostics, and serve.
- `codex-plugin/telegram-mcp/`: self-contained Codex UX bundle and canonical Python runtime; root entrypoints expose the same runtime to generic MCP clients.

## Publication recommendation

Publish v2 first as a prerelease and keep the v1 tag available. Require existing users to run the wizard because silently enabling new write capabilities would violate the v1 security contract. Distribute the generic Python package and Codex bundle from the same signed release, document their checksums, and test clean installs on macOS, Windows, and Linux before marking v2 stable.
