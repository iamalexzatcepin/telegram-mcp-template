from pathlib import Path

import pytest

from telegram_mcp import session_store
from telegram_mcp.session_store import SessionStoreError, StoredSession


class BrokenKeyring:
    def get_password(self, *_args):
        raise session_store.KeyringError("unavailable")

    def set_password(self, *_args):
        raise session_store.KeyringError("unavailable")

    def delete_password(self, *_args):
        raise session_store.KeyringError("unavailable")


def test_encrypted_fallback_is_atomic_owner_only_and_multi_account(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TELEGRAM_MCP_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(session_store, "keyring", BrokenKeyring())
    work = StoredSession(1, "hash-work", "session-work")
    personal = StoredSession(2, "hash-personal", "session-personal")
    assert session_store.save_session("work", work, master_key="correct horse") == "encrypted-file"
    assert session_store.save_session("personal", personal, master_key="correct horse") == "encrypted-file"
    assert session_store.load_session("work", master_key="correct horse") == work
    assert session_store.load_session("personal", master_key="correct horse") == personal
    paths = sorted((tmp_path / "sessions").glob("*.enc"))
    assert [path.name for path in paths] == ["personal.enc", "work.enc"]
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in paths)
    assert not list((tmp_path / "sessions").glob("*.tmp"))
    assert "session-work" not in (tmp_path / "sessions" / "work.enc").read_text(encoding="utf-8")


def test_wrong_fallback_key_is_rejected(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TELEGRAM_MCP_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(session_store, "keyring", BrokenKeyring())
    session_store.save_session("work", StoredSession(1, "h", "s"), master_key="right")
    with pytest.raises(SessionStoreError, match="could not be decrypted"):
        session_store.load_session("work", master_key="wrong")


def test_keyring_is_preferred(monkeypatch, tmp_path: Path):
    values = {}

    class MemoryKeyring:
        def set_password(self, service, account, value): values[(service, account)] = value
        def get_password(self, service, account): return values.get((service, account))
        def delete_password(self, service, account): values.pop((service, account), None)

    monkeypatch.setenv("TELEGRAM_MCP_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(session_store, "keyring", MemoryKeyring())
    record = StoredSession(1, "h", "s")
    assert session_store.save_session("work", record) == "keyring"
    assert session_store.load_session("work") == record
    assert not (tmp_path / "sessions" / "work.enc").exists()

