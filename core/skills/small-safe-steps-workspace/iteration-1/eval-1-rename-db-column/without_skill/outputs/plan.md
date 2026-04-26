# Plan: Rename `email` column to `email_address` in the users table

## Context

The `users` table has an `email` column defined in `_setup_schema()`. Several methods
reference this column name in SQL queries and in Python code that reads result dictionaries.
The test suite also accesses `user["email"]` directly. All of these touch points must be
updated in a single coherent change.

---

## Step 1 — Update the schema definition

**File**: `user_service.py`, method `_setup_schema`

Change the `CREATE TABLE` statement so the column is declared as `email_address` instead
of `email`.

```sql
-- before
email TEXT UNIQUE NOT NULL,

-- after
email_address TEXT UNIQUE NOT NULL,
```

---

## Step 2 — Update `get_user_by_email`

**File**: `user_service.py`, method `get_user_by_email`

Update the `WHERE` clause to use the new column name.

```sql
-- before
SELECT * FROM users WHERE email = ?

-- after
SELECT * FROM users WHERE email_address = ?
```

---

## Step 3 — Update `create_user`

**File**: `user_service.py`, method `create_user`

Update the `INSERT` statement column list.

```sql
-- before
INSERT INTO users (username, email, role) VALUES (?, ?, ?)

-- after
INSERT INTO users (username, email_address, role) VALUES (?, ?, ?)
```

---

## Step 4 — Update `update_email`

**File**: `user_service.py`, method `update_email`

Update the `SET` clause to use the new column name.

```sql
-- before
UPDATE users SET email = ? WHERE id = ?

-- after
UPDATE users SET email_address = ? WHERE id = ?
```

---

## Step 5 — Update tests that read `user["email"]`

**File**: `test_user_service.py`

Two tests read the `email` key from a returned dict. Because `sqlite3.Row` uses actual
column names as keys, those accesses must be updated to `email_address`.

- `test_create_and_get_user`: change `user["email"]` → `user["email_address"]`
- `test_update_email`: change `updated["email"]` → `updated["email_address"]`

---

## Step 6 — Run the tests

```bash
pytest test_user_service.py -v
```

All 8 tests should pass with no failures.

---

## Summary of all changes

| Location | Change |
|---|---|
| `_setup_schema` | `email TEXT` → `email_address TEXT` |
| `get_user_by_email` | `WHERE email = ?` → `WHERE email_address = ?` |
| `create_user` | `(username, email, role)` → `(username, email_address, role)` |
| `update_email` | `SET email = ?` → `SET email_address = ?` |
| `test_create_and_get_user` | `user["email"]` → `user["email_address"]` |
| `test_update_email` | `updated["email"]` → `updated["email_address"]` |
