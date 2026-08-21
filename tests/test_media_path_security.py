from pathlib import Path

import pytest

from telegram_mcp.tools.write import _upload_path


def test_upload_requires_explicit_root(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("TELEGRAM_MCP_UPLOAD_DIR", raising=False)
    with pytest.raises(RuntimeError, match="UPLOAD_DIR"):
        _upload_path(str(tmp_path / "file.txt"))


def test_upload_path_must_stay_inside_root(monkeypatch, tmp_path: Path):
    root = tmp_path / "allowed"
    root.mkdir()
    inside = root / "file.txt"
    inside.write_text("ok", encoding="utf-8")
    outside = tmp_path / "secret.txt"
    outside.write_text("no", encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_MCP_UPLOAD_DIR", str(root))
    assert _upload_path(str(inside)) == inside.resolve()
    with pytest.raises(ValueError, match="must stay inside"):
        _upload_path(str(outside))

