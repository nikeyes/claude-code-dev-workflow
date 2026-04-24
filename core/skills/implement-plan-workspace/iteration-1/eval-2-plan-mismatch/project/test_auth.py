import logging
from auth import UserService


def test_successful_login_logs_info(caplog):
    service = UserService()
    with caplog.at_level(logging.INFO):
        service.verify_credentials("admin", "secret123")
    assert "Login successful for user: admin" in caplog.text


def test_failed_login_logs_warning(caplog):
    service = UserService()
    with caplog.at_level(logging.WARNING):
        service.verify_credentials("admin", "wrongpassword")
    assert "Failed login attempt for user: admin" in caplog.text


def test_unknown_user_logs_warning(caplog):
    service = UserService()
    with caplog.at_level(logging.WARNING):
        service.verify_credentials("nonexistent", "pass")
    assert "Login attempt for unknown user: nonexistent" in caplog.text
