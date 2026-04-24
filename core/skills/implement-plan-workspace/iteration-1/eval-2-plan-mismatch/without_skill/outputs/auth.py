import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.users = {
            "admin": "secret123",
            "user1": "password1",
        }

    def verify_credentials(self, username, password):
        """Verify user credentials and return True if valid."""
        if username not in self.users:
            logger.warning("Login attempt for unknown user: %s", username)
            return False
        if self.users[username] == password:
            logger.info("Login successful for user: %s", username)
            return True
        logger.warning("Failed login attempt for user: %s", username)
        return False

    def get_user(self, username):
        """Return user info if exists."""
        if username in self.users:
            return {"username": username, "active": True}
        return None
