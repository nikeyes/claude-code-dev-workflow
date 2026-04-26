# Result: git show HEAD + git status

## git show HEAD

```
commit 2ad429fa9373030adef3f2bc318ab38710d6d8c9
Author: Dev User <dev@example.com>
Date:   2026-04-26 14:21

    Update config for production environment

    Switch database to PostgreSQL, disable debug mode, and add allowed hosts.

diff --git a/src/config.py b/src/config.py
index 77507c4..e5c6b70 100644
--- a/src/config.py
+++ b/src/config.py
@@ -1,3 +1,4 @@
-DATABASE_URL = "sqlite:///db.sqlite3"
+DATABASE_URL = "postgresql://localhost/myapp"
 SECRET_KEY = "changeme"
-DEBUG = True
+DEBUG = False
+ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
```

## git status

```
On branch master
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.env

nothing added to commit but untracked files present (use "git add" to track)
```
