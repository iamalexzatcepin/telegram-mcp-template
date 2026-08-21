from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import atomic_write_json, config_dir, secure_account_name

try:
    import keyring
    from keyring.errors import KeyringError, NoKeyringError
except ImportError:  # pragma: no cover - dependency is present in supported installs
    keyring = None

    class KeyringError(Exception):
        pass

    NoKeyringError = KeyringError

SERVICE_NAME = "telegram-mcp-v2"
MASTER_KEY_ENV = "TELEGRAM_MCP_MASTER_KEY"
SESSION_ENV_PREFIX = "TELEGRAM_MCP_SESSION_"
PBKDF2_ITERATIONS = 600_000


class SessionStoreError(RuntimeError):
    pass


class MissingSessionError(SessionStoreError):
    pass


@dataclass(frozen=True)
class StoredSession:
    api_id: int
    api_hash: str
    session_string: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, value: str) -> "StoredSession":
        raw = json.loads(value)
        return cls(
            api_id=int(raw["api_id"]),
            api_hash=str(raw["api_hash"]),
            session_string=str(raw["session_string"]),
        )


def _session_path(account: str) -> Path:
    return config_dir() / "sessions" / f"{secure_account_name(account)}.enc"


def _keyring_account(account: str) -> str:
    return f"account:{secure_account_name(account)}"


def _derive_key(master_key: str, salt: bytes) -> Fernet:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return Fernet(base64.urlsafe_b64encode(kdf.derive(master_key.encode("utf-8"))))


def _encrypt(value: str, master_key: str) -> dict[str, str | int]:
    salt = os.urandom(16)
    token = _derive_key(master_key, salt).encrypt(value.encode("utf-8"))
    return {
        "version": 1,
        "kdf": "pbkdf2-sha256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": base64.urlsafe_b64encode(salt).decode("ascii"),
        "token": token.decode("ascii"),
    }


def _decrypt(payload: dict[str, Any], master_key: str) -> str:
    if payload.get("version") != 1:
        raise SessionStoreError("Unsupported encrypted session format")
    salt = base64.urlsafe_b64decode(str(payload["salt"]).encode("ascii"))
    try:
        return _derive_key(master_key, salt).decrypt(
            str(payload["token"]).encode("ascii")
        ).decode("utf-8")
    except (InvalidToken, KeyError, ValueError) as exc:
        raise SessionStoreError("Encrypted session could not be decrypted") from exc


def _read_keyring(account: str) -> StoredSession | None:
    if keyring is None:
        return None
    try:
        value = keyring.get_password(SERVICE_NAME, _keyring_account(account))
    except (KeyringError, NoKeyringError):
        return None
    if not value:
        return None
    try:
        return StoredSession.from_json(value)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return None


def _write_keyring(account: str, record: StoredSession) -> bool:
    if keyring is None:
        return False
    try:
        keyring.set_password(SERVICE_NAME, _keyring_account(account), record.to_json())
        return True
    except (KeyringError, NoKeyringError):
        return False


def load_session(account: str, master_key: str | None = None) -> StoredSession:
    safe = secure_account_name(account)
    env_suffix = safe.upper().replace("-", "_").replace(".", "_")
    env_value = os.getenv(f"{SESSION_ENV_PREFIX}{env_suffix}")
    env_api_id = os.getenv("TELEGRAM_API_ID")
    env_api_hash = os.getenv("TELEGRAM_API_HASH")
    if env_value and env_api_id and env_api_hash:
        return StoredSession(int(env_api_id), env_api_hash, env_value)

    stored = _read_keyring(safe)
    if stored:
        return stored

    path = _session_path(safe)
    if not path.exists():
        raise MissingSessionError(f"No Telegram session for account '{safe}'")
    if path.is_symlink():
        raise SessionStoreError(f"Refusing symlinked session file: {path}")
    key = master_key or os.getenv(MASTER_KEY_ENV)
    if not key:
        raise MissingSessionError(
            f"Encrypted session exists for '{safe}', but {MASTER_KEY_ENV} is unset"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return StoredSession.from_json(_decrypt(payload, key))
    except (OSError, json.JSONDecodeError) as exc:
        raise SessionStoreError(f"Invalid encrypted session for '{safe}'") from exc


def save_session(
    account: str,
    record: StoredSession,
    master_key: str | None = None,
) -> str:
    safe = secure_account_name(account)
    if _write_keyring(safe, record):
        return "keyring"
    key = master_key or os.getenv(MASTER_KEY_ENV)
    if not key:
        raise SessionStoreError(
            f"OS keyring unavailable; set {MASTER_KEY_ENV} for encrypted-file fallback"
        )
    atomic_write_json(_session_path(safe), _encrypt(record.to_json(), key))
    return "encrypted-file"


def delete_session(account: str) -> bool:
    safe = secure_account_name(account)
    removed = False
    if keyring is not None:
        try:
            keyring.delete_password(SERVICE_NAME, _keyring_account(safe))
            removed = True
        except (KeyringError, NoKeyringError):
            pass
    path = _session_path(safe)
    if path.exists():
        path.unlink()
        removed = True
    return removed


def inspect_storage(account: str) -> dict[str, Any]:
    safe = secure_account_name(account)
    path = _session_path(safe)
    return {
        "account": safe,
        "keyring_present": _read_keyring(safe) is not None,
        "encrypted_file_present": path.exists(),
        "encrypted_file": str(path),
        "encrypted_file_mode": oct(path.stat().st_mode & 0o777) if path.exists() else None,
    }

