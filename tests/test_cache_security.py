from pathlib import Path

import pytest

from telegram_mcp import cache


def test_plain_cache_is_account_scoped_and_owner_only(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TELEGRAM_MCP_CONFIG_DIR", str(tmp_path))
    connection = cache.connect_cache("work")
    connection.close()
    path = tmp_path / "cache" / "work.db"
    assert path.exists()
    assert path.stat().st_mode & 0o777 == 0o600


def test_encrypted_cache_fails_closed_without_sqlcipher(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TELEGRAM_MCP_CONFIG_DIR", str(tmp_path))

    def missing(_name):
        raise ImportError

    monkeypatch.setattr(cache.importlib, "import_module", missing)
    with pytest.raises(cache.CacheError, match="refusing plaintext fallback"):
        cache.connect_cache("work", encrypted=True, key="secret")
    assert not (tmp_path / "cache" / "work.db").exists()

