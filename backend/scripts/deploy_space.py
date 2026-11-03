#!/usr/bin/env python
"""Publish the backend to a free Hugging Face Gradio Space.

Usage (from the repo root, with HF_TOKEN in .env):
    python backend/scripts/deploy_space.py

Gradio Spaces run on ZeroGPU for free personal accounts; Docker Spaces need
PRO, which is why this uses the Gradio SDK with FastAPI mounted inside it.
"""
import os
import sys

from dotenv import dotenv_values
from huggingface_hub import HfApi

SPACE_NAME = "fairlens-probe"


def main() -> int:
    env = dotenv_values(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    token = env.get("HF_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN missing from .env")
        return 1

    api = HfApi(token=token)
    user = api.whoami()["name"]
    repo_id = f"{user}/{SPACE_NAME}"

    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="gradio",
        space_hardware="zero-a10g",
        exist_ok=True,
    )
    api.upload_folder(
        folder_path=os.path.join(os.path.dirname(__file__), "..", "space"),
        repo_id=repo_id,
        repo_type="space",
    )
    api.upload_folder(
        folder_path=os.path.join(os.path.dirname(__file__), "..", "app"),
        path_in_repo="app",
        repo_id=repo_id,
        repo_type="space",
    )
    api.upload_folder(
        folder_path=os.path.join(os.path.dirname(__file__), "..", "..", "samples"),
        path_in_repo="samples",
        repo_id=repo_id,
        repo_type="space",
        allow_patterns=["loan_approvals.csv", "hiring_shortlist.csv", "scholarship.csv", "README.md"],
    )

    for name in ("BREVO_API_KEY", "BREVO_SENDER"):
        if env.get(name):
            api.add_space_secret(repo_id=repo_id, key=name, value=env[name])

    print(f"Space: https://huggingface.co/spaces/{repo_id}")
    print(f"URL:   https://{user.lower()}-{SPACE_NAME}.hf.space")
    print("The first build takes a few minutes. Then run the gates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
