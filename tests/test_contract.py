from __future__ import annotations

import ast
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import telegram_ro_common


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "telegram_mcp_server.py"


class ReadOnlyContractTests(unittest.TestCase):
    def test_exactly_three_mcp_tools_are_exposed(self) -> None:
        tree = ast.parse(SERVER.read_text(encoding="utf-8"))
        tools = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                target = decorator.func
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "mcp"
                    and target.attr == "tool"
                ):
                    tools.add(node.name)

        self.assertEqual(tools, {"list_chats", "read_chat", "search_chat"})

    def test_no_telegram_write_methods_are_referenced(self) -> None:
        denied = {
            "send_message",
            "send_file",
            "edit_message",
            "delete_messages",
            "delete_dialog",
            "forward_messages",
            "upload_file",
        }
        found = set()
        for path in (ROOT / "telegram_mcp_server.py", ROOT / "telegram_ro_common.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr in denied:
                    found.add(node.attr)
        self.assertEqual(found, set())

    def test_server_is_stdio_only(self) -> None:
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn('mcp.run(transport="stdio")', source)
        self.assertNotIn("streamable-http", source)
        self.assertNotIn('transport="sse"', source)

    def test_account_name_stays_inside_session_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "TELEGRAM_API_ID": "12345",
                "TELEGRAM_API_HASH": "0123456789abcdef0123456789abcdef",
                "TELEGRAM_SESSION_DIR": tmp,
            }
            with patch.dict(os.environ, env, clear=False):
                _, _, session_path = telegram_ro_common.load_settings("../Work Account")

            self.assertEqual(session_path.parent.resolve(), Path(tmp).resolve())
            self.assertEqual(session_path.name, ".._Work_Account.session")

    def test_dot_only_account_uses_safe_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "TELEGRAM_API_ID": "12345",
                "TELEGRAM_API_HASH": "0123456789abcdef0123456789abcdef",
                "TELEGRAM_SESSION_DIR": tmp,
            }
            with patch.dict(os.environ, env, clear=False):
                _, _, session_path = telegram_ro_common.load_settings("..")

            self.assertEqual(session_path.name, "user.session")


if __name__ == "__main__":
    unittest.main()
