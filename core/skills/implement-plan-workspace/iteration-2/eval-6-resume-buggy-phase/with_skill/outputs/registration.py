import re
from datetime import datetime, timezone


def validate_email(email):
    if not email or not isinstance(email, str):
        raise ValueError("Email is required")
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return True


def validate_age(age):
    if age is None:
        raise ValueError("Age is required")
    if not isinstance(age, int):
        raise ValueError("Age must be an integer")
    if age < 18 or age > 120:
        raise ValueError("Age must be between 18 and 120")
    return True


def validate_username(username):
    if not username or not isinstance(username, str):
        raise ValueError("Username is required")
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters")
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValueError("Username can only contain letters, numbers, and underscores")
    return True


def register(username, email, age):
    validate_username(username)
    validate_email(email)
    validate_age(age)
    return {
        "username": username,
        "email": email,
        "age": age,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }


def batch_register(users):
    succeeded = []
    failed = []
    for user in users:
        try:
            result = register(user["username"], user["email"], user["age"])
            succeeded.append(result)
        except (ValueError, KeyError) as e:
            failed.append({**user, "error": str(e)})
    return {"succeeded": succeeded, "failed": failed}
