"""Central config shared by the server and the one-time auth setup script.

Google OAuth scopes. These define what the refresh token is allowed to do.
If you change this list, you MUST re-run `python setup_auth.py` to mint a new
refresh token with the updated scopes.

To extend this MCP to other Google services, uncomment / add the scope here,
enable the matching API in Google Cloud, then register a new tool module in
src/server.py (see src/tools/docs.py as the template).
"""

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    # Google Sheets:  "https://www.googleapis.com/auth/spreadsheets",
    # Google Drive (only files this app creates/opens):
    #                 "https://www.googleapis.com/auth/drive.file",
]
