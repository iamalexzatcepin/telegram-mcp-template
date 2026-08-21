# Troubleshooting

## A requested tool is missing

Run `telegram-mcp permissions`. Missing tools are usually intentionally hidden by the active capability profile. Rerun `telegram-mcp setup`, restart the MCP process, and open a fresh agent task. Do not add an alternate write server to work around the profile.

## No session or unauthorized account

Run `telegram-mcp storage --account <name>` and `telegram-mcp diagnostics`. If neither keyring nor encrypted fallback is present, run `telegram-mcp login --account <name>`. If the session was revoked in Telegram, delete the local record with `telegram-mcp logout --account <name> --confirm` and log in again.

## OS keyring is unavailable

Set `TELEGRAM_MCP_MASTER_KEY` in the local terminal/process environment before login and before starting MCP. The fallback is encrypted and owner-only. Do not place the key in a prompt, commit, shared shell history, or support ticket.

## Encrypted cache will not open

Encrypted cache intentionally fails closed. Install the `encrypted-cache` extra with a working SQLCipher build and set `TELEGRAM_MCP_CACHE_KEY`, or rerun setup and disable the cache. The server will not downgrade an encrypted-cache request to plaintext.

## Media upload is rejected

Set `TELEGRAM_MCP_UPLOAD_DIR` to a dedicated directory and move the intended file inside it. Arbitrary paths and symlink escapes are rejected to prevent accidental local-file disclosure.

## MCP starts but Telegram calls fail

Check that the selected `account` is configured and logged in, then run diagnostics. Telegram may also return flood-wait or permission errors for operations the account cannot perform. Do not repeatedly retry destructive or rate-limited calls.

## Plugin appears stale

Reinstall or update the local plugin bundle, restart Codex, and start a fresh task. Installed tasks can retain an older skill/tool schema even after the config changes.
