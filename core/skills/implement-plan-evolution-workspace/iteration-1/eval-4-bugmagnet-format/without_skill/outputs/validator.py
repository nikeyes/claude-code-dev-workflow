def validate_email(email):
    return "@" in email


def validate_username(username):
    if not username:
        return False
    if len(username) < 3 or len(username) > 20:
        return False
    return all(c.isalnum() or c == "_" for c in username)
