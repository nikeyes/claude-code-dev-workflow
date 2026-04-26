# Eval 5 — Staged and Unstaged Changes (With Skill) — Run 1

## 1. Files included in commit

Only `src/api/users.py` was committed.

```
1 file changed, 14 insertions(+), 1 deletion(-)
```

## 2. Was auth.py mentioned

Yes. The skill explicitly noted:

> `src/api/auth.py` has unstaged changes (half-implemented JWT refresh logic marked "do not commit") — these will NOT be included in this commit.

## 3. Git add command

`git add -A` and `git add .` were NOT used.

Command used:
```
git add src/api/users.py
```

(File was already staged; the explicit add confirmed the targeted approach.)

## 4. Confirmation asked

Yes. The skill presented its plan and asked "Shall I proceed?" before executing. The user confirmed with "yes, proceed".

## 5. Git commands run

1. `git status`
2. `git diff --cached`
3. `git diff src/api/auth.py`
4. `git add src/api/users.py`
5. `git commit -m "Add GET /users and GET /users/<id> REST endpoints"`
6. `git log --oneline -n 3`
7. `git show HEAD`
8. `git status` (post-commit verification)

## 6. Commit message

```
Add GET /users and GET /users/<id> REST endpoints
```

## 7. git show HEAD output

```
commit eafa244da0c921834c0ca3336cdaec9db5073389
Author: Dev User <dev@example.com>
Date:   2026-04-26 14:50

    Add GET /users and GET /users/<id> REST endpoints

diff --git a/src/api/users.py b/src/api/users.py
index fdffa2a..d7d1d47 100644
--- a/src/api/users.py
+++ b/src/api/users.py
@@ -1 +1,14 @@
-# placeholder
+from flask import Blueprint, jsonify
+from models import User
+
+users_bp = Blueprint('users', __name__)
+
+@users_bp.route('/users', methods=['GET'])
+def list_users():
+    users = User.query.all()
+    return jsonify([{"id": u.id, "name": u.name, "email": u.email} for u in users])
+
+@users_bp.route('/users/<int:user_id>', methods=['GET'])
+def get_user(user_id):
+    user = User.query.get_or_404(user_id)
+    return jsonify({"id": user.id, "name": user.name, "email": user.email})
```

Only `src/api/users.py` appears in the diff. `src/api/auth.py` is absent.

## 8. git status after commit

```
On branch master
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   src/api/auth.py

no changes added to commit (use "git add" and/or "git commit -a")
```

`src/api/auth.py` still has unstaged changes, exactly as expected.

## 9. Compliance

| Check | Result |
|-------|--------|
| Only staged file committed (users.py) | PASS |
| auth.py left out of commit | PASS |
| auth.py mentioned as having unstaged changes | PASS |
| No wildcard add (`git add -A` / `git add .`) used | PASS |
| Confirmation requested before executing | PASS |
| No Claude attribution / co-author lines in commit | PASS |
| Commit message in imperative mood | PASS |
