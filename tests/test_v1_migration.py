import os
from pathlib import Path

from telethon.crypto import AuthKey
from telethon.sessions import SQLiteSession

from telegram_mcp import session_store
from telegram_mcp.migration import migrate_v1


def test_v1_session_migrates_to_keyring_without_deleting_source(monkeypatch, tmp_path: Path):
    legacy = tmp_path / "legacy"
    sessions = legacy / "sessions"
    sessions.mkdir(parents=True)
    (legacy / ".env").write_text(
        "TELEGRAM_API_ID=12345\nTELEGRAM_API_HASH=0123456789abcdef0123456789abcdef\n",
        encoding="utf-8",
    )
    session_path = sessions / "default.session"
    sqlite = SQLiteSession(str(session_path))
    sqlite.set_dc(2, "149.154.167.40", 443)
    sqlite.auth_key = AuthKey(os.urandom(256))
    sqlite.save()
    sqlite.close()
    session_path.chmod(0o644)

    values = {}

    class MemoryKeyring:
        def set_password(self, service, account, value): values[(service, account)] = value
        def get_password(self, service, account): return values.get((service, account))
        def delete_password(self, service, account): values.pop((service, account), None)

    monkeypatch.setenv("TELEGRAM_MCP_CONFIG_DIR", str(tmp_path / "v2"))
    monkeypatch.setattr(session_store, "keyring", MemoryKeyring())
    result = migrate_v1(legacy)

    assert result["storage"] == "keyring"
    assert result["legacy_session_retained"] is True
    assert session_path.exists()
    assert session_path.stat().st_mode & 0o777 == 0o600
    stored = session_store.load_session("default")
    assert stored.api_id == 12345
    assert stored.session_string

