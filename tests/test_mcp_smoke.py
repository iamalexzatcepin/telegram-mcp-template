from __future__ import annotations

import sys
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parents[1]


class McpSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_server_initializes_and_lists_read_only_tools(self) -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(ROOT / "telegram_mcp_server.py")],
            cwd=str(ROOT),
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                response = await session.list_tools()

        self.assertEqual(
            {tool.name for tool in response.tools},
            {"list_chats", "read_chat", "search_chat"},
        )


if __name__ == "__main__":
    unittest.main()
