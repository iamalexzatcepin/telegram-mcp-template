from __future__ import annotations

import os
from pathlib import Path

from telethon.sessions import SQLiteSession, StringSession

from .config import secure_account_name
from .session_store import StoredSession, save_session


class MigrationError(RuntimeError):
    pass


def _legacy_credentials(repo: Path) -> tuple[int, str]:
    env_path = repo / ".env"
    if not env_path.is_file() or env_path.is_symlink():
        raise MigrationError("Legacy .env is missing or is a symlink")
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    api_id = values.get("TELEGRAM_API_ID") or os.getenv("TELEGRAM_API_ID")
    api_hash = values.get("TELEGRAM_API_HASH") or os.getenv("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        raise MigrationError("Legacy Telegram API credentials were not found")
    return int(api_id), api_hash


def migrate_v1(repo: Path, account: str = "default", master_key: str | None = None) -> dict:
    """Migrate a v1 SQLite session without printing or deleting secret material."""
    root = repo.expanduser().resolve()
    safe = secure_account_name(account)
    session_path = root / "sessions" / f"{safe}.session"
    if not session_path.is_file() or session_path.is_symlink():
        raise MigrationError(f"Legacy session is missing or is a symlink: {session_path}")
    try:
        session_path.chmod(0o600)
    except OSError as exc:
        raise MigrationError("Could not restrict legacy session permissions") from exc
    api_id, api_hash = _legacy_credentials(root)
    legacy = SQLiteSession(str(session_path))
    try:
        if legacy.auth_key is None:
            raise MigrationError("Legacy session contains no Telegram authorization key")
        session_string = StringSession.save(legacy)
    finally:
        legacy.close()
    backend = save_session(
        safe,
        StoredSession(api_id=api_id, api_hash=api_hash, session_string=session_string),
        master_key=master_key,
    )
    return {
        "ok": True,
        "account": safe,
        "storage": backend,
        "legacy_session_retained": True,
        "legacy_session_mode": oct(session_path.stat().st_mode & 0o777),
    }

