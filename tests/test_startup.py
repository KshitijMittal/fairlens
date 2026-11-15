"""Production startup guards (F8-AC1, F8-AC6)."""
import pytest

from app import main
from app.api import auth
from app.core.config import settings


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "development")
    monkeypatch.setattr(settings, "BREVO_API_KEY", None)
    monkeypatch.setattr(settings, "BREVO_SENDER", None)
    monkeypatch.setattr(main, "GOOGLE_SCOPES", auth.GOOGLE_SCOPES)


def test_sensitive_google_scope_exits(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "BREVO_API_KEY", "key")
    monkeypatch.setattr(settings, "BREVO_SENDER", "sender@example.com")
    monkeypatch.setattr(main, "GOOGLE_SCOPES",
                        (*auth.GOOGLE_SCOPES, "https://www.googleapis.com/auth/drive"))

    with pytest.raises(SystemExit):
        main._startup_guards()


def test_production_without_brevo_exits(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")

    with pytest.raises(SystemExit):
        main._startup_guards()


def test_production_with_safe_config_passes(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "BREVO_API_KEY", "key")
    monkeypatch.setattr(settings, "BREVO_SENDER", "sender@example.com")

    main._startup_guards()


def test_development_skips_guards():
    main._startup_guards()
