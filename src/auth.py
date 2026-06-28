"""Bearer-token auth for the MCP server itself.

Poke sends `Authorization: Bearer <MCP_API_KEY>` on every request. We validate
it here. If MCP_API_KEY is unset, auth is disabled (handy for local dev, but do
NOT do that on a public deployment — the server can edit your Google Docs).
"""

import functools
import os
import secrets

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers


def _check_api_key() -> None:
    expected = os.environ.get("MCP_API_KEY")
    if not expected:
        return  # auth disabled

    # NOTE: get_http_headers() strips "authorization" by default (it's on
    # FastMCP's exclude list to avoid forwarding creds downstream), so we must
    # opt it back in explicitly or every authed tool call sees an empty header.
    headers = get_http_headers(include={"authorization"})  # lowercased names
    value = headers.get("authorization", "")
    token = value[7:].strip() if value.lower().startswith("bearer ") else ""

    if not (token and secrets.compare_digest(token, expected)):
        raise ToolError("Unauthorized: missing or invalid API key.")


def require_auth(fn):
    """Decorator that enforces the Bearer token before a tool runs.

    Apply it *under* @mcp.tool() so FastMCP still sees the original signature:

        @mcp.tool()
        @require_auth
        def my_tool(...): ...
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        _check_api_key()
        return fn(*args, **kwargs)

    return wrapper
