import json
from pathlib import Path

import pytest

from telegram_mcp.config import AppConfig, ConfigError, load_config, resolve_account, save_config, secure_account_name


@pytest.mark.parametrize("value", ["..", ".", "@@@", "   "])
def test_empty_or_path_only_account_name_is_rejected(value):
    with pytest.raises(ConfigError):
        secure_account_name(value)


def test_account_name_is_confined():
    assert secure_account_name("../work") == "work"


def test_config_write_is_owner_only_and_round_trips(tmp_path: Path):
    path = tmp_path / "nested" / "config.json"
    config = AppConfig(profile="custom", capabilities=("read",), accounts=("work",))
    save_config(config, path)
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert load_config(path) == config.normalized()


def test_symlinked_config_is_rejected(tmp_path: Path):
    real = tmp_path / "real.json"
    real.write_text(json.dumps({"profile": "read-only"}), encoding="utf-8")
    link = tmp_path / "config.json"
    link.symlink_to(real)
    with pytest.raises(ConfigError, match="symlinked"):
        load_config(link)


def test_unknown_capability_fails_closed():
    with pytest.raises(ConfigError, match="Unknown capabilities"):
        AppConfig(profile="custom", capabilities=("root-everything",)).resolved_capabilities()


def test_omitted_account_resolves_to_wizard_default(monkeypatch, tmp_path: Path):
    path = tmp_path / "config.json"
    save_config(AppConfig(default_account="work", accounts=("work", "personal")), path)
    monkeypatch.setenv("TELEGRAM_MCP_CONFIG", str(path))
    assert resolve_account(None) == "work"
    assert resolve_account("personal") == "personal"
