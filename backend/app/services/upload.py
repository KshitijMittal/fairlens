"""Upload guards — order matters per TRD §11.2.

1. Content-Length missing → 411
2. Content-Length > 50 MB → 413 without reading body
3. Streamed read capped at 50 MB regardless of header
4. Extension and magic-byte sniff → CSV, XLSX or 415
5. Row and column caps after parsing → 422 with specific limit
6. Parse failure → unsupported_file with human sentence
"""
import hashlib
import io
import logging
import mimetypes
from typing import BinaryIO

import openpyxl
import pandas as pd
from fastapi import HTTPException, Request, UploadFile

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_ROWS = 100_000
MAX_COLUMNS = 60

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",  # some clients send this for xlsx
}

CSV_SNIFF_BYTES = 8192


class UploadError(HTTPException):
    """Upload validation error with proper RFC 9457 code."""

    def __init__(self, code: str, title: str, detail: str, status: int):
        super().__init__(
            status_code=status,
            detail={
                "type": f"urn:fairlens:error:{code}",
                "title": title,
                "status": status,
                "detail": detail,
                "code": code,
            },
        )


async def validate_and_read_upload(
    request: Request, file: UploadFile, sheet: str | None = None
) -> tuple[bytes, str, pd.DataFrame, dict]:
    """
    Validate upload and return (file_bytes, file_type, frame, parse_metadata).

    file_type is "csv" or "xlsx". The frame is already parsed, so callers do not
    read the file twice. Raises UploadError on any validation failure.
    """
    # 1. Content-Length is required (411) and checked before reading (413).
    content_length = request.headers.get("content-length")
    if content_length is None:
        raise UploadError(
            "length_required",
            "Content-Length required",
            "The request must include a Content-Length header.",
            411,
        )
    try:
        cl = int(content_length)
    except ValueError:
        cl = None
    # Multipart framing adds a little over the file size; allow for it.
    if cl is not None and cl > MAX_FILE_SIZE + 64 * 1024:
        raise UploadError(
            "file_too_large",
            "File too large",
            f"The upload is {cl / (1024*1024):.1f} MB. The maximum file size is 50 MB.",
            413,
        )

    # 2. Streamed read capped at MAX_FILE_SIZE regardless of the header.
    chunks = []
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > MAX_FILE_SIZE:
            raise UploadError(
                "file_too_large",
                "File too large",
                "The file exceeds 50 MB.",
                413,
            )
        chunks.append(chunk)

    file_bytes = b"".join(chunks)

    if not file_bytes:
        raise UploadError(
            "unsupported_file",
            "Empty file",
            "The uploaded file is empty.",
            415,
        )

    # 3. Extension and magic-byte sniff
    filename = file.filename or ""
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    mime_type = file.content_type or mimetypes.guess_type(filename)[0] or ""

    file_type = _detect_file_type(file_bytes, ext, mime_type)

    # 4. Parse once with row/column limits
    frame, parse_meta = _read_table(file_bytes, file_type, sheet)

    # 5. Row and column caps
    if frame.shape[0] > MAX_ROWS:
        raise UploadError(
            "too_many_rows",
            "Too many rows",
            f"The file has {frame.shape[0]:,} rows. The maximum is {MAX_ROWS:,}. "
            "Split the file and analyse the parts.",
            422,
        )
    if frame.shape[1] > MAX_COLUMNS:
        raise UploadError(
            "too_many_columns",
            "Too many columns",
            f"The file has {frame.shape[1]} columns. The maximum is {MAX_COLUMNS}.",
            422,
        )
    if frame.shape[0] < 50:
        raise UploadError(
            "too_few_rows",
            "Too few rows",
            f"The file has {frame.shape[0]} rows. At least 50 rows are required.",
            422,
        )
    if frame.shape[1] < 2:
        raise UploadError(
            "too_few_columns",
            "Too few columns",
            f"The file has {frame.shape[1]} usable columns. At least 2 are required.",
            422,
        )

    return file_bytes, file_type, frame, parse_meta


def _detect_file_type(file_bytes: bytes, ext: str, mime_type: str) -> str:
    """Detect file type from extension, MIME, and magic bytes."""
    # Check extension first
    if ext in ALLOWED_EXTENSIONS:
        if ext == ".xlsx":
            return "xlsx"
        if ext == ".csv":
            return "csv"

    # Check MIME type
    if mime_type in ALLOWED_MIME_TYPES:
        if "spreadsheetml" in mime_type or "octet-stream" in mime_type:
            # Could be xlsx, check magic bytes
            if file_bytes[:4] == b"PK\x03\x04":  # ZIP signature (xlsx is a zip)
                return "xlsx"
        if mime_type == "text/csv":
            return "csv"

    # Check magic bytes
    if file_bytes[:4] == b"PK\x03\x04":
        return "xlsx"

    # Default to CSV for text-like content
    try:
        text = file_bytes[:CSV_SNIFF_BYTES].decode("utf-8")
        # Check if it looks like a CSV (has delimiters)
        if "," in text or ";" in text or "\t" in text:
            return "csv"
    except UnicodeDecodeError:
        pass

    raise UploadError(
        "unsupported_file",
        "Unsupported file type",
        "Only CSV and XLSX files are supported.",
        415,
    )


def _read_table(file_bytes: bytes, file_type: str,
                sheet_name: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Parse CSV or an XLSX sheet (the first unless named), with parse metadata."""
    if file_type == "csv":
        from app.services.parsing import ParseError, read_csv

        try:
            return read_csv(file_bytes)
        except ParseError as exc:
            raise UploadError("unsupported_file", "Could not parse CSV", str(exc), 415)

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
        if sheet_name is not None and sheet_name not in wb.sheetnames:
            raise UploadError(
                "unknown_sheet",
                "Sheet not found",
                f"The workbook has no sheet named '{sheet_name}'.",
                422,
            )
        sheet = wb[sheet_name] if sheet_name is not None else wb.worksheets[0]
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            raise UploadError(
                "unsupported_file",
                "Empty spreadsheet",
                "The spreadsheet has no data.",
                415,
            )
        headers = [str(h).strip().lower().replace(" ", "_") if h is not None else f"col_{i}"
                   for i, h in enumerate(rows[0])]
        frame = pd.DataFrame(rows[1:], columns=headers)
        frame = frame.drop(columns=[c for c in frame.columns if frame[c].isna().all()])
        return frame, {"encoding": "xlsx", "delimiter": "n/a",
                       "sheet": sheet.title, "sheet_names": wb.sheetnames}
    except UploadError:
        raise
    except Exception as exc:
        raise UploadError(
            "unsupported_file",
            "Could not parse XLSX",
            f"The file is not a valid Excel spreadsheet: {exc}",
            415,
        )


def compute_sha256(file_bytes: bytes) -> str:
    """Compute SHA-256 hex digest of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()