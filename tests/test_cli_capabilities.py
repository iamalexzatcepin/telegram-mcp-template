from pathlib import Path

import pytest

from telegram_mcp.cli import main
from telegram_mcp.config import AppConfig, ConfigError, load_config, save_config


def test_enable_capability_preserves_profile_accounts_and_read_only_base(tmp_path: Path):
    path = tmp_path / "config.json"
    save_config(
        AppConfig(profile="read-only", accounts=("default", "work"), default_account="work"),
        path,
    )

    assert main(["capabilities", "enable", "schedule", "--config", str(path)]) == 0

    updated = load_config(path)
    assert updated.profile == "read-only"
    assert updated.accounts == ("default", "work")
    assert updated.default_account == "work"
    assert {"read", "search", "analysis", "schedule"} <= updated.resolved_capabilities()
    assert "write" not in updated.resolved_capabilities()
    assert path.stat().st_mode & 0o777 == 0o600


def test_disable_capability_removes_profile_capability_without_resetting_config(tmp_path: Path):
    path = tmp_path / "config.json"
    save_config(AppConfig(profile="assistant", accounts=("default",)), path)

    assert main(["capabilities", "disable", "schedule", "--config", str(path)]) == 0

    updated = load_config(path)
    assert "schedule" not in updated.resolved_capabilities()
    assert "write" in updated.resolved_capabilities()


def test_cache_cannot_be_enabled_without_explicit_storage_setup(tmp_path: Path):
    path = tmp_path / "config.json"
    save_config(AppConfig(), path)

    with pytest.raises(ConfigError, match="storage encryption"):
        main(["capabilities", "enable", "cache", "--config", str(path)])
