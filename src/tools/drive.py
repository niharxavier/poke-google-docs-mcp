"""Google Drive tools: list and delete files (any type).

Listing uses the read-only metadata scope (sees every file in the Drive), while
deletion is limited by the drive.file scope to files THIS app created/opened —
so Poke can browse everything but can only remove files it made itself.
"""

from fastmcp.exceptions import ToolError
from googleapiclient.errors import HttpError

from auth import require_auth
from google_client import drive_service

# Friendly file_type aliases -> Google MIME types.
MIME_BY_TYPE = {
    "doc": "application/vnd.google-apps.document",
    "sheet": "application/vnd.google-apps.spreadsheet",
    "slide": "application/vnd.google-apps.presentation",
    "folder": "application/vnd.google-apps.folder",
    "pdf": "application/pdf",
}


def register_drive_tools(mcp) -> None:
    @mcp.tool()
    @require_auth
    def list_files(
        name_contains: str = "", file_type: str = "", max_results: int = 20
    ) -> dict:
        """List files in the connected account's Google Drive, newest first.

        Args:
            name_contains: Optional case-insensitive substring to filter names.
            file_type: Optional filter. One of: "doc", "sheet", "slide",
                "folder", "pdf". Empty means all file types.
            max_results: Maximum number of files to return (1-100).

        Returns each file's id, name, type (MIME), last-modified time, and a
        link to open it.
        """
        max_results = max(1, min(max_results, 100))
        query = ["trashed=false"]
        if file_type:
            mime = MIME_BY_TYPE.get(file_type.lower())
            if not mime:
                raise ToolError(
                    f"Unknown file_type '{file_type}'. Use one of: "
                    f"{', '.join(MIME_BY_TYPE)} (or leave empty for all)."
                )
            query.append(f"mimeType='{mime}'")
        if name_contains:
            escaped = name_contains.replace("\\", "\\\\").replace("'", "\\'")
            query.append(f"name contains '{escaped}'")
        try:
            resp = (
                drive_service()
                .files()
                .list(
                    q=" and ".join(query),
                    pageSize=max_results,
                    orderBy="modifiedTime desc",
                    fields="files(id,name,mimeType,modifiedTime,webViewLink)",
                )
                .execute()
            )
        except HttpError as e:
            raise ToolError(f"Failed to list files: {e}") from e

        files = [
            {
                "file_id": f["id"],
                "name": f.get("name", ""),
                "type": f.get("mimeType", ""),
                "modified_time": f.get("modifiedTime", ""),
                "url": f.get("webViewLink", ""),
            }
            for f in resp.get("files", [])
        ]
        return {"count": len(files), "files": files}

    @mcp.tool()
    @require_auth
    def delete_file(file_id: str) -> dict:
        """Move a file to the Drive trash.

        Only works on files this server created or opened (drive.file scope);
        deleting other files will fail with a permission error. The file goes to
        Trash and can be restored from Google Drive for ~30 days.

        Args:
            file_id: The Drive file ID (the long string in the file's URL).
        """
        try:
            drive_service().files().update(
                fileId=file_id, body={"trashed": True}
            ).execute()
        except HttpError as e:
            if e.resp.status in (403, 404):
                raise ToolError(
                    f"Cannot delete {file_id}: this server can only delete files "
                    "it created itself, or the file doesn't exist."
                ) from e
            raise ToolError(f"Failed to delete file: {e}") from e
        return {"file_id": file_id, "status": "trashed"}
