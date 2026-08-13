"""Verify both public MCP endpoints with the independent Python MCP client."""

from __future__ import annotations

import argparse
import asyncio
import os

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def verify(base_url: str, api_key: str | None) -> None:
    headers = {"X-MCP-API-Key": api_key} if api_key else {}
    timeout = httpx.Timeout(15.0)
    for path, expected_prefix in (
        ("/mcp/operations", "epicenter_"),
        ("/mcp/insurance-registry", "registry_"),
    ):
        async with httpx.AsyncClient(headers=headers, timeout=timeout) as http:
            async with streamable_http_client(f"{base_url.rstrip('/')}{path}", http_client=http) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=15)
                    tools = await asyncio.wait_for(session.list_tools(), timeout=15)
                    names = [tool.name for tool in tools.tools]
                    if not names or any(not name.startswith(expected_prefix) for name in names):
                        raise RuntimeError(f"Unexpected inventory from {path}: {names}")
                    print(f"{path}: initialized; {len(names)} bounded tools discovered")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default=os.getenv("EPICENTER_MCP_API_KEY"))
    args = parser.parse_args()
    asyncio.run(verify(args.base_url, args.api_key))


if __name__ == "__main__":
    main()
