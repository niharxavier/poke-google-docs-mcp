# Poke ↔ Google Docs MCP

A remote [MCP](https://modelcontextprotocol.io) server that lets your
[Poke](https://poke.com) agent **create and edit Google Docs**. Built with
Python + [FastMCP](https://github.com/jlowin/fastmcp), deployable to Render in a
few minutes, and structured so you can extend it to Sheets, Drive, and other
Google APIs.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/niharxavier/poke-google-docs-mcp)

> **Auth model:** single-tenant per deployment. You (or anyone who forks this)
> bring your *own* Google OAuth client and mint your *own* refresh token. There's
> no shared multi-user server to run — clone it, plug in your credentials, deploy.

## Tools

| Tool | What it does |
|------|--------------|
| `create_document(title, content="")` | Create a new Doc, optionally with starting text. Returns its ID + edit URL. |
| `read_document(document_id)` | Return the document's title and plain-text body. |
| `append_text(document_id, text)` | Add text to the end of a Doc. |
| `insert_text(document_id, text, index=1)` | Insert text at a character index (1 = start). |
| `replace_text(document_id, find, replace, match_case=False)` | Find & replace all occurrences. |

A document ID is the long string in a Doc's URL:
`https://docs.google.com/document/d/`**`THIS_PART`**`/edit`.

---

## Setup

### 1. Google Cloud: create OAuth credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create
   (or pick) a project.
2. **APIs & Services → Library →** enable the **Google Docs API**.
   *(Enable Google Sheets API / Google Drive API here too if you extend later.)*
3. **APIs & Services → OAuth consent screen:**
   - User type: **External**.
   - Fill in app name + your email.
   - Under **Test users**, add your own Google address. (In "Testing" mode the
     refresh token works indefinitely for test users.)
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID:**
   - Application type: **Desktop app**.
   - Download the JSON, rename it to `client_secret.json`, and put it in this
     project's root folder.

### 2. Mint your refresh token (one time, local)

```bash
pip install -r requirements.txt
python setup_auth.py
```

A browser opens — sign in and approve. The script prints:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
```

Keep these secret.

### 3. Generate an API key for Poke

This protects your public server URL so only Poke can use it:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save the output as `MCP_API_KEY`.

### 4. Deploy to Render

Fork this repo first (so the env vars are yours), then click the button on your
fork's README — or do it manually:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/niharxavier/poke-google-docs-mcp)

1. Push this repo to your own GitHub.
2. In [Render](https://render.com): **New → Blueprint** (it auto-detects
   `render.yaml`) or **New → Web Service**, and connect your repo.
3. Add these environment variables (Environment tab):
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`
   - `MCP_API_KEY`
4. Deploy. Your server is at `https://<your-service>.onrender.com/mcp`.

> Render's free tier sleeps when idle, so the first request after a pause has a
> cold-start delay of ~30s. Upgrade the plan if that bothers you.

### 5. Connect it to Poke

In Poke → **Settings → Integrations → Connect MCP** (or
[poke.com/settings/connections](https://poke.com/settings/connections)):

- **URL:** `https://<your-service>.onrender.com/mcp`
  — ⚠️ **the `/mcp` suffix is required.** The bare domain
  (`https://<your-service>.onrender.com`) has nothing listening on it and Poke
  will reject it with *"Invalid MCP server URL."*
- **API Key:** the `MCP_API_KEY` from step 3.

Then ask Poke something like:
*"Create a Google Doc called 'Weekly Plan' and add a heading and three bullet points."*

---

## Troubleshooting

**Poke says "Invalid MCP server URL. Please check your URL and try again."**
You almost certainly left off the `/mcp` path. Use
`https://<your-service>.onrender.com/mcp`, not the bare domain.

**Verify the server yourself** (replace the URL and key). A `GET` returns
`405 Method Not Allowed` — that's *correct*, MCP only accepts `POST`:

```bash
# Should print: HTTP 405, allow: POST, DELETE
curl -i https://<your-service>.onrender.com/mcp

# Full handshake — should return HTTP 200 and serverInfo "Google Docs MCP":
curl -i -X POST https://<your-service>.onrender.com/mcp \
  -H "Authorization: Bearer <MCP_API_KEY>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

- `404` on the root (`/`) is normal — only `/mcp` is mounted.
- `401`/auth errors → the `Authorization: Bearer` key doesn't match the
  `MCP_API_KEY` set in Render's Environment tab.
- First request after the server's been idle takes ~30s (free-tier cold start);
  retry if Poke times out.
- If the handshake fails entirely, check the Render dashboard: the latest deploy
  should be **Live** and all 4 env vars must be set.

---

## Run locally

```bash
cp .env.example .env        # fill in the values from setup_auth.py
# load .env into your shell, then:
python src/server.py        # serves http://localhost:8000/mcp
```

To expose a local server to Poke for testing, tunnel it with e.g.
[`ngrok http 8000`](https://ngrok.com) and give Poke the `https://…/mcp` URL.

---

## Extending to Sheets, Drive, etc.

The codebase is built for this:

1. **Add the scope** in `src/config.py` (e.g. uncomment the Sheets scope) and
   **re-run `python setup_auth.py`** to get a token with the new permission.
2. **Enable the API** in Google Cloud (e.g. Google Sheets API).
3. **Add a client helper** in `src/google_client.py`:
   ```python
   def sheets_service():
       return get_service("sheets", "v4")
   ```
4. **Copy `src/tools/docs.py` → `src/tools/sheets.py`**, write a
   `register_sheets_tools(mcp)` with your new `@mcp.tool()` functions.
5. **Register it** in `src/server.py`:
   ```python
   from tools.sheets import register_sheets_tools
   register_sheets_tools(mcp)
   ```

Every tool just needs the `@require_auth` decorator (under `@mcp.tool()`) to stay
protected by your API key.

---

## How it works / security notes

- **Transport:** streamable HTTP at `/mcp`, stateless — the format Poke expects.
- **MCP auth:** every tool checks `Authorization: Bearer <MCP_API_KEY>` via the
  `@require_auth` decorator. If `MCP_API_KEY` is unset, auth is disabled — only do
  that locally.
- **Google auth:** a long-lived refresh token (yours) is exchanged for short-lived
  access tokens automatically by `google-auth`.
- Secrets live in env vars only. `.gitignore` excludes `.env`, `client_secret.json`,
  and `token.json` so they never reach git.

## Project layout

```
setup_auth.py          # one-time: mint your refresh token
render.yaml            # Render deploy config
requirements.txt
.env.example
src/
  server.py            # FastMCP app + HTTP transport; registers tool modules
  config.py            # OAuth scopes (single source of truth)
  auth.py              # Bearer-token check for the MCP server (@require_auth)
  google_client.py     # builds cached, auto-refreshing Google API clients
  tools/
    docs.py            # Google Docs tools  (template for new services)
```
