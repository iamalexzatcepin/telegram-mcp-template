from __future__ import annotations

import importlib
import os
from pathlib import Path
import sqlite3
from typing import Any

from .config import config_dir, secure_account_name

CACHE_KEY_ENV = "TELEGRAM_MCP_CACHE_KEY"

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    account TEXT NOT NULL,
    chat_ref TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    date TEXT,
    sender_id TEXT,
    sender TEXT,
    text TEXT,
    outgoing INTEGER NOT NULL DEFAULT 0,
    has_media INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (account, chat_ref, message_id)
);
CREATE INDEX IF NOT EXISTS idx_messages_search ON messages(account, chat_ref, date);
CREATE TABLE IF NOT EXISTS sync_state (
    account TEXT NOT NULL,
    chat_ref TEXT NOT NULL,
    last_sync TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    PRIMARY KEY (account, chat_ref)
);
"""


class CacheError(RuntimeError):
    pass


def cache_path(account: str) -> Path:
    safe = secure_account_name(account)
    path = config_dir() / "cache" / f"{safe}.db"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    return path


def _driver(encrypted: bool):
    if not encrypted:
        return sqlite3
    try:
        return importlib.import_module("pysqlcipher3.dbapi2")
    except ImportError as exc:
        raise CacheError(
            "Encrypted cache requested but pysqlcipher3 is unavailable; refusing plaintext fallback"
        ) from exc


def connect_cache(account: str, encrypted: bool = False, key: str | None = None):
    path = cache_path(account)
    driver = _driver(encrypted)
    connection = driver.connect(str(path))
    try:
        if encrypted:
            secret = key or os.getenv(CACHE_KEY_ENV)
            if not secret:
                raise CacheError(f"Encrypted cache requires {CACHE_KEY_ENV}")
            escaped = secret.replace("'", "''")
            connection.execute(f"PRAGMA key = '{escaped}'")
            connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
        connection.row_factory = getattr(driver, "Row", sqlite3.Row)
        connection.executescript(SCHEMA)
        connection.commit()
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return connection
    except BaseException:
        connection.close()
        if encrypted and path.exists() and path.stat().st_size == 0:
            path.unlink(missing_ok=True)
        raise


def upsert_messages(connection, account: str, chat: str, rows: list[dict[str, Any]]) -> None:
    connection.executemany(
        """
        INSERT INTO messages(account, chat_ref, message_id, date, sender_id, sender, text, outgoing, has_media)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(account, chat_ref, message_id) DO UPDATE SET
          date=excluded.date, sender_id=excluded.sender_id, sender=excluded.sender,
          text=excluded.text, outgoing=excluded.outgoing, has_media=excluded.has_media
        """,
        [
            (
                account,
                chat,
                row["id"],
                row.get("date"),
                str(row.get("sender_id")) if row.get("sender_id") is not None else None,
                row.get("sender"),
                row.get("text"),
                int(bool(row.get("outgoing"))),
                int(bool(row.get("has_media"))),
            )
            for row in rows
        ],
    )

