# Poke ↔ Google Workspace MCP

A remote [MCP](https://modelcontextprotocol.io) server that lets your
[Poke](https://poke.com) agent **create and edit Google Docs, browse Google
Drive, and read/write Google Sheets**. Built with Python +
[FastMCP](https://github.com/jlowin/fastmcp), deployable to Render in a few
minutes, and structured so you can extend it to Slides, Gmail, and other Google
APIs.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/niharxavier/poke-google-docs-mcp)

> **Auth model:** single-tenant per deployment. You (or anyone who forks this)
> bring your *own* Google OAuth client and mint your *own* refresh token. There's
> no shared multi-user server to run — clone it, plug in your credentials, deploy.

## Tools

### Google Docs

| Tool | What it does |
|------|--------------|
| `create_document(title, content="")` | Create a new Doc, optionally with starting text. Returns its ID + edit URL. |
| `read_document(document_id)` | Return the document's title and plain-text body. |
| `append_text(document_id, text)` | Add text to the end of a Doc. |
| `insert_text(document_id, text, index=1)` | Insert text at a character index (1 = start). |
| `replace_text(document_id, find, replace, match_case=False)` | Find & replace all occurrences. |

### Google Drive

| Tool | What it does |
|------|--------------|
| `list_files(name_contains="", file_type="", max_results=20)` | List files newest-first. `file_type` ∈ `doc`, `sheet`, `slide`, `folder`, `pdf` (empty = all). Read-only — sees everything in your Drive. |
| `delete_file(file_id)` | Move a file to the Drive **Trash** (recoverable ~30 days). Limited to files this server created (see [security notes](#how-it-works--security-notes)). |

### Google Sheets

| Tool | What it does |
|------|--------------|
| `create_spreadsheet(title)` | Create a new Sheet. Returns its ID + edit URL. |
| `read_values(spreadsheet_id, range_a1="A1:Z1000")` | Read a range as rows of cell values. |
| `write_values(spreadsheet_id, range_a1, values)` | Overwrite a range with rows, e.g. `[["Name","Age"],["Alex","30"]]`. |
| `append_values(spreadsheet_id, values, range_a1="A1")` | Append rows after the last row of data. |

> **IDs** are the long string in the file's URL:
> Docs `docs.google.com/document/d/`**`ID`**`/edit` ·
> Sheets `docs.google.com/spreadsheets/d/`**`ID`**`/edit`. Drive `file_id`s are
> returned by `list_files`. Sheets ranges use A1 notation, e.g. `Sheet1!A1:C10`.

---

## Setup

There are five one-time steps: **(1)** create Google OAuth credentials,
**(2)** enable the Google APIs, **(3)** mint a refresh token, **(4)** generate an
API key, **(5)** deploy & connect. The whole flow looks like this:

```
You (Google Cloud)                    Render (your server)            Poke
─────────────────────                 ────────────────────           ────────
client_secret.json  ─┐
setup_auth.py       ─┼─▶ GOOGLE_CLIENT_ID / SECRET / REFRESH_TOKEN ─▶ env vars ─┐
secrets.token_urlsafe ─▶ MCP_API_KEY ──────────────────────────────▶ env var  ─┤
                                            │                                    │
                                  https://<svc>.onrender.com/mcp ◀── URL + key ──┘
                                            │
                                            ▼
                                   Google Docs / Drive / Sheets APIs
```

### 1. Google Cloud: create OAuth credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create
   (or pick) a project.
2. **APIs & Services → OAuth consent screen:**
   - User type: **External**.
   - Fill in app name + your email.
   - Under **Test users**, add your own Google address. (In "Testing" mode the
     refresh token works indefinitely for test users.)
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID:**
   - Application type: **Desktop app**.
   - Download the JSON, rename it to `client_secret.json`, and put it in this
     project's root folder.

### 2. Enable the Google APIs

**APIs & Services → Library →** enable each API this server uses:

- **Google Docs API**
- **Google Drive API**
- **Google Sheets API**

> If you skip one, its tools will fail at call time with a "has not been used /
> is disabled" error. Enable only what you need — but the scopes in
> `src/config.py` must match the APIs you enable.

### 3. Mint your refresh token (one time, local)

```bash
pip install -r requirements.txt
python setup_auth.py
```

A browser opens — sign in and approve. **You'll be asked to grant Docs, Drive,
and Sheets access** (these come from the scopes in `src/config.py`). The script
prints:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
```

Keep these secret.

> **Adding/removing a service later changes the scopes**, so you must **re-run
> `python setup_auth.py`** to mint a fresh token and **update `GOOGLE_REFRESH_TOKEN`
> everywhere** (your `.env` *and* Render's Environment tab). An old token keeps
> its old permissions.

### 4. Generate an API key for Poke

This protects your public server URL so only Poke can use it:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save the output as `MCP_API_KEY`.

### 5. Deploy to Render

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

> `render.yaml` sets `autoDeploy: true`, so pushes to `main` redeploy
> automatically. (Render reads the blueprint when the service is created; for an
> existing service, also flip **Settings → Build & Deploy → Auto-Deploy → Yes**
> once.) Updating an env var also triggers a redeploy.

> Render's free tier sleeps when idle, so the first request after a pause has a
> cold-start delay of ~30s. Upgrade the plan if that bothers you.

### 6. Connect it to Poke

In Poke → **Settings → Integrations → Connect MCP** (or
[poke.com/settings/connections](https://poke.com/settings/connections)):

- **URL:** `https://<your-service>.onrender.com/mcp`
  — ⚠️ **the `/mcp` suffix is required.** The bare domain
  (`https://<your-service>.onrender.com`) has nothing listening on it and Poke
  will reject it with *"Invalid MCP server URL."*
- **API Key:** the `MCP_API_KEY` from step 4.

Then ask Poke something like:
- *"Create a Google Doc called 'Weekly Plan' with three bullet points."*
- *"List my Google Sheets."*
- *"Make a spreadsheet 'Budget' and add rows for rent, food, and transport."*

---

## Troubleshooting

**Poke says "Invalid MCP server URL. Please check your URL and try again."**
You almost certainly left off the `/mcp` path. Use
`https://<your-service>.onrender.com/mcp`, not the bare domain.

**A tool fails with "Unauthorized: missing or invalid API key."**
The `MCP_API_KEY` in Poke doesn't match the one in Render's Environment tab.
Re-copy it (no stray spaces) and save.

**A tool fails with a Google "API has not been used / is disabled" error.**
You didn't enable that API in step 2 (e.g. Sheets API for spreadsheet tools).

**A tool fails with a permission/insufficient-scope error.**
Your refresh token predates a scope change. Re-run `python setup_auth.py` and
update `GOOGLE_REFRESH_TOKEN` in `.env` and Render (see step 3's note).

**`delete_file` says it can only delete files it created.**
That's by design — the `drive.file` scope only permits deleting files this server
made. Delete others from Google Drive directly.

**Verify the server yourself** (replace the URL and key). A `GET` returns
`405 Method Not Allowed` — that's *correct*, MCP only accepts `POST`:

```bash
# Should print: HTTP 405, allow: POST, DELETE
curl -i https://<your-service>.onrender.com/mcp

# Full handshake — should return HTTP 200 and serverInfo "Google Workspace MCP":
curl -i -X POST https://<your-service>.onrender.com/mcp \
  -H "Authorization: Bearer <MCP_API_KEY>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

- `404` on the root (`/`) is normal — only `/mcp` is mounted.
- The `initialize` handshake does **not** check the API key; auth is enforced when
  a tool actually runs. So a green handshake doesn't prove your key works — test a
  real tool call.
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

## Extending to Slides, Gmail, etc.

The codebase is built for this — each Google service is one module with a
`register_<service>_tools(mcp)` function. To add a service:

1. **Add the scope** in `src/config.py` and **re-run `python setup_auth.py`** to
   mint a token with the new permission (then update `GOOGLE_REFRESH_TOKEN`).
2. **Enable the API** in Google Cloud (step 2 above).
3. **Add a client helper** in `src/google_client.py`:
   ```python
   def slides_service():
       return get_service("slides", "v1")
   ```
4. **Create `src/tools/<service>.py`** (copy `docs.py`, `drive.py`, or `sheets.py`
   as a template) with a `register_<service>_tools(mcp)` and your `@mcp.tool()`
   functions.
5. **Register it** in `src/server.py`:
   ```python
   from tools.slides import register_slides_tools
   register_slides_tools(mcp)
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
  access tokens automatically by `google-auth`. The token's power is bounded by
  the scopes in `src/config.py`:
  - `documents` + `spreadsheets` — full read/write on Docs and Sheets.
  - `drive.metadata.readonly` — list/search **all** files, but metadata only.
  - `drive.file` — create/modify/delete **only files this app created or opened**.
    This is why `delete_file` can't touch unrelated files in your Drive — a
    deliberately conservative default.
- Secrets live in env vars only. `.gitignore` excludes `.env`, `client_secret.json`,
  and `token.json` so they never reach git.

## Project layout

```
setup_auth.py          # one-time: mint your refresh token
render.yaml            # Render deploy config (autoDeploy on)
requirements.txt
.env.example
src/
  server.py            # FastMCP app + HTTP transport; registers tool modules
  config.py            # OAuth scopes (single source of truth)
  auth.py              # Bearer-token check for the MCP server (@require_auth)
  google_client.py     # builds cached, auto-refreshing Google API clients
  tools/
    docs.py            # Google Docs tools
    drive.py           # Google Drive tools (list / delete)
    sheets.py          # Google Sheets tools
```
