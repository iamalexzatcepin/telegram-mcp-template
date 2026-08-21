import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "codex-plugin" / "telegram-mcp"


def test_plugin_manifest_and_runtime_are_self_contained():
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    mcp = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["telegram"]
    assert manifest["name"] == "telegram-mcp"
    assert manifest["version"] == "2.0.0"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["interface"]["displayName"] == "Telegram"
    assert manifest["interface"]["composerIcon"] == "./assets/telegram-logo.svg"
    assert (PLUGIN / "assets" / "telegram-logo.svg").is_file()
    assert server["type"] == "stdio"
    assert server["command"] == "uv"
    assert server["args"][:3] == ["run", "--project", "./mcp_server"]
    assert (PLUGIN / "mcp_server" / "pyproject.toml").is_file()
    assert (PLUGIN / "mcp_server" / "uv.lock").is_file()


def test_plugin_skills_have_no_scaffold_placeholders():
    skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
    assert {path.parent.name for path in skills} == {
        "telegram",
        "telegram-chtenie",
        "telegram-otpravka",
        "telegram-upravlenie",
        "telegram-nastroika",
    }
    assert all("TODO" not in path.read_text(encoding="utf-8") for path in skills)

    for skill_file in skills:
        skill_dir = skill_file.parent
        ui = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
        assert 'icon_small: "./assets/telegram-logo.svg"' in ui
        assert 'icon_large: "./assets/telegram-logo.svg"' in ui
        assert (skill_dir / "assets" / "telegram-logo.svg").is_file()


def test_plugin_ui_is_russian_and_old_english_commands_are_absent():
    manifest_text = (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    assert "Чтение" in manifest_text
    assert "Отправка" in manifest_text

    skill_names = {path.name for path in (PLUGIN / "skills").iterdir() if path.is_dir()}
    assert not {"telegram-read", "telegram-send", "telegram-manage", "telegram-setup"} & skill_names
