commit 0e4d2a0eabe5fe17b226b978a9d177a1bdb59c66
Author: Dev User <dev@example.com>
Date:   2026-04-26 13:39

    Add sliding-window rate limiter to protect login endpoint from brute-force
    
    After a production incident where bots were brute-forcing logins—causing
    account lockouts and spiking AWS costs—this adds a per-IP sliding-window
    rate limiter that blocks IPs exceeding 5 requests per 60-second window.

diff --git a/src/auth/__init__.py b/src/auth/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/src/auth/rate_limiter.py b/src/auth/rate_limiter.py
new file mode 100644
index 0000000..d317a49
--- /dev/null
+++ b/src/auth/rate_limiter.py
@@ -0,0 +1,30 @@
+from collections import defaultdict
+import time
+
+
+class RateLimiter:
+    """Per-IP rate limiter for the login endpoint.
+    
+    Added after 2024-03-15 production incident: login endpoint was being
+    brute-forced, causing account lockouts and elevated AWS costs.
+    """
+
+    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
+        self.max_requests = max_requests
+        self.window_seconds = window_seconds
+        self._buckets: dict[str, list[float]] = defaultdict(list)
+
+    def is_allowed(self, ip: str) -> bool:
+        now = time.time()
+        cutoff = now - self.window_seconds
+        self._buckets[ip] = [t for t in self._buckets[ip] if t > cutoff]
+        if len(self._buckets[ip]) >= self.max_requests:
+            return False
+        self._buckets[ip].append(now)
+        return True
+
+    def remaining(self, ip: str) -> int:
+        now = time.time()
+        cutoff = now - self.window_seconds
+        recent = [t for t in self._buckets[ip] if t > cutoff]
+        return max(0, self.max_requests - len(recent))
