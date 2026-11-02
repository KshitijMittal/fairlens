"""Day Zero probe. Throwaway - replaced at M0.

Runs on a free Hugging Face Gradio Space: one process serves FastAPI on 7860,
with Gradio mounted at /ui. Endpoints:

  GET  /v1/health            liveness, database flag, shap/fairlearn versions (G4)
  GET  /v1/dev/stream-probe  three NDJSON frames 500 ms apart (G1)
  POST /v1/dev/echo-size     counts the multipart body bytes (G3)
  GET  /v1/dev/bench         one timed pipeline pass; call twice for cold/warm (G9)
"""
try:
    import spaces  # ZeroGPU runtime handshake; no-op elsewhere
except ImportError:  # local run without the spaces package
    spaces = None

import json
import os
import time
import tempfile
import urllib.request

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

app = FastAPI(title="FairLens Day Zero Probe")


def _versions() -> dict:
    out = {}
    for name in ("shap", "fairlearn"):
        try:
            out[name] = __import__(name).__version__
        except Exception as exc:  # the gate reports the failure, not a crash
            out[name] = f"unavailable: {exc}"
    return out


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok", "database": False, "versions": _versions(), "time": time.time()}


@app.get("/v1/dev/stream-probe")
def stream_probe():
    def gen():
        for i in range(1, 4):
            yield f'{{"event":"stage","stage":"probe","index":{i},"total":3,"label":"Frame {i}"}}\n'
            time.sleep(0.5)

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@app.post("/v1/dev/echo-size")
async def echo_size(file: UploadFile) -> dict:
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
    return {"bytes": total}


def _bench_once(n: int = 50_000, cols: int = 60, seed: int = 42) -> dict:
    """Parse, then train, bootstrap and explain - the pipeline's expensive parts."""
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold

    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({f"col_{i:02d}": rng.normal(0, 1, n) for i in range(cols - 3)})
    frame["outcome"] = rng.integers(0, 2, n)
    frame["group"] = rng.choice(["A", "B", "C"], n)
    frame["age"] = rng.integers(18, 70, n)

    path = tempfile.mktemp(suffix=".csv")
    frame.to_csv(path, index=False)

    t0 = time.perf_counter()
    frame = pd.read_csv(path)
    os.unlink(path)
    t_parse = time.perf_counter() - t0

    t0 = time.perf_counter()
    frame["group"] = pd.Categorical(frame["group"]).codes
    y = frame.pop("outcome").to_numpy()
    x = frame.to_numpy()
    oof = np.zeros_like(y, dtype=float)
    for train_idx, test_idx in StratifiedKFold(5, shuffle=True, random_state=42).split(x, y):
        clf = LogisticRegression(max_iter=1000).fit(x[train_idx], y[train_idx])
        oof[test_idx] = clf.predict_proba(x[test_idx])[:, 1]
    t_train = time.perf_counter() - t0

    t0 = time.perf_counter()
    boot = np.random.default_rng(123)
    for _ in range(1_000):
        idx = boot.integers(0, len(y), len(y))
        _ = y[idx].mean()
    t_boot = time.perf_counter() - t0

    t0 = time.perf_counter()
    shap_ok = False
    try:
        import shap

        explainer = shap.LinearExplainer(LogisticRegression(max_iter=1000).fit(x, y), x[:100])
        _ = explainer.shap_values(x[:500])
        shap_ok = True
    except Exception:
        pass
    t_shap = time.perf_counter() - t0

    return {
        "parse_seconds": round(t_parse, 2),
        "train_seconds": round(t_train, 2),
        "bootstrap_seconds": round(t_boot, 2),
        "shap_seconds": round(t_shap, 2),
        "shap_ok": shap_ok,
        "total_seconds": round(t_parse + t_train + t_boot + t_shap, 2),
    }


_runs = {"count": 0}


@app.get("/v1/dev/bench")
def bench() -> dict:
    started = time.perf_counter()
    detail = _bench_once()
    _runs["count"] += 1
    return {"run": _runs["count"], "seconds": round(time.perf_counter() - started, 2), "detail": detail}


@app.post("/v1/dev/mail-probe")
def mail_probe(to: str, request: Request) -> dict:
    """G2. Token-gated so a public probe is not an open mail relay."""
    if not os.environ.get("PROBE_TOKEN") or request.headers.get("x-probe-token") != os.environ["PROBE_TOKEN"]:
        raise HTTPException(404)
    key = os.environ.get("BREVO_API_KEY")
    sender = os.environ.get("BREVO_SENDER")
    if not (key and sender):
        raise HTTPException(500, detail="BREVO_API_KEY/BREVO_SENDER not set")

    body = json.dumps(
        {
            "sender": {"email": sender, "name": "FairLens"},
            "to": [{"email": to}],
            "subject": "FairLens G2 probe",
            "htmlContent": "<p>If this arrived, Brevo works from the host.</p>",
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=body,
        headers={"api-key": key, "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {"status": resp.status, "to": to}
    except Exception as exc:
        raise HTTPException(502, detail=str(exc))


def _page():
    import gradio as gr

    with gr.Blocks(title="FairLens Day Zero Probe") as demo:
        gr.Markdown("# FairLens v2 - Day Zero probe\nThe real UI starts at M0.")
        gr.Markdown(
            "- [/v1/health](/v1/health)\n"
            "- [/v1/dev/stream-probe](/v1/dev/stream-probe)\n"
        )
    return demo


if __name__ == "__main__":
    import socket

    import gradio as gr
    import uvicorn

    asgi = gr.mount_gradio_app(app, _page(), path="/")

    for name in ("SPACES_ZERO_GPU", "SPACES_ZERO_DEVICE_API_URL", "PORT", "GRADIO_SERVER_PORT"):
        print(f"env {name}={os.environ.get(name)}", flush=True)

    # Bind the platform's app port first (the health check pings 7860);
    # gradio-style fallback scan only if 7860 is genuinely taken.
    port = None
    for candidate in [7860, 7861] + list(range(7862, 7960)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("0.0.0.0", candidate))
            except OSError as exc:
                print(f"bind {candidate} failed: {exc}", flush=True)
                continue
        port = candidate
        print(f"bound port {candidate}", flush=True)
        break
    if port is None:
        raise SystemExit("no free port in 7860-7959")

    if spaces is not None:
        try:
            from spaces.config import Config

            print(f"zero_gpu={Config.zero_gpu}", flush=True)
            if Config.zero_gpu:
                from spaces.zero.client import startup_report

                startup_report()
                print("startup_report sent", flush=True)
        except Exception as exc:
            print(f"startup_report failed: {exc!r}", flush=True)

    uvicorn.run(asgi, host="0.0.0.0", port=port)
