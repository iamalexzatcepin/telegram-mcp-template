import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "codex-plugin" / "telegram-mcp"


def test_plugin_manifest_and_runtime_are_self_contained():
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    mcp = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["telegram_local"]
    assert manifest["name"] == "telegram-mcp"
    assert manifest["version"] == "2.0.0"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert server["type"] == "stdio"
    assert server["command"] == "uv"
    assert server["args"][:3] == ["run", "--project", "./mcp_server"]
    assert (PLUGIN / "mcp_server" / "pyproject.toml").is_file()
    assert (PLUGIN / "mcp_server" / "uv.lock").is_file()


def test_plugin_skills_have_no_scaffold_placeholders():
    skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
    assert {path.parent.name for path in skills} == {
        "telegram", "telegram-setup", "telegram-read", "telegram-send", "telegram-manage"
    }
    assert all("TODO" not in path.read_text(encoding="utf-8") for path in skills)

