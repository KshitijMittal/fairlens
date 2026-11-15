"""Upload guards in TRD 11.2 order (F1-AC2, F12-AC4)."""
import io

import openpyxl
import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.services import upload
from app.services.upload import MAX_FILE_SIZE, UploadError, validate_and_read_upload


class _Request:
    def __init__(self, headers):
        self.headers = headers


def _file(data: bytes, filename: str, content_type: str) -> UploadFile:
    return UploadFile(io.BytesIO(data), filename=filename,
                      headers=Headers({"content-type": content_type}))


def _csv(rows: int = 60) -> bytes:
    return ("a,b\n" + "".join(f"{i},{i % 3}\n" for i in range(rows))).encode()


@pytest.mark.asyncio
async def test_missing_content_length_is_411():
    with pytest.raises(UploadError) as exc:
        await validate_and_read_upload(_Request({}), _file(_csv(), "data.csv", "text/csv"))

    assert exc.value.status_code == 411


@pytest.mark.asyncio
async def test_content_length_over_limit_is_413_before_reading():
    request = _Request({"content-length": str(MAX_FILE_SIZE + 100 * 1024)})
    with pytest.raises(UploadError) as exc:
        await validate_and_read_upload(request, _file(b"x", "data.csv", "text/csv"))

    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_stream_cap_is_enforced_when_header_lies(monkeypatch):
    monkeypatch.setattr(upload, "MAX_FILE_SIZE", 10)
    request = _Request({"content-length": "11"})
    with pytest.raises(UploadError) as exc:
        await validate_and_read_upload(request, _file(b"x" * 11, "data.csv", "text/csv"))

    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_binary_file_is_415():
    data = b"\x00\x01\x02\x03" * 100
    request = _Request({"content-length": str(len(data))})
    with pytest.raises(UploadError) as exc:
        await validate_and_read_upload(request, _file(data, "data.bin", "application/octet-stream"))

    assert exc.value.status_code == 415


@pytest.mark.asyncio
async def test_csv_returns_parsed_frame_and_metadata():
    data = _csv()
    request = _Request({"content-length": str(len(data))})
    file_bytes, file_type, frame, meta = await validate_and_read_upload(
        request, _file(data, "data.csv", "text/csv"))

    assert file_bytes == data
    assert file_type == "csv"
    assert frame.shape == (60, 2)
    assert meta["delimiter"] == ","


def _workbook() -> bytes:
    wb = openpyxl.Workbook()
    first = wb.active
    first.title = "Approvals"
    first.append(["a", "b"])
    for i in range(60):
        first.append([i, i % 3])
    second = wb.create_sheet("Archive")
    second.append(["c", "d"])
    for i in range(60):
        second.append([i * 2, i % 2])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_xlsx_reads_the_first_sheet_by_default():
    data = _workbook()
    request = _Request({"content-length": str(len(data))})
    _bytes, _type, frame, meta = await validate_and_read_upload(
        request, _file(data, "data.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))

    assert list(frame.columns) == ["a", "b"]
    assert meta["sheet"] == "Approvals"
    assert meta["sheet_names"] == ["Approvals", "Archive"]


@pytest.mark.asyncio
async def test_xlsx_reads_the_named_sheet():
    data = _workbook()
    request = _Request({"content-length": str(len(data))})
    _bytes, _type, frame, meta = await validate_and_read_upload(
        request, _file(data, "data.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        sheet="Archive")

    assert list(frame.columns) == ["c", "d"]
    assert meta["sheet"] == "Archive"


@pytest.mark.asyncio
async def test_xlsx_unknown_sheet_is_422():
    data = _workbook()
    request = _Request({"content-length": str(len(data))})
    with pytest.raises(UploadError) as exc:
        await validate_and_read_upload(
            request, _file(data, "data.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            sheet="Missing")

    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_xlsx_returns_parsed_frame_and_sheet_metadata():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["a", "b"])
    for i in range(60):
        ws.append([i, i % 3])
    buffer = io.BytesIO()
    wb.save(buffer)
    data = buffer.getvalue()

    request = _Request({"content-length": str(len(data))})
    _bytes, file_type, frame, meta = await validate_and_read_upload(
        request, _file(data, "data.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))

    assert file_type == "xlsx"
    assert frame.shape == (60, 2)
    assert meta["sheet"] == "Sheet"
