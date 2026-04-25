import time
import uuid


class APIGateway:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}
        self._allowlist = set()

    def _get_session_id(self, request_context):
        return request_context.get("session_id", str(uuid.uuid4()))

    def check_rate_limit(self, session_id):
        if session_id in self._allowlist:
            return True
        now = time.time()
        if session_id not in self._requests:
            return True
        recent = [t for t in self._requests[session_id] if now - t < self.window_seconds]
        self._requests[session_id] = recent
        return len(recent) < self.max_requests

    def record_request(self, session_id):
        now = time.time()
        if session_id not in self._requests:
            self._requests[session_id] = []
        self._requests[session_id].append(now)

    def get_remaining(self, session_id):
        if session_id in self._allowlist:
            return self.max_requests
        now = time.time()
        if session_id not in self._requests:
            return self.max_requests
        recent = [t for t in self._requests[session_id] if now - t < self.window_seconds]
        return max(0, self.max_requests - len(recent))

    def is_allowlisted(self, session_id):
        return session_id in self._allowlist

    def add_to_allowlist(self, session_id):
        self._allowlist.add(session_id)

    def remove_from_allowlist(self, session_id):
        self._allowlist.discard(session_id)

    def get_top_offenders(self, n=5):
        now = time.time()
        counts = {}
        for session_id, timestamps in self._requests.items():
            recent = [t for t in timestamps if now - t < self.window_seconds]
            if recent:
                counts[session_id] = len(recent)
        sorted_ids = sorted(counts, key=lambda k: counts[k], reverse=True)
        return sorted_ids[:n]
