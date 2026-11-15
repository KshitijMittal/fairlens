"""The FastAPI app (M2): health, auth, analyses, streaming."""
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import auth, analyses
from app.api.auth import GOOGLE_SCOPES, SENSITIVE_GOOGLE_SCOPES
from app.auth.sessions import optional_user, sweep_expired
from app.core import result_cache
from app.core.config import settings
from app.core.settings import ENGINE_VERSION
from app.db import Repository, close_pool, get_pool, init_db
from app.services import engine

logger = logging.getLogger(__name__)


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


def _startup_guards() -> None:
    """Refuse to boot in production with a dangerous or incomplete configuration."""
    if settings.ENV != "production":
        return
    if set(GOOGLE_SCOPES) & SENSITIVE_GOOGLE_SCOPES:
        sys.exit("Startup failed: Google sign-in requests a sensitive scope (F8-AC1)")
    if not settings.BREVO_API_KEY or not settings.BREVO_SENDER:
        sys.exit("Startup failed: BREVO_API_KEY and BREVO_SENDER are required in production (F8-AC6)")
    logger.info("Production startup guards passed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _startup_guards()
    init_db()
    app.state.repo = Repository(get_pool())
    sweep_expired()
    yield
    close_pool()


app = FastAPI(title="FairLens", version=ENGINE_VERSION, lifespan=lifespan)

# Include routers
app.include_router(auth.router)
app.include_router(auth.me_router)
app.include_router(analyses.router)


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
            mod = __import__(module)
            versions[name] = getattr(mod, "__version__", "unavailable")
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
async def run_sample(slug: str, request: Request,
                     user_id: uuid.UUID | None = Depends(optional_user)) -> JSONResponse:
    filename = SAMPLE_FILES.get(slug)
    if filename is None:
        return problem(request, 404, "not_found", "Unknown sample", f"No bundled sample named '{slug}'.")
    path = SAMPLES_DIR / filename
    if not path.exists():
        return problem(request, 500, "internal_error", "Sample missing",
                       "The bundled sample file is missing from the deployment.")

    result = engine.run(path.read_bytes(), filename)
    result["id"] = str(uuid.uuid4())
    result["dataset"]["is_sample"] = True
    result["dataset"]["sample"] = {"slug": slug}

    if user_id:
        request.app.state.repo.create_analysis(result, user_id)
    else:
        # Anonymous runs are never written to the database; the payload lives in
        # the in-process cache for 30 minutes (BACKEND_SCHEMA 3.1).
        result_cache.put(result["id"], result)
    return JSONResponse(content=result)


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