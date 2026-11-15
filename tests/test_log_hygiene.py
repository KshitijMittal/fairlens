"""Log hygiene: passwords and tokens never reach a log line (F8-AC4)."""
import logging

from app.auth.security import (
    hash_password,
    hash_token,
    new_auth_token,
    new_session_token,
    verify_password,
)


def test_password_and_tokens_never_logged(caplog):
    password = "correct-horse-battery-staple"
    token = new_auth_token()
    session = new_session_token()

    with caplog.at_level(logging.DEBUG):
        password_hash = hash_password(password)
        assert verify_password(password, password_hash)
        assert not verify_password("wrong-password", password_hash)
        hash_token(token)
        hash_token(session)

    for secret in (password, token, session):
        assert secret not in caplog.text
    assert password_hash not in caplog.text
