# Result: git show HEAD + git status

## git show HEAD

```
commit 6c0b1aa43a2ffb9ce164ac4e82bc9a077da15d60
Author: Dev User <dev@example.com>
Date:   2026-04-26 14:21

    Switch database to PostgreSQL and harden production settings

    Update DATABASE_URL to use PostgreSQL, disable DEBUG mode, and add
    ALLOWED_HOSTS list to restrict allowed origins for production deployment.

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
