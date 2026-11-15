"""Analyses API: inspect, run (streaming), list, get."""
import asyncio
import json
import logging
import os
import queue
import threading
import time
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.api.auth import require_user
from app.auth.sessions import optional_user
from app.core import result_cache
from app.core.settings import SAMPLING_THRESHOLD
from app.db import Repository
from app.services import engine
from app.services.parsing import build_confirmation_card, clean, detect, ParseError
from app.services.upload import compute_sha256, validate_and_read_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/analyses", tags=["analyses"])

# TRD 7.4: one flag, one code path, decided by measurement of the proxy.
STREAMING_ENABLED = os.getenv("NEXT_PUBLIC_ANALYSIS_STREAMING", "1") != "0"

STAGES = [
    ("parsing", "Reading your file"),
    ("cleaning", "Cleaning and encoding"),
    ("training", "Training the stand-in model"),
    ("measuring", "Measuring fairness"),
    ("influence", "Computing feature influence"),
    ("saving", "Saving results"),
]


class InspectResponse(BaseModel):
    shape: dict
    card: dict
    metadata: dict


def _problem(code: str, title: str, status: int, detail: str) -> dict:
    return {"type": f"urn:fairlens:error:{code}", "title": title,
            "status": status, "detail": detail, "code": code}


@router.post("/inspect")
async def inspect(request: Request, file: UploadFile = File(...),
                  sheet: str | None = Form(None)) -> InspectResponse:
    """Parse and validate an uploaded file, return the confirmation card.

    No authentication and no storage: the rows live only for this request.
    """
    file_bytes, file_type, frame, parse_meta = await validate_and_read_upload(request, file, sheet)
    frame, clean_stats = clean(frame)

    try:
        detection = detect(frame)
    except ParseError as exc:
        raise HTTPException(status_code=422,
                            detail=_problem("ambiguous_confirmation", "Cannot auto-detect columns",
                                            422, str(exc)))
    card = build_confirmation_card(frame, detection)

    metadata = {
        "rows": frame.shape[0],
        "columns": frame.shape[1],
        "column_names": list(frame.columns),
        "dtypes": {c: str(frame[c].dtype) for c in frame.columns},
        "parse": parse_meta,
        "clean": clean_stats,
        "sha256": compute_sha256(file_bytes),
        "file_type": file_type,
        "filename": file.filename,
        "is_sample": False,
        "sampling_required": frame.shape[0] > SAMPLING_THRESHOLD,
    }
    return InspectResponse(shape={"rows": frame.shape[0], "columns": frame.shape[1]},
                           card=card, metadata=metadata)


def _execute(request: Request, file_bytes: bytes, frame, clean_stats: dict,
             confirmations: dict, filename: str, user_id: uuid.UUID, progress=None) -> dict:
    """Run the engine and store the result. Called from a worker thread or inline."""
    result = engine.run(file_bytes, filename, confirmations=confirmations, frame=frame,
                        clean_stats=clean_stats, progress=progress)
    result["id"] = str(uuid.uuid4())
    result["dataset"]["name"] = filename
    result["dataset"]["sha256"] = compute_sha256(file_bytes)
    result["dataset"]["is_sample"] = False
    result["dataset"]["sheet"] = confirmations.get("sheet")
    request.app.state.repo.create_analysis(result, user_id)
    return result


async def _stream(request: Request, file_bytes: bytes, frame, clean_stats: dict,
                  confirmations: dict, filename: str, user_id: uuid.UUID):
    """Yield NDJSON frames while the engine works in a worker thread (TRD 7.2)."""
    events: queue.Queue = queue.Queue()

    def progress(index: int) -> None:
        events.put(("stage", {"stage": STAGES[index - 1][0], "index": index,
                              "total": len(STAGES), "label": STAGES[index - 1][1]}))

    def work() -> None:
        try:
            result = _execute(request, file_bytes, frame, clean_stats, confirmations,
                              filename, user_id, progress)
        except Exception:
            logger.exception("Analysis run failed")
            events.put(("error", {"problem": _problem(
                "internal_error", "Analysis failed", 500,
                "An internal error occurred during analysis.")}))
            return
        events.put(("stage", {"stage": "saving", "index": 6, "total": len(STAGES),
                              "label": STAGES[5][1]}))
        events.put(("result", {"payload": result}))

    threading.Thread(target=work, daemon=True).start()

    last_ping = time.monotonic()
    while True:
        try:
            event, body = events.get_nowait()
        except queue.Empty:
            if time.monotonic() - last_ping >= 5:
                last_ping = time.monotonic()
                yield json.dumps({"event": "ping"}) + "\n"
            await asyncio.sleep(0.1)
            continue
        yield json.dumps({"event": event, **body}) + "\n"
        if event in ("result", "error"):
            return


@router.post("", response_model=None)
async def run_analysis(
    request: Request,
    file: UploadFile = File(...),
    confirmations: str = Form(...),
    user_id: uuid.UUID = Depends(require_user),
) -> StreamingResponse | JSONResponse:
    """Run a full analysis. Own-file uploads require a session (F8-AC5)."""
    try:
        data = json.loads(confirmations)
        for key in ("outcome", "positive", "group"):
            data[key]
        confirmations_dict = data
    except (json.JSONDecodeError, KeyError, TypeError):
        raise HTTPException(status_code=422, detail=_problem(
            "invalid_confirmation", "Invalid confirmation", 422,
            "The confirmation must name the outcome, positive value and group column."))

    filename = file.filename or "upload.csv"
    file_bytes, _file_type, frame, _parse_meta = await validate_and_read_upload(
        request, file, confirmations_dict.get("sheet"))
    frame, clean_stats = clean(frame)

    group_col = confirmations_dict["group"]
    if group_col not in frame.columns or frame[group_col].nunique(dropna=True) < 2:
        raise HTTPException(status_code=422, detail=_problem(
            "single_value_demographic", "Only one group", 422,
            f"The demographic column '{group_col}' must contain at least two distinct values."))

    if len(frame) > SAMPLING_THRESHOLD and not (confirmations_dict.get("sampling") or {}).get("enabled"):
        raise HTTPException(status_code=422, detail=_problem(
            "sampling_required", "Sampling choice required", 422,
            f"The file has {len(frame):,} rows. Choose a {SAMPLING_THRESHOLD:,}-row sample "
            "before running."))

    if not STREAMING_ENABLED:
        return JSONResponse(content=_execute(request, file_bytes, frame, clean_stats,
                                           confirmations_dict, filename, user_id))

    return StreamingResponse(
        _stream(request, file_bytes, frame, clean_stats, confirmations_dict, filename, user_id),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("")
async def list_analyses(
    request: Request,
    user_id: uuid.UUID = Depends(require_user),
    limit: int = 50,
    offset: int = 0,
) -> JSONResponse:
    repo: Repository = request.app.state.repo
    analyses = repo.list_analyses(user_id, limit=limit, offset=offset)
    return JSONResponse(content=jsonable_encoder(
        {"analyses": analyses, "limit": limit, "offset": offset}))


@router.get("/{analysis_id}")
async def get_analysis(
    request: Request,
    analysis_id: str,
    user_id: uuid.UUID | None = Depends(optional_user),
) -> JSONResponse:
    """Stored payload for its owner, or the cached payload of an anonymous sample run."""
    try:
        parsed_id = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")

    cached = result_cache.get(str(parsed_id))
    if cached:
        return JSONResponse(content=cached)

    repo: Repository = request.app.state.repo
    owner = repo.get_analysis_owner(parsed_id)
    if owner is None or user_id is None or owner != user_id:
        raise HTTPException(status_code=404, detail="Not found")
    payload = repo.get_analysis(parsed_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content=payload)
