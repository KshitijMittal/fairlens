import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest  # noqa: E402

from app.services import engine  # noqa: E402

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.fixture(scope="session")
def scholarship_result():
    return engine.run((SAMPLES / "scholarship.csv").read_bytes(), "scholarship.csv")


@pytest.fixture(scope="session")
def loans_result():
    return engine.run((SAMPLES / "loan_approvals.csv").read_bytes(), "loan_approvals.csv")


@pytest.fixture(scope="session")
def hiring_result():
    return engine.run((SAMPLES / "hiring_shortlist.csv").read_bytes(), "hiring_shortlist.csv")
