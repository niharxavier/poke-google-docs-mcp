#!/usr/bin/env python3
"""Poke <-> Google Docs MCP server.

Runs as a remote, streamable-HTTP MCP server (the transport Poke connects to).
Endpoint: http://<host>:<port>/mcp

Add more Google services by importing and calling their register_*_tools()
function below (see src/tools/docs.py for the pattern).
"""

import os

from fastmcp import FastMCP

from tools.docs import register_docs_tools

mcp = FastMCP("Google Docs MCP")

register_docs_tools(mcp)
# To extend, e.g.:
#   from tools.sheets import register_sheets_tools
#   register_sheets_tools(mcp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        stateless_http=True,  # Poke connects statelessly per request
    )
