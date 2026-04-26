commit 6357962e1755a2dc73b84eebef84099aa5e85c86
Author: Dev User <dev@example.com>
Date:   2026-04-26 14:21

    Add login validation and email format check
    
    Implement validate_login to enforce non-empty credentials and minimum
    password length, and check_email_format to verify basic email structure.

diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..a85d02c
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,9 @@
+def validate_login(username: str, password: str) -> bool:
+    if not username or not password:
+        raise ValueError("Username and password required")
+    if len(password) < 8:
+        raise ValueError("Password must be at least 8 characters")
+    return True
+
+def check_email_format(email: str) -> bool:
+    return "@" in email and "." in email.split("@")[-1]
