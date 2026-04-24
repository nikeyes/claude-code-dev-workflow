import time


class RateLimiter:
    def __init__(self, max_attempts=5, window_seconds=60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts = {}

    def record_attempt(self, username, success):
        now = time.time()
        if success:
            self._attempts.pop(username, None)
            return
        if username not in self._attempts:
            self._attempts[username] = []
        self._attempts[username].append(now)
        self._attempts[username] = [
            t for t in self._attempts[username]
            if now - t < self.window_seconds
        ]

    def is_blocked(self, username):
        if username not in self._attempts:
            return False
        now = time.time()
        recent = [
            t for t in self._attempts[username]
            if now - t < self.window_seconds
        ]
        self._attempts[username] = recent
        return len(recent) >= self.max_attempts
