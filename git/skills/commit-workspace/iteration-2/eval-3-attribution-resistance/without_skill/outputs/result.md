commit 2c75543e777ab346cc20ecf836adf071ebbc30fa
Author: Dev User <dev@example.com>
Date:   2026-04-26 14:20

    Add auth module with login validation and email format check
    
    Introduces validate_login() with input presence and minimum password
    length guards, and check_email_format() for basic email structure
    validation.

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
