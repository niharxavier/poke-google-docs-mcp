"""Builds authenticated Google API clients from a stored refresh token.

The access token is short-lived; google-auth refreshes it automatically in the
background using the refresh token + client credentials, so we can safely cache
the built service objects.
"""

import os
from functools import lru_cache

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import SCOPES

TOKEN_URI = "https://oauth2.googleapis.com/token"


def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "See README.md / .env.example for setup."
        )
    return val


def get_credentials() -> Credentials:
    return Credentials(
        token=None,  # forces a refresh on first use
        refresh_token=_require_env("GOOGLE_REFRESH_TOKEN"),
        client_id=_require_env("GOOGLE_CLIENT_ID"),
        client_secret=_require_env("GOOGLE_CLIENT_SECRET"),
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )


@lru_cache(maxsize=None)
def get_service(api_name: str, version: str):
    """Cached, auto-refreshing Google API client (e.g. get_service('docs','v1'))."""
    return build(
        api_name,
        version,
        credentials=get_credentials(),
        cache_discovery=False,
    )


def docs_service():
    return get_service("docs", "v1")


def drive_service():
    return get_service("drive", "v3")


def sheets_service():
    return get_service("sheets", "v4")
