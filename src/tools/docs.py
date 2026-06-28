"""Google Docs tools.

This module is the template for extending the server: each Google service gets
a `register_<service>_tools(mcp)` function that defines its tools and is called
from src/server.py. To add Sheets, copy this file to sheets.py, swap the API
calls, add the scope in config.py, and register it in server.py.
"""

from fastmcp.exceptions import ToolError
from googleapiclient.errors import HttpError

from auth import require_auth
from google_client import docs_service

DOC_URL = "https://docs.google.com/document/d/{}/edit"


def _doc_url(document_id: str) -> str:
    return DOC_URL.format(document_id)


def _batch_update(document_id: str, requests: list) -> None:
    """Run a batchUpdate, surfacing Google errors as clean tool errors."""
    try:
        docs_service().documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()
    except HttpError as e:
        raise ToolError(f"Google Docs API error: {e}") from e


def _get_doc(document_id: str) -> dict:
    try:
        return docs_service().documents().get(documentId=document_id).execute()
    except HttpError as e:
        raise ToolError(f"Could not open document {document_id}: {e}") from e


def _extract_text(doc: dict) -> str:
    parts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for el in paragraph.get("elements", []):
            text_run = el.get("textRun")
            if text_run and "content" in text_run:
                parts.append(text_run["content"])
    return "".join(parts)


def _end_index(doc: dict) -> int:
    """Index just before the document's final newline — the safe append point."""
    content = doc.get("body", {}).get("content", [])
    if not content:
        return 1
    return max(content[-1].get("endIndex", 1) - 1, 1)


def register_docs_tools(mcp) -> None:
    @mcp.tool()
    @require_auth
    def create_document(title: str, content: str = "") -> dict:
        """Create a new Google Doc owned by the connected account.

        Args:
            title: The title of the new document.
            content: Optional initial text to insert into the body.

        Returns the document_id and a shareable edit URL.
        """
        try:
            doc = docs_service().documents().create(body={"title": title}).execute()
        except HttpError as e:
            raise ToolError(f"Failed to create document: {e}") from e

        document_id = doc["documentId"]
        if content:
            _batch_update(
                document_id,
                [{"insertText": {"location": {"index": 1}, "text": content}}],
            )
        return {
            "document_id": document_id,
            "title": title,
            "url": _doc_url(document_id),
        }

    @mcp.tool()
    @require_auth
    def read_document(document_id: str) -> dict:
        """Read the plain-text contents of a Google Doc.

        Args:
            document_id: The document ID (the long string in the doc's URL).
        """
        doc = _get_doc(document_id)
        return {
            "document_id": document_id,
            "title": doc.get("title", ""),
            "text": _extract_text(doc),
            "url": _doc_url(document_id),
        }

    @mcp.tool()
    @require_auth
    def append_text(document_id: str, text: str) -> dict:
        """Append text to the end of a Google Doc.

        Args:
            document_id: The document ID.
            text: Text to add. Include a leading "\\n" to start a new line.
        """
        doc = _get_doc(document_id)
        _batch_update(
            document_id,
            [{"insertText": {"location": {"index": _end_index(doc)}, "text": text}}],
        )
        return {"document_id": document_id, "status": "appended", "url": _doc_url(document_id)}

    @mcp.tool()
    @require_auth
    def insert_text(document_id: str, text: str, index: int = 1) -> dict:
        """Insert text at a specific character index in a Google Doc.

        Args:
            document_id: The document ID.
            text: Text to insert.
            index: Character index to insert at (1 = very start of the body).
        """
        _batch_update(
            document_id,
            [{"insertText": {"location": {"index": index}, "text": text}}],
        )
        return {"document_id": document_id, "status": "inserted", "url": _doc_url(document_id)}

    @mcp.tool()
    @require_auth
    def replace_text(
        document_id: str, find: str, replace: str, match_case: bool = False
    ) -> dict:
        """Find and replace all occurrences of a string in a Google Doc.

        Args:
            document_id: The document ID.
            find: The text to search for.
            replace: The text to replace it with.
            match_case: Whether the search is case-sensitive.
        """
        _batch_update(
            document_id,
            [
                {
                    "replaceAllText": {
                        "containsText": {"text": find, "matchCase": match_case},
                        "replaceText": replace,
                    }
                }
            ],
        )
        return {"document_id": document_id, "status": "replaced", "url": _doc_url(document_id)}
