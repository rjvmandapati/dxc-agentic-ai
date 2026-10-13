from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gatekeeper import needs_approval as gatekeeper_needs_approval, route


mcp = FastMCP("AskIT Gatekeeper")


@mcp.tool(description="Route a ticket description to the correct support team.")
def route_ticket(text: str) -> str:
    return route(text)


@mcp.tool(description="Decide whether an action needs approval for a user at a given hour.")
def needs_approval(action: str, user_id: str, hour: int) -> bool:
    return bool(gatekeeper_needs_approval(action, user_id, hour)["approval"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true")
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="http", port=8778)
    else:
        mcp.run()


if __name__ == "__main__":
    main()