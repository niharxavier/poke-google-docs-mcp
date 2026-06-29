"""Google Sheets tools: create spreadsheets and read/write cell values.

Cell values use A1 notation for ranges (e.g. "Sheet1!A1:C10"). Writes use
USER_ENTERED so "123" becomes a number and "=A1+B1" becomes a formula, matching
how a person typing into the grid would expect it to behave.
"""

from fastmcp.exceptions import ToolError
from googleapiclient.errors import HttpError

from auth import require_auth
from google_client import sheets_service

SHEET_URL = "https://docs.google.com/spreadsheets/d/{}/edit"


def register_sheets_tools(mcp) -> None:
    @mcp.tool()
    @require_auth
    def create_spreadsheet(title: str) -> dict:
        """Create a new Google Sheet owned by the connected account.

        Args:
            title: The title of the new spreadsheet.

        Returns the spreadsheet_id and a shareable edit URL.
        """
        try:
            ss = (
                sheets_service()
                .spreadsheets()
                .create(body={"properties": {"title": title}})
                .execute()
            )
        except HttpError as e:
            raise ToolError(f"Failed to create spreadsheet: {e}") from e
        sid = ss["spreadsheetId"]
        return {"spreadsheet_id": sid, "title": title, "url": SHEET_URL.format(sid)}

    @mcp.tool()
    @require_auth
    def read_values(spreadsheet_id: str, range_a1: str = "A1:Z1000") -> dict:
        """Read cell values from a range of a Google Sheet.

        Args:
            spreadsheet_id: The spreadsheet ID (the long string in its URL).
            range_a1: A1-notation range, e.g. "Sheet1!A1:C10" or "A1:Z1000".

        Returns a list of rows; each row is a list of cell values.
        """
        try:
            resp = (
                sheets_service()
                .spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_a1)
                .execute()
            )
        except HttpError as e:
            raise ToolError(f"Could not read spreadsheet {spreadsheet_id}: {e}") from e
        return {
            "spreadsheet_id": spreadsheet_id,
            "range": resp.get("range", range_a1),
            "values": resp.get("values", []),
        }

    @mcp.tool()
    @require_auth
    def write_values(
        spreadsheet_id: str, range_a1: str, values: list[list[str]]
    ) -> dict:
        """Overwrite a range of a Google Sheet with rows of values.

        Args:
            spreadsheet_id: The spreadsheet ID.
            range_a1: A1-notation top-left anchor / range, e.g. "Sheet1!A1".
            values: Rows of cell values, e.g. [["Name","Age"],["Alex","30"]].
        """
        try:
            resp = (
                sheets_service()
                .spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_a1,
                    valueInputOption="USER_ENTERED",
                    body={"values": values},
                )
                .execute()
            )
        except HttpError as e:
            raise ToolError(f"Failed to write to spreadsheet: {e}") from e
        return {
            "spreadsheet_id": spreadsheet_id,
            "updated_cells": resp.get("updatedCells", 0),
            "url": SHEET_URL.format(spreadsheet_id),
        }

    @mcp.tool()
    @require_auth
    def append_values(
        spreadsheet_id: str, values: list[list[str]], range_a1: str = "A1"
    ) -> dict:
        """Append rows after the last row of data in a Google Sheet.

        Args:
            spreadsheet_id: The spreadsheet ID.
            values: Rows of cell values to add, e.g. [["Alex","30"]].
            range_a1: A1-notation range identifying the table to append to
                (defaults to "A1", i.e. the first sheet).
        """
        try:
            resp = (
                sheets_service()
                .spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_a1,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": values},
                )
                .execute()
            )
        except HttpError as e:
            raise ToolError(f"Failed to append to spreadsheet: {e}") from e
        updates = resp.get("updates", {})
        return {
            "spreadsheet_id": spreadsheet_id,
            "updated_cells": updates.get("updatedCells", 0),
            "url": SHEET_URL.format(spreadsheet_id),
        }
