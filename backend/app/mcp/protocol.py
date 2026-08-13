"""Small, client-neutral MCP JSON-RPC helpers shared by both servers."""

from __future__ import annotations

import json
from typing import Any

from fastapi.responses import JSONResponse

PROTOCOL_VERSION = "2025-06-18"
MAX_TOOL_RESULT_CHARS = 25_000


def jsonrpc_result(request_id: object, result: dict[str, Any], *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"jsonrpc": "2.0", "id": request_id, "result": result},
        headers={"MCP-Protocol-Version": PROTOCOL_VERSION},
    )


def jsonrpc_error(request_id: object, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}},
        headers={"MCP-Protocol-Version": PROTOCOL_VERSION},
    )


def tool_result(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    serialized = json.dumps(payload, separators=(",", ":"), default=str)
    if len(serialized) > MAX_TOOL_RESULT_CHARS:
        payload = {
            "error": "response_too_large",
            "message": f"Tool result exceeded the {MAX_TOOL_RESULT_CHARS}-character response bound.",
        }
        serialized = json.dumps(payload, separators=(",", ":"))
        is_error = True
    return {
        "content": [{"type": "text", "text": serialized}],
        "structuredContent": payload,
        "isError": is_error,
    }


def governed_tool(tool: dict[str, Any], governance: dict[str, str]) -> dict[str, Any]:
    read_only = bool(tool.pop("readOnly", True))
    return {
        **tool,
        "annotations": {
            "title": governance["title"],
            "readOnlyHint": read_only,
            "destructiveHint": False,
            "idempotentHint": read_only,
            "openWorldHint": False,
        },
        "_meta": {"epicenter/governance": governance},
    }
