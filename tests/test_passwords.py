"""Password policy tests (F8): length plus capital, number and special character."""
import pytest

from app.auth.security import password_problem


@pytest.mark.parametrize(
    "password, fragment",
    [
        ("Short1!", "8 characters"),
        ("alllowercase1!", "capital letter"),
        ("NoNumbers!", "number"),
        ("NoSymbols1", "special character"),
    ],
)
def test_rejects_unmet_rule(password, fragment):
    problem = password_problem(password)
    assert problem is not None
    assert fragment in problem


@pytest.mark.parametrize("password", ["Correct-horse-1", "Another-password-1", "Aa1!aaaa"])
def test_accepts_compliant_password(password):
    assert password_problem(password) is None
