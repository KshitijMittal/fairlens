"""The FastAPI app (M0): health, sample runs, cached reads. No database, no upload."""
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core import result_cache
from app.core.settings import ENGINE_VERSION
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

app = FastAPI(title="FairLens", version=ENGINE_VERSION)


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


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok", "database": False, "versions": _versions(), "time": time.time()}


@app.post("/v1/dev/sample/{slug}")
def run_sample(slug: str, request: Request) -> JSONResponse:
    filename = SAMPLE_FILES.get(slug)
    if filename is None:
        return problem(request, 404, "not_found", "Unknown sample", f"No bundled sample named '{slug}'.")
    path = SAMPLES_DIR / filename
    if not path.exists():
        return problem(request, 500, "internal_error", "Sample missing",
                       "The bundled sample file is missing from the deployment.")
    result = engine.run(path.read_bytes(), filename)
    run_id = str(uuid.uuid4())
    result["id"] = run_id
    result["dataset"]["sample"] = {"slug": slug}
    result_cache.put(run_id, result)
    return JSONResponse(content=result)


@app.get("/v1/analyses/{run_id}")
def get_analysis(run_id: str, request: Request) -> JSONResponse:
    payload = result_cache.get(run_id)
    if payload is None:
        return problem(request, 404, "not_found", "Not found",
                       "No analysis with this id. Anonymous sample runs expire after 30 minutes.")
    return JSONResponse(content=payload)
