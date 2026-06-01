def validate_email(email):
    return "@" in email


def validate_username(username):
    if not username:
        return False
    if not (3 <= len(username) <= 20):
        return False
    for c in username:
        if not (c.isalnum() or c == "_"):
            return False
    return True
