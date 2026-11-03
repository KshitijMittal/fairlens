"""FairLens backend on a free Hugging Face Gradio Space (M0).

The real FastAPI app lives in backend/app; this file is only the mount
wrapper the Gradio SDK needs. Probe endpoints are gone - replaced at M0.
"""
import socket

try:
    import spaces  # ZeroGPU runtime handshake; no-op elsewhere
except ImportError:  # local run without the spaces package
    spaces = None

import os

import gradio as gr
import uvicorn

from app.main import app as fastapi_app


def _page():
    with gr.Blocks(title="FairLens") as demo:
        gr.Markdown("# FairLens\nThe analysis API is served from this Space.")
    return demo


if __name__ == "__main__":
    asgi = gr.mount_gradio_app(fastapi_app, _page(), path="/")

    for name in ("SPACES_ZERO_GPU", "SPACES_ZERO_DEVICE_API_URL", "PORT", "GRADIO_SERVER_PORT"):
        print(f"env {name}={os.environ.get(name)}", flush=True)

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
