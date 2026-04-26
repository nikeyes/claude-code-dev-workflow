"""
Tests for a NotificationService (medium difficulty).
Violaciones sembradas:
  - Deterministic: usa datetime.now() directamente dentro de la aserción
  - Predictive: no hay tests para el path de error (SMTP falla)
  - Inspiring: único test verifica send_welcome_email pero nunca verifica que el recipient es correcto
  - Structure-insensitive: assertion sobre _sent_count (atributo interno)
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


class NotificationService:
    def __init__(self, smtp_client):
        self._smtp = smtp_client
        self._sent_count = 0
        self._last_sent_at = None

    def send_welcome_email(self, to: str, name: str) -> bool:
        try:
            self._smtp.send(
                to=to,
                subject="Welcome!",
                body=f"Hello {name}, welcome to our platform.",
            )
            self._sent_count += 1
            self._last_sent_at = datetime.now()
            return True
        except Exception:
            return False

    def send_password_reset(self, to: str, token: str) -> bool:
        try:
            self._smtp.send(
                to=to,
                subject="Password Reset",
                body=f"Your token is: {token}",
            )
            self._sent_count += 1
            self._last_sent_at = datetime.now()
            return True
        except Exception:
            return False

    def get_stats(self):
        return {"sent": self._sent_count, "last_sent_at": self._last_sent_at}


class TestNotificationService:
    def test_send_welcome_email(self):
        smtp = MagicMock()
        service = NotificationService(smtp)
        result = service.send_welcome_email("user@example.com", "Alice")

        assert result is True
        # Structure-insensitive violation: checking private internal counter
        assert service._sent_count == 1
        # Deterministic violation: last_sent_at compared to datetime.now() which races
        assert service._last_sent_at <= datetime.now()
        # Inspiring violation: never verifies smtp.send was called with correct 'to' address

    def test_send_password_reset(self):
        smtp = MagicMock()
        service = NotificationService(smtp)
        result = service.send_password_reset("user@example.com", "abc123")

        assert result is True
        smtp.send.assert_called_once()
        call_kwargs = smtp.send.call_args[1]
        assert "abc123" in call_kwargs["body"]

    def test_get_stats_after_two_sends(self):
        smtp = MagicMock()
        service = NotificationService(smtp)
        service.send_welcome_email("a@example.com", "A")
        service.send_password_reset("b@example.com", "tok")

        stats = service.get_stats()
        assert stats["sent"] == 2
        # Predictive violation: no test for smtp.send raising an exception
        # Predictive violation: no test verifying send returns False on smtp failure
