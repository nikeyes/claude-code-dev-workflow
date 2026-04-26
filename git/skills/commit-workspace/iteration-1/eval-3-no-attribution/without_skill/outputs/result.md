commit 5b6c6efa58acfc5777eb9f4dbb56309605dff702
Author: Dev User <dev@example.com>
Date:   2026-04-26 13:40

    Add installation, configuration, and API documentation to README
    
    Document setup requirements including pip dependencies and server startup,
    environment variables needed for deployment, and pointer to API endpoint
    reference.

diff --git a/README.md b/README.md
new file mode 100644
index 0000000..5f1c9f4
--- /dev/null
+++ b/README.md
@@ -0,0 +1,19 @@
+# MyApp
+
+## Overview
+Web application for task management.
+
+## Installation
+```bash
+pip install -r requirements.txt
+python manage.py runserver
+```
+
+## Configuration
+Set the following environment variables before running:
+- `DATABASE_URL`: PostgreSQL connection string
+- `SECRET_KEY`: Django secret key
+- `DEBUG`: Set to `false` in production
+
+## API Documentation
+See `/docs/api.md` for endpoint reference.
