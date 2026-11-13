"""The FastAPI app (M1): health, sample runs, database-backed analyses."""
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core import result_cache
from app.core.settings import ENGINE_VERSION
from app.db import Repository, close_pool, get_pool, init_db
from app.services import engine


def _samples_dir() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "samples"
        if (candidate / "scholarship.csv").exists():
            return candidate
    return here.parents[1] / "samples"


SAMPLES_DIR = _samples_dir()
SAMPLE_FILES = {
    "scholarship": "scholarship.csv",
    "loan_approvals": "loan_approvals.csv",
    "hiring_shortlist": "hiring_shortlist.csv",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.repo = Repository(get_pool())
    yield
    close_pool()


app = FastAPI(title="FairLens", version=ENGINE_VERSION, lifespan=lifespan)


def problem(request: Request, status: int, code: str, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"type": f"urn:fairlens:error:{code}", "title": title, "status": status,
                 "detail": detail, "instance": request.url.path, "code": code},
    )


def _versions() -> dict:
    versions = {"engine": ENGINE_VERSION}
    for name in ("shap", "fairlearn", "pandas", "numpy", "scikit-learn"):
        module = {"scikit-learn": "sklearn"}.get(name, name)
        try:
            versions[name] = __import__(module).__version__
        except Exception:
            versions[name] = "unavailable"
    return versions


async def _check_database() -> bool:
    try:
        with get_pool().connection() as conn:
            return conn.execute("select 1 as ok").fetchone()["ok"] == 1
    except Exception:
        return False


@app.get("/v1/health")
async def health() -> dict:
    return {
        "status": "ok",
        "database": await _check_database(),
        "versions": _versions(),
        "time": time.time(),
    }


@app.post("/v1/dev/sample/{slug}")
async def run_sample(slug: str, request: Request) -> JSONResponse:
    filename = SAMPLE_FILES.get(slug)
    if filename is None:
        return problem(request, 404, "not_found", "Unknown sample", f"No bundled sample named '{slug}'.")
    path = SAMPLES_DIR / filename
    if not path.exists():
        return problem(request, 500, "internal_error", "Sample missing",
                       "The bundled sample file is missing from the deployment.")

    result = engine.run(path.read_bytes(), filename)
    result["id"] = str(uuid.uuid4())
    result["dataset"]["sample"] = {"slug": slug}

    # Anonymous runs are never written to the database; the payload lives in the
    # in-process cache for 30 minutes (BACKEND_SCHEMA 3.1).
    result_cache.put(result["id"], result)
    return JSONResponse(content=result)


@app.get("/v1/analyses/{analysis_id}")
async def get_analysis(analysis_id: str, request: Request) -> JSONResponse:
    try:
        parsed_id = uuid.UUID(analysis_id)
    except ValueError:
        return problem(request, 404, "not_found", "Not found", "No analysis with this id.")

    payload = result_cache.get(str(parsed_id))
    if payload is None:
        payload = request.app.state.repo.get_analysis(parsed_id)
    if payload is None:
        return problem(request, 404, "not_found", "Not found",
                       "No analysis with this id. Anonymous sample runs expire after 30 minutes.")
    return JSONResponse(content=payload)


@app.get("/v1/samples")
def samples() -> dict:
    return {
        "samples": [
            {"slug": "scholarship", "name": "Scholarship awards", "file": "scholarship.csv",
             "demonstrates": "A fair dataset: passes all five checks.",
             "expected_verdict": "pass"},
            {"slug": "loan_approvals", "name": "Loan approvals", "file": "loan_approvals.csv",
             "demonstrates": "Real decisions with a large historical disparity.",
             "expected_verdict": "fail"},
            {"slug": "hiring_shortlist", "name": "Hiring shortlist", "file": "hiring_shortlist.csv",
             "demonstrates": "Moderate disparity; proxies the drop-repair cannot fix.",
             "expected_verdict": "warn"},
        ]
    }
