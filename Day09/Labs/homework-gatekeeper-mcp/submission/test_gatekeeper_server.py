from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from fastmcp import Client


ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "gatekeeper_server.py"

sys.path.insert(0, str(ROOT.parent))

from gatekeeper_server import mcp


def report(label: str, ok: bool) -> None:
    print(f"{label}: {'PASS' if ok else 'FAIL'}")


def main() -> int:
    async def run_checks() -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()
            report("list_tools", any(tool.name == "route_ticket" for tool in tools) and any(tool.name == "needs_approval" for tool in tools))

            route_examples = [
                ("phishing email reported", "Security"),
                ("wifi is down in the office", "Network"),
                ("new keyboard needed", "Hardware"),
            ]
            for index, (text, expected) in enumerate(route_examples, start=1):
                result = await client.call_tool("route_ticket", {"text": text})
                report(f"route_ticket_{index}", result.content[0].text == expected)

            approval_examples = [
                (("search_kb", "EMP-1001", 10), True),
                (("get_ticket", "EMP-2000", 14), False),
                (("reset_password", "EMP-2000", 21), True),
            ]
            for index, ((action, user_id, hour), expected) in enumerate(approval_examples, start=1):
                result = await client.call_tool("needs_approval", {"action": action, "user_id": user_id, "hour": hour})
                report(f"needs_approval_{index}", result.content[0].text.lower() == str(expected).lower())

    asyncio.run(run_checks())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())