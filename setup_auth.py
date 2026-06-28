#!/usr/bin/env python3
"""One-time local OAuth setup. Run this ONCE on your own machine to mint a
refresh token that the deployed server uses to act on your Google account.

Prerequisites:
  1. A Google Cloud project with the Google Docs API enabled.
  2. An OAuth 2.0 Client ID of type "Desktop app". Download its JSON and save it
     next to this file as `client_secret.json`.
  3. pip install -r requirements.txt

Usage:
    python setup_auth.py

A browser window opens for you to grant access. On success it prints the three
values you set as env vars (locally in .env, or in the Render dashboard):
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN.
"""

import os
import sys

# Make src/config.py importable so scopes stay in one place.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from config import SCOPES  # noqa: E402

from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402

CLIENT_SECRET_FILE = "client_secret.json"


def main() -> None:
    if not os.path.exists(CLIENT_SECRET_FILE):
        sys.exit(
            f"'{CLIENT_SECRET_FILE}' not found. Download your OAuth Desktop "
            "client JSON from Google Cloud Console > Credentials and save it "
            "here with that name."
        )

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    # access_type=offline + prompt=consent guarantees a refresh_token is returned.
    creds = flow.run_local_server(
        port=0, access_type="offline", prompt="consent"
    )

    if not creds.refresh_token:
        sys.exit(
            "No refresh token returned. Revoke the app's access at "
            "https://myaccount.google.com/permissions and run this again."
        )

    print("\n" + "=" * 70)
    print("SUCCESS — set these as environment variables (Render or .env):")
    print("=" * 70)
    print(f"GOOGLE_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print("=" * 70)
    print("Keep these secret. Do NOT commit them to git.\n")


if __name__ == "__main__":
    main()
